"""
Subscriptions API
- GET  /subscriptions/pricing?country=   → цены с гео-мультипликатором
- GET  /subscriptions/status             → статус подписки пользователя
- POST /subscriptions/purchase/{plan}?country=  → создать invoice в Cryptobot
"""
import math
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.invoice import Invoice
from app.models.user import User
from app.services.cryptobot import cryptobot
from app.api.users import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# ── Каталог тарифов (глобальные базовые цены USD) ─────────────────────────────

PLANS = {
    "weekly":    {"days": 7,   "months": 0,  "price": 2.99,  "label": "1 Week"},
    "monthly":   {"days": 30,  "months": 1,  "price": 5.99,  "label": "1 Month"},
    "quarterly": {"days": 90,  "months": 3,  "price": 14.99, "label": "3 Months"},
    "yearly":    {"days": 365, "months": 12, "price": 29.99, "label": "12 Months"},
}

# ── Конфиг гео-ценообразования ────────────────────────────────────────────────
# geo_mult  — множитель к базовой цене (может меняться demand-авто-тюном, квартально)
# fx_rate   — курс к локальной валюте (обновляется вручную Owner'ом)
# currency  — ISO-код локальной валюты для отображения

# geo_mult = local_monthly / global_monthly:
#   TR: 4.99 / 5.99 = 0.8330  → месячный $4.99
#   AE: 9.99 / 5.99 = 1.6678  → месячный $9.99
# Остальные тарифы считаются пропорционально тому же коэффициенту.
PRICING_CONFIG: dict[str, dict] = {
    "AE": {"geo_mult": 1.6678, "currency": "AED", "fx_rate": 3.67},
    "TR": {"geo_mult": 0.8330, "currency": "TRY", "fx_rate": 38.0},
}


def _round_price(price: float) -> float:
    """
    Психологическое округление до X.49 или X.99.
    25.00 → 24.99,  50.02 → 49.99,  4.99 → 4.99,  2.49 → 2.49
    """
    floored  = math.floor(price)
    fraction = price - floored
    if fraction < 0.25:
        return floored - 0.01
    elif fraction < 0.74:
        return floored + 0.49
    else:
        return floored + 0.99


def _country_prices(country: str) -> dict:
    """
    Возвращает список тарифов с geo-скорректированными ценами для указанной страны.
    Если страна не в PRICING_CONFIG — применяются глобальные цены.
    """
    country = country.upper()
    cfg = PRICING_CONFIG.get(country, {"geo_mult": 1.0, "currency": "USD", "fx_rate": 1.0})
    geo_mult   = cfg["geo_mult"]
    fx_rate    = cfg["fx_rate"]
    currency   = cfg["currency"]

    plans = []
    for plan_id, plan in PLANS.items():
        raw_usd     = plan["price"] * geo_mult
        usd_price   = _round_price(raw_usd) if country in PRICING_CONFIG else round(raw_usd, 2)
        local_price = round(usd_price * fx_rate) if currency != "USD" else usd_price
        plans.append({
            "plan":         plan_id,
            "label":        plan["label"],
            "duration_days": plan["days"],
            "usd":          usd_price,
            "local":        local_price,
        })

    return {
        "country":    country,
        "currency":   currency,
        "fx_rate":    fx_rate,
        "load_badge": None,   # TODO: подключить к /vpn/servers-status (нагрузка)
        "plans":      plans,
    }


# ── GET /subscriptions/pricing?country= ──────────────────────────────────────

@router.get("/pricing")
async def get_pricing(
    country: str = Query(default="", description="ISO-код страны: AE, TR, ... (пусто = глобальные)"),
):
    """
    Возвращает актуальные цены с учётом гео-мультипликатора.
    Flutter кэширует ответ на 1 час в SharedPreferences.

    Для обратной совместимости: ?country= не передан → глобальные цены
    в старом формате {monthly_price, quarterly_price, yearly_price}.
    """
    if not country:
        # Backward-compatible ответ (старый формат Flutter использовал)
        return {
            "monthly_price":   PLANS["monthly"]["price"],
            "quarterly_price": PLANS["quarterly"]["price"],
            "yearly_price":    PLANS["yearly"]["price"],
            "lifetime_price":  0,
        }

    return _country_prices(country)


# ── GET /subscriptions/status ─────────────────────────────────────────────────

@router.get("/status")
async def get_status(user: User = Depends(get_current_user)):
    return {
        "is_premium":    user.is_premium,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
    }


# ── POST /subscriptions/purchase/{plan} ──────────────────────────────────────

@router.post("/purchase/{plan}")
async def purchase(
    plan: str,
    country: Optional[str] = Query(default="", description="ISO-код страны для гео-цены"),
    use_compute_credits: bool = False,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """
    Создаёт инвойс в Cryptobot с гео-скорректированной ценой.

    ?country=AE  → invoice на $9.99 вместо $5.99 для monthly
    ?country=TR  → invoice на $4.99 вместо $5.99 для monthly
    Без country  → глобальная базовая цена
    """
    plan_info = PLANS.get(plan)
    if not plan_info:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plan: {plan}. Valid: {list(PLANS.keys())}",
        )

    # Применяем гео-мультипликатор если указана страна
    base_price = plan_info["price"]
    if country and country.upper() in PRICING_CONFIG:
        cfg    = PRICING_CONFIG[country.upper()]
        amount = _round_price(base_price * cfg["geo_mult"])
    else:
        amount = base_price

    days   = plan_info["days"]
    months = plan_info["months"]

    # payload кодирует дни (для weekly) или месяцы (для остальных)
    # payments_cryptobot.py знает как парсить оба варианта
    if plan == "weekly":
        payload = f"user:{user.id}:days:{days}:ts:{int(datetime.utcnow().timestamp())}"
    else:
        payload = f"user:{user.id}:months:{months}:ts:{int(datetime.utcnow().timestamp())}"

    desc = f"SafeNet VPN Premium — {plan_info['label']}"
    if country:
        desc += f" ({country.upper()})"

    data = await cryptobot.create_invoice(amount=amount, payload=payload, description=desc)
    if not data.get("ok"):
        raise HTTPException(status_code=502, detail={"provider_error": data})

    inv = data["result"]
    provider_invoice_id = str(inv["invoice_id"])

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
        "invoice_url": inv.get("pay_url"),
        "invoice_id":  provider_invoice_id,
        "plan":        plan,
        "days":        days,
        "months":      months,
        "amount":      amount,
        "currency":    "USD",
    }
