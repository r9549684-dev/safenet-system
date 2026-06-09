import 'dart:convert';
import 'storage_adapter.dart';

/// Чистый компонент управления очередью конфигураций.
/// Не содержит платформозависимого кода и сетевых вызовов.
/// Управляет слотами: добавление, сдвиг при извлечении, проверка TTL.
class ConfigQueue {
  final IStorageAdapter _storage;
  final int maxSlots;
  final int ttlHours;

  ConfigQueue({
    required IStorageAdapter storage,
    this.maxSlots = 3,
    this.ttlHours = 24,
  }) : _storage = storage;

  // ── Ключи ──────────────────────────────────────────────────────────────────

  String _slotKey(String country, int i) => 'spare_config_${country.toUpperCase()}_$i';
  String _slotTsKey(String country, int i) => 'spare_config_ts_${country.toUpperCase()}_$i';

  // ── ОЧЕРЕДЬ ────────────────────────────────────────────────────────────────

  /// Взять конфиг из головы очереди и сдвинуть остальные.
  /// Возвращает null, если очередь пуста или все конфиги устарели.
  Future<Map<String, dynamic>?> dequeue(String country) async {
    Map<String, dynamic>? head;
    int headIdx = -1;

    // Найти первый живой слот
    for (int i = 0; i < maxSlots; i++) {
      final entry = await _readSlot(country, i);
      if (entry != null) {
        head = entry;
        headIdx = i;
        break;
      }
    }
    if (headIdx < 0) return null;

    // Сдвинуть: каждый слот = следующий
    for (int i = headIdx; i < maxSlots - 1; i++) {
      final next = await _storage.read(_slotKey(country, i + 1));
      final nextTs = await _storage.read(_slotTsKey(country, i + 1));
      if (next != null && nextTs != null) {
        await _storage.write(_slotKey(country, i), next);
        await _storage.write(_slotTsKey(country, i), nextTs);
      } else {
        await _storage.delete(_slotKey(country, i));
        await _storage.delete(_slotTsKey(country, i));
      }
    }
    // Очистить последний (он теперь занят предыдущим или должен быть пустым)
    await _storage.delete(_slotKey(country, maxSlots - 1));
    await _storage.delete(_slotTsKey(country, maxSlots - 1));

    return head;
  }

  /// Добавить конфиг в конец очереди.
  /// Если очередь заполнена — перезаписать самый старый слот (maxSlots - 1).
  Future<void> enqueue(String country, Map<String, dynamic> config) async {
    for (int i = 0; i < maxSlots; i++) {
      final raw = await _storage.read(_slotKey(country, i));
      if (raw == null) {
        await _writeSlot(country, i, config);
        return;
      }
    }
    // Очередь полна — заменить последний слот
    await _writeSlot(country, maxSlots - 1, config);
  }

  /// Количество живых (не устаревших) конфигов в очереди.
  Future<int> queueLength(String country) async {
    int count = 0;
    for (int i = 0; i < maxSlots; i++) {
      if (await _readSlot(country, i) != null) count++;
    }
    return count;
  }

  /// Очистить всю очередь для страны.
  Future<void> clearQueue(String country) async {
    for (int i = 0; i < maxSlots; i++) {
      await _storage.delete(_slotKey(country, i));
      await _storage.delete(_slotTsKey(country, i));
    }
  }

  /// Проверить, есть ли валидный кэш (хотя бы 1 живой слот).
  Future<bool> hasValidCache(String country) async => (await queueLength(country)) > 0;

  /// Устаревший метод совместимости: читает слот 0 без его удаления.
  Future<Map<String, dynamic>?> getCached(String country) => _readSlot(country, 0);

  /// Устаревший метод совместимости: кладёт в слот 0 (или первый свободный).
  Future<void> saveCache(String country, Map<String, dynamic> config) =>
      enqueue(country, config);

  // ── ПРИВАТНЫЕ ХЕЛПЕРЫ ─────────────────────────────────────────────────────

  Future<Map<String, dynamic>?> _readSlot(String country, int i) async {
    final raw = await _storage.read(_slotKey(country, i));
    if (raw == null) return null;
    
    final tsStr = await _storage.read(_slotTsKey(country, i));
    if (tsStr != null) {
      final ts = DateTime.tryParse(tsStr);
      if (ts != null && DateTime.now().difference(ts).inHours >= ttlHours) {
        // TTL истек — удаляем
        await _storage.delete(_slotKey(country, i));
        await _storage.delete(_slotTsKey(country, i));
        return null;
      }
    }
    
    try {
      return Map<String, dynamic>.from(jsonDecode(raw) as Map);
    } catch (_) {
      return null;
    }
  }

  Future<void> _writeSlot(String country, int i, Map<String, dynamic> config) async {
    await _storage.write(_slotKey(country, i), jsonEncode(config));
    await _storage.write(
      _slotTsKey(country, i),
      DateTime.now().toIso8601String(),
    );
  }
}
