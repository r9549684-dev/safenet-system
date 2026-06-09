"""SafeNet ANO — Knowledge Graph Engine.

In-memory граф на NetworkX. Структурные сущности сети: Server, Provider, ASN,
DataCenter, Protocol, GeoZone, Incident, Pattern.

Телеметрия НЕ хранится в графе — отдельно в TimescaleDB (scout_log, route_ranking).
Граф сбрасывается на диск через pickle в фоновом потоке (не блокирует event loop).

Путь хранения: D:\Felix\data\ano\graph_snapshot.pkl
"""

from __future__ import annotations

import logging
import os
import pickle
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import networkx as nx

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    SERVER = "server"
    PROVIDER = "provider"
    DATACENTER = "datacenter"
    ASN = "asn"
    PROTOCOL = "protocol"
    GEOZONE = "geozone"
    INCIDENT = "incident"
    PATTERN = "pattern"


class EdgeRelation(str, Enum):
    HOSTED_BY = "hosted_by"
    LOCATED_IN = "located_in"
    BELONGS_TO = "belongs_to"
    SUPPORTS = "supports"
    OPERATES_IN = "operates_in"
    SAME_POOL = "same_pool"
    DEGRADES_WITH = "degrades_with"
    CAUSED_BY = "caused_by"
    MATCHES = "matches"


@dataclass
class NodeData:
    node_id: str
    node_type: NodeType
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class EdgeData:
    source: str
    target: str
    relation: EdgeRelation
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0


