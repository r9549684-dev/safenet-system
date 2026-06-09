"""
Server Status API
Проверяет доступность и задержку серверов (для техподдержки и бота SEIFY).
Маршрут: GET /service/servers-status
"""
import asyncio
import time
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from app.database import get_session
from app.models.server import Server

router = APIRouter(tags=["service"])


async def _check_server(host: str, port: int, timeout: float = 3.0) -> dict:
    """
    Пытается TCP-подключиться к серверу за timeout секунд.
    Возвращает latency_ms или None если недоступен.
    """
    t0 = time.monotonic()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {"reachable": True, "latency_ms": latency_ms}
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return {"reachable": False, "latency_ms": None}


def _classify_status(reachable: bool, latency_ms: int | None) -> str:
    if not reachable:
        return "offline"
    if latency_ms is not None and latency_ms > 800:
        return "degraded"
    return "online"


@router.get("/service/servers-status")
async def servers_status(session: AsyncSession = Depends(get_session)):
    """
    GET /service/servers-status

    Возвращает статус каждого сервера из БД.
    Проверяет WireGuard-порт (443/UDP — через TCP fallback) и Xray-порт.

    Формат ответа совместим с ботом SEIFY (@SafeBypass_bot).
    """
    q = await session.execute(select(Server).where(Server.is_active == True))
    servers = q.scalars().all()

    # Параллельная проверка всех серверов
    async def _check_one(srv: Server) -> dict:
        host    = srv.host or "89.208.107.67"
        wg_port = int((srv.meta or {}).get("wg_port", 443))
        xr_port = int((srv.meta or {}).get("xray_port", 2053))

        wg_result = await _check_server(host, wg_port)
        xr_result = await _check_server(host, xr_port)

        wg_status = _classify_status(wg_result["reachable"], wg_result["latency_ms"])
        xr_status = _classify_status(xr_result["reachable"], xr_result["latency_ms"])

        # Итоговый статус — лучший из двух
        if wg_status == "online" or xr_status == "online":
            overall = "online"
        elif wg_status == "degraded" or xr_status == "degraded":
            overall = "degraded"
        else:
            overall = "offline"

        return {
            "id":          srv.id,
            "name":        srv.name or f"Server-{srv.id}",
            "country":     srv.country,
            "host":        host,
            "status":      overall,
            "latency_ms":  wg_result["latency_ms"] or xr_result["latency_ms"],
            "protocols": {
                "wireguard": {
                    "port":       wg_port,
                    "status":     wg_status,
                    "latency_ms": wg_result["latency_ms"],
                },
                "vless_reality": {
                    "port":       xr_port,
                    "status":     xr_status,
                    "latency_ms": xr_result["latency_ms"],
                },
            },
        }

    results = await asyncio.gather(*[_check_one(s) for s in servers])

    online  = sum(1 for r in results if r["status"] == "online")
    total   = len(results)

    return {
        "summary": {
            "total":    total,
            "online":   online,
            "offline":  total - online,
            "health":   "ok" if online > 0 else "critical",
        },
        "servers": list(results),
    }
