from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models.invoice import Invoice
from app.models.user import User
from app.services.cryptobot import cryptobot
from app.services.entitlements import is_user_premium
from app.api.users import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Plan catalogue: id -> (months, price_usd)
PLANS = {
    "monthly":   {"months": 1,  "price": 5.99,  "label": "1 Month"},
    "quarterly": {"months": 3,  "price": 14.99, "label": "3 Months"},
    "yearly":    {"months": 12, "price": 29.99, "label": "12 Months"},
}


@router.get("/pricing")
async def get_pricing():
    return {
        "monthly_price":  PLANS["monthly"]["price"],
        "quarterly_price": PLANS["quarterly"]["price"],
        "yearly_price":   PLANS["yearly"]["price"],
        "lifetime_price": 0,
    }


@router.get("/status")
async def get_status(user: User = Depends(get_current_user)):
    return {
        "is_premium":    user.is_premium,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
    }


@router.post("/purchase/{plan}")
async def purchase(
    plan: str,
    use_compute_credits: bool = False,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    plan_info = PLANS.get(plan)
    if not plan_info:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}. Valid: {list(PLANS.keys())}")

    months = plan_info["months"]
    amount = plan_info["price"]

    payload = f"user:{user.id}:months:{months}:ts:{int(datetime.utcnow().timestamp())}"
    desc = f"SafeNet VPN Premium — {plan_info['label']}"

    data = await cryptobot.create_invoice(amount=amount, payload=payload, description=desc)
    if not data.get("ok"):
        raise HTTPException(status_code=502, detail={"provider_error": data})

    inv = data["result"]
    provider_invoice_id = str(inv["invoice_id"])

    existing = await session.execute(select(Invoice).where(Invoice.provider_invoice_id == provider_invoice_id))
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

    # Flutter expects "invoice_url" field
    return {
        "invoice_url": inv.get("pay_url"),
        "invoice_id":  provider_invoice_id,
        "plan":        plan,
        "months":      months,
        "amount":      amount,
    }
