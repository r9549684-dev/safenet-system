from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.config import settings
import secrets

def _now() -> datetime:
    return datetime.utcnow()

def _new_ref_code() -> str:
    return secrets.token_hex(8)

async def get_or_create_user(session: AsyncSession, device_id: str, country: str | None) -> User:
    q = await session.execute(select(User).where(User.device_id == device_id))
    user = q.scalar_one_or_none()
    if user:
        if country and user.country != country:
            user.country = country
            await session.commit()
        return user

    user = User(
        device_id=device_id,
        country=country,
        referral_code=_new_ref_code(),
        referred_by=None,
        is_premium=False,
        premium_until=None,
        trial_ends_at=_now() + timedelta(days=settings.TRIAL_DAYS),
        created_at=_now(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user