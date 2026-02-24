from datetime import datetime
from secrets import token_urlsafe
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.users import get_current_user
from app.config import settings
from app.database import get_session
from app.models.promocode import PromoCode, PromoCodeRedemption
from app.models.user import User
from app.services.entitlements import grant_premium

router = APIRouter(prefix="/promocodes", tags=["promocodes"])

PROMO_KIND_MONTHS = {
    "1m": 1,
    "3m": 3,
    "12m": 12,
}


class PromoCreateRequest(BaseModel):
    kind: str = Field(pattern="^(1m|3m|12m)$")
    code: Optional[str] = Field(default=None, min_length=4, max_length=64)
    expires_at: Optional[datetime] = None


class PromoRedeemRequest(BaseModel):
    code: str = Field(min_length=4, max_length=64)


async def require_admin(
    x_admin_secret: Optional[str] = Header(default=None, alias="X-Admin-Secret"),
) -> None:
    if not settings.ADMIN_SECRET or not x_admin_secret:
        raise HTTPException(status_code=403, detail="Admin access required")
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Admin access required")


def _normalize_code(code: str) -> str:
    return code.strip().upper()


def _generate_code(kind: str) -> str:
    raw = token_urlsafe(8).replace("-", "").replace("_", "").upper()
    return f"{kind.upper()}-{raw[:10]}"


@router.post("/admin/create", dependencies=[Depends(require_admin)])
async def create_promocode(
    body: PromoCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    kind = body.kind.lower()
    duration_months = PROMO_KIND_MONTHS[kind]
    code = _normalize_code(body.code) if body.code else _generate_code(kind)

    existing = await session.execute(select(PromoCode).where(PromoCode.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Promo code already exists")

    row = PromoCode(
        code=code,
        kind=kind,
        duration_months=duration_months,
        max_uses=1,
        used_count=0,
        is_revoked=False,
        expires_at=body.expires_at,
        created_by="admin",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    return {
        "id": row.id,
        "code": row.code,
        "kind": row.kind,
        "duration_months": row.duration_months,
        "max_uses": row.max_uses,
        "used_count": row.used_count,
        "is_revoked": row.is_revoked,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/admin/list", dependencies=[Depends(require_admin)])
async def list_promocodes(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PromoCode).order_by(PromoCode.created_at.desc()).limit(500))
    items = result.scalars().all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "kind": p.kind,
            "duration_months": p.duration_months,
            "used_count": p.used_count,
            "max_uses": p.max_uses,
            "is_revoked": p.is_revoked,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ]


@router.post("/admin/{code}/revoke", dependencies=[Depends(require_admin)])
async def revoke_promocode(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    norm = _normalize_code(code)
    result = await session.execute(select(PromoCode).where(PromoCode.code == norm))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    promo.is_revoked = True
    session.add(promo)
    await session.commit()
    return {"ok": True, "code": norm, "is_revoked": True}


@router.post("/redeem")
async def redeem_promocode(
    body: PromoRedeemRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    norm = _normalize_code(body.code)
    result = await session.execute(select(PromoCode).where(PromoCode.code == norm))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    if promo.is_revoked:
        raise HTTPException(status_code=400, detail="Promo code revoked")
    if promo.expires_at and promo.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Promo code expired")

    redeemed = await session.execute(
        select(PromoCodeRedemption).where(
            PromoCodeRedemption.promo_code_id == promo.id,
            PromoCodeRedemption.user_id == user.id,
        )
    )
    if redeemed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Promo code already redeemed by this user")

    upd = (
        update(PromoCode)
        .where(
            PromoCode.id == promo.id,
            PromoCode.is_revoked == False,
            PromoCode.used_count < PromoCode.max_uses,
        )
        .values(used_count=PromoCode.used_count + 1)
    )
    res = await session.execute(upd)
    if res.rowcount != 1:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Promo code already used")

    redemption = PromoCodeRedemption(
        promo_code_id=promo.id,
        user_id=user.id,
        granted_months=promo.duration_months,
    )
    session.add(redemption)
    await session.commit()

    await grant_premium(session, user, promo.duration_months)
    await session.refresh(user)

    return {
        "ok": True,
        "code": norm,
        "granted_months": promo.duration_months,
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
    }

