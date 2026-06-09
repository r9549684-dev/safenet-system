"""
Admin Payments API — создание инвойса от имени пользователя из Telegram-бота.

POST /payments/admin/create-invoice (X-Admin-Secret)
  Body: { tg_id OR device_id, plan, country }
  → создаёт CryptoBot-инвойс по гео-цене
  → возвращает pay_url, который бот отправляет пользователю
  → после оплаты стандартный CryptoBot-вебхук активирует premium
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import require_admin
from app.api.subscriptions import PLANS, PRICING_CONFIG, _round_price
from app.database import get_session
from app.models.invoice import Invoice
from app.models.user import User
from app.services.cryptobot import cryptobot

router = APIRouter(prefix="/payments/admin", tags=["payments-admin"])


class AdminCreateInvoiceRequest(BaseModel):
    tg_id: Optional[int] = None
    device_id: Optional[str] = None
    plan: str                   # weekly | monthly | quarterly | yearly
    country: Optional[str] = None  # ISO-код страны для гео-цены

    @model_validator(mode="after")
    def check_identifier(self) -> "AdminCreateInvoiceRequest":
        if not self.tg_id and not self.device_id:
            raise ValueError("Provide either tg_id or device_id")
        return self


@router.post("/create-invoice", dependencies=[Depends(require_admin)])
async def admin_create_invoice(
    body: AdminCreateInvoiceRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Создаёт CryptoBot-инвойс от имени пользователя.
    Вызывается @SafeBypass_bot при команде /pay.

    Порядок поиска пользователя:
      1. По tg_id (если привязан)
      2. По device_id (резерв)

    После оплаты стандартный вебхук /payments/cryptobot/webhook
    активирует premium — без дополнительной логики.
    """
    # ── Найти пользователя ─────────────────────────────────────────────────
    user: Optional[User] = None

    if body.tg_id:
        result = await session.execute(
            select(User).where(User.telegram_id == body.tg_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Telegram account not linked. Ask user to open SafeNet app → Subscribe → 'Link Telegram'.",
            )

    if user is None and body.device_id:
        result = await session.execute(
            select(User).where(User.device_id == body.device_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

    # ── Тариф и гео-цена ──────────────────────────────────────────────────
    plan_info = PLANS.get(body.plan)
    if not plan_info:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plan: '{body.plan}'. Valid: {list(PLANS.keys())}",
        )

    country = (body.country or user.country or "").upper()
    base_price = plan_info["price"]
    if country in PRICING_CONFIG:
        cfg = PRICING_CONFIG[country]
        amount_usd = _round_price(base_price * cfg["geo_mult"])
        amount_local = round(amount_usd * cfg["fx_rate"])
        currency = cfg["currency"]
        fx_rate = cfg["fx_rate"]
    else:
        amount_usd = base_price
        amount_local = amount_usd
        currency = "USD"
        fx_rate = 1.0

    days = plan_info["days"]
    months = plan_info["months"]

    # ── Payload инвойса (совместим с вебхуком) ────────────────────────────
    if body.plan == "weekly":
        payload = f"user:{user.id}:days:{days}:ts:{int(datetime.utcnow().timestamp())}"
    else:
        payload = f"user:{user.id}:months:{months}:ts:{int(datetime.utcnow().timestamp())}"

    desc = f"SafeNet service Premium — {plan_info['label']}"
    if country:
        desc += f" ({country})"

    # ── Создать инвойс в CryptoBot ────────────────────────────────────────
    data = await cryptobot.create_invoice(
        amount=amount_usd, payload=payload, description=desc
    )
    if not data.get("ok"):
        raise HTTPException(status_code=502, detail={"provider_error": data})

    inv = data["result"]
    provider_invoice_id = str(inv["invoice_id"])

    # Idempotency: не дублировать если уже создан
    existing = await session.execute(
        select(Invoice).where(Invoice.provider_invoice_id == provider_invoice_id)
    )
    if not existing.scalar_one_or_none():
        row = Invoice(
            user_id=str(user.id),
            provider="cryptobot",
            provider_invoice_id=provider_invoice_id,
            asset=inv.get("asset", "USDT"),
            amount=Decimal(str(inv.get("amount"))),
            status=inv.get("status", "active"),
            payload=payload,
            raw=data,
            created_at=datetime.utcnow(),
            paid_at=None,
        )
        session.add(row)
        await session.commit()

    return {
        "invoice_id": provider_invoice_id,
        "pay_url": inv.get("pay_url"),
        "plan": body.plan,
        "days": days,
        "amount_usd": amount_usd,
        "amount_local": amount_local,
        "currency": currency,
        "country": country or None,
        "expires_at": inv.get("expiration_date"),
    }
