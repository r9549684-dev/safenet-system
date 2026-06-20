import '../data/repositories/server_repo.dart';

/// SafeNet AMO: Сервис управления пулом конфигов для бесшовного фэйловера.
class AmoPoolService {
  final _repo = ServerRepository();

  // Локальный кэш пула: ключ - serverId, значение - данные конфига
  final Map<int, Map<String, dynamic>> _localPool = {};
  final List<int> _activeServerIds = [];

  /// Возвращает текущий размер пула (ACTIVE + STANDBY).
  int get poolSize => _activeServerIds.length;

  /// Запрашивает актуальный пул конфигов с бэкенда.
  Future<List<Map<String, dynamic>>?> refreshPool() async {
    try {
      final pool = await _repo.getConnectionPool();
      _localPool.clear();
      _activeServerIds.clear();

      for (var config in pool) {
        final rawId = config['server_id'];
        if (rawId == null) continue;
        final serverId = int.tryParse(rawId.toString()) ?? 0;
        if (serverId == 0) continue;
        final status = config['status'] as String?;
        if (status == 'ACTIVE' || status == 'STANDBY') {
          _localPool[serverId] = config;
          _activeServerIds.add(serverId);
        }
      }
      return pool;
    } catch (e) {
      print('[AMO] Ошибка получения пула: $e');
      return null;
    }
  }

  /// Возвращает следующий доступный STANDBY конфиг, исключая текущий activeServerId.
  Map<String, dynamic>? getNextStandbyConfig(int currentServerId) {
    // Сначала ищем именно STANDBY
    for (var serverId in _activeServerIds) {
      if (serverId != currentServerId) {
        final config = _localPool[serverId];
        if (config != null && config['status'] == 'STANDBY') {
          return config;
        }
      }
    }
    // Fallback: любой другой валидный конфиг из пула, если STANDBY внезапно нет
    for (var serverId in _activeServerIds) {
      if (serverId != currentServerId) {
        return _localPool[serverId];
      }
    }
    return null;
  }

  /// Сообщает бэкенду о блокировке и запускает фоновое обновление пула.
  Future<void> reportAndHeal(String allocatedIp) async {
    final success = await _repo.reportBlockedConfig(allocatedIp);
    if (success) {
      print('[AMO] Отчет о блокировке отправлен для IP $allocatedIp. Ожидание исцеления пула...');
      // Через 5 секунд обновляем пул, чтобы получить новый STANDBY конфиг от бэкенда
      Future.delayed(const Duration(seconds: 5), () {
        refreshPool();
      });
    }
  }

  /// Извлекает allocated_ip из WG-конфига для отчета о блокировке.
  /// Ищет строку вида Address = 10.8.0.5/32 или 10.8.0.5
  static String? extractAllocatedIp(String wgConfig) {
    final match = RegExp(r'Address\s*=\s*([0-9\.]+)').firstMatch(wgConfig);
    return match?.group(1);
  }
}