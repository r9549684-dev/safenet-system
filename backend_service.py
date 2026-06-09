"""
service API — эндпоинт для получения WireGuard-конфига и ByeDPI-профиля.

POST /service/connect/{server_id}
  → Возвращает персональный WireGuard-конфиг + профиль ByeDPI для страны сервера.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.server import Server
from app.models.user import User
from app.models.connection import UserConnection
from app.services.wireguard import WireGuardService
from app.services.entitlements import is_user_premium, has_trial
from app.utils.security import decode_token

router = APIRouter(prefix="/service", tags=["service"])
# auto_error=False: возвращаем 401 вместо 403 при отсутствии токена
_bearer = HTTPBearer(auto_error=False)


# ── Schemas ───────────────────────────────────────────────────────────────────

class VpnConnectResponse(BaseModel):
    server_id: int
    server_country: str
    wg_config: str
    peer_ip: str
    byedpi_profile: dict[str, Any]
    mode: str  # "hybrid" | "amnezia_only"


# ── Auth dependency ────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Декодирует JWT и возвращает объект User из БД."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/connect/{server_id}", response_model=VpnConnectResponse)
async def connect_vpn(
    server_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VpnConnectResponse:
    """
    Возвращает персональный WireGuard-конфиг и ByeDPI-профиль для подключения.

    Логика:
    1. Проверяет доступ (trial или premium).
    2. Загружает сервер.
    3. Ищет существующее активное подключение (user, server) — переиспользует.
       Если нет — создаёт новое: генерирует ключи, выделяет IP.
    4. Обновляет last_used_at.
    5. Формирует WG-конфиг и ByeDPI-профиль по коду страны сервера.
    """
    # 1. Проверка доступа
    if not (is_user_premium(user) or has_trial(user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription expired. Please upgrade to continue.",
        )

    # 2. Загрузка сервера
    server_result = await session.execute(
        select(Server).where(Server.id == server_id, Server.is_active == True)
    )
    server = server_result.scalar_one_or_none()
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found or inactive",
        )

    # 3. Поиск или создание подключения
    conn_result = await session.execute(
        select(UserConnection).where(
            UserConnection.user_id == user.id,
            UserConnection.server_id == server_id,
            UserConnection.is_active == True,
        )
    )
    connection = conn_result.scalar_one_or_none()

    if connection is None:
        # Генерируем новую пару ключей
        private_key, public_key = WireGuardService.generate_keypair()

        # Выделяем свободный IP
        peer_ip = await WireGuardService.allocate_ip(session, server_id)

        # Сохраняем подключение
        connection = UserConnection(
            user_id=user.id,
            server_id=server_id,
            peer_private_key=private_key,
            peer_public_key=public_key,
            allocated_ip=peer_ip,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        session.add(connection)

    # 4. Обновляем время последнего использования
    connection.last_used_at = datetime.utcnow()
    await session.commit()

    # 5. Формируем WG-конфиг
    wg_config = WireGuardService.generate_wg_config(
        server=server,
        peer_private_key=connection.peer_private_key,
        peer_ip=connection.allocated_ip,
    )

    # 6. ByeDPI-профиль по стране сервера
    byedpi_profile = WireGuardService.get_byedpi_profile(server.country)

    # 7. Определяем режим: строгие страны → hybrid, остальные → amnezia_only
    strict_countries = {"TR", "EG", "AE", "SA", "IR", "CN", "RU"}
    mode = "hybrid" if server.country.upper() in strict_countries else "amnezia_only"

    return VpnConnectResponse(
        server_id=server.id,
        server_country=server.country,
        wg_config=wg_config,
        peer_ip=connection.allocated_ip,
        byedpi_profile=byedpi_profile,
        mode=mode,
    )
