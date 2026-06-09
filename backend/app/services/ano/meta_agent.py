"""SafeNet ANO — Meta-Agent & Shadow Mode.

Shadow Mode: Пассивное накопление данных о предлагаемых действиях без их реального применения.
LLM-анализ: Генерация паттернов на основе исторических инцидентов (эвристическая заглушка).
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .causality_engine import Incident
from .decision_memory import DecisionMemory

logger = logging.getLogger(__name__)


@dataclass
class ShadowAction:
    action_id: str
    timestamp: float
    context: dict[str, Any]
    proposed_action: str
    predicted_downtime: float
    executed: bool = False


class MetaAgent:
    """Управляет Shadow Mode и анализом инцидентов.

    В Shadow Mode все предлагаемые изменения маршрутизации или политик
    только логируются и оцениваются через Decision Memory, но не применяются.
    """

    def __init__(self, memory: DecisionMemory, shadow_mode: bool = True) -> None:
        self._memory = memory
        self._shadow_mode = shadow_mode
        self._shadow_log: list[ShadowAction] = []

    def evaluate_proposal(
        self,
        context: dict[str, Any],
        proposed_action: str,
        predicted_downtime: float = 1.0,
    ) -> str:
        """Оценивает предложение в Shadow Mode (не применяет его)."""
        action_id = str(uuid.uuid4())
        
        shadow_action = ShadowAction(
            action_id=action_id,
            timestamp=time.time(),
            context=context,
            proposed_action=proposed_action,
            predicted_downtime=predicted_downtime,
            executed=False,
        )
        self._shadow_log.append(shadow_action)
        
        if self._shadow_mode:
            # Фиксируем в памяти с префиксом SHADOW: для отличия от реальных действий
            self._memory.record(
                context=context,
                hypotheses_ranked=[],
                action_taken=f"SHADOW:{proposed_action}",
                trigger_reason="meta_agent_evaluation",
            )
            logger.debug("Shadow evaluation recorded: %s", proposed_action)
            
        return action_id

    def get_shadow_log(self) -> list[ShadowAction]:
        """Возвращает журнал теневых действий."""
        return list(self._shadow_log)

    def analyze_incidents(self, incidents: list[Incident]) -> str:
        """Генерирует отчёт о паттернах сбоев (эвристическая заглушка для LLM)."""
        if not incidents:
            return "ANALYSIS REPORT: No incidents to analyze."
        
        scope_counts: dict[str, int] = {}
        root_causes: dict[str, int] = {}
        
        for inc in incidents:
            scope_counts[inc.scope] = scope_counts.get(inc.scope, 0) + 1
            root_causes[inc.root_cause] = root_causes.get(inc.root_cause, 0) + 1
            
        top_scope = max(scope_counts, key=scope_counts.get) if scope_counts else "unknown"
        top_cause = max(root_causes, key=root_causes.get) if root_causes else "unknown"
        
        report = (
            f"=== META-AGENT ANALYSIS REPORT ===\n"
            f"Total incidents analyzed: {len(incidents)}\n"
            f"Most frequent scope: {top_scope} ({scope_counts.get(top_scope, 0)} cases)\n"
            f"Most frequent root cause: {top_cause} ({root_causes.get(top_cause, 0)} cases)\n"
            f"Shadow Mode Status: {'ACTIVE' if self._shadow_mode else 'INACTIVE'}\n"
            f"Recommendation: Review {top_scope} infrastructure before disabling Shadow Mode.\n"
        )
        return report
