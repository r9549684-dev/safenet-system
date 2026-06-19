package com.safenet.vpn

import android.app.Application

// Минимальная заглушка для обеспечения успешной компиляции.
// Вся логика инициализации остается в MainActivity.
class SafeVPNApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}