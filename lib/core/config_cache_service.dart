import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'config_queue.dart';
import 'constants.dart';
import 'storage_adapter.dart';

/// Адаптер для FlutterSecureStorage, реализующий IStorageAdapter.
class SecureStorageAdapter implements IStorageAdapter {
  final FlutterSecureStorage _storage;
  
  SecureStorageAdapter(this._storage);

  @override
  Future<String?> read(String key) => _storage.read(key: key);

  @override
  Future<void> write(String key, String value) => _storage.write(key: key, value: value);

  @override
  Future<void> delete(String key) => _storage.delete(key: key);
}

/// Тонкая обертка над ConfigQueue, предоставляющая совместимый API
/// и интегрирующая сетевые вызовы (Dio) и WG-кэш.
class ConfigCacheService {
  static const _secureStorage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  
  // Единственный экземпляр очереди, использующий реальное хранилище
  static final ConfigQueue _queue = ConfigQueue(
    storage: SecureStorageAdapter(_secureStorage),
    maxSlots: 3,
    ttlHours: 24,
  );

  static const _apiBase = AppConstants.apiBaseUrl;
  static const _wgTtlHours = 48;

  // ── WG-КЭШ (по serverId) ──────────────────────────────────────────────────

  static String _wgKey(String serverId) => 'wg_config_$serverId';
  static String _wgTsKey(String serverId) => 'wg_config_ts_$serverId';

  /// Сохранить wg_config после успешного подключения.
  static Future<void> saveWgCache(String serverId, String wgConfig) async {
    await _secureStorage.write(key: _wgKey(serverId), value: wgConfig);
    await _secureStorage.write(
      key: _wgTsKey(serverId), 
      value: DateTime.now().toIso8601String(),
    );
  }

  /// Прочитать закешированный wg_config. null если нет или устарел.
  static Future<String?> getWgCache(String serverId) async {
    final raw = await _secureStorage.read(key: _wgKey(serverId));
    if (raw == null) return null;
    
    final tsStr = await _secureStorage.read(key: _wgTsKey(serverId));
    if (tsStr != null) {
      final ts = DateTime.tryParse(tsStr);
      if (ts != null && DateTime.now().difference(ts).inHours >= _wgTtlHours) {
        await _secureStorage.delete(key: _wgKey(serverId));
        await _secureStorage.delete(key: _wgTsKey(serverId));
        return null;
      }
    }
    return raw;
  }

  // ── ИСПОЛЬЗОВАНИЕ + ФОНОВОЕ ПОПОЛНЕНИЕ ────────────────────────────────────

  /// Вызвать после успешного подключения через очередной конфиг.
  /// 1. Уведомляет сервер (fire-and-forget).
  /// 2. Фоново загружает новый конфиг и кладёт в хвост очереди.
  static Future<void> consumeAndRefresh(
    String token,
    String country, {
    int? serverId,
  }) async {
    _consumeAndRefreshImpl(token, country, serverId: serverId);
  }

  static Future<void> _consumeAndRefreshImpl(
    String token,
    String country, {
    int? serverId,
  }) async {
    final dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    ));
    try {
      await dio.post(
        '$_apiBase/config/consume/$token',
        queryParameters: {'country': country},
      );
    } catch (_) {}

    await _fetchAndEnqueue(token, country, serverId: serverId);
  }

  /// Заранее заполнить очередь (вызывать при старте приложения).
  static Future<void> preload(
    String token,
    String country, {
    int? serverId,
  }) async {
    final len = await _queue.queueLength(country);
    // Добираем до maxSlots
    for (int i = len; i < 3; i++) {
      await _fetchAndEnqueue(token, country, serverId: serverId);
    }
  }

  static Future<void> _fetchAndEnqueue(
    String token,
    String country, {
    int? serverId,
  }) async {
    try {
      final dio = Dio(BaseOptions(
        connectTimeout: const Duration(seconds: 12),
        receiveTimeout: const Duration(seconds: 20),
      ));
      final params = <String, dynamic>{'country': country};
      if (serverId != null) params['server_id'] = serverId;
      final resp = await dio.get(
        '$_apiBase/config/cached/$token',
        queryParameters: params,
      );
      if (resp.statusCode == 200 && resp.data is Map) {
        await _queue.enqueue(country, Map<String, dynamic>.from(resp.data as Map));
      }
    } catch (_) {}
  }

  // ── SINGBOX JSON (извлекает строку из конфига в очереди) ──────────────────

  /// Взять singbox JSON из головы очереди.
  /// Если очередь пуста — загрузить из сети напрямую.
  static Future<String?> dequeueSingboxJson(
    String token,
    String country,
  ) async {
    // 1. Из очереди
    final entry = await _queue.dequeue(country);
    if (entry != null) {
      if (entry['format'] == 'singbox') {
        final cfg = entry['config'];
        if (cfg is String) return cfg;
        if (cfg != null) return jsonEncode(cfg);
      }
    }

    // 2. Сеть (резервный путь)
    try {
      final dio = Dio(BaseOptions(
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
      ));
      final resp = await dio.get<String>(
        '$_apiBase/iran/subscribe/$token',
        queryParameters: {'fmt': 'singbox'},
        options: Options(responseType: ResponseType.plain),
      );
      if (resp.statusCode == 200 && resp.data != null) {
        return resp.data;
      }
    } catch (_) {}

    return null;
  }

  // ── СОВМЕСТИМЫЕ ОБЁРТКИ (делегирование в ConfigQueue) ─────────────────────

  static Future<Map<String, dynamic>?> dequeue(String country) => 
      _queue.dequeue(country);

  static Future<void> enqueue(String country, Map<String, dynamic> config) => 
      _queue.enqueue(country, config);

  static Future<int> queueLength(String country) => 
      _queue.queueLength(country);

  static Future<Map<String, dynamic>?> getCached(String country) => 
      _queue.getCached(country);

  static Future<void> saveCache(String country, Map<String, dynamic> config) => 
      _queue.saveCache(country, config);

  static Future<void> clearCache(String country) => 
      _queue.clearQueue(country);

  static Future<bool> hasValidCache(String country) => 
      _queue.hasValidCache(country);
}
