"""Тесты для SafeNet ANO — Predictive Engine + Decision Memory.

Запуск: pytest tests/test_ano/ -v
"""

import math

import pytest

from app.services.ano.predictive_engine import (
    PredictiveEngine,
    PredictiveResult,
)
from app.services.ano.decision_memory import DecisionEntry, DecisionMemory


# ── Predictive Engine Tests ───────────────────────────────────────────


class TestPredictiveEngine:
    def _add_degrading_samples(
        self, engine: PredictiveEngine, server_id: str, count: int = 20
    ) -> None:
        """Добавить сэмплы с плавной деградацией."""
        for i in range(count):
            engine.add_sample(server_id, {
                "rtt_ms": 45 + i * 3,  # растёт
                "jitter_ms": 8 + i * 2,  # растёт
                "loss_pct": i * 0.8,  # растёт
                "throughput_kbps": 800 - i * 10,
            })

    def _add_stable_samples(
        self, engine: PredictiveEngine, server_id: str, count: int = 20
    ) -> None:
        """Добрить стабильные сэмплы."""
        for _ in range(count):
            engine.add_sample(server_id, {
                "rtt_ms": 45,
                "jitter_ms": 8,
                "loss_pct": 0,
                "throughput_kbps": 800,
            })

    def test_tanh_normalization(self) -> None:
        """tanh должен удерживать значения в [0, 1]."""
        engine = PredictiveEngine()
        # Экстремальные значения
        for _ in range(10):
            engine.add_sample("srv-1", {
                "loss_pct": 50, "rtt_ms": 5000, "jitter_ms": 200,
            })
        result = engine.analyze("srv-1")
        assert 0.0 <= result.trend.loss_score <= 1.0
        assert 0.0 <= result.trend.rtt_score <= 1.0
        assert 0.0 <= result.trend.jitter_score <= 1.0

    def test_no_division_by_zero(self) -> None:
        """При Loss=0 не должно быть деления на ноль."""
        engine = PredictiveEngine()
        for _ in range(10):
            engine.add_sample("srv-1", {
                "loss_pct": 0, "rtt_ms": 45, "jitter_ms": 8,
            })
        result = engine.analyze("srv-1")
        assert math.isfinite(result.trend.forecast_score)
        assert result.trend.recommendation == "normal"

    def test_proactive_handover_trigger(self) -> None:
        """При сильной деградации — проактивный хендовер."""
        engine = PredictiveEngine()
        self._add_degrading_samples(engine, "srv-1", count=20)
        result = engine.analyze("srv-1")
        # forecast_score < 0.7 и confidence > 0.8
        assert result.trend.forecast_score < 0.7
        assert result.should_migrate or result.enhanced_monitoring

    def test_enhanced_monitoring_low_confidence(self) -> None:
        """При деградации, но мало данных — усиленный мониторинг."""
        engine = PredictiveEngine()
        for i in range(5):  # мало данных
            engine.add_sample("srv-1", {
                "rtt_ms": 45 + i * 10,
                "jitter_ms": 8 + i * 5,
                "loss_pct": i * 2,
            })
        result = engine.analyze("srv-1")
        if result.trend.forecast_score < 0.7:
            # При малом количестве данных confidence низкий → enhanced_monitoring
            assert result.trend.prediction_confidence < 0.8 or result.enhanced_monitoring

    def test_normal_mode_stable(self) -> None:
        """Стабильный сервер — нормальный режим."""
        engine = PredictiveEngine()
        self._add_stable_samples(engine, "srv-1", count=20)
        result = engine.analyze("srv-1")
        assert result.trend.forecast_score > 0.7
        assert not result.should_migrate
        assert not result.enhanced_monitoring

    def test_insufficient_data(self) -> None:
        """Мало данных — рекомендация normal."""
        engine = PredictiveEngine()
        engine.add_sample("srv-1", {"rtt_ms": 45, "jitter_ms": 8, "loss_pct": 0})
        result = engine.analyze("srv-1")
        assert not result.should_migrate
        assert result.trend.recommendation == "normal"

    def test_recommended_interval(self) -> None:
        """Интервал опроса зависит от состояния."""
        engine = PredictiveEngine()
        # Enhanced monitoring → интервал 2с
        self._add_degrading_samples(engine, "srv-1", count=10)
        interval = engine.get_recommended_interval("srv-1")
        result = engine.analyze("srv-1")
        if result.enhanced_monitoring:
            assert interval == 2


