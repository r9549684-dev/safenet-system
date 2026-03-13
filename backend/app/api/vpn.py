"""
VPN API — эндпоинт для получения WireGuard-конфига, ByeDPI-профиля и VLESS+Reality.

POST /vpn/connect/{server_id}
  → Возвращает персональный WireGuard-конфиг + профиль ByeDPI + vless_config.
"""
import uuid
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
log = logging.getLogger(__name__)
from app.models.server import Server
from app.models.user import User
from app.models.connection import UserConnection
from app.services.wireguard import WireGuardService
from app.services.xray import get_vless_config
from app.services.entitlements import is_user_premium, has_trial
from app.utils.security import decode_token

router = APIRouter(prefix="/vpn", tags=["vpn"])
_bearer = HTTPBearer(auto_error=False)


# ── Schemas ───────────────────────────────────────────────────────────────────

class VpnConnectResponse(BaseModel):
    server_id: int
    server_country: str
    wg_config: str
    peer_ip: str
    byedpi_profile: dict[str, Any]
    mode: str  # "hybrid" | "amnezia_only"
    vless_config: dict[str, Any]
    show_paywall: bool = False  # true на 2-м, 4-м... подключении после истечения триала


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
    Возвращает персональный WireGuard-конфиг, ByeDPI-профиль и VLESS+Reality конфиг.

    Логика:
    1. Проверяет доступ (trial или premium).
    2. Загружает сервер.
    3. Ищет существующее активное подключение (user, server) — переиспользует.
       Если нет — создаёт новое: генерирует ключи, выделяет IP, регистрирует пир на сервере.
    4. Обновляет last_used_at.
    5. Формирует WG-конфиг, ByeDPI-профиль и VLESS+Reality конфиг.
    """
    # 1. Проверка доступа
    # premium / активный триал → полный доступ
    # истёкший триал (не premium) → ограниченный доступ: сессия 5 мин, watchdog обрывает
    is_limited = not (is_user_premium(user) or has_trial(user))

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
    # Ищем любую запись (активную ИЛИ деактивированную watchdog'ом) — сначала последнюю.
    conn_result = await session.execute(
        select(UserConnection)
        .where(
            UserConnection.user_id == user.id,
            UserConnection.server_id == server_id,
        )
        .order_by(UserConnection.created_at.desc())
        .limit(1)
    )
    connection = conn_result.scalar_one_or_none()

    peer_was_active = False  # флаг: peer уже был активен до этого вызова

    if connection is None:
        # Первое подключение: создаём запись с ключами и IP
        private_key, public_key = WireGuardService.generate_keypair()
        peer_ip = await WireGuardService.allocate_ip(session, server_id)
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
    else:
        # Переиспользуем существующую запись (IP и ключи не меняем, просто реактивируем)
        peer_was_active = connection.is_active  # запоминаем статус ДО реактивации
        connection.is_active = True

    # 4. Обновляем время последнего использования (это старт сессии для watchdog'а)
    connection.last_used_at = datetime.utcnow()

    # 4.1 Для limited-пользователей: счётчик подключений → show_paywall через раз
    show_paywall = False
    if is_limited:
        user.post_trial_connect_count += 1
        show_paywall = (user.post_trial_connect_count % 2 == 0)

    await session.commit()

    # 5. Регистрируем пир на WireGuard-интерфейсе
    await WireGuardService.add_peer_to_server(
        pubkey=connection.peer_public_key,
        ip=connection.allocated_ip,
    )

    # 5.1 Лимит скорости: только при НОВОМ подключении или реактивации после watchdog-кика.
    # Если peer уже был активен — пропускаем, чтобы не прерывать трафик
    # (tc class del/add вызывает кратковременный packet loss, критичный для VoIP).
    _user_is_premium = is_user_premium(user)
    if not peer_was_active:
        tier = "premium" if _user_is_premium else "trial"
        log.info("[SPEED] user=%s tier=%s peer_ip=%s (new/reactivated)", user.device_id, tier, connection.allocated_ip)
        await WireGuardService.apply_speed_limit(peer_ip=connection.allocated_ip, tier=tier)
    else:
        log.info("[SPEED] skip set-speed for %s — peer already active (VoIP safe)", connection.allocated_ip)

    # 6. Формируем WG-конфиг
    wg_config = WireGuardService.generate_wg_config(
        server=server,
        peer_private_key=connection.peer_private_key,
        peer_ip=connection.allocated_ip,
    )

    # 7. ByeDPI-профиль по стране сервера
    byedpi_profile = WireGuardService.get_byedpi_profile(server.country)

    # 8. Определяем режим
    strict_countries = {"TR", "EG", "AE", "SA", "IR", "CN", "RU"}
    mode = "hybrid" if server.country.upper() in strict_countries else "amnezia_only"

    # 9. VLESS+Reality конфиг (фолбэк-режим)
    vless_config = get_vless_config(server_ip=server.host)

    return VpnConnectResponse(
        server_id=server.id,
        server_country=server.country,
        wg_config=wg_config,
        peer_ip=connection.allocated_ip,
        byedpi_profile=byedpi_profile,
        mode=mode,
        vless_config=vless_config,
        show_paywall=show_paywall,
    )
