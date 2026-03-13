package com.safenet.vpn

import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import org.amnezia.awg.backend.GoBackend
import org.amnezia.awg.backend.Tunnel
import org.amnezia.awg.config.Config
import java.io.BufferedReader
import java.io.StringReader

/**
 * AmneziaWGService — реальный WireGuard/AmneziaWG туннель через GoBackend (JNI + libwg.so).
 * GoBackend внутри управляет GoBackend.VpnService (задекларирован в AAR-манифесте).
 */
class AmneziaWGService(private val context: Context) {

    companion object {
        private const val TAG = "AmneziaWGService"
    }

    private val backend = GoBackend(context)
    private var activeTunnel: SafeNetTunnel? = null

    suspend fun connect(configString: String) {
        withContext(Dispatchers.IO) {
            Log.i(TAG, "Parsing WireGuard config (${configString.length} chars)")
            val config = Config.parse(BufferedReader(StringReader(configString)))
            val tunnel = SafeNetTunnel("safenet0")
            activeTunnel = tunnel
            Log.i(TAG, "Starting AmneziaWG tunnel via GoBackend...")
            backend.setState(tunnel, Tunnel.State.UP, config)
            Log.i(TAG, "AmneziaWG tunnel UP")
        }
    }

    suspend fun disconnect() {
        val tunnel = activeTunnel ?: return
        activeTunnel = null
        withContext(Dispatchers.IO) {
            try {
                backend.setState(tunnel, Tunnel.State.DOWN, null)
                Log.i(TAG, "AmneziaWG tunnel DOWN")
            } catch (e: Exception) {
                Log.e(TAG, "Disconnect error: ${e.message}")
            }
        }
    }

    fun isConnected(): Boolean = activeTunnel != null

    /** Возвращает (rxBytes, txBytes) из GoBackend.getStatistics(). */
    fun getStatistics(): Pair<Long, Long> {
        val t = activeTunnel ?: return Pair(0L, 0L)
        return try {
            val stats = backend.getStatistics(t)
            Pair(stats.totalRx(), stats.totalTx())
        } catch (e: Exception) {
            Log.w(TAG, "getStatistics failed: ${e.message}")
            Pair(0L, 0L)
        }
    }
}

/** Реализация Tunnel-интерфейса для AmneziaWG GoBackend. */
class SafeNetTunnel(private val name: String) : Tunnel {
    override fun getName(): String = name
    override fun onStateChange(newState: Tunnel.State) {
        android.util.Log.i("SafeNetTunnel", "Tunnel state changed: $newState")
    }
}
