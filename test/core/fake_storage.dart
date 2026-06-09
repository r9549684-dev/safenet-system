import 'package:safenet_vpn/core/storage_adapter.dart';

/// Имитация хранилища в оперативной памяти для юнит-тестов.
/// Позволяет тестировать логику ConfigQueue без платформозависимых вызовов.
class FakeStorage implements IStorageAdapter {
  final Map<String, String> _data = {};

  @override
  Future<String?> read(String key) async {
    return _data[key];
  }

  @override
  Future<void> write(String key, String value) async {
    _data[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    _data.remove(key);
  }

  /// Утилита для очистки состояния между тестами.
  void clear() {
    _data.clear();
  }

  /// Утилита для проверки внутреннего состояния (только для тестов).
  Map<String, String> get internalState => Map.unmodifiable(_data);
}