# ── Decision Memory Tests ─────────────────────────────────────────────


class TestDecisionMemory:
    def test_record(self) -> None:
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[{"type": "DPI_Block", "confidence": 0.8}],
            action_taken="switch_to_WireGuard",
            trigger_reason="loss_spike",
        )
        assert did is not None
        assert len(mem._entries) == 1

    def test_update_success_fast(self) -> None:
        """Успех с малым downtime — confidence растёт быстро."""
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="switch_to_WireGuard",
            trigger_reason="test",
            confidence=0.5,
        )
        mem.update_result(did, "success", downtime_seconds=0.5)
        entry = mem._entries[did]
        assert entry.confidence == 0.58  # 0.5 + 0.08
        assert entry.result_status == "success"

    def test_update_success_slow(self) -> None:
        """Успех с большим downtime — confidence растёт медленно."""
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="switch_to_WireGuard",
            trigger_reason="test",
            confidence=0.5,
        )
        mem.update_result(did, "success", downtime_seconds=8.0)
        entry = mem._entries[did]
        assert entry.confidence == 0.51  # 0.5 + 0.01

    def test_update_failure(self) -> None:
        """Неудача — confidence падает."""
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="switch_to_WireGuard",
            trigger_reason="test",
            confidence=0.7,
        )
        mem.update_result(did, "failed", downtime_seconds=15.0)
        entry = mem._entries[did]
        assert entry.confidence == pytest.approx(0.55, rel=1e-4)  # 0.7 - 0.15

    def test_find_best_action(self) -> None:
        """Поиск лучшего действия для контекста."""
        mem = DecisionMemory()
        # Два решения для одного контекста
        did1 = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="switch_to_WireGuard",
            trigger_reason="test",
            confidence=0.5,
        )
        mem.update_result(did1, "success", downtime_seconds=0.5)  # confidence=0.58
        mem.update_result(did1, "success", downtime_seconds=0.3)  # confidence=0.66

        did2 = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="switch_protocol",
            trigger_reason="test",
            confidence=0.5,
        )
        mem.update_result(did2, "success", downtime_seconds=8.0)  # confidence=0.51

        best = mem.find_best_action({
            "geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner",
        })
        assert best == "switch_to_WireGuard"  # выше скоринг

    def test_decay_removes_stale(self) -> None:
        """Decay удаляет устаревшие записи."""
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="test_action",
            trigger_reason="test",
            confidence=0.2,  # низкий confidence
        )
        removed = mem.apply_decay(ttl_seconds=0)  # TTL=0 → все удаляются
        assert removed == 1
        assert did not in mem._entries

    def test_decay_keeps_active(self) -> None:
        """Decay сохраняет активные записи."""
        mem = DecisionMemory()
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="test_action",
            trigger_reason="test",
            confidence=0.8,
        )
        removed = mem.apply_decay(ttl_seconds=1_209_600)  # 14 дней
        assert removed == 0
        assert did in mem._entries

    def test_stats(self) -> None:
        mem = DecisionMemory()
        mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[],
            action_taken="test",
            trigger_reason="test",
        )
        stats = mem.stats()
        assert stats["total"] == 1
        assert stats["pending"] == 1

    def test_save_and_load(self, tmp_path) -> None:
        """Тест сохранения и загрузки из JSON."""
        path = str(tmp_path / "test_memory.json")
        mem = DecisionMemory(storage_path=path)
        did = mem.record(
            context={"geo": "UAE", "protocol": "VLESS", "provider_source": "Hetzner"},
            hypotheses_ranked=[{"type": "DPI", "confidence": 0.7}],
            action_taken="switch_to_WG",
            trigger_reason="loss",
            confidence=0.6,
        )
        mem.update_result(did, "success", 0.5)
        mem.save()

        # Загрузка
        mem2 = DecisionMemory(storage_path=path)
        assert len(mem2._entries) == 1
        assert mem2._entries[did].confidence == pytest.approx(0.68, rel=1e-4)
