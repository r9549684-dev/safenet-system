"""SafeNet ANO — Decision Memory Layer.

Хранение пар «Контекст — Действие — Результат — Стоимость».
Интеграция с LightRAG для семантического поиска.
Decay: confidence снижается при отсутствии подтверждений.

Единая семантика confidence ∈ [0, 1]:
  0.0 = нет уверенности
  0.5 = умеренная
  0.8 = высокая (порог для действий)
  1.0 = абсолютная
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DecisionEntry:
    decision_id: str
    timestamp: float
    context: dict[str, str]
    hypotheses_ranked: list[dict[str, Any]]
    action_taken: str
    trigger_reason: str
    result_status: str  # "success" | "failed" | "pending"
    downtime_seconds: float
    rtt_post_migration: float
    confidence: float  # [0, 1]
    use_count: int = 1
    created_at: float = 0.0
    last_used: float = 0.0

    def __post_init__(self) -> None:
        if self.created_at == 0.0:
            object.__setattr__(self, "created_at", time.time())
        if self.last_used == 0.0:
            object.__setattr__(self, "last_used", time.time())


class DecisionMemory:
    """Память решений SafeNet ANO.

    Хранит историю решений хендовера с привязкой к контексту
    (geo, protocol, provider). Используется для:
      - Семантического поиска похожих решений
      - Оценки качества через Score = confidence × use_count / (1 + avg_downtime)
      - Decay: confidence снижается при неудачах

    Первичная реализация: in-memory + JSON файл.
    Целевая: LightRAG для семантического поиска.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self._entries: dict[str, DecisionEntry] = {}
        self._storage_path = storage_path
        if storage_path:
            self._load()

    # ── CRUD ─────────────────────────────────────────────────────────

    def record(
        self,
        context: dict[str, str],
        hypotheses_ranked: list[dict[str, Any]],
        action_taken: str,
        trigger_reason: str,
        result_status: str = "pending",
        downtime_seconds: float = 0.0,
        rtt_post_migration: float = 0.0,
        confidence: float = 0.5,
    ) -> str:
        """Записать новое решение."""
        decision_id = str(uuid.uuid4())
        entry = DecisionEntry(
            decision_id=decision_id,
            timestamp=time.time(),
            context=context,
            hypotheses_ranked=hypotheses_ranked,
            action_taken=action_taken,
            trigger_reason=trigger_reason,
            result_status=result_status,
            downtime_seconds=downtime_seconds,
            rtt_post_migration=rtt_post_migration,
            confidence=confidence,
            use_count=1,
        )
        self._entries[decision_id] = entry
        logger.info(
            "Decision recorded: %s action=%s confidence=%.2f",
            decision_id,
            action_taken,
            confidence,
        )
        return decision_id

    def update_result(
        self,
        decision_id: str,
        result_status: str,
        downtime_seconds: float,
        rtt_post_migration: float = 0.0,
    ) -> None:
        """Обновить результат решения (после хендовера)."""
        entry = self._entries.get(decision_id)
        if not entry:
            logger.warning("Decision not found: %s", decision_id)
            return

        entry.result_status = result_status
        entry.downtime_seconds = downtime_seconds
        entry.rtt_post_migration = rtt_post_migration
        entry.last_used = time.time()

        # Обновить confidence с учётом качества
        if result_status == "success":
            if downtime_seconds < 2.0:
                entry.confidence = min(entry.confidence + 0.08, 1.0)
            elif downtime_seconds <= 5.0:
                entry.confidence = min(entry.confidence + 0.04, 1.0)
            else:
                entry.confidence = min(entry.confidence + 0.01, 1.0)
        else:
            entry.confidence = max(entry.confidence - 0.15, 0.0)

        entry.use_count += 1
        logger.info(
            "Decision updated: %s status=%s downtime=%.1fs confidence=%.2f",
            decision_id,
            result_status,
            downtime_seconds,
            entry.confidence,
        )

    def find_best_action(self, context: dict[str, str]) -> Optional[str]:
        """Найти лучшее решение для текущего контекста.

        Скоринг: confidence × use_count / (1 + avg_downtime)
        """
        candidates: list[tuple[str, float]] = []

        for entry in self._entries.values():
            if entry.result_status == "failed":
                continue
            # Проверка совпадения контекста (минимум 2 из 3 полей)
            match_count = sum(
                1
                for key in ("geo", "protocol", "provider_source")
                if entry.context.get(key) == context.get(key)
            )
            if match_count < 2:
                continue

            # Скоринг
            score = entry.confidence * entry.use_count / (1 + entry.downtime_seconds)
            candidates.append((entry.action_taken, score))

        if not candidates:
            return None

        # Вернуть action с максимальным скорингом
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    # ── Decay ────────────────────────────────────────────────────────

    def apply_decay(self, ttl_seconds: float = 1_209_600) -> int:
        """Удалить устаревшие записи (по умолчанию TTL = 14 дней).

        Returns:
            Количество удалённых записей.
        """
        now = time.time()
        to_remove = [
            did
            for did, entry in self._entries.items()
            if now - entry.last_used > ttl_seconds or entry.confidence < 0.3
        ]
        for did in to_remove:
            del self._entries[did]
        if to_remove:
            logger.info("Decay: removed %d stale decisions", len(to_remove))
        return len(to_remove)

    # ── Stats ────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        total = len(self._entries)
        success = sum(1 for e in self._entries.values() if e.result_status == "success")
        failed = sum(1 for e in self._entries.values() if e.result_status == "failed")
        pending = sum(1 for e in self._entries.values() if e.result_status == "pending")
        avg_confidence = (
            sum(e.confidence for e in self._entries.values()) / total if total else 0
        )
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "pending": pending,
            "avg_confidence": round(avg_confidence, 4),
        }

    # ── Persistence ──────────────────────────────────────────────────

    def _load(self) -> None:
        """Загрузка из JSON файла."""
        import json
        import os

        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                entry = DecisionEntry(**item)
                self._entries[entry.decision_id] = entry
            logger.info("Decision memory loaded: %d entries", len(self._entries))
        except Exception as exc:
            logger.warning("Failed to load decision memory: %s", exc)

    def save(self) -> None:
        """Сохранение в JSON файл."""
        import json
        import os

        if not self._storage_path:
            return
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        data = [
            {
                "decision_id": e.decision_id,
                "timestamp": e.timestamp,
                "context": e.context,
                "hypotheses_ranked": e.hypotheses_ranked,
                "action_taken": e.action_taken,
                "trigger_reason": e.trigger_reason,
                "result_status": e.result_status,
                "downtime_seconds": e.downtime_seconds,
                "rtt_post_migration": e.rtt_post_migration,
                "confidence": e.confidence,
                "use_count": e.use_count,
                "created_at": e.created_at,
                "last_used": e.last_used,
            }
            for e in self._entries.values()
        ]
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Decision memory saved: %d entries", len(self._entries))
