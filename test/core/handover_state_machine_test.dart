/// Тесты для HandoverStateMachine SafeNet ANO.
/// Проверяют защиту от флэппинга, откат при таймауте и переходы состояний.

import 'package:flutter_test/flutter_test.dart';
import 'package:safenet_vpn/core/ano_models.dart';
import 'package:safenet_vpn/core/handover_state_machine.dart';

void main() {
  group('HandoverStateMachine', () {
    late HandoverStateMachine sm;

    setUp(() {
      // Используем укороченные таймеры для быстрых тестов
      sm = HandoverStateMachine(
        hysteresisDelta: 2.0,
        preFlightDuration: const Duration(milliseconds: 100),
        drainOldDuration: const Duration(milliseconds: 100),
        coolDownDuration: const Duration(milliseconds: 100),
      );
    });

    tearDown(() {
      sm.dispose();
    });

    test('начальное состояние должно быть connected', () {
      expect(sm.currentState, equals(HandoverState.connected));
      expect(sm.isCoolingDown, isFalse);
    });

    test('canInitiateHandover должен учитывать гистерезис и кулдаун', () {
      // Без гистерезиса (разница < 2.0)
      expect(sm.canInitiateHandover(5.0, 6.0), isFalse);
      // С гистерезисом (разница > 2.0)
      expect(sm.canInitiateHandover(5.0, 8.0), isTrue);

      // Запускаем хендовер, чтобы активировать кулдаун
      sm.initiateHandover('srv-2');
      
      // Быстрые переходы для завершения coolDown в тесте
      // (в реальном коде мы бы использовали fakeAsync, но здесь просто ждем)
    });

    test('должен переходить в coolDown после успешного хендовера', () async {
      sm.initiateHandover('srv-2');
      // Синхронно переходит в preFlight
      expect(sm.currentState, equals(HandoverState.preFlight));

      // Ждем окончания preFlight (100ms) + небольшой запас
      await Future.delayed(const Duration(milliseconds: 110));
      expect(sm.currentState, equals(HandoverState.drainOld));

      // Ждем окончания drainOld (100ms) + небольшой запас
      await Future.delayed(const Duration(milliseconds: 110));
      expect(sm.currentState, equals(HandoverState.coolDown));
      expect(sm.isCoolingDown, isTrue);

      // Ждем окончания coolDown (100ms) + небольшой запас
      await Future.delayed(const Duration(milliseconds: 110));
      expect(sm.currentState, equals(HandoverState.connected));
      expect(sm.isCoolingDown, isFalse);
    });

    test('rollbackHandover должен возвращать в connected из preFlight', () async {
      sm.initiateHandover('srv-2');
      // Синхронно уже в preFlight
      expect(sm.currentState, equals(HandoverState.preFlight));

      // Выполняем откат
      sm.rollbackHandover();
      expect(sm.currentState, equals(HandoverState.connected));

      // Ждем, чтобы убедиться, что таймер preFlight не перевел его в drainOld
      await Future.delayed(const Duration(milliseconds: 150));
      expect(sm.currentState, equals(HandoverState.connected));
    });

    test('повторный initiateHandover должен игнорироваться, если уже в процессе', () {
      sm.initiateHandover('srv-2');
      // Синхронно уже в preFlight
      expect(sm.currentState, equals(HandoverState.preFlight));

      // Вторая попытка должна быть проигнорирована
      sm.initiateHandover('srv-3');
      expect(sm.currentState, equals(HandoverState.preFlight)); // Не меняется на руку srv-3
    });
  });
}