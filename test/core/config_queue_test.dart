import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:safenet_vpn/core/config_queue.dart';
import 'fake_storage.dart';

void main() {
  group('ConfigQueue', () {
    late FakeStorage fakeStorage;
    late ConfigQueue queue;
    const String testCountry = 'IR';
    const int maxSlots = 3;
    const int ttlHours = 24;

    setUp(() {
      fakeStorage = FakeStorage();
      queue = ConfigQueue(
        storage: fakeStorage,
        maxSlots: maxSlots,
        ttlHours: ttlHours,
      );
    });

    Map<String, dynamic> _makeConfig(String id) => {
          'format': 'singbox',
          'config': '{"outbounds": [{"tag": "$id"}]}',
          'id': id,
        };

    String _slotKey(int i) => 'spare_config_${testCountry.toUpperCase()}_$i';
    String _slotTsKey(int i) => 'spare_config_ts_${testCountry.toUpperCase()}_$i';

    test('Добавление новой конфигурации в пустую очередь занимает слот 0', () async {
      final config = _makeConfig('srv-1');
      await queue.enqueue(testCountry, config);

      expect(await queue.queueLength(testCountry), equals(1));
      
      final raw = await fakeStorage.read(_slotKey(0));
      expect(raw, isNotNull);
      
      final decoded = jsonDecode(raw!) as Map;
      expect(decoded['id'], equals('srv-1'));
      
      // Слот 1 и 2 должны быть пустыми
      expect(await fakeStorage.read(_slotKey(1)), isNull);
      expect(await fakeStorage.read(_slotKey(2)), isNull);
    });

    test('Извлечение (dequeue) сдвигает элементы и очищает последний слот', () async {
      // Заполняем очередь: 0, 1, 2
      await queue.enqueue(testCountry, _makeConfig('srv-1'));
      await queue.enqueue(testCountry, _makeConfig('srv-2'));
      await queue.enqueue(testCountry, _makeConfig('srv-3'));

      expect(await queue.queueLength(testCountry), equals(3));

      // Извлекаем голову (должна быть srv-1)
      final head = await queue.dequeue(testCountry);
      expect(head, isNotNull);
      expect(head!['id'], equals('srv-1'));

      // Проверяем сдвиг: srv-2 теперь в слоте 0, srv-3 в слоте 1
      final slot0 = await fakeStorage.read(_slotKey(0));
      final slot1 = await fakeStorage.read(_slotKey(1));
      final slot2 = await fakeStorage.read(_slotKey(2));

      expect(jsonDecode(slot0!)['id'], equals('srv-2'));
      expect(jsonDecode(slot1!)['id'], equals('srv-3'));
      expect(slot2, isNull); // Последний слот очищен

      expect(await queue.queueLength(testCountry), equals(2));
    });

    test('Конфигурация старше TTL (24 часа) считается невалидной и пропускается', () async {
      final oldTime = DateTime.now().subtract(const Duration(hours: 25)).toIso8601String();
      
      // Пишем вручную устаревший конфиг в слот 0
      await fakeStorage.write(_slotKey(0), jsonEncode(_makeConfig('old-srv')));
      await fakeStorage.write(_slotTsKey(0), oldTime);

      // Пишем свежий конфиг в слот 1
      final freshTime = DateTime.now().toIso8601String();
      await fakeStorage.write(_slotKey(1), jsonEncode(_makeConfig('fresh-srv')));
      await fakeStorage.write(_slotTsKey(1), freshTime);

      // queueLength должен игнорировать устаревший слот 0
      expect(await queue.queueLength(testCountry), equals(1));

      // dequeue должен пропустить слот 0 и вернуть свежий из слота 1 (который сдвинется в 0)
      final head = await queue.dequeue(testCountry);
      expect(head, isNotNull);
      expect(head!['id'], equals('fresh-srv'));

      // Устаревший слот должен быть удален
      expect(await fakeStorage.read(_slotKey(0)), isNull);
      expect(await fakeStorage.read(_slotTsKey(0)), isNull);
    });

    test('Переполнение очереди перезаписывает последний слот (maxSlots - 1)', () async {
      // Заполняем 3 слота
      await queue.enqueue(testCountry, _makeConfig('srv-1'));
      await queue.enqueue(testCountry, _makeConfig('srv-2'));
      await queue.enqueue(testCountry, _makeConfig('srv-3'));

      // Добавляем 4-й элемент
      await queue.enqueue(testCountry, _makeConfig('srv-4'));

      // Длина должна остаться 3
      expect(await queue.queueLength(testCountry), equals(3));

      // Последний слот (2) должен содержать srv-4
      final slot2 = await fakeStorage.read(_slotKey(2));
      expect(slot2, isNotNull);
      expect(jsonDecode(slot2!)['id'], equals('srv-4'));
    });

    test('clearQueue удаляет все слоты для указанной страны', () async {
      await queue.enqueue(testCountry, _makeConfig('srv-1'));
      await queue.enqueue(testCountry, _makeConfig('srv-2'));

      await queue.clearQueue(testCountry);

      expect(await queue.queueLength(testCountry), equals(0));
      expect(await fakeStorage.read(_slotKey(0)), isNull);
      expect(await fakeStorage.read(_slotKey(1)), isNull);
      expect(await fakeStorage.read(_slotKey(2)), isNull);
    });

    test('hasValidCache возвращает true только при наличии живых слотов', () async {
      expect(await queue.hasValidCache(testCountry), isFalse);

      await queue.enqueue(testCountry, _makeConfig('srv-1'));
      expect(await queue.hasValidCache(testCountry), isTrue);

      await queue.clearQueue(testCountry);
      expect(await queue.hasValidCache(testCountry), isFalse);
    });
  });
}
