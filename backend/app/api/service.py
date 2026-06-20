"""
service API — эндпоинт для получения WireGuard-конфига, ByeDPI-профиля и VLESS+Reality.

POST /service/connect/{server_id}
  → Возвращает персональный WireGuard-конфиг + профиль ByeDPI + vless_config.
"""
import uuid
import logging
from datetime import datetime
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
log = logging.getLogger(__name__)
from app.models.server import Server
from app.models.user import User
from app.models.connection import UserConnection, ConnectionStatus
from app.models.node_metrics import NodeMetrics
from app.services.wireguard import WireGuardService
from app.services.xray import get_vless_config
from app.services.entitlements import is_user_premium, has_trial
from app.utils.security import decode_token
from app.services.ano.node_ranker import NodeRanker

router = APIRouter(prefix="/service", tags=["service"])
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
    status: str = "ACTIVE" # Для обратной совместимости


class VpnConfigItem(BaseModel):
    """Элемент пула конфигов для бесшовного фэйловера."""
    server_id: int
    server_country: str
    wg_config: str
    peer_ip: str
    byedpi_profile: dict[str, Any]
    mode: str
    vless_config: dict[str, Any]
    status: str  # ACTIVE или STANDBY


class VpnPoolResponse(BaseModel):
    """Ответ эндпоинта пула конфигов (до 3 шт.)."""
    configs: List[VpnConfigItem]


