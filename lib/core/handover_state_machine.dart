/// Конечный автомат состояний (State Machine) для SafeNet ANO.
/// Управляет переходами при хендовере с защитой от флэппинга.
///
/// Состояния:
/// CONNECTED ──(Рейтинг < 5)──► HANDOVER_INIT ──► PRE_FLIGHT (3с)
///                                       │              │
///                                       │         (таймаут)
///                                       │              ▼
///                                       │         CONNECTED (откат)
///                                       ▼
///                               DRAIN_OLD (5–10с) ──► COOL_DOWN (60с) ──► CONNECTED

import 'dart:async';
import 'ano_models.dart';

typedef OnStateChange = void Function(HandoverState oldState, HandoverState newState);
typedef OnHandoverComplete = void Function(String targetServerId, bool success);

class HandoverStateMachine {
  HandoverState _currentState = HandoverState.connected;
  
  Timer? _preFlightTimer;
  Timer? _drainOldTimer;
  Timer? _coolDownTimer;

  final double hysteresisDelta; // ΔH = 2.0
  final Duration preFlightDuration; // 3с
  final Duration drainOldDuration; // 5-10с (берем 7с)
  final Duration coolDownDuration; // 60с

  final OnStateChange? onStateChange;
  final OnHandoverComplete? onHandoverComplete;

  HandoverStateMachine({
    this.hysteresisDelta = 2.0,
    this.preFlightDuration = const Duration(seconds: 3),
    this.drainOldDuration = const Duration(seconds: 7),
    this.coolDownDuration = const Duration(seconds: 60),
    this.onStateChange,
    this.onHandoverComplete,
  });

  HandoverState get currentState => _currentState;
  bool get isCoolingDown => _currentState == HandoverState.coolDown || _coolDownTimer?.isActive == true;

  /// Проверка, разрешен ли хендовер с учетом гистерезиса и кулдауна.
  bool canInitiateHandover(double currentRating, double targetRating) {
    if (isCoolingDown) return false;
    // Гистерезис: цель должна быть значительно лучше текущей
    return targetRating > (currentRating + hysteresisDelta);
  }

  /// Запуск процедуры хендовера.
  void initiateHandover(String targetServerId) {
    if (_currentState != HandoverState.connected) {
      return; // Игнорируем, если уже в процессе
    }

    _changeState(HandoverState.handoverInit);
    
    // Переход в PRE_FLIGHT
    _changeState(HandoverState.preFlight);
    _preFlightTimer = Timer(preFlightDuration, () {
      // Если за время pre-flight не было отмены, переходим к DRAIN_OLD
      if (_currentState == HandoverState.preFlight) {
        _changeState(HandoverState.drainOld);
        _drainOldTimer = Timer(drainOldDuration, () {
          _completeHandover(targetServerId, success: true);
        });
      }
    });
  }

  /// Принудительный откат из PRE_FLIGHT обратно в CONNECTED.
  void rollbackHandover() {
    if (_currentState == HandoverState.preFlight || _currentState == HandoverState.handoverInit) {
      _preFlightTimer?.cancel();
      _changeState(HandoverState.connected);
    }
  }

  void _completeHandover(String targetServerId, {required bool success}) {
    _drainOldTimer?.cancel();
    onHandoverComplete?.call(targetServerId, success);
    
    if (success) {
      _changeState(HandoverState.coolDown);
      _coolDownTimer = Timer(coolDownDuration, () {
        _changeState(HandoverState.connected);
      });
    } else {
      _changeState(HandoverState.connected);
    }
  }

  /// Форсированный сброс кулдауна (только для административных/аварийных нужд).
  void forceResetCoolDown() {
    _coolDownTimer?.cancel();
    if (_currentState == HandoverState.coolDown) {
      _changeState(HandoverState.connected);
    }
  }

  void _changeState(HandoverState newState) {
    final oldState = _currentState;
    if (oldState != newState) {
      _currentState = newState;
      onStateChange?.call(oldState, newState);
    }
  }

  void dispose() {
    _preFlightTimer?.cancel();
    _drainOldTimer?.cancel();
    _coolDownTimer?.cancel();
  }
}