class GraphEngine:
    """In-memory граф знаний SafeNet ANO.

    Потокобезопасность: все операции чтения/записи через threading.Lock.
    Сброс на диск: фоновый поток (daemon), не блокирует async event loop.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._lock = threading.RLock()  # Reentrant lock для предотвращения deadlock при вложенных вызовах (напр., stats -> get_nodes_by_type)

        # Вычисляем пути в момент инициализации, чтобы подхватить os.environ из conftest.py
        target_dir = os.environ.get("ANO_DATA_DIR", r"D:\Felix\data")
        self._snapshot_dir = os.path.join(target_dir, "ano")
        self._snapshot_path = os.path.join(self._snapshot_dir, "graph_snapshot.pkl")
        
        os.makedirs(self._snapshot_dir, exist_ok=True)
        self._load_snapshot()

    # ── Node operations ──────────────────────────────────────────────

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        import time

        props = dict(properties) if properties else {}
        node_type_val = node_type.value if isinstance(node_type, NodeType) else str(node_type)
        with self._lock:
            if self._graph.has_node(node_id):
                existing = self._graph.nodes[node_id]
                existing.setdefault("properties", {}).update(props)
                existing["updated_at"] = time.time()
            else:
                self._graph.add_node(
                    node_id,
                    node_type=node_type_val,
                    properties=props,
                    created_at=time.time(),
                    updated_at=time.time(),
                )

    def get_node(self, node_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            if not self._graph.has_node(node_id):
                return None
            return dict(self._graph.nodes[node_id])

    def get_nodes_by_type(self, node_type: NodeType) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {"node_id": n, **dict(self._graph.nodes[n])}
                for n in self._graph.nodes
                if self._graph.nodes[n].get("node_type") == node_type.value
            ]

    def update_node_properties(
        self, node_id: str, properties: dict[str, Any]
    ) -> None:
        import time

        with self._lock:
            if not self._graph.has_node(node_id):
                raise KeyError(f"Node not found: {node_id}")
            self._graph.nodes[node_id].update(properties)
            self._graph.nodes[node_id]["updated_at"] = time.time()

    # ── Edge operations ──────────────────────────────────────────────

    def add_edge(
        self,
        source: str,
        target: str,
        relation: EdgeRelation,
        weight: float = 1.0,
        properties: Optional[dict[str, Any]] = None,
    ) -> None:
        import time

        with self._lock:
            self._graph.add_edge(
                source,
                target,
                relation=relation.value,
                weight=weight,
                properties=properties or {},
                created_at=time.time(),
                updated_at=time.time(),
            )

    def update_edge_weight(
        self, source: str, target: str, weight: float
    ) -> None:
        import time

        with self._lock:
            if not self._graph.has_edge(source, target):
                raise KeyError(f"Edge not found: {source} → {target}")
            self._graph[source][target]["weight"] = weight
            self._graph[source][target]["updated_at"] = time.time()

    def get_neighbors(
        self, node_id: str, relation: Optional[EdgeRelation] = None, depth: int = 1
    ) -> list[dict[str, Any]]:
        """Построить подграф соседей до указанной глубины."""
        with self._lock:
            if not self._graph.has_node(node_id):
                return []

            visited: set[str] = {node_id}
            frontier: set[str] = {node_id}
            result: list[dict[str, Any]] = []

            for _ in range(depth):
                next_frontier: set[str] = set()
                for n in frontier:
                    for succ in self._graph.successors(n):
                        if succ not in visited:
                            edge_data = self._graph[n][succ]
                            if (
                                relation is None
                                or edge_data.get("relation") == relation.value
                            ):
                                visited.add(succ)
                                next_frontier.add(succ)
                                result.append(
                                    {
                                        "node": succ,
                                        "relation": edge_data.get("relation"),
                                        "edge_weight": edge_data.get("weight", 1.0),
                                        **dict(self._graph.nodes[succ]),
                                    }
                                )
                frontier = next_frontier

            return result

    def query_pattern(self, node_type: EdgeRelation, **filters) -> list[dict[str, Any]]:
        """Найти узлы по типу отношения и фильтрам."""
        with self._lock:
            results = []
            for n in self._graph.nodes:
                nd = self._graph.nodes[n]
                if nd.get("node_type") == node_type.value:
                    match = all(nd.get(k) == v for k, v in filters.items())
                    if match:
                        results.append({"node_id": n, **dict(nd)})
            return results

    # ── Persistence ──────────────────────────────────────────────────

    def snapshot_sync(self) -> None:
        """Синхронный сброс графа на диск."""
        with self._lock:
            with open(self._snapshot_path, "wb") as f:
                pickle.dump(self._graph, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("Graph snapshot saved: %s", self._snapshot_path)

    def snapshot_async(self) -> None:
        """Асинхронный сброс графа на диск в фоновом потоке."""
        thread = threading.Thread(target=self.snapshot_sync, daemon=True)
        thread.start()
        logger.info("Graph snapshot scheduled (background thread)")

    def _load_snapshot(self) -> None:
        if os.path.exists(self._snapshot_path):
            try:
                with open(self._snapshot_path, "rb") as f:
                    self._graph = pickle.load(f)
                logger.info(
                    "Graph snapshot loaded: %s (%d nodes, %d edges)",
                    self._snapshot_path,
                    self._graph.number_of_nodes(),
                    self._graph.number_of_edges(),
                )
            except Exception as exc:
                logger.warning("Failed to load graph snapshot: %s", exc)
                self._graph = nx.DiGraph()

    # ── Stats ────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "nodes": self._graph.number_of_nodes(),
                "edges": self._graph.number_of_edges(),
                "node_types": {
                    nt.value: len(self.get_nodes_by_type(nt))
                    for nt in NodeType
                },
            }


# ── Factory helpers ──────────────────────────────────────────────────


def build_server_node(server_id: str, **props) -> tuple[str, NodeType, dict]:
    return (server_id, NodeType.SERVER, props)


def build_incident_node(
    incident_id: str,
    scope: str,
    confidence: float,
    affected_entities: list[str],
    root_cause: str = "unknown",
    resolution: str = "none",
    evidence: Optional[dict] = None,
) -> tuple[str, NodeType, dict]:
    return (
        incident_id,
        NodeType.INCIDENT,
        {
            "scope": scope,
            "confidence": confidence,
            "affected_entities": affected_entities,
            "root_cause": root_cause,
            "resolution": resolution,
            "evidence": evidence or {},
        },
    )


def build_pattern_node(
    pattern_id: str,
    description: str,
    confidence: float,
    ttl_days: int = 14,
) -> tuple[str, NodeType, dict]:
    import time

    return (
        pattern_id,
        NodeType.PATTERN,
        {
            "description": description,
            "confidence": confidence,
            "ttl_days": ttl_days,
            "last_confirmed": time.time(),
            "created_at": time.time(),
        },
    )
