package com.safenet.vpn

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.provider.Settings
import android.util.Log
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import kotlinx.coroutines.*
import java.io.File

class MainActivity : FlutterActivity() {

    private val CHANNEL          = "com.safenet.vpn/methods"
    private val INSTALLER_CHANNEL = "com.safenet.safenet_vpn/installer"
    private val SINGBOX_CHANNEL   = "com.safenet.vpn/singbox"
    private val VPN_PERMISSION_CODE = 1001
    private val VPN_PERM_SINGBOX    = 1002
    private val TAG = "MainActivity"

    // Сохраняем pending-запрос пока ждём разрешения VPN
    private var pendingResult: MethodChannel.Result? = null
    private var pendingOp: String? = null
    private var pendingConfig: String? = null
    private var pendingCountry: String? = null
    private var pendingByeDPI: Map<String, Any>? = null

    // Singbox pending
    private var pendingSingboxConfig: String? = null
    private var pendingSingboxResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        Log.i(TAG, "configureFlutterEngine called - SafeNet VPN initializing")

        // ── Hiddify Installer Channel ────────────────────────────────────
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, INSTALLER_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "isHiddifyInstalled" -> {
                        val installed = try {
                            packageManager.getPackageInfo("app.hiddify.com", 0)
                            true
                        } catch (e: Exception) { false }
                        result.success(installed)
                    }
                    "installApk" -> {
                        val path = call.argument<String>("path")
                        if (path == null) {
                            result.error("NO_PATH", "path is required", null)
                            return@setMethodCallHandler
                        }
                        try {
                            val file = File(path)
                            val uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                                FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
                            } else {
                                Uri.fromFile(file)
                            }
                            val intent = Intent(Intent.ACTION_VIEW).apply {
                                setDataAndType(uri, "application/vnd.android.package-archive")
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }
                            startActivity(intent)
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("INSTALL_ERROR", e.message, null)
                        }
                    }
                    else -> result.notImplemented()
                }
            }

        // ── Singbox (Iran Mode) Channel ───────────────────────────────
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, SINGBOX_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "start" -> {
                        val cfg = call.argument<String>("config")
                        if (cfg.isNullOrBlank()) {
                            result.error("NO_CONFIG", "config required", null)
                            return@setMethodCallHandler
                        }
                        val prepare = android.net.VpnService.prepare(this)
                        if (prepare != null) {
                            pendingSingboxConfig = cfg
                            pendingSingboxResult = result
                            startActivityForResult(prepare, VPN_PERM_SINGBOX)
                        } else {
                            launchSingbox(cfg, result)
                        }
                    }
                    "stop" -> {
                        startService(Intent(this, SingboxVpnService::class.java).apply {
                            action = SingboxVpnService.ACTION_STOP
                        })
                        result.success(true)
                    }
                    "status" -> result.success(mapOf(
                        "running" to SingboxVpnService.isRunning,
                        "error"   to (SingboxVpnService.lastError ?: "")
                    ))
                    else -> result.notImplemented()
                }
            }

        // ── VPN Channel ──────────────────────────────────────────────────────
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {

                    "startHybrid" -> {
                        val config = call.argument<String>("config") ?: ""
                        val byeDPI = mapOf(
                            "split" to (call.argument<Int>("split") ?: 2),
                            "desync" to (call.argument<String>("desync") ?: "fake"),
                            "fake_ttl" to (call.argument<Int>("fake_ttl") ?: 8)
                        )
                        val desyncMode = byeDPI["desync"] as? String ?: "fake"
                        Log.i(TAG, "[USER MODE] Hybrid selected — WG + ByeDPI desync=$desyncMode")
                        startVpnWithPermission("hybrid", config, "XX", byeDPI, result)
                    }

                    "startAmnezia" -> {
                        val config = call.argument<String>("config") ?: ""
                        Log.i(TAG, "[USER MODE] AmneziaWG selected — pure WireGuard only")
                        startVpnWithPermission("amnezia", config, "XX", emptyMap(), result)
                    }

                    "startAuto" -> {
                        val config = call.argument<String>("config") ?: ""
                        val country = call.argument<String>("country") ?: "XX"
                        val byeDPI = mapOf(
                            "split" to (call.argument<Int>("split") ?: 2),
                            "desync" to (call.argument<String>("desync") ?: "fake"),
                            "fake_ttl" to (call.argument<Int>("fake_ttl") ?: 8)
                        )
                        Log.i(TAG, "[USER MODE] Stealth/Auto selected — country=$country")
                        startVpnWithPermission("auto", config, country, byeDPI, result)
                    }

                    "stop" -> {
                        CoroutineScope(Dispatchers.IO).launch {
                            StealthVPNService.stop(applicationContext)
                            withContext(Dispatchers.Main) {
                                result.success(mapOf("status" to "disconnected"))
                            }
                        }
                    }

                    "getStatus" -> {
                        val (rx, tx) = StealthVPNService.getTunnelStats()
                        result.success(mapOf(
                            "mode"          to StealthVPNService.getCurrentMode().name,
                            "proxy"         to StealthVPNService.getProxyAddress(),
                            "byedpi_running" to ByeDPIService.isRunning(),
                            "rx_bytes"      to rx,
                            "tx_bytes"      to tx
                        ))
                    }

                    "getAndroidId" -> {
                        Log.i(TAG, "getAndroidId method called from Dart")
                        try {
                            val androidId = Settings.Secure.getString(
                                contentResolver,
                                Settings.Secure.ANDROID_ID
                            ) ?: ""
                            Log.i(TAG, "Returning Android ID: $androidId")
                            result.success(androidId)
                        } catch (e: Exception) {
                            Log.e(TAG, "Error getting Android ID", e)
                            result.error("ANDROID_ID_ERROR", e.message, null)
                        }
                    }

                    else -> result.notImplemented()
                }
            }
    }

    /**
     * Проверяем разрешение VPN.
     * Если нет — показываем системный диалог, ждём onActivityResult.
     */
    private fun startVpnWithPermission(
        op: String,
        config: String,
        country: String,
        byeDPI: Map<String, Any>,
        result: MethodChannel.Result
    ) {
        val prepareIntent = VpnService.prepare(this)
        if (prepareIntent != null) {
            Log.i(TAG, "VPN permission required, showing dialog")
            pendingResult  = result
            pendingOp      = op
            pendingConfig  = config
            pendingCountry = country
            pendingByeDPI  = byeDPI
            startActivityForResult(prepareIntent, VPN_PERMISSION_CODE)
        } else {
            Log.i(TAG, "VPN permission already granted, connecting...")
            launchVpnConnection(op, config, country, byeDPI, result)
        }
    }

    private fun launchSingbox(cfg: String, result: MethodChannel.Result) {
        startService(Intent(this, SingboxVpnService::class.java).apply {
            action = SingboxVpnService.ACTION_START
            putExtra(SingboxVpnService.EXTRA_OUTBOUNDS_JSON, cfg)
        })
        result.success(mapOf("status" to "starting"))
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == VPN_PERM_SINGBOX) {
            val cfg = pendingSingboxConfig
            val res = pendingSingboxResult
            pendingSingboxConfig = null; pendingSingboxResult = null
            if (resultCode == Activity.RESULT_OK && cfg != null && res != null) {
                launchSingbox(cfg, res)
            } else {
                res?.error("VPN_PERMISSION_DENIED", "User denied VPN permission", null)
            }
        }
        if (requestCode == VPN_PERMISSION_CODE) {
            val res = pendingResult ?: return
            if (resultCode == Activity.RESULT_OK) {
                Log.i(TAG, "VPN permission granted")
                launchVpnConnection(
                    pendingOp ?: "auto",
                    pendingConfig ?: "",
                    pendingCountry ?: "XX",
                    pendingByeDPI ?: emptyMap(),
                    res
                )
            } else {
                Log.w(TAG, "VPN permission denied by user")
                res.error("VPN_PERMISSION_DENIED", "User denied VPN permission", null)
            }
            clearPending()
        }
    }

    /**
     * Запускает подключение в корутине IO (GoBackend.setState блокирует до установки туннеля).
     * result.success/error вызываются на Main-потоке после завершения.
     */
    private fun launchVpnConnection(
        op: String,
        config: String,
        country: String,
        byeDPI: Map<String, Any>,
        result: MethodChannel.Result
    ) {
        CoroutineScope(Dispatchers.Main).launch {
            try {
                withContext(Dispatchers.IO) {
                    when (op) {
                        "hybrid"  -> StealthVPNService.startHybrid(applicationContext, config, byeDPI)
                        "amnezia" -> StealthVPNService.startAmneziaOnly(applicationContext, config)
                        else      -> StealthVPNService.startAuto(applicationContext, country, config, byeDPI)
                    }
                }
                result.success(mapOf(
                    "status" to "connected",
                    "mode"   to StealthVPNService.getCurrentMode().name,
                    "proxy"  to StealthVPNService.getProxyAddress()
                ))
            } catch (e: Exception) {
                Log.e(TAG, "VPN connection failed: ${e.message}", e)
                result.error("VPN_ERROR", e.message ?: "Unknown error", null)
            }
        }
    }

    private fun clearPending() {
        pendingResult  = null
        pendingOp      = null
        pendingConfig  = null
        pendingCountry = null
        pendingByeDPI  = null
    }
}
