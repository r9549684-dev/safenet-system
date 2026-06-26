"""
Iran Subscription API
Генерирует VLESS+Reality+Fragment конфиги для иранских пользователей.
Поддерживает форматы: vless://, sing-box JSON, hiddify deep link.
"""
import base64
import json
import time
import asyncio
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.user import User
from app.models.server import Server
from app.config import settings
from app.api.users import get_current_user

router = APIRouter(prefix="/iran", tags=["iran"])

# ── Xray/Reality параметры (из .env) ─────────────────────────────────────────

def _xray_params() -> dict:
    return {
        "server":     "safenetsystem.duckdns.org",
        "port":       int(getattr(settings, "XRAY_PORT", 8443)),
        "uuid":       getattr(settings, "XRAY_UUID", ""),
        "public_key": getattr(settings, "XRAY_PUBLIC_KEY", ""),
        "short_id":   getattr(settings, "XRAY_SHORT_ID", ""),
        "dest":       "www.microsoft.com",  # SNI — должен совпадать с xray server reality.dest
        "fingerprint": "chrome",
    }


# ── VLESS URI с Fragment параметрами (для v2rayNG / Hiddify) ─────────────────

def build_vless_uri(p: dict, tag: str = "SafeNet-Iran") -> str:
    """
    Строит vless://UUID@host:port?... ссылку.
    Fragment параметры совместимы с v2rayNG ≥1.8 и Hiddify.
    """
    params = (
        f"type=tcp"
        f"&security=reality"
        f"&pbk={p['public_key']}"
        f"&sid={p['short_id']}"
        f"&fp={p['fingerprint']}"
        f"&sni={p['dest']}"
        f"&flow=xtls-rprx-vision"
        f"&fragment=1"           # включает фрагментацию ClientHello
        f"&fragment_size=50-100" # размер чанков в байтах
        f"&fragment_interval=10" # интервал мс
    )
    name = quote(tag)
    return f"vless://{p['uuid']}@{p['server']}:{p['port']}?{params}#{name}"


# ── Sing-box JSON конфиг ──────────────────────────────────────────────────────

def build_singbox_config(p: dict) -> dict:
    """
    Возвращает минимальный sing-box outbound конфиг.
    Hiddify понимает этот формат напрямую.
    """
    return {
        "outbounds": [
            {
                "type":        "vless",
                "tag":         "SafeNet-Iran",
                "server":      p["server"],
                "server_port": p["port"],
                "uuid":        p["uuid"],
                "flow":        "xtls-rprx-vision",
                "tls": {
                    "enabled":     True,
                    "server_name": p["dest"],
                    "utls": {
                        "enabled":     True,
                        "fingerprint": p["fingerprint"],
                    },
                    "reality": {
                        "enabled":    True,
                        "public_key": p["public_key"],
                        "short_id":   p["short_id"],
                    },
                    "fragment": {
                        "packets": "tlshello",
                    },
                },
                # Fragment (внутри tls) — фрагментация ClientHello для обхода DPI
                # transport.type=tcp НАМЕРЕННО УДАЛЁН: FATAL для sing-box 1.12+ с vision flow
            },
            {"type": "direct", "tag": "direct"},
            {"type": "block",  "tag": "block"},
        ],
        "route": {
            "rules": [
                {"geoip": ["private"], "outbound": "direct"},
            ],
            "final": "SafeNet-Iran",
        },
        "experimental": {
            "cache_file": {"enabled": True},
        },
    }


# ── Subscription endpoint (публичный — по токену) ────────────────────────────

@router.get("/subscribe/{token}")
async def subscribe(
    token: str,
    fmt: str = Query(default="base64", description="base64 | singbox | hiddify"),
    session: AsyncSession = Depends(get_session),
):
    """
    GET /iran/subscribe/{token}
    token = JWT токена пользователя (первые 32 символа)
    fmt   = base64 (по умолчанию) | singbox | hiddify

    - base64  → plain text base64 ссылки, понимают все клиенты
    - singbox → sing-box JSON
    - hiddify → hiddify://import/... deep link
    """
    # Ищем юзера по первым 32 символам токена (лёгкая идентификация)
    q = await session.execute(select(User))
    users = q.scalars().all()
    user = next(
        (u for u in users if token.startswith(str(u.device_id)[:16]) or token == str(u.id)[:32]),
        None,
    )
    # Для анонимного доступа — просто отдаём общий конфиг (без привязки к юзеру)
    p = _xray_params()
    vless_uri = build_vless_uri(p)

    if fmt == "singbox":
        return build_singbox_config(p)

    if fmt == "hiddify":
        from fastapi.responses import RedirectResponse
        sub_url = f"https://safenetsystem.duckdns.org/iran/subscribe/{token}?fmt=base64"
        deep = f"hiddify://import/{quote(sub_url, safe='')}"
        return {"hiddify_deeplink": deep, "sub_url": sub_url}

    # base64 (default) — формат subscription link
    raw = base64.b64encode(vless_uri.encode()).decode()
    return PlainTextResponse(raw, headers={
        "Content-Type": "text/plain; charset=utf-8",
        "profile-title": "SafeNet Iran",
        "profile-update-interval": "24",
    })


# ── Admin: генерация ссылки для конкретного юзера ────────────────────────────

async def _require_admin(
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
) -> None:
    if not x_admin_secret or x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/admin/user-config", dependencies=[Depends(_require_admin)])
async def generate_user_iran_config(
    body: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    POST /iran/admin/user-config
    Header: X-Admin-Secret: ...
    Body: {"device_id": "...", "tag": "optional name"}

    Возвращает:
    - vless_url:        vless://...
    - hiddify_deeplink: hiddify://import/...
    - sub_url:          https://safenetsystem.duckdns.org/iran/subscribe/{token}
    - singbox_config:   {...} sing-box JSON
    """
    device_id = body.get("device_id", "")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    q = await session.execute(select(User).where(User.device_id == device_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {device_id} not found")

    tag = body.get("tag") or f"SafeNet-{user.country or 'IR'}"
    p   = _xray_params()

    vless_url = build_vless_uri(p, tag=tag)
    token     = str(user.device_id)[:16]
    sub_url   = f"https://safenetsystem.duckdns.org/iran/subscribe/{token}"
    hiddify   = f"hiddify://import/{quote(sub_url, safe='')}"

    return {
        "device_id":        device_id,
        "user_country":     user.country,
        "vless_url":        vless_url,
        "sub_url":          sub_url,
        "hiddify_deeplink": hiddify,
        "singbox_config":   build_singbox_config(p),
        "instructions": {
            "hiddify": f"Откройте Hiddify → вставьте: {hiddify}",
            "v2rayng":  f"v2rayNG → + → Импорт из буфера → вставьте vless_url",
            "safenet":  f"SafeNet → Настройки → Iran Mode → Открыть",
        },
    }
