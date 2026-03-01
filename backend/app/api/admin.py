"""
Admin API — lookup клиента по device_id (UUID).
Используется техподдержкой и Telegram-ботом агента.

Защита: X-Admin-Secret header == settings.ADMIN_SECRET
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.models.connection import UserConnection

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth ───────────────────────────────────────────────────────────────────────

def require_admin(x_admin_secret: Optional[str] = Header(default=None)):
    if not settings.ADMIN_SECRET or x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin secret",
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _trial_status(user: User) -> str:
    if user.is_premium:
        return "premium"
    if user.trial_ends_at and user.trial_ends_at > datetime.utcnow():
        return "trial_active"
    return "trial_expired"


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.get("/users/lookup", dependencies=[Depends(require_admin)])
async def lookup_user(
    device_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Поиск клиента по UUID (device_id).
    Возвращает полный профиль + последние 5 подключений.

    Пример:
        GET /admin/users/lookup?device_id=9af931ec-2496-47cf-9325-a1bea5327f6e
        X-Admin-Secret: safenet_admin_2026
    """
    result = await session.execute(
        select(User).where(User.device_id == device_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with device_id '{device_id}' not found",
        )

    # Последние 5 подключений
    conn_result = await session.execute(
        select(UserConnection)
        .where(UserConnection.user_id == user.id)
        .order_by(UserConnection.created_at.desc())
        .limit(5)
    )
    connections = conn_result.scalars().all()

    return {
        "device_id": user.device_id,
        "country": user.country,
        "status": _trial_status(user),
        "is_premium": user.is_premium,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "post_trial_connect_count": user.post_trial_connect_count,
        "account_created_at": user.created_at.isoformat(),
        "connections": [
            {
                "server_id": c.server_id,
                "allocated_ip": c.allocated_ip,
                "is_active": c.is_active,
                "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in connections
        ],
    }