class ReportBlockedRequest(BaseModel):
    """Запрос на отчет о блокировке конфига."""
    allocated_ip: str


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
            status=ConnectionStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
        session.add(connection)
    else:
        # Переиспользуем существующую запись (IP и ключи не меняем, просто реактивируем)
        peer_was_active = (connection.status == ConnectionStatus.ACTIVE)  # запоминаем статус ДО реактивации
        connection.status = ConnectionStatus.ACTIVE

    # 4. Обновляем время последнего использования (это старт сессии для watchdog'а)
    connection.last_used_at = datetime.utcnow()

    # 4.1 Для limited-пользователей: счётчик подключений → show_paywall через раз
    show_paywall = False
    if is_limited:
        user.post_trial_connect_count += 1
        show_paywall = (user.post_trial_connect_count % 2 == 0)

    await session.commit()

    # 5. Регистрируем пир на WireGuard-интерфейсе (graceful: wg-manager опционален)
    peer_registered = await WireGuardService.add_peer_to_server(
        pubkey=connection.peer_public_key,
        ip=connection.allocated_ip,
    )
    if not peer_registered:
        log.warning(
            "connect_vpn: wg-manager unavailable, peer NOT registered on server. "
            "VPN tunnel will not work until wg-manager is deployed. "
            "user=%s server=%s peer_ip=%s",
            user.device_id, server_id, connection.allocated_ip,
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


# ── ANO Smart Connect Logic ─────────────────────────────────────────────────

@router.post("/smart-connect", response_model=VpnConnectResponse)
async def smart_connect(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Умное подключение через SafeNet ANO.
    Вместо случайного выбора, запрашивает реальные метрики Скаута, ранжирует узлы 
    и выдает только сервер из "Зеленой зоны" (ANO Rating > 15).
    """
    # 1. Получаем все активные серверы вместе с их метриками (LEFT JOIN)
    query = (
        select(Server, NodeMetrics)
        .outerjoin(NodeMetrics, Server.id == NodeMetrics.server_id)
        .where(Server.is_active == True)
    )
    results = (await session.execute(query)).all()
    
    if not results:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Нет доступных серверов")

    # 2. Формируем список для ранкера из реальных данных БД (или дефолтных плохих метрик, если Скаут еще не обновил)
    nodes_for_ranking = []
    for srv, metrics in results:
        nodes_for_ranking.append({
            "id": srv.id,
            "country": srv.country,
            "host": srv.host,
            "rtt_avg": float(metrics.rtt_avg) if metrics else 999.0,
            "jitter": float(metrics.jitter) if metrics else 100.0,
            "loss_pct": float(metrics.loss_pct) if metrics else 50.0,
            "throughput_kbps": float(metrics.throughput_kbps) if metrics else 10.0,
            "life_hours": float(metrics.life_hours) if metrics else 1.0
        })

    # 3. ANO Ранжирование: ищем лучший узел в Зеленой зоне (rating > 15)
    best_node = NodeRanker.select_best_node(nodes_for_ranking, min_rating=15.0)
    
    if not best_node:
        log.warning("[ANO] Ни один сервер не прошел порог Зеленой зоны. Fallback на первый доступный.")
        best_node = next(({"id": srv.id, "country": srv.country, "host": srv.host} for srv, _ in results), None)
        if not best_node:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Нет доступных серверов")

    log.info(f"[ANO] Выбран оптимизированный узел: ID={best_node['id']}, Рейтинг={best_node.get('ano_rating', 'N/A')}, Зона={best_node.get('ano_zone', 'FALLBACK')}")
    
    # 4. Получаем реальный объект сервера из результатов по выбранному ID
    server = next((srv for srv, _ in results if srv.id == best_node["id"]), None)
    if not server:
        raise HTTPException(status_code=500, detail="Ошибка выбора сервера ANO")

    # 5. Продакшен-логика аллокации подключения (идентична /connect, но для выбранного ANO узла)
    is_limited = not (is_user_premium(user) or has_trial(user))
    
    conn_result = await session.execute(
        select(UserConnection)
        .where(UserConnection.user_id == user.id, UserConnection.server_id == server.id)
        .order_by(UserConnection.created_at.desc())
        .limit(1)
    )
    connection = conn_result.scalar_one_or_none()
    peer_was_active = False

    if connection is None:
        private_key, public_key = WireGuardService.generate_keypair()
        peer_ip = await WireGuardService.allocate_ip(session, server.id)
        connection = UserConnection(
            user_id=user.id,
            server_id=server.id,
            peer_private_key=private_key,
            peer_public_key=public_key,
            allocated_ip=peer_ip,
            status=ConnectionStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
        session.add(connection)
    else:
        peer_was_active = (connection.status == ConnectionStatus.ACTIVE)
        connection.status = ConnectionStatus.ACTIVE

    connection.last_used_at = datetime.utcnow()
    
    show_paywall = False
    if is_limited:
        user.post_trial_connect_count += 1
        show_paywall = (user.post_trial_connect_count % 2 == 0)

    await session.commit()

    await WireGuardService.add_peer_to_server(
        pubkey=connection.peer_public_key,
        ip=connection.allocated_ip,
    )

    _user_is_premium = is_user_premium(user)
    if not peer_was_active:
        tier = "premium" if _user_is_premium else "trial"
        log.info("[SPEED] user=%s tier=%s peer_ip=%s (new/reactivated)", user.device_id, tier, connection.allocated_ip)
        await WireGuardService.apply_speed_limit(peer_ip=connection.allocated_ip, tier=tier)
    else:
        log.info("[SPEED] skip set-speed for %s — peer already active (VoIP safe)", connection.allocated_ip)

    wg_config = WireGuardService.generate_wg_config(
        server=server,
        peer_private_key=connection.peer_private_key,
        peer_ip=connection.allocated_ip,
    )
    
    byedpi_profile = WireGuardService.get_byedpi_profile(server.country)
    strict_countries = {"TR", "EG", "AE", "SA", "IR", "CN", "RU"}
    mode = "hybrid" if server.country.upper() in strict_countries else "amnezia_only"
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


# ── SafeNet AMO: Seamless Failover & Pool Management ────────────────────────

async def _build_config_item(
    session: AsyncSession, 
    user: User, 
    server: Server, 
    target_status: ConnectionStatus = ConnectionStatus.STANDBY
) -> VpnConfigItem:
    """Вспомогательная функция для генерации элемента пула конфигов."""
    private_key, public_key = WireGuardService.generate_keypair()
    peer_ip = await WireGuardService.allocate_ip(session, server.id)
    
    connection = UserConnection(
        user_id=user.id,
        server_id=server.id,
        peer_private_key=private_key,
        peer_public_key=public_key,
        allocated_ip=peer_ip,
        status=target_status,
        created_at=datetime.utcnow(),
    )
    session.add(connection)
    await session.commit()

    # Регистрируем пир и применяем лимиты (только для нового подключения)
    await WireGuardService.add_peer_to_server(pubkey=public_key, ip=peer_ip)
    tier = "premium" if is_user_premium(user) else "trial"
    await WireGuardService.apply_speed_limit(peer_ip=peer_ip, tier=tier)

    wg_config = WireGuardService.generate_wg_config(
        server=server,
        peer_private_key=private_key,
        peer_ip=peer_ip,
    )
    
    byedpi_profile = WireGuardService.get_byedpi_profile(server.country)
    strict_countries = {"TR", "EG", "AE", "SA", "IR", "CN", "RU"}
    mode = "hybrid" if server.country.upper() in strict_countries else "amnezia_only"
    vless_config = get_vless_config(server_ip=server.host)

    return VpnConfigItem(
        server_id=server.id,
        server_country=server.country,
        wg_config=wg_config,
        peer_ip=peer_ip,
        byedpi_profile=byedpi_profile,
        mode=mode,
        vless_config=vless_config,
        status=target_status.value,
    )


@router.post("/pool", response_model=VpnPoolResponse)
async def get_connection_pool(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    SafeNet AMO: Возвращает пул конфигураций для пользователя (1 ACTIVE + до 2 STANDBY).
    Если пул неполный, генерирует недостающие конфиги через NodeRanker.
    """
    # 1. Получаем текущие активные и резервные конфиги пользователя
    existing_conns = (await session.execute(
        select(UserConnection).where(
            UserConnection.user_id == user.id,
            UserConnection.status.in_([ConnectionStatus.ACTIVE, ConnectionStatus.STANDBY])
        )
    )).scalars().all()

    existing_server_ids = {conn.server_id for conn in existing_conns}
    
    configs = []
    for conn in existing_conns:
        server = (await session.execute(select(Server).where(Server.id == conn.server_id))).scalar_one()
        wg_config = WireGuardService.generate_wg_config(
            server=server,
            peer_private_key=conn.peer_private_key,
            peer_ip=conn.allocated_ip,
        )
        strict_countries = {"TR", "EG", "AE", "SA", "IR", "CN", "RU"}
        mode = "hybrid" if server.country.upper() in strict_countries else "amnezia_only"
        
        configs.append(VpnConfigItem(
            server_id=server.id,
            server_country=server.country,
            wg_config=wg_config,
            peer_ip=conn.allocated_ip,
            byedpi_profile=WireGuardService.get_byedpi_profile(server.country),
            mode=mode,
            vless_config=get_vless_config(server_ip=server.host),
            status=conn.status.value,
        ))

    # 2. Если конфигов меньше 3, добираем через NodeRanker
    while len(configs) < 3:
        all_servers = (await session.execute(select(Server).where(Server.is_active == True))).scalars().all()
        if not all_servers:
            break
            
        nodes_for_ranking = []
        for srv in all_servers:
            if srv.id in existing_server_ids:
                continue
                
            metrics = (await session.execute(
                select(NodeMetrics).where(NodeMetrics.server_id == srv.id)
            )).scalar_one_or_none()
            
            nodes_for_ranking.append({
                "id": srv.id,
                "rtt_avg": float(metrics.rtt_avg) if metrics else 999.0,
                "jitter": float(metrics.jitter) if metrics else 100.0,
                "loss_pct": float(metrics.loss_pct) if metrics else 50.0,
                "throughput_kbps": float(metrics.throughput_kbps) if metrics else 10.0,
                "life_hours": float(metrics.life_hours) if metrics else 1.0
            })

        best_node = NodeRanker.select_best_node(nodes_for_ranking, min_rating=5.0)
        
        if not best_node:
            log.warning("[AMO] Не найдено подходящих серверов для пополнения пула.")
            break
            
        best_server = next((s for s in all_servers if s.id == best_node["id"]), None)
        if best_server:
            log.info(f"[AMO] Генерация STANDBY конфига для сервера {best_server.id} (Rating: {best_node.get('ano_rating', 'N/A')})")
            new_config = await _build_config_item(session, user, best_server, ConnectionStatus.STANDBY)
            configs.append(new_config)
            existing_server_ids.add(best_server.id)
        else:
            break

    if configs and not any(c.status == "ACTIVE" for c in configs):
        configs[0].status = "ACTIVE"

    return VpnPoolResponse(configs=configs)


@router.post("/report-blocked")
async def report_blocked_config(
    req: ReportBlockedRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    SafeNet AMO: Клиент сообщает о блокировке конфига.
    Мгновенно помечает его как REVOKED и асинхронно запускает исцеление пула.
    """
    conn = (await session.execute(
        select(UserConnection).where(
            UserConnection.user_id == user.id,
            UserConnection.allocated_ip == req.allocated_ip,
            UserConnection.status.in_([ConnectionStatus.ACTIVE, ConnectionStatus.STANDBY])
        )
    )).scalar_one_or_none()

    if conn:
        conn.status = ConnectionStatus.REVOKED
        await session.commit()
        log.info(f"[AMO] Конфиг с IP {req.allocated_ip} помечен как REVOKED для пользователя {user.id}")
        
        background_tasks.add_task(heal_pool_task, user.id)
        return {"status": "revoked", "healing_initiated": True}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found or already revoked")


async def heal_pool_task(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """
    Фоновая задача SafeNet AMO: Восполняет пул конфигов до 3 штук после блокировки.
    """
    log.info(f"[AMO HEALER] Запуск исцеления пула для пользователя {user_id}")
    try:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not user:
            return

        existing_conns = (await session.execute(
            select(UserConnection).where(
                UserConnection.user_id == user_id,
                UserConnection.status.in_([ConnectionStatus.ACTIVE, ConnectionStatus.STANDBY])
            )
        )).scalars().all()

        slots_to_fill = 3 - len(existing_conns)
        if slots_to_fill <= 0:
            log.info(f"[AMO HEALER] Пул пользователя {user_id} уже полон ({len(existing_conns)}). Пропуск.")
            return

        existing_server_ids = {conn.server_id for conn in existing_conns}
        all_servers = (await session.execute(select(Server).where(Server.is_active == True))).scalars().all()
        
        for _ in range(slots_to_fill):
            nodes_for_ranking = []
            for srv in all_servers:
                if srv.id in existing_server_ids:
                    continue
                metrics = (await session.execute(
                    select(NodeMetrics).where(NodeMetrics.server_id == srv.id)
                )).scalar_one_or_none()
                
                nodes_for_ranking.append({
                    "id": srv.id,
                    "rtt_avg": float(metrics.rtt_avg) if metrics else 999.0,
                    "jitter": float(metrics.jitter) if metrics else 100.0,
                    "loss_pct": float(metrics.loss_pct) if metrics else 50.0,
                    "throughput_kbps": float(metrics.throughput_kbps) if metrics else 10.0,
                    "life_hours": float(metrics.life_hours) if metrics else 1.0
                })

            best_node = NodeRanker.select_best_node(nodes_for_ranking, min_rating=5.0)
            if not best_node:
                log.warning(f"[AMO HEALER] Нет подходящих серверов для пользователя {user_id}")
                break
                
            best_server = next((s for s in all_servers if s.id == best_node["id"]), None)
            if best_server:
                log.info(f"[AMO HEALER] Создание нового STANDBY конфига на сервере {best_server.id}")
                await _build_config_item(session, user, best_server, ConnectionStatus.STANDBY)
                existing_server_ids.add(best_server.id)
                
    except Exception as e:
        log.error(f"[AMO HEALER] Ошибка исцеления пула для {user_id}: {e}", exc_info=True)
