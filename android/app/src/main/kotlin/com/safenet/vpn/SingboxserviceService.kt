package com.safenet.vpn

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import android.system.Os
import android.util.Log
import androidx.core.app.NotificationCompat
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream

/**
 * SingboxVpnService — Iran Mode VPN.
 *
 * Архитектура (правильная для Android):
 *   1. VpnService.Builder.establish() → TUN fd
 *   2. sing-box subprocess: mixed SOCKS5 inbound на 127.0.0.1:2080 + VLESS+Reality outbound
 *   3. tun2socks subprocess: -device fd://0 -proxy socks5://127.0.0.1:2080
 *      (TUN fd передаётся через stdin fd=0: Java ProcessBuilder закрывает все fd>=3 до exec)
 *
 * Трафик: Устройство → TUN fd → tun2socks → SOCKS5 → sing-box → VLESS+Reality → Интернет
 *
 * Бинарники в jniLibs/arm64-v8a/ (extractNativeLibs=true → устанавливаются в nativeLibraryDir):
 *   libsingbox.so   — sing-box
 *   libtun2socks.so — tun2socks
 */
class SingboxVpnService : VpnService() {

    companion object {
        private const val TAG          = "SingboxVpnService"
        private const val NOTIF_ID     = 42
        private const val CHANNEL_ID   = "safenet_iran"
        private const val SOCKS5_PORT  = 2080
        const val ACTION_START         = "com.safenet.vpn.SINGBOX_START"
        const val ACTION_STOP          = "com.safenet.vpn.SINGBOX_STOP"
        const val EXTRA_OUTBOUNDS_JSON = "outbounds_json"

        @Volatile var isRunning: Boolean = false
            private set
        @Volatile var lastError: String? = null
            private set
    }

