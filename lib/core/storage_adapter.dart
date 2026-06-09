/// Абстрактный интерфейс-мост для операций чтения/записи/удаления данных.
/// Позволяет изолировать бизнес-логику от платформозависимых реализаций
/// (например, FlutterSecureStorage) для чистого юнит-тестирования.
abstract class IStorageAdapter {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
}
