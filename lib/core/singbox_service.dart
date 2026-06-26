import 'package:flutter/services.dart';
import 'package:dio/dio.dart';
import 'package:safenet_vpn/core/config_cache_service.dart';

/// Управляет Iran Mode service (sing-box subprocess).
/// Только для Iran-билда (bundleHiddify → заменяем на bundleSingbox).
const bundleSingbox = bool.fromEnvironment('BUNDLE_HIDDIFY', defaultValue: false);

class SingboxVpn {
  static const _channel = MethodChannel('com.safenet.vpn/singbox');
  static const _apiBase = 'https://safenetsystem.duckdns.org';

  /// Взять singbox config из очереди (удалить из головы), при пустой — сеть.
  static Future<String?> fetchConfig(String deviceId) async {
    final token = deviceId.length >= 16 ? deviceId.substring(0, 16) : deviceId;
    return ConfigCacheService.dequeueSingboxJson(token, 'IR');
  }

  /// Фоново пополняет очередь после успешного подключения (fire-and-forget).
  static Future<void> consumeAndRefreshCache(String deviceId) async {
    final token = deviceId.length >= 16 ? deviceId.substring(0, 16) : deviceId;
    await ConfigCacheService.consumeAndRefresh(token, 'IR');
  }

  /// Взять следующий конфиг из очереди (failover, без уведомления сервера).
  static Future<String?> fetchNextConfig(String deviceId) async {
    final token = deviceId.length >= 16 ? deviceId.substring(0, 16) : deviceId;
    return ConfigCacheService.dequeueSingboxJson(token, 'IR');
  }

  /// Запустить Iran service.
  /// [configJson] — JSON из API (только outbounds + route).
  static Future<bool> start(String configJson) async {
    try {
      await _channel.invokeMethod('start', {'config': configJson});
      return true;
    } on PlatformException catch (e) {
      // ignore: avoid_print
      print('[SingboxVpn] start error: ${e.code} — ${e.message}');
      return false;
    }
  }

  /// Остановить Iran service.
  static Future<void> stop() async {
    try { await _channel.invokeMethod('stop'); } catch (_) {}
  }

  /// Текущий статус.
  static Future<({bool running, String error})> status() async {
    try {
      final r = await _channel.invokeMapMethod<String, dynamic>('status');
      return (
        running: (r?['running'] as bool?) ?? false,
        error:   (r?['error']   as String?) ?? '',
      );
    } catch (_) {
      return (running: false, error: '');
    }
  }
}
