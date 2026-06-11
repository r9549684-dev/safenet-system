"""
Session Watchdog — фоновая задача для ограничения сессий post-trial пользователей.

Логика:
- Каждые 30 секунд ищет активные подключения, где:
  - Пользователь НЕ premium И триал истёк
  - Сессия (last_used_at) длится дольше SESSION_LIMIT_MINUTES
- Для каждого такого подключения:
  - Удаляет WireGuard peer с сервера
  - Помечает connection.is_active = False
"""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.connection import UserConnection, ConnectionStatus
from app.models.user import User
from app.services.wireguard import WireGuardService

log = logging.getLogger(__name__)

SESSION_LIMIT_MINUTES = 5
WATCHDOG_INTERVAL_SECONDS = 30


async def _run_cycle(session: AsyncSession) -> None:
    """Один цикл watchdog: найти и отключить истёкшие сессии."""
    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_LIMIT_MINUTES)

    result = await session.execute(
        select(UserConnection, User)
        .join(User, UserConnection.user_id == User.id)
        .where(
            and_(
                UserConnection.status == ConnectionStatus.ACTIVE,
                User.is_premium == False,
                User.trial_ends_at < datetime.utcnow(),
                UserConnection.last_used_at.is_not(None),
                UserConnection.last_used_at < cutoff,
            )
        )
    )
    rows = result.all()

    if not rows:
        return

    log.info("[WATCHDOG] Найдено %d сессий для отключения", len(rows))

    for conn, user in rows:
        try:
            await WireGuardService.remove_peer_from_server(conn.peer_public_key)
            conn.status = ConnectionStatus.REVOKED
            log.info(
                "[WATCHDOG] Отключён: device=%s ip=%s server_id=%s",
                user.device_id,
                conn.allocated_ip,
                conn.server_id,
            )
        except Exception as exc:
            log.warning(
                "[WATCHDOG] Ошибка отключения device=%s: %s",
                user.device_id,
                exc,
            )

    await session.commit()


async def run_session_watchdog() -> None:
    """Бесконечный цикл watchdog. Запускается через asyncio.create_task() в lifespan."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    log.info("[WATCHDOG] Запущен (интервал %ds, лимит %d мин)",
             WATCHDOG_INTERVAL_SECONDS, SESSION_LIMIT_MINUTES)

    while True:
        try:
            async with Session() as session:
                await _run_cycle(session)
        except asyncio.CancelledError:
            log.info("[WATCHDOG] Остановлен")
            break
        except Exception as exc:
            log.error("[WATCHDOG] Необработанная ошибка: %s", exc)

        await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
