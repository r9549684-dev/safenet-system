import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models.user import User
from app.schemas.users import MeResponse
from app.utils.security import decode_token
from app.services.entitlements import is_user_premium, now_utc

router = APIRouter(prefix="/users", tags=["users"])
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/device")

_TOKEN_CHARS = string.ascii_uppercase + string.digits
_TOKEN_TTL_MINUTES = 10


async def get_current_user(session: AsyncSession = Depends(get_session), token: str = Depends(oauth2)) -> User:
    try:
        data = decode_token(token)
        user_id = data["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    q = await session.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return user


# ── POST /users/telegram-link-token ──────────────────────────────────────────

@router.post("/telegram-link-token")
async def generate_telegram_link_token(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """
    Генерирует одноразовый 6-символьный токен для привязки Telegram-аккаунта.
    Flutter вызывает этот эндпоинт, затем открывает:
      https://t.me/{BOT_USERNAME}?start={token}
    Бот вызывает POST /users/link-telegram с токеном и своим telegram_id.
    TTL токена: 10 минут.
    """
    token = "".join(random.choices(_TOKEN_CHARS, k=6))
    expires = datetime.utcnow() + timedelta(minutes=_TOKEN_TTL_MINUTES)

    user.link_token = token
    user.link_token_expires = expires
    await session.commit()

    bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}"
    return {
        "token": token,
        "bot_url": bot_url,
        "expires_at": expires.isoformat(),
        "ttl_minutes": _TOKEN_TTL_MINUTES,
    }


# ── POST /users/link-telegram (admin) ────────────────────────────────────────

class LinkTelegramRequest(BaseModel):
    token: str
    telegram_id: int


def _require_admin(x_admin_secret: Optional[str] = Header(default=None)):
    if not settings.ADMIN_SECRET or x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/link-telegram", dependencies=[Depends(_require_admin)])
async def link_telegram(
    body: LinkTelegramRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Вызывается @SafeBypass_bot при команде /start {token}.
    Находит пользователя по link_token, проверяет TTL,
    записывает telegram_id и очищает токен.
    """
    q = await session.execute(select(User).where(User.link_token == body.token))
    user = q.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Token not found or already used")

    if not user.link_token_expires or user.link_token_expires < datetime.utcnow():
        user.link_token = None
        user.link_token_expires = None
        await session.commit()
        raise HTTPException(status_code=410, detail="Token expired")

    # Привязываем telegram_id
    user.telegram_id = body.telegram_id
    user.link_token = None
    user.link_token_expires = None
    await session.commit()

    return {
        "ok": True,
        "device_id": user.device_id,
        "country": user.country,
        "status": "premium" if user.is_premium else ("trial_active" if user.is_trial else "expired"),
    }


# ── POST /users/unlink-telegram (admin) ───────────────────────────────────────────

class UnlinkTelegramRequest(BaseModel):
    telegram_id: int


@router.post("/unlink-telegram", dependencies=[Depends(_require_admin)])
async def unlink_telegram(
    body: UnlinkTelegramRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Вызывается @SafeBypass_bot при команде /unlink.
    Очищает telegram_id у пользователя — связь между VPN-аккаунтом
    и Telegram полностью удаляется.
    """
    q = await session.execute(select(User).where(User.telegram_id == body.telegram_id))
    user = q.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="No user linked to this Telegram ID")

    user.telegram_id = None
    await session.commit()

    return {
        "ok": True,
        "message": "Telegram account unlinked successfully",
        "device_id": user.device_id,
    }
