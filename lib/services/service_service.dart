import 'package:flutter/services.dart';

enum VPNMode { hybrid, amneziaOnly, auto }

class VPNConnectionResult {
  final String status;
  final String mode;
  final String? proxyAddress; // socks5://127.0.0.1:1080 если ByeDPI активен

  VPNConnectionResult({
    required this.status,
    required this.mode,
    this.proxyAddress,
  });
}

class VPNService {
  static const _channel = MethodChannel('com.safenet.service/methods');

  /// Гибридный режим: AmneziaWG туннель + ByeDPI поверх него
  /// Рекомендуется для TR, EG, AE, SA, IR
  Future<VPNConnectionResult> connectHybrid({
    required String wgConfig,
    int splitPosition = 2,
    String desyncMode = 'fake',
    int fakeTTL = 8,
  }) async {
    final result = await _channel.invokeMapMethod<String, dynamic>(
      'startHybrid',
      {
        'config': wgConfig,
        'split': splitPosition,
        'desync': desyncMode,
        'fake_ttl': fakeTTL,
      },
    );
    return VPNConnectionResult(
      status: result?['status'] ?? 'unknown',
      mode: result?['mode'] ?? 'hybrid',
      proxyAddress: result?['proxy'],
    );
  }

  /// Только AmneziaWG (для PK, ID и других стран с умеренной блокировкой)
  Future<VPNConnectionResult> connectAmnezia(String wgConfig) async {
    final result = await _channel.invokeMapMethod<String, dynamic>(
      'startAmnezia',
      {'config': wgConfig},
    );
    return VPNConnectionResult(
      status: result?['status'] ?? 'unknown',
      mode: result?['mode'] ?? 'amnezia',
    );
  }

  /// Авто-режим: выбирает гибрид или только AmneziaWG по коду страны
  Future<VPNConnectionResult> connectAuto({
    required String wgConfig,
    required String countryCode,
    int splitPosition = 2,
    String desyncMode = 'fake',
  }) async {
    final result = await _channel.invokeMapMethod<String, dynamic>(
      'startAuto',
      {
        'config': wgConfig,
        'country': countryCode,
        'split': splitPosition,
        'desync': desyncMode,
      },
    );
    return VPNConnectionResult(
      status: result?['status'] ?? 'unknown',
      mode: result?['mode'] ?? 'auto',
      proxyAddress: result?['proxy'],
    );
  }

  Future<void> disconnect() async {
    await _channel.invokeMethod('stop');
  }

  Future<Map<String, dynamic>> getStatus() async {
    final result = await _channel.invokeMapMethod<String, dynamic>('getStatus');
    return result ?? {};
  }
}
