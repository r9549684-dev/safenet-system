"""Тесты для NodeRanker (SafeNet ANO: Эволюционное ранжирование узлов)."""
import pytest
from app.services.ano.node_ranker import NodeRanker, NodeMetrics


class TestNodeRanker:
    def test_calculate_rating_green_zone_excellent(self):
        """Отличный узел должен получить высокий рейтинг (> 15)."""
        metrics = NodeMetrics(
            node_id="node-1",
            rtt_avg=30.0,         # Низкий пинг
            jitter=5.0,           # Стабильное соединение
            loss_pct=0.5,         # Минимальные потери
            throughput_kbps=8000.0, # Высокая скорость
            life_hours=100.0      # Давно не блокировался
        )
        rating = NodeRanker.calculate_rating(metrics)
        assert rating > 15.0
        assert NodeRanker.get_zone(rating) == "GREEN"

    def test_calculate_rating_red_zone_high_loss(self):
        """Узел с высокими потерями (>15%) должен получить штраф и попасть в Красную зону [2.0, 5.0)."""
        metrics = NodeMetrics(
            node_id="node-2",
            rtt_avg=10.0,         # Отличный пинг для компенсации
            jitter=10.0,
            loss_pct=20.0,        # Высокие потери (штраф x0.3 применяется ПОСЛЕ базового расчета)
            throughput_kbps=8000.0, # Высокая скорость
            life_hours=100.0
        )
        rating = NodeRanker.calculate_rating(metrics)
        assert NodeRanker.get_zone(rating) == "RED"
        # Убедимся, что рейтинг попал в диапазон Красной зоны
        assert 2.0 <= rating < 5.0

    def test_calculate_rating_black_zone_extreme_loss(self):
        """Узел с экстремальными потерями (>30%) должен получить жесткий штраф (x0.1)."""
        metrics = NodeMetrics(
            node_id="node-3",
            rtt_avg=50.0,
            jitter=15.0,
            loss_pct=35.0,        # Экстремальные потери (штраф x0.1)
            throughput_kbps=2000.0,
            life_hours=10.0
        )
        rating = NodeRanker.calculate_rating(metrics)
        assert NodeRanker.get_zone(rating) == "BLACK"
        assert rating < 2.0

    def test_calculate_rating_jitter_penalty(self):
        """Узел с высоким джиттером (>100мс) должен получить штраф x0.5."""
        metrics = NodeMetrics(
            node_id="node-4",
            rtt_avg=40.0,
            jitter=120.0,         # Высокий джиттер (штраф x0.5)
            loss_pct=2.0,
            throughput_kbps=6000.0,
            life_hours=80.0
        )
        rating = NodeRanker.calculate_rating(metrics)
        assert rating < 15.0 # Должен упасть из-за штрафа джиттера

    def test_select_best_node_filters_and_sorts(self):
        """select_best_node должен отфильтровать плохие узлы и вернуть лучший из зеленых."""
        nodes_data = [
            {"id": "bad-1", "rtt_avg": 100.0, "jitter": 50.0, "loss_pct": 25.0, "throughput_kbps": 1000.0, "life_hours": 5.0},
            {"id": "good-1", "rtt_avg": 35.0, "jitter": 8.0, "loss_pct": 1.0, "throughput_kbps": 7000.0, "life_hours": 150.0},
            {"id": "good-2", "rtt_avg": 40.0, "jitter": 10.0, "loss_pct": 2.0, "throughput_kbps": 6000.0, "life_hours": 120.0},
            {"id": "black-1", "rtt_avg": 200.0, "jitter": 100.0, "loss_pct": 40.0, "throughput_kbps": 500.0, "life_hours": 2.0},
        ]

        best = NodeRanker.select_best_node(nodes_data, min_rating=15.0)
        
        assert best is not None
        assert best["id"] == "good-1" # good-1 должен быть выше good-2 по рейтингу
        assert best["ano_zone"] == "GREEN"
        
        # Убедимся, что плохие узлы не были выбраны
        assert best["id"] not in ["bad-1", "black-1"]

    def test_select_best_node_fallback_to_none(self):
        """Если все узлы в красной/черной зоне, метод должен вернуть None."""
        nodes_data = [
            {"id": "bad-1", "rtt_avg": 150.0, "jitter": 80.0, "loss_pct": 20.0, "throughput_kbps": 1000.0, "life_hours": 5.0},
            {"id": "black-1", "rtt_avg": 300.0, "jitter": 150.0, "loss_pct": 45.0, "throughput_kbps": 200.0, "life_hours": 1.0},
        ]

        best = NodeRanker.select_best_node(nodes_data, min_rating=15.0)
        assert best is None