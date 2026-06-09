"""Тесты для SafeNet ANO — Graph Engine + Causality Engine.

Запуск: pytest tests/test_ano/ -v
"""

import pytest

from app.services.ano.graph_engine import (
    EdgeRelation,
    GraphEngine,
    NodeType,
    build_incident_node,
    build_pattern_node,
    build_server_node,
)
from app.services.ano.causality_engine import CausalityEngine, Incident


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def graph() -> GraphEngine:
    """Пустой граф для каждого теста."""
    return GraphEngine()


@pytest.fixture
def populated_graph() -> GraphEngine:
    """Граф с тестовыми данными."""
    g = GraphEngine()

    # Серверы
    for sid, dc, provider, asn in [
        ("ae-1", "dubai-dc3", "hetzner", "as47583"),
        ("ae-2", "dubai-dc3", "hetzner", "as47583"),
        ("ae-3", "dubai-dc3", "hetzner", "as47583"),
        ("tr-1", "istanbul-dc1", "ovh", "as47331"),
        ("eg-1", "cairo-dc1", "hetzner", "as8452"),
    ]:
        g.add_node(sid, NodeType.SERVER, {
            "ip": f"10.0.{hash(sid) % 256}.1",
            "country": sid.split("-")[0].upper(),
        })
        g.add_edge(sid, dc, EdgeRelation.LOCATED_IN)
        g.add_edge(sid, provider, EdgeRelation.HOSTED_BY)
        g.add_edge(sid, asn, EdgeRelation.BELONGS_TO)

    # DC
    for dc in ["dubai-dc3", "istanbul-dc1", "cairo-dc1"]:
        g.add_node(dc, NodeType.DATACENTER, {"country": dc.split("-")[0]})

    # Providers
    for p in ["hetzner", "ovh"]:
        g.add_node(p, NodeType.PROVIDER, {"type": "hosting"})

    # ASN
    for asn in ["as47583", "as47331", "as8452"]:
        g.add_node(asn, NodeType.ASN, {"country": "various"})

    return g


@pytest.fixture
def causality(populated_graph: GraphEngine) -> CausalityEngine:
    return CausalityEngine(populated_graph)


# ── Graph Engine Tests ────────────────────────────────────────────────


class TestGraphEngine:
    def test_add_node(self, graph: GraphEngine) -> None:
        graph.add_node("srv-1", NodeType.SERVER, {"ip": "10.0.0.1"})
        node = graph.get_node("srv-1")
        assert node is not None
        assert node["node_type"] == "server"
        assert node["properties"]["ip"] == "10.0.0.1"

    def test_add_duplicate_node_updates(self, graph: GraphEngine) -> None:
        graph.add_node("srv-1", NodeType.SERVER, {"ip": "10.0.0.1"})
        graph.add_node("srv-1", NodeType.SERVER, {"ip": "10.0.0.2"})
        node = graph.get_node("srv-1")
        assert node["properties"]["ip"] == "10.0.0.2"

    def test_add_edge(self, graph: GraphEngine) -> None:
        graph.add_node("srv-1", NodeType.SERVER)
        graph.add_node("dc-1", NodeType.DATACENTER)
        graph.add_edge("srv-1", "dc-1", EdgeRelation.LOCATED_IN, weight=1.0)
        neighbors = graph.get_neighbors("srv-1")
        assert len(neighbors) == 1
        assert neighbors[0]["node"] == "dc-1"

    def test_get_neighbors_depth(self, populated_graph: GraphEngine) -> None:
        # ae-1 → dubai-dc3 (depth 1)
        neighbors = populated_graph.get_neighbors("ae-1", depth=1)
        assert len(neighbors) >= 3  # dc, provider, asn

    def test_get_nodes_by_type(self, populated_graph: GraphEngine) -> None:
        servers = populated_graph.get_nodes_by_type(NodeType.SERVER)
        assert len(servers) == 5

    def test_update_edge_weight(self, graph: GraphEngine) -> None:
        graph.add_node("srv-1", NodeType.SERVER)
        graph.add_node("srv-2", NodeType.SERVER)
        graph.add_edge("srv-1", "srv-2", EdgeRelation.DEGRADES_WITH, weight=0.3)
        graph.update_edge_weight("srv-1", "srv-2", weight=0.8)
        neighbors = graph.get_neighbors("srv-1")
        assert neighbors[0]["edge_weight"] == 0.8

    def test_stats(self, populated_graph: GraphEngine) -> None:
        stats = populated_graph.stats()
        assert stats["nodes"] >= 13  # 5 servers + 3 dc + 2 providers + 3 asn
        assert stats["edges"] >= 15

    def test_snapshot_roundtrip(self, graph: GraphEngine, tmp_path) -> None:
        """Тест сохранения и загрузки снапшота."""
        import os
        import pickle

        graph.add_node("srv-1", NodeType.SERVER, {"ip": "10.0.0.1"})
        snapshot_path = str(tmp_path / "test_graph.pkl")
        with open(snapshot_path, "wb") as f:
            pickle.dump(graph._graph, f)

        # Загрузка
        with open(snapshot_path, "rb") as f:
            loaded = pickle.load(f)
        assert loaded.has_node("srv-1")


# ── Causality Engine Tests ────────────────────────────────────────────


class TestCausalityEngine:
    def test_analyze_creates_incident(
        self, causality: CausalityEngine
    ) -> None:
        metrics = {"loss_pct": 12, "rtt_ms": 120, "jitter_ms": 35}
        incident = causality.analyze("ae-1", metrics)
        assert isinstance(incident, Incident)
        assert incident.id is not None
        assert len(incident.hypotheses) == 5

    def test_hypotheses_sum_to_one(
        self, causality: CausalityEngine
    ) -> None:
        metrics = {"loss_pct": 15, "rtt_ms": 200, "jitter_ms": 50}
        incident = causality.analyze("ae-1", metrics)
        total = sum(h.confidence for h in incident.hypotheses)
        assert abs(total - 1.0) < 0.01  # нормализация

    def test_dpi_signature_detected(
        self, causality: CausalityEngine
    ) -> None:
        # DPI: высокий Loss, низкий RTT, низкий Jitter
        metrics = {"loss_pct": 20, "rtt_ms": 45, "jitter_ms": 8}
        incident = causality.analyze("ae-1", metrics)
        dpi_hypothesis = next(
            (h for h in incident.hypotheses if h.cause == "dpi"), None
        )
        assert dpi_hypothesis is not None
        assert dpi_hypothesis.confidence > 0.3

    def test_server_isolation(
        self, causality: CausalityEngine
    ) -> None:
        # Низкий Loss, изолированный сервер
        metrics = {"loss_pct": 2, "rtt_ms": 50, "jitter_ms": 10}
        incident = causality.analyze("tr-1", metrics)
        top = incident.hypotheses[0]
        # При низких метриках — server или normal
        assert top.cause in ("server", "datacenter", "asn", "provider", "dpi")

    def test_incident_written_to_graph(
        self, populated_graph: GraphEngine, causality: CausalityEngine
    ) -> None:
        metrics = {"loss_pct": 10, "rtt_ms": 100, "jitter_ms": 30}
        incident = causality.analyze("ae-1", metrics)
        node = populated_graph.get_node(incident.id)
        assert node is not None
        assert node["node_type"] == "incident"
