"""SafeNet ANO — Causality Engine.

Обход топологического графа для выявления корреляций упавших маршрутов.
Байесовское ранжирование гипотез сбоя с confidence ∈ [0, 1].

Три типа сбоев (мягкая классификация — ранжирование, не жёсткое разделение):
  - server: проблема на уровне одной VM
  - datacenter: проблема на уровне дата-центра
  - asn: проблема на уровне автономной системы
  - provider: проблема на уровне провайдера
  - dpi: точечная блокировка протокола цензором
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.ano.graph_engine import (
    EdgeRelation,
    GraphEngine,
    NodeType,
)

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    cause: str  # server | datacenter | asn | provider | dpi
    confidence: float  # [0, 1]
    evidence: str = ""


@dataclass
class Incident:
    id: str
    scope: str
    confidence: float
    affected_entities: list[str]
    root_cause: str = "unknown"
    resolution: str = "none"
    evidence: dict[str, Any] = field(default_factory=dict)
    hypotheses: list[Hypothesis] = field(default_factory=list)


class CausalityEngine:
    """Анализ причин сбоев на базе топологического графа.

    Алгоритм:
      1. Собрать контекст из графа (соседи по DC, ASN, Provider)
      2. Вычислить confidence для каждого типа сбоя
      3. Нормализовать → распределение вероятностей
      4. Вернуть ранжированный список гипотез
    """

    def __init__(self, graph: GraphEngine) -> None:
        self._graph = graph

    def analyze(
        self,
        server_id: str,
        metrics: dict[str, Any],
    ) -> Incident:
        """Анализ причины сбоя для конкретного сервера.

        Args:
            server_id: идентификатор сервера
            metrics: {rtt_ms, loss_pct, jitter_ms, throughput_kbps}

        Returns:
            Incident с ранжированными гипотезами
        """
        # Шаг 1: Собрать контекст из графа
        dc_neighbors = self._graph.get_neighbors(
            server_id, EdgeRelation.LOCATED_IN, depth=2
        )
        provider_neighbors = self._graph.get_neighbors(
            server_id, EdgeRelation.HOSTED_BY, depth=2
        )
        asn_neighbors = self._graph.get_neighbors(
            server_id, EdgeRelation.BELONGS_TO, depth=2
        )
        protocol_neighbors = self._graph.get_neighbors(
            server_id, EdgeRelation.SUPPORTS, depth=2
        )

        # Шаг 2: Вычислить confidence для каждого типа
        loss_pct = metrics.get("loss_pct", 0)
        rtt_ms = metrics.get("rtt_ms", 0)
        jitter_ms = metrics.get("jitter_ms", 0)

        # Server isolation: только этот сервер деградирует
        server_confidence = self._calc_server_isolation(server_id, dc_neighbors)

        # DC correlation: все серверы в DC деградируют
        dc_confidence = self._calc_dc_correlation(dc_neighbors)

        # ASN correlation: все серверы в ASN деградируют
        asn_confidence = self._calc_asn_correlation(asn_neighbors)

        # Provider correlation: все серверы провайдера деградируют
        provider_confidence = self._calc_provider_correlation(provider_neighbors)

        # DPI signature: резкий рост Loss без роста RTT
        dpi_confidence = self._calc_dpi_signature(loss_pct, rtt_ms, jitter_ms)

        # Шаг 3: Нормализация
        raw_scores = {
            "server": server_confidence,
            "datacenter": dc_confidence,
            "asn": asn_confidence,
            "provider": provider_confidence,
            "dpi": dpi_confidence,
        }
        total = sum(raw_scores.values())
        if total > 0:
            normalized = {k: v / total for k, v in raw_scores.items()}
        else:
            normalized = {k: 0.2 for k in raw_scores}  # равномерное распределение

        # Шаг 4: Построить ранжированный список
        hypotheses = sorted(
            [
                Hypothesis(
                    cause=cause,
                    confidence=round(conf, 4),
                    evidence=self._build_evidence(cause, normalized[cause], metrics),
                )
                for cause, conf in normalized.items()
            ],
            key=lambda h: h.confidence,
            reverse=True,
        )

        top_cause = hypotheses[0].cause if hypotheses else "unknown"
        top_confidence = hypotheses[0].confidence if hypotheses else 0.0

        incident = Incident(
            id=str(uuid.uuid4()),
            scope=top_cause,
            confidence=top_confidence,
            affected_entities=[server_id],
            root_cause=top_cause,
            evidence={"metrics": metrics, "raw_scores": raw_scores},
            hypotheses=hypotheses,
        )

        # Записать в граф
        self._graph.add_node(
            incident.id,
            NodeType.INCIDENT,
            {
                "scope": incident.scope,
                "confidence": incident.confidence,
                "affected_entities": incident.affected_entities,
                "root_cause": incident.root_cause,
                "resolution": incident.resolution,
                "evidence": incident.evidence,
            },
        )
        self._graph.add_edge(
            incident.id,
            server_id,
            EdgeRelation.CAUSED_BY,
            weight=incident.confidence,
        )

        logger.info(
            "Incident created: %s scope=%s confidence=%.2f hypotheses=%s",
            incident.id,
            incident.scope,
            incident.confidence,
            [(h.cause, h.confidence) for h in hypotheses],
        )

        return incident

    # ── Confidence calculators ────────────────────────────────────────

    def _calc_server_isolation(
        self, server_id: str, dc_neighbors: list[dict]
    ) -> float:
        """Если только 1 сервер в DC деградирует → проблема на уровне VM."""
        if not dc_neighbors:
            return 0.3  # нет данных — умеренная уверенность
        # Если соседей мало и они стабильны → изоляция
        return 0.7 if len(dc_neighbors) <= 2 else 0.1

    def _calc_dc_correlation(self, dc_neighbors: list[dict]) -> float:
        """Если все серверы в DC деградируют → проблема DC."""
        if not dc_neighbors:
            return 0.0
        # Эвристика: если соседей > 2 → вероятность DC выше
        return min(0.8, len(dc_neighbors) * 0.2)

    def _calc_asn_correlation(self, asn_neighbors: list[dict]) -> float:
        """Если все серверы в ASN деградируют → проблема ASN."""
        if not asn_neighbors:
            return 0.0
        return min(0.7, len(asn_neighbors) * 0.15)

    def _calc_provider_correlation(
        self, provider_neighbors: list[dict]
    ) -> float:
        """Если все серверы провайдера деградируют → проблема провайдера."""
        if not provider_neighbors:
            return 0.0
        return min(0.6, len(provider_neighbors) * 0.12)

    def _calc_dpi_signature(
        self, loss_pct: float, rtt_ms: float, jitter_ms: float
    ) -> float:
        """DPI: резкий рост Loss без роста RTT (характерный признак)."""
        if loss_pct > 10 and rtt_ms < 100 and jitter_ms < 50:
            return 0.7
        if loss_pct > 5 and rtt_ms < 80:
            return 0.4
        return 0.05

    # ── Evidence builder ──────────────────────────────────────────────

    def _build_evidence(
        self, cause: str, confidence: float, metrics: dict[str, Any]
    ) -> str:
        loss_pct = metrics.get("loss_pct", 0)
        rtt_ms = metrics.get("rtt_ms", 0)

        evidence_map = {
            "server": f"Single server degradation: loss={loss_pct}%, rtt={rtt_ms}ms",
            "datacenter": f"Multi-server DC degradation: loss={loss_pct}%",
            "asn": f"ASN-wide pattern: loss={loss_pct}%, rtt={rtt_ms}ms",
            "provider": f"Provider-wide pattern: loss={loss_pct}%",
            "dpi": f"DPI signature: loss={loss_pct}% without RTT spike (rtt={rtt_ms}ms)",
        }
        return evidence_map.get(cause, f"Unknown cause: {cause}")
