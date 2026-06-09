import json
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.config import settings
from app.models.invoice import Invoice
from app.models.user import User
from app.services.cryptobot import cryptobot
from app.services.entitlements import grant_premium
from app.services.affiliate import process_referral_reward
from app.utils.idempotency import stable_hash
from app.api.users import get_current_user

router = APIRouter(prefix="/payments/cryptobot", tags=["payments"])


@router.post("/invoice")
async def create_invoice(
    body: dict,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    amount = float(body.get("amount", 0))
    months = int(body.get("months", 1))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")
    if months < 1 or months > 24:
        raise HTTPException(status_code=400, detail="months invalid")

    payload = f"user:{user.id}:months:{months}:ts:{int(datetime.utcnow().timestamp())}"
    desc = f"SafeNet service Premium {months} month(s)"

    data = await cryptobot.create_invoice(amount=amount, payload=payload, description=desc)
    if not data.get("ok"):
        raise HTTPException(status_code=502, detail={"provider_error": data})

    inv = data["result"]
    provider_invoice_id = str(inv["invoice_id"])

    existing = await session.execute(select(Invoice).where(Invoice.provider_invoice_id == provider_invoice_id))
    if existing.scalar_one_or_none():
        return {"provider": "cryptobot", "invoice_id": provider_invoice_id, "raw": data}

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
        "provider": "cryptobot",
        "invoice_id": provider_invoice_id,
        "pay_url": inv.get("pay_url"),
        "raw": data,
    }


@router.post("/webhook")
async def cryptobot_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    cryptopay_signature: str | None = Header(default=None, alias="Crypto-Pay-Signature"),
):
    raw_body = await request.body()
    sig = cryptopay_signature
    if not sig:
        sig = request.headers.get(settings.CRYPTOBOT_SIGNATURE_HEADER)

    if not sig:
        raise HTTPException(status_code=400, detail="Missing signature header")

    if not cryptobot.verify_signature(raw_body, sig):
        raise HTTPException(status_code=401, detail="Bad signature")

    body_hash = stable_hash(raw_body)

    payload = json.loads(raw_body.decode("utf-8"))
    if not payload.get("update_type") == "invoice_paid":
        return {"ok": True, "ignored": True}

    invoice_obj = payload.get("invoice") or payload.get("data") or payload.get("payload") or {}
    invoice_id = str(invoice_obj.get("invoice_id") or invoice_obj.get("id") or "")

    if not invoice_id:
        invoice_id = str(payload.get("invoice_id") or "")

    if not invoice_id:
        raise HTTPException(status_code=400, detail="invoice_id not found in webhook")

    q = await session.execute(select(Invoice).where(Invoice.provider_invoice_id == invoice_id))
    invoice_row = q.scalar_one_or_none()
    if not invoice_row:
        return {"ok": True, "unknown_invoice": True}

    if invoice_row.status == "paid":
        return {"ok": True, "idempotent": True}

    # Mark paid
    invoice_row.status = "paid"
    invoice_row.paid_at = datetime.utcnow()
    invoice_row.raw = invoice_row.raw or {}
    invoice_row.raw["webhook_last_hash"] = body_hash
    invoice_row.raw["webhook_last_payload"] = payload

    # Extract days or months from payload (new format: days:N; legacy: months:N)
    grant_days = 0
    grant_months = 0
    try:
        parts = (invoice_row.payload or "").split(":")
        if "days" in parts:
            grant_days = int(parts[parts.index("days") + 1])
        elif "months" in parts:
            grant_months = int(parts[parts.index("months") + 1])
    except Exception:
        grant_months = 1

    # Load paying user
    uq = await session.execute(select(User).where(User.id == invoice_row.user_id))
    user = uq.scalar_one_or_none()
    if user:
        await session.commit()
        await grant_premium(session, user, months=grant_months, days=grant_days)

        # Referral reward: если у юзера есть реферер — начисляем вознаграждение
        if user.referred_by:
            rq = await session.execute(select(User).where(User.id == user.referred_by))
            referrer = rq.scalar_one_or_none()
            if referrer:
                payment_amount_usd = Decimal(str(invoice_row.amount or "0"))
                await process_referral_reward(
                    db=session,
                    referrer=referrer,
                    referred=user,
                    payment_amount_usd=payment_amount_usd,
                    invoice_id=invoice_id,
                )
    else:
        await session.commit()

    return {"ok": True}