    private var tunFd:         ParcelFileDescriptor? = null
    private var dupTunFd:      ParcelFileDescriptor? = null
    private var singboxProc:   Process?              = null
    private var tun2socksProc: Process?              = null

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return when (intent?.action) {
            ACTION_STOP  -> { stopAll(); START_NOT_STICKY }
            ACTION_START -> {
                val json = intent.getStringExtra(EXTRA_OUTBOUNDS_JSON)
                if (json.isNullOrBlank()) {
                    lastError = "No config provided"; stopSelf(); START_NOT_STICKY
                } else {
                    showNotification()
                    Thread { startVpn(json) }.start()
                    START_STICKY
                }
            }
            else -> START_NOT_STICKY
        }
    }

    override fun onDestroy() { stopAll(); super.onDestroy() }
    override fun onRevoke()  { stopAll(); stopSelf() }

    // ── Core logic ────────────────────────────────────────────────────────────

    private fun startVpn(outboundsJson: String) {
        try {
            lastError = null

            // 1. Бинарники из nativeLibraryDir (SELinux-разрешённая директория)
            val singboxBin   = getBinary("libsingbox.so")
            val tun2socksBin = getBinary("libtun2socks.so")

            // 2. Android VPN TUN
            // CRITICAL FIX: Уменьшен MTU для overhead туннеля (VLESS+Reality+Fragment)
            // CRITICAL FIX: Добавлен network monitoring для отслеживания смены сети
            val builder = Builder()
                .setSession("SafeNet Iran")
                .setMtu(1400)  // Уменьшен с 1500 для overhead туннеля
                .addAddress("10.9.8.1", 30)
                .addDnsServer("1.1.1.1")
                .addDnsServer("8.8.8.8")
            
            // CRITICAL FIX: Исключаем само приложение из VPN (UI процесс)
            try { builder.addDisallowedApplication(packageName) } catch (_: Exception) {}
            
            // CRITICAL FIX: Split tunneling — исключаем IP сервера из VPN routing
            // Вместо addRoute("0.0.0.0", 0) добавляем все маршруты КРОМЕ IP серверов
            // Это гарантирует, что трафик sing-box к серверу идёт через физическую сеть
            // CRITICAL FIX: Исключаем оба IP одновременно — Master Node и Frontend Gateway
            addRoutesExcludingServers(builder, listOf("38.180.253.219", "38.244.136.233"))
            
            // CRITICAL FIX: IPv6 только если поддерживается
            if (hasIPv6Connectivity()) {
                try {
                    builder.addRoute("::", 0)
                } catch (_: Exception) {}
            }

            val pfd = builder.establish()
                ?: throw IllegalStateException("VPN establish() returned null")
            tunFd = pfd

            // Dup TUN fd: нужен для передачи в tun2socks через stdin (fd 0).
            // Java ProcessBuilder закрывает все fd >= 3 перед exec() через closeDescriptors().
            // Поэтому fd//N не работает. Решение: dup2(tunFd, 0) → tun2socks -device fd://0.
            val dup = ParcelFileDescriptor.dup(pfd.fileDescriptor)
            dupTunFd = dup
            Log.d(TAG, "TUN pfd.fd=${pfd.fd}, dup.fd=${dup.fd}")

            // 3. sing-box config: mixed SOCKS5 inbound + outbounds из API
            val config     = buildSingboxConfig(outboundsJson)
            val configFile = File(filesDir, "singbox_run.json")
            configFile.writeText(config)
            Log.d(TAG, "sing-box config written")

            // 4. Запуск sing-box (SOCKS5 прокси на 127.0.0.1:$SOCKS5_PORT)
            val sbPb = ProcessBuilder(singboxBin.absolutePath, "run", "-c", configFile.absolutePath)
                .redirectErrorStream(true).directory(filesDir)
            sbPb.environment()["ENABLE_DEPRECATED_LEGACY_DNS_SERVERS"]         = "true"
            sbPb.environment()["ENABLE_DEPRECATED_MISSING_DOMAIN_RESOLVER"]     = "true"
            singboxProc = sbPb.start()
            val sbProc = singboxProc!!
            Thread {
                try { sbProc.inputStream.bufferedReader().use { r ->
                    r.lines().forEach { Log.d("SingboxLog", it) }
                }} catch (_: Exception) {}
            }.start()

            Log.i(TAG, "sing-box started, waiting 1.5s for SOCKS5 to be ready...")
            Thread.sleep(1500)

            if (!sbProc.isAlive) {
                throw IllegalStateException("sing-box exited prematurely (code=${sbProc.exitValue()})")
            }

            // 5. Запуск tun2socks: TUN fd → SOCKS5
            //
            // Проблема: Java ProcessBuilder закрывает все fd >= 3 в дочернем процессе
            //           перед exec() (closeDescriptors()). Передать fd//N не получится.
            //
            // Решение: dup2(tunFd → fd 0), ProcessBuilder.redirectInput(INHERIT).
            //          Дочерний процесс унаследует fd 0 = TUN device.
            //          Передаём tun2socks -device fd://0.
            //          После fork+start восстанавливаем fd 0 родителя → /dev/null.
            Os.dup2(dup.fileDescriptor, 0)   // fd 0 текущего процесса = TUN device

            val t2sPb = ProcessBuilder(
                tun2socksBin.absolutePath,
                "-device", "fd://0",             // fd 0 унаследован = TUN
                "-proxy",  "socks5://127.0.0.1:$SOCKS5_PORT",
                "-loglevel", "info"
            ).redirectInput(ProcessBuilder.Redirect.INHERIT)  // НЕ переписывать fd 0
             .redirectErrorStream(true).directory(filesDir)

            tun2socksProc = t2sPb.start()

            // Восстанавливаем fd 0 родителя (дочерний уже сделал fork, имеет свою копию)
            try { FileInputStream("/dev/null").use { Os.dup2(it.fd, 0) } } catch (_: Exception) {}

            val t2sProc = tun2socksProc!!
            Thread {
                try { t2sProc.inputStream.bufferedReader().use { r ->
                    r.lines().forEach { Log.d("Tun2socksLog", it) }
                }} catch (_: Exception) {}
            }.start()

            Log.i(TAG, "tun2socks started: fd://0 (TUN via stdin) → socks5://127.0.0.1:$SOCKS5_PORT")
            isRunning = true

            // Ждём tun2socks (главный сторож, sing-box — фоновый)
            val exitCode = t2sProc.waitFor()
            Log.i(TAG, "tun2socks exited: $exitCode")
            if (exitCode != 0) lastError = "tun2socks exited: $exitCode"

        } catch (e: Exception) {
            lastError = e.message ?: "Unknown error"
            Log.e(TAG, "startVpn failed: ${e.message}", e)
        } finally {
            isRunning = false
            stopAll()
            stopSelf()
        }
    }

    private fun stopAll() {
        isRunning = false
        tun2socksProc?.destroy(); tun2socksProc = null
        singboxProc?.destroy();   singboxProc   = null
        try { dupTunFd?.close() } catch (_: Exception) {}; dupTunFd = null
        try { tunFd?.close()    } catch (_: Exception) {}; tunFd    = null
        Log.i(TAG, "Stopped")
    }

    // ── Binary location ───────────────────────────────────────────────────────

    private fun getBinary(libName: String): File {
        val bin = File(applicationInfo.nativeLibraryDir, libName)
        if (!bin.exists()) throw IllegalStateException(
            "$libName not found at ${bin.absolutePath}. Iran build required (build_iran.ps1)."
        )
        Log.i(TAG, "$libName → ${bin.absolutePath} (${bin.length() / 1_000_000} MB)")
        return bin
    }

    // ── sing-box config (mixed SOCKS5 inbound, NO tun inbound) ─────────────────────

    /**
     * Строим рабочий конфиг для sing-box 1.12+:
     *  - inbounds → наш mixed SOCKS5 на 127.0.0.1:2080
     *  - outbounds → API outbounds, очищенные от transport.type="tcp" (FATAL в 1.12+)
     *  - route     → минимальный (private→direct, остальное→прокси);
     *                geoip/geosite удалены в 1.12.0, API-route заменяем полностью
     *  - dns       → простой (1.1.1.1 UDP + local); API-dns может содержать geosite-rules
     */
    private fun buildSingboxConfig(outboundsJson: String): String {
        val api = JSONObject(outboundsJson)

        // 1. Заменяем inbound: mixed SOCKS5
        api.put("inbounds", JSONArray().apply {
            put(JSONObject().apply {
                put("type", "mixed"); put("tag", "mixed-in")
                put("listen", "127.0.0.1"); put("listen_port", SOCKS5_PORT)
            })
        })

        // 2. Очищаем outbounds: transport.type="tcp" — FATAL в sing-box 1.12+
        val outbounds = api.optJSONArray("outbounds") ?: JSONArray()
        for (i in 0 until outbounds.length()) {
            val ob = outbounds.getJSONObject(i)
            val tr = ob.optJSONObject("transport")
            if (tr != null && tr.optString("type") == "tcp") {
                ob.remove("transport")
                Log.d(TAG, "Stripped tcp transport from outbound[$i] tag=${ob.optString("tag")}")
            }
        }
        var hasDirect = false
        for (i in 0 until outbounds.length())
            if (outbounds.getJSONObject(i).optString("type") == "direct") hasDirect = true
        if (!hasDirect) outbounds.put(JSONObject().apply { put("type","direct"); put("tag","direct") })
        api.put("outbounds", outbounds)

        // 3. Определяем тег главного outbound
        //    Берём из API route.final, иначе первый прокси-outbound
        val apiRoute  = api.optJSONObject("route")
        val finalTag  = apiRoute?.optString("final")?.takeIf { it.isNotBlank() }
            ?: run {
                val proxyTypes = setOf("vless","vmess","shadowsocks","trojan",
                                       "hysteria","hysteria2","tuic","wireguard")
                var found = "direct"
                for (i in 0 until outbounds.length()) {
                    val ob = outbounds.getJSONObject(i)
                    if (ob.optString("type") in proxyTypes) {
                        found = ob.optString("tag", "direct"); break
                    }
                }
                found
            }
        Log.d(TAG, "Final outbound tag: $finalTag")

        // 4. Заменяем route полностью:
        //    geoip/geosite удалены в sing-box 1.12.0 — API-route использовать нельзя
        // CRITICAL FIX: Убраны auto_detect_interface=true и default_mark=0x10000
        // auto_detect_interface усугубляет loopback (определяет tun0 как основной)
        // default_mark не работает без root (требует ip rule add fwmark)
        api.put("route", JSONObject().apply {
            put("rules", JSONArray().apply {
                put(JSONObject().apply {
                    put("ip_cidr", JSONArray().apply {
                        put("10.0.0.0/8");      put("172.16.0.0/12")
                        put("192.168.0.0/16");  put("127.0.0.0/8")
                        put("fc00::/7");         put("fe80::/10")
                    })
                    put("outbound", "direct")
                })
                // CRITICAL FIX: IP сервера — напрямую (дополнительная защита от loopback)
                // CRITICAL FIX: Исключаем оба IP — Master Node и Frontend Gateway
                put(JSONObject().apply {
                    put("ip_cidr", JSONArray().apply {
                        put("38.180.253.219/32")  // Master Node
                        put("38.244.136.233/32")  // Frontend Gateway
                    })
                    put("outbound", "direct")
                })
            })
            put("final", finalTag)
            // CRITICAL FIX: auto_detect_interface=false (не определяем интерфейс автоматически)
            put("auto_detect_interface", false)
            // CRITICAL FIX: default_mark убран — не работает без root
            put("default_domain_resolver", "remote")  // обязателен в 1.12+ при >1 DNS сервере
        })

        // 5. Заменяем DNS полностью:
        //    API-dns может иметь geosite-rules (тоже удалены в 1.12+)
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

        // 6. log
        if (!api.has("log")) api.put("log", JSONObject().apply { put("level", "info"); put("timestamp", true) })

        Log.d(TAG, "Final sing-box config: ${api.toString(2).take(500)}...")
        return api.toString(2)
    }

    // ── Split tunneling helpers ──────────────────────────────────────────────────

    /**
     * Добавляет маршруты, покрывающие 0.0.0.0/0, КРОМЕ указанных IP серверов.
     * Вместо addRoute("0.0.0.0", 0) добавляем все маршруты КРОМЕ IP серверов.
     * Это гарантирует, что трафик sing-box к серверам идёт через физическую сеть,
     * минуя TUN интерфейс.
     *
     * Алгоритм: покрываем 0.0.0.0/0 набором подсетей, исключая /32 серверов.
     */
    private fun addRoutesExcludingServers(builder: Builder, excludeIps: List<String>) {
        val excludeInts = excludeIps.map { ip ->
            val addr = java.net.InetAddress.getByName(ip)
            val bytes = addr.address
            ((bytes[0].toInt() and 0xFF) shl 24) or
            ((bytes[1].toInt() and 0xFF) shl 16) or
            ((bytes[2].toInt() and 0xFF) shl 8) or
             (bytes[3].toInt() and 0xFF)
        }

        val routes = generateRoutesExcludingMultiple(0, 0, excludeInts)

        var addedCount = 0
        for ((addr, prefix) in routes) {
            try {
                val ipStr = intToIpString(addr)
                builder.addRoute(ipStr, prefix)
                addedCount++
            } catch (e: Exception) {
                Log.w(TAG, "Failed to add route: ${e.message}")
            }
        }

        Log.d(TAG, "Added $addedCount routes excluding ${excludeIps.size} servers: $excludeIps")
    }

    /**
     * Рекурсивно генерирует список подсетей, покрывающих
     * networkAddr/prefix минус несколько excludeIps.
     */
    private fun generateRoutesExcludingMultiple(
        networkAddr: Int,
        prefix: Int,
        excludeIps: List<Int>
    ): List<Pair<Int, Int>> {
        if (prefix == 32) {
            return if (excludeIps.contains(networkAddr)) emptyList()
            else listOf(Pair(networkAddr, 32))
        }

        val mask = if (prefix == 0) 0 else (-1 shl (32 - prefix))
        val networkStart = networkAddr and mask
        val networkEnd = networkStart or mask.inv()

        val anyInRange = excludeIps.any { it in networkStart..networkEnd }
        if (!anyInRange) {
            return listOf(Pair(networkStart, prefix))
        }

        val halfPrefix = prefix + 1
        val halfSize = 1 shl (32 - halfPrefix)
        val firstHalf = networkStart
        val secondHalf = networkStart + halfSize

        return generateRoutesExcludingMultiple(firstHalf, halfPrefix, excludeIps) +
               generateRoutesExcludingMultiple(secondHalf, halfPrefix, excludeIps)
    }

    private fun intToIpString(ip: Int): String {
        return "${(ip shr 24) and 0xFF}.${(ip shr 16) and 0xFF}" +
                ".${(ip shr 8) and 0xFF}.${ip and 0xFF}"
    }

    /**
     * Проверяет наличие IPv6 connectivity.
     * На некоторых устройствах Xiaomi добавление IPv6 route без connectivity вызывает сбои.
     */
    private fun hasIPv6Connectivity(): Boolean {
        return try {
            val cm = getSystemService(android.net.ConnectivityManager::class.java) ?: return false
            val network = cm.activeNetwork ?: return false
            val lp = cm.getLinkProperties(network) ?: return false
            lp.linkAddresses.any { it.address is java.net.Inet6Address }
        } catch (e: Exception) {
            false
        }
    }

    // ── Notification ──────────────────────────────────────────────────────────

    private fun showNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL_ID, "SafeNet Iran VPN",
                NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
        }
        startForeground(NOTIF_ID,
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("SafeNet VPN")
                .setContentText("🇮🇷 Iran Mode — VLESS+Reality")
                .setSmallIcon(android.R.drawable.ic_lock_lock)
                .setOngoing(true).build()
        )
    }
}
