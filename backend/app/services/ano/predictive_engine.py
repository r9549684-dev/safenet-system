"""SafeNet ANO — Predictive Engine.

Прогнозирование деградации на базе трендов телеметрии.
Проактивный хендовер при forecast_score < 0.7 AND prediction_confidence > 0.8.
Режим «Усиленного мониторинга» при низкой уверенности.

Нормализация через tanh для защиты от деления на ноль.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysis:
    loss_score: float  # tanh(loss_pct / 10) ∈ [0, 1]
    rtt_score: float  # tanh(rtt_delta_pct / 20) ∈ [0, 1]
    jitter_score: float  # tanh(jitter_delta_pct / 20) ∈ [0, 1]
    forecast_score: float  # 1 - avg(scores) ∈ [0, 1]
    prediction_confidence: float  # [0, 1] — уверенность в прогнозе
    recommendation: str  # "proactive_handover" | "enhanced_monitoring" | "normal"


@dataclass
class PredictiveResult:
    server_id: str
    trend: TrendAnalysis
    should_migrate: bool
    enhanced_monitoring: bool
    cooldown_seconds: int = 0
    reason: str = ""


class PredictiveEngine:
    """Прогнозирование деградации маршрутов.

    Использует нормализованные функции затухания (tanh) для защиты
    от деления на ноль при стабильном соединении (Loss=0).

    Логика принятия решений:
      - forecast_score < 0.7 AND prediction_confidence > 0.8 → проактивный хендовер
      - forecast_score < 0.7 AND prediction_confidence ≤ 0.8 → усиленный мониторинг
      - forecast_score ≥ 0.7 → нормальный режим
    """

    # Пороги
    FORECAST_CRITICAL = 0.7
    CONFIDENCE_THRESHOLD = 0.8
    ENHANCED_MONITORING_INTERVAL = 2  # секунды
    NORMAL_INTERVAL = 10  # секунды
    COOLDOWN_SECONDS = 300  # 5 минут при усиленном мониторинге

    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, float]]] = {}

    def add_sample(self, server_id: str, metrics: dict[str, float]) -> None:
        """Добавить сэмпл телеметрии для сервера."""
        if server_id not in self._history:
            self._history[server_id] = []
        self._history[server_id].append(metrics)
        # Храним последние 30 сэмплов (15 минут при интервале 30с)
        if len(self._history[server_id]) > 30:
            self._history[server_id] = self._history[server_id][-30:]

    def analyze(self, server_id: str) -> PredictiveResult:
        """Анализ тренда для сервера."""
        history = self._history.get(server_id, [])
        if len(history) < 5:
            return PredictiveResult(
                server_id=server_id,
                trend=TrendAnalysis(0, 0, 0, 1.0, 0.0, "normal"),
                should_migrate=False,
                enhanced_monitoring=False,
                reason="Insufficient data (< 5 samples)",
            )

        # Текущие метрики (последний сэмпл)
        current = history[-1]
        loss_pct = current.get("loss_pct", 0)
        rtt_ms = current.get("rtt_ms", 0)
        jitter_ms = current.get("jitter_ms", 0)

        # Базовые значения (среднее за первые 5 сэмплов)
        baseline = history[:5]
        avg_rtt = sum(s.get("rtt_ms", 0) for s in baseline) / len(baseline)
        avg_jitter = sum(s.get("jitter_ms", 0) for s in baseline) / len(baseline)

        # Нормализация через tanh
        loss_score = math.tanh(loss_pct / 10.0)
        rtt_delta_pct = ((rtt_ms - avg_rtt) / max(avg_rtt, 1)) * 100
        rtt_score = math.tanh(rtt_delta_pct / 20.0)
        jitter_delta_pct = ((jitter_ms - avg_jitter) / max(avg_jitter, 1)) * 100
        jitter_score = math.tanh(jitter_delta_pct / 20.0)

        # Прогнозный скор
        forecast_score = 1.0 - (loss_score + rtt_score + jitter_score) / 3.0

        # Уверенность в прогнозе (на основе количества данных и стабильности)
        prediction_confidence = min(len(history) / 30.0, 1.0)

        # Рекомендация
        if forecast_score < self.FORECAST_CRITICAL:
            if prediction_confidence > self.CONFIDENCE_THRESHOLD:
                recommendation = "proactive_handover"
            else:
                recommendation = "enhanced_monitoring"
        else:
            recommendation = "normal"

        trend = TrendAnalysis(
            loss_score=round(loss_score, 4),
            rtt_score=round(rtt_score, 4),
            jitter_score=round(jitter_score, 4),
            forecast_score=round(forecast_score, 4),
            prediction_confidence=round(prediction_confidence, 4),
            recommendation=recommendation,
        )

        should_migrate = recommendation == "proactive_handover"
        enhanced = recommendation == "enhanced_monitoring"

        result = PredictiveResult(
            server_id=server_id,
            trend=trend,
            should_migrate=should_migrate,
            enhanced_monitoring=enhanced,
            cooldown_seconds=self.COOLDOWN_SECONDS if enhanced else 0,
            reason=f"forecast={forecast_score:.2f} confidence={prediction_confidence:.2f}",
        )

        logger.info(
            "Predictive analysis: server=%s forecast=%.2f confidence=%.2f → %s",
            server_id,
            forecast_score,
            prediction_confidence,
            recommendation,
        )

        return result

    def get_recommended_interval(self, server_id: str) -> int:
        """Рекомендуемый интервал опроса для сервера."""
        result = self.analyze(server_id)
        if result.enhanced_monitoring:
            return self.ENHANCED_MONITORING_INTERVAL
        return self.NORMAL_INTERVAL

    def clear_history(self, server_id: str) -> None:
        """Очистить историю сервера (после успешного хендовера)."""
        self._history.pop(server_id, None)
