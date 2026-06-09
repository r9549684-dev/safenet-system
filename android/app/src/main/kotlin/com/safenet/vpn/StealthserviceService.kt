package com.safenet.vpn

import android.content.Context
import android.content.Intent
import android.util.Log
import kotlinx.coroutines.*

/**
 * Управляет двумя слоями:
 * 1. AmneziaWG — зашифрованный туннель (реальный GoBackend)
 * 2. ByeDPI — SOCKS5-прокси поверх туннеля для обхода DPI
 */
object StealthVPNService {

    private const val TAG = "StealthVPNService"

    /** Режим работы оркестратора */
    enum class Mode { AMNEZIA_ONLY, BYEDPI_OVER_AMNEZIA, BYEDPI_ONLY }

    /** Режим VPN для FallbackController */
    enum class VPNMode { STEALTH, OBFS, BYEDPI, VLESS }

    private var currentMode: Mode = Mode.AMNEZIA_ONLY
    private var amneziaService: AmneziaWGService? = null

    /**
     * Запуск в режиме AmneziaWG + ByeDPI (рекомендуется для TR/EG/AE/SA).
     * Suspend — GoBackend.setState() блокирует поток до установки туннеля.
     */
    suspend fun startHybrid(
        context: Context,
        wgConfig: String,
        byeDPIConfig: Map<String, Any>
    ) {
        val desync = byeDPIConfig["desync"] as? String ?: "fake"
        val split  = byeDPIConfig["split"]  as? Int    ?: 2
        Log.i(TAG, "Starting HYBRID mode: AmneziaWG + ByeDPI [desync=$desync, split=$split]")

        amneziaService = AmneziaWGService(context)
        amneziaService!!.connect(wgConfig)
        Log.i(TAG, "AmneziaWG tunnel UP")

        val byeDPIIntent = Intent(context, ByeDPIService::class.java).apply {
            putExtra("split_position", byeDPIConfig["split"] as? Int ?: 2)
            putExtra("desync_mode", byeDPIConfig["desync"] as? String ?: "fake")
            putExtra("fake_ttl", byeDPIConfig["fake_ttl"] as? Int ?: 8)
        }
        context.startService(byeDPIIntent)
        Log.i(TAG, "ByeDPI SOCKS5 proxy UP on port ${ByeDPIService.PROXY_PORT}")

        currentMode = Mode.BYEDPI_OVER_AMNEZIA
    }

    /**
     * Только AmneziaWG (для стран с умеренной блокировкой: PK, ID).
     */
    suspend fun startAmneziaOnly(context: Context, wgConfig: String) {
        Log.i(TAG, "Starting AMNEZIA-ONLY mode: pure WireGuard tunnel, no ByeDPI")
        amneziaService = AmneziaWGService(context)
        amneziaService!!.connect(wgConfig)
        currentMode = Mode.AMNEZIA_ONLY
    }

    /**
     * Автоматический выбор режима по стране.
     */
    suspend fun startAuto(
        context: Context,
        countryCode: String,
        wgConfig: String,
        byeDPIConfig: Map<String, Any>
    ) {
        val strictCountries = setOf("TR", "EG", "AE", "SA", "IR", "CN", "RU")
        Log.i(TAG, "Starting AUTO mode: country=$countryCode, strictList=${countryCode.uppercase() in strictCountries}")
        if (countryCode.uppercase() in strictCountries) {
            startHybrid(context, wgConfig, byeDPIConfig)
        } else {
            startAmneziaOnly(context, wgConfig)
        }
    }

    suspend fun stop(context: Context) {
        amneziaService?.disconnect()   // suspend — ждём полного DOWN перед освобождением
        amneziaService = null

        val intent = Intent(context, ByeDPIService::class.java)
        context.stopService(intent)

        currentMode = Mode.AMNEZIA_ONLY
        Log.i(TAG, "All VPN layers stopped")
    }

    fun getCurrentMode() = currentMode

    /** Возвращает (rxBytes, txBytes) активного туннеля. */
    fun getTunnelStats(): Pair<Long, Long> =
        amneziaService?.getStatistics() ?: Pair(0L, 0L)

    fun getProxyAddress(): String? {
        return if (currentMode == Mode.BYEDPI_OVER_AMNEZIA && ByeDPIService.isRunning()) {
            "socks5://127.0.0.1:${ByeDPIService.PROXY_PORT}"
        } else null
    }
}
