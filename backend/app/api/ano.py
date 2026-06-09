"""SafeNet ANO API endpoints.

Интеграция когнитивного слоя (Graph, Causality, Predictive, Memory, Meta-Agent)
с REST API для взаимодействия с клиентскими скаутами и административной панелью.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status

from app.services.ano.causality_engine import CausalityEngine, Incident
from app.services.ano.decision_memory import DecisionMemory
from app.services.ano.graph_engine import GraphEngine, NodeType
from app.services.ano.meta_agent import MetaAgent
from app.services.ano.predictive_engine import PredictiveEngine
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ano", tags=["ano"])

# ── Глобальные сервисы (в проде должны быть через DI / FastAPI Depends) ──
_graph = GraphEngine()
_causality = CausalityEngine(_graph)
_predictive = PredictiveEngine()
_memory = DecisionMemory()
_meta_agent = MetaAgent(memory=_memory, shadow_mode=True)


# ── Pydantic Models ──────────────────────────────────────────────────────

class MetricsRequest(BaseModel):
    server_id: str
    rtt_ms: float
    jitter_ms: float
    loss_pct: float
    throughput_kbps: float = 0.0
    context: dict[str, Any] = {}


class IncidentResponse(BaseModel):
    incident_id: str
    scope: str
    confidence: float
    root_cause: str
    hypotheses: list[dict[str, Any]]
    predictive_recommendation: str
    should_migrate: bool


class RecommendationResponse(BaseModel):
    server_id: str
    recommended_action: Optional[str]
    confidence: float
    avg_downtime: float
    is_shadow: bool


class ShadowReportResponse(BaseModel):
    total_shadow_actions: int
    analysis_report: str


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=IncidentResponse, status_code=status.HTTP_200_OK)
async def analyze_metrics(request: MetricsRequest) -> IncidentResponse:
    """Анализ аномальных метрик: причинный анализ + прогноз."""
    # 1. Добавляем сэмпл в predictive engine
    _predictive.add_sample(request.server_id, {
        "rtt_ms": request.rtt_ms,
        "jitter_ms": request.jitter_ms,
        "loss_pct": request.loss_pct,
        "throughput_kbps": request.throughput_kbps,
    })

    # 2. Запускаем причинный анализ
    metrics_dict = request.model_dump(exclude={"server_id", "context"})
    incident = _causality.analyze(request.server_id, metrics_dict)

    # 3. Получаем прогноз
    pred_result = _predictive.analyze(request.server_id)

    # 4. Фиксируем в памяти (Shadow Mode, если включен)
    _meta_agent.evaluate_proposal(
        context=request.context or {"server_id": request.server_id},
        proposed_action=pred_result.trend.recommendation,
        predicted_downtime=1.0,  # Заглушка, реальный downtime известен постфактум
    )

    return IncidentResponse(
        incident_id=incident.id,
        scope=incident.scope,
        confidence=incident.confidence,
        root_cause=incident.root_cause,
        hypotheses=[{"cause": h.cause, "confidence": h.confidence} for h in incident.hypotheses],
        predictive_recommendation=pred_result.trend.recommendation,
        should_migrate=pred_result.should_migrate,
    )


@router.get("/recommendation/{server_id}", response_model=RecommendationResponse)
async def get_recommendation(server_id: str) -> RecommendationResponse:
    """Получить лучшую историческую рекомендацию для сервера/контекста."""
    # Для упрощения ищем по server_id в контексте
    context = {"server_id": server_id}
    best_action = _memory.find_best_action(context)
    
    if not best_action:
        return RecommendationResponse(
            server_id=server_id,
            recommended_action=None,
            confidence=0.0,
            avg_downtime=0.0,
            is_shadow=False,
        )

    # Находим запись для получения деталей
    entry = next(
        (e for e in _memory._entries.values() if e.action_taken.endswith(best_action)),
        None
    )

    is_shadow = best_action.startswith("SHADOW:")
    clean_action = best_action.replace("SHADOW:", "") if is_shadow else best_action

    return RecommendationResponse(
        server_id=server_id,
        recommended_action=clean_action,
        confidence=entry.confidence if entry else 0.0,
        avg_downtime=entry.avg_downtime if entry else 0.0,
        is_shadow=is_shadow,
    )


@router.get("/shadow/report", response_model=ShadowReportResponse)
async def get_shadow_report() -> ShadowReportResponse:
    """Получить аналитический отчёт Meta-Agent по накопленным данным."""
    shadow_log = _meta_agent.get_shadow_log()
    
    # Собираем инциденты из графа для анализа
    incidents = []
    for node_data in _graph.get_nodes_by_type(NodeType.INCIDENT):
        # В реальной реализации здесь был бы маппинг из dict в Incident
        # Для демо-целей пропускаем, отчёт сформируется на основе shadow_log
        pass

    # Генерируем отчёт на основе накопленных данных
    report = _meta_agent.analyze_incidents([])
    
    return ShadowReportResponse(
        total_shadow_actions=len(shadow_log),
        analysis_report=report.strip(),
    )
