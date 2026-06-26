package com.safenet.vpn

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * SingboxProxyService — тестовый HTTP proxy на базе sing-box (без VpnService).
 *
 * Назначение: E2E тест VLESS+Reality без необходимости JNI protect().
 * Sing-box запускается как subprocess и слушает mixed (HTTP+SOCKS5) на 127.0.0.1:2080.
 * Flutter клиент отправляет запросы через proxy или через adb reverse.
 *
 * Для production используется SingboxVpnService (с FFI libcore + JNI protect).
 */
class SingboxProxyService : Service() {

    companion object {
        private const val TAG = "SingboxProxyService"
        private const val NOTIF_ID = 43
        private const val CHANNEL_ID = "safenet_proxy"
        private const val PROXY_PORT = 2080
        const val ACTION_START = "com.safenet.vpn.PROXY_START"
        const val ACTION_STOP = "com.safenet.vpn.PROXY_STOP"
        const val EXTRA_OUTBOUNDS_JSON = "outbounds_json"

        @Volatile var isRunning: Boolean = false
            private set
    }

    private var singboxProc: Process? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return when (intent?.action) {
            ACTION_STOP  -> { stopProxy(); stopSelf(); START_NOT_STICKY }
            ACTION_START -> {
                val json = intent.getStringExtra(EXTRA_OUTBOUNDS_JSON)
                if (json.isNullOrBlank()) {
                    Log.e(TAG, "No config provided")
                    stopSelf()
                    START_NOT_STICKY
                } else {
                    showNotification()
                    Thread { startProxy(json) }.start()
                    START_STICKY
                }
            }
            else -> START_NOT_STICKY
        }
    }

    override fun onDestroy() { stopProxy(); super.onDestroy() }

    private fun startProxy(outboundsJson: String) {
        try {
            val singboxBin = getBinary("libsingbox.so")
            val config = buildProxyConfig(outboundsJson)
            val configFile = File(filesDir, "singbox_proxy.json")
            configFile.writeText(config)
            Log.d(TAG, "Proxy config written: ${configFile.absolutePath}")

            val pb = ProcessBuilder(singboxBin.absolutePath, "run", "-c", configFile.absolutePath)
                .redirectErrorStream(true)
                .directory(filesDir)
            pb.environment()["ENABLE_DEPRECATED_LEGACY_DNS_SERVERS"] = "true"
            pb.environment()["ENABLE_DEPRECATED_MISSING_DOMAIN_RESOLVER"] = "true"
            singboxProc = pb.start()

            val proc = singboxProc!!
            Thread {
                try {
                    proc.inputStream.bufferedReader().use { r ->
                        r.lines().forEach { Log.d("SingboxProxyLog", it) }
                    }
                } catch (_: Exception) {}
            }.start()

            isRunning = true
            Log.i(TAG, "sing-box proxy started on 127.0.0.1:$PROXY_PORT")

            // Wait for process
            val exitCode = proc.waitFor()
            Log.w(TAG, "sing-box exited with code $exitCode")
            isRunning = false

        } catch (e: Exception) {
            Log.e(TAG, "Proxy start failed: ${e.message}", e)
            isRunning = false
        }
    }

    private fun stopProxy() {
        singboxProc?.destroy()
        singboxProc = null
        isRunning = false
        Log.i(TAG, "Proxy stopped")
    }

    private fun getBinary(name: String): File {
        val libDir = applicationInfo.nativeLibraryDir ?: throw IllegalStateException("No nativeLibraryDir")
        val binary = File(libDir, name)
        if (!binary.exists()) throw IllegalStateException("Binary not found: ${binary.absolutePath}")
        return binary
    }

    /**
     * Build proxy-only config: mixed inbound (HTTP+SOCKS5) + VLESS outbound.
     * No TUN, no tun2socks, no route rules for local traffic.
     */
    private fun buildProxyConfig(outboundsJson: String): String {
        val api = JSONObject(outboundsJson)

        // HTTP/SOCKS5 mixed inbound
        api.put("inbounds", JSONArray().apply {
            put(JSONObject().apply {
                put("type", "mixed")
                put("tag", "mixed-in")
                put("listen", "127.0.0.1")
                put("listen_port", PROXY_PORT)
            })
        })

        // Clean outbounds: strip transport.type=tcp (FATAL in sing-box 1.12+)
        val outbounds = api.optJSONArray("outbounds") ?: JSONArray()
        for (i in 0 until outbounds.length()) {
            val ob = outbounds.getJSONObject(i)
            val tr = ob.optJSONObject("transport")
            if (tr != null && tr.optString("type") == "tcp") {
                ob.remove("transport")
            }
        }
        // Add direct outbound if missing
        var hasDirect = false
        for (i in 0 until outbounds.length())
            if (outbounds.getJSONObject(i).optString("type") == "direct") hasDirect = true
        if (!hasDirect) outbounds.put(JSONObject().apply {
            put("type", "direct"); put("tag", "direct")
        })
        api.put("outbounds", outbounds)

        // Proxy-friendly route: all → proxy outbound (final)
        val proxyTag = run {
            val proxyTypes = setOf("vless","vmess","shadowsocks","trojan","hysteria","hysteria2","tuic")
            var found = "direct"
            for (i in 0 until outbounds.length()) {
                val ob = outbounds.getJSONObject(i)
                if (ob.optString("type") in proxyTypes) {
                    found = ob.optString("tag", "direct"); break
                }
            }
            found
        }

        api.put("route", JSONObject().apply {
            put("rules", JSONArray())
            put("final", proxyTag)
        })

        // DNS: simple
        api.put("dns", JSONObject().apply {
            put("servers", JSONArray().apply {
                put(JSONObject().apply {
                    put("type", "udp"); put("tag", "remote")
                    put("server", "1.1.1.1"); put("server_port", 53)
                })
                put(JSONObject().apply { put("type", "local"); put("tag", "local") })
            })
            put("final", "remote")
        })

        api.put("log", JSONObject().apply { put("level", "info"); put("timestamp", true) })
        Log.d(TAG, "Proxy config built: ${api.toString(2).take(400)}")
        return api.toString(2)
    }

    private fun showNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL_ID, "SafeNet Proxy Test",
                NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
        }
        startForeground(NOTIF_ID,
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("SafeNet VLESS Proxy Test")
                .setContentText("🧪 Proxy mode on 127.0.0.1:$PROXY_PORT")
                .setSmallIcon(android.R.drawable.ic_lock_lock)
                .setOngoing(true).build()
        )
    }
}
