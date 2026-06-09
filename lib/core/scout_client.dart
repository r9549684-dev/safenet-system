/// Клиентский контур скрытого зондирования (Скаут) SafeNet ANO.
/// Зондирует фиксированную тройку серверов с интервалом 30с ± джиттер 5с.
/// Кэширует последние 3 результата и отправляет агрегированный POST на бэкенд.

import 'dart:async';
import 'dart:math';
import 'dart:io'; // Для Socket (TCP SYN маскировка под keep-alive)
import 'ano_models.dart';

/// Интерфейс для локального защищенного хранилища (например, flutter_secure_storage)
abstract class SecureStorage {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
}

/// Интерфейс для HTTP-клиента (например, http или dio)
abstract class HttpClient {
  Future<void> postAggregatedMetrics(List<Map<String, dynamic>> payloads);
}

class ScoutClient {
  final String _currentServerId;
  final List<String> _topServers;
  final SecureStorage _storage;
  final HttpClient _httpClient;
  
  Timer? _probeTimer;
  final List<ScoutMetrics> _localCache = [];
  final int _maxCacheSize = 3;
  final Random _random = Random();

  ScoutClient({
    required String currentServerId,
    required List<String> topServers,
    required SecureStorage storage,
    required HttpClient httpClient,
  }) : _currentServerId = currentServerId,
       _topServers = topServers,
       _storage = storage,
       _httpClient = httpClient;

  /// Запускает фоновое зондирование.
  void startProbing() {
    stopProbing();
    _scheduleNextProbe();
  }

  /// Останавливает зондирование.
  void stopProbing() {
    _probeTimer?.cancel();
    _probeTimer = null;
  }

  void _scheduleNextProbe() {
    // Интервал 30с ± джиттер 5с (от 25с до 35с)
    final jitterMs = (_random.nextDouble() * 10000) - 5000; 
    final interval = Duration(milliseconds: (30000 + jitterMs).toInt());
    
    _probeTimer = Timer(interval, () async {
      await _executeProbe();
      _scheduleNextProbe();
    });
  }

  Future<void> _executeProbe() async {
    final serversToProbe = [_currentServerId, ..._topServers.take(2)];
    final results = <ScoutMetrics>[];

    for (final serverId in serversToProbe) {
      final metrics = await _probeServer(serverId);
      if (metrics != null) {
        results.add(metrics);
      }
    }

    if (results.isNotEmpty) {
      _updateLocalCache(results);
      await _sendAggregatedMetrics(results);
    }
  }

  /// Имитация TCP SYN зондирования к рабочему порту (маскировка под keep-alive).
  /// В реальной реализации: подключение к порту service и измерение времени до SYN-ACK.
  Future<ScoutMetrics?> _probeServer(String serverId) async {
    try {
      final stopwatch = Stopwatch()..start();
      // TODO: Реальный Socket.connect(serverIp, port, timeout: Duration(seconds: 5))
      await Future.delayed(const Duration(milliseconds: 50)); // Заглушка для примера
      stopwatch.stop();

      // Заглушка метрик (в реальности вычисляется на основе реальных попыток)
      return ScoutMetrics(
        serverId: serverId,
        rttMs: stopwatch.elapsedMilliseconds.toDouble(),
        jitterMs: 5.0, // Заглушка
        lossPct: 0.0,  // Заглушка
        throughputKbps: 800.0, // Заглушка
      );
    } catch (e) {
      // При ошибке подключения считаем как 100% loss
      return ScoutMetrics(
        serverId: serverId,
        rttMs: 0.0,
        jitterMs: 0.0,
        lossPct: 100.0,
        throughputKbps: 0.0,
      );
    }
  }

  void _updateLocalCache(List<ScoutMetrics> newMetrics) {
    _localCache.addAll(newMetrics);
    // Храним только последние _maxCacheSize результатов
    if (_localCache.length > _maxCacheSize) {
      _localCache.removeRange(0, _localCache.length - _maxCacheSize);
    }
    
    // Сохраняем в SecureStorage (сериализуем в JSON строку)
    final jsonStr = _localCache.map((m) => m.toJson()).toList().toString();
    _storage.write('ano_scout_cache', jsonStr);
  }

  Future<void> _sendAggregatedMetrics(List<ScoutMetrics> metrics) async {
    try {
      final payloads = metrics.map((m) => m.toJson()).toList();
      await _httpClient.postAggregatedMetrics(payloads);
    } catch (e) {
      // Ошибка отправки не должна ломать цикл зондирования
      // Логируем ошибку (в реальности: logger.e('Aggregated metrics send failed', e))
    }
  }

  /// Возвращает последние закэшированные метрики для локального принятия решений.
  List<ScoutMetrics> get cachedMetrics => List.unmodifiable(_localCache);
}