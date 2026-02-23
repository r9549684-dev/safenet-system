from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

def now_utc() -> datetime:
    return datetime.utcnow()

def is_user_premium(user: User) -> bool:
    if user.is_premium and user.premium_until and user.premium_until > now_utc():
        return True
    return False

def has_trial(user: User) -> bool:
    return user.trial_ends_at > now_utc()

async def grant_premium(session: AsyncSession, user: User, months: int) -> None:
    # Simple: month = 30 days
    add = timedelta(days=30 * months)
    base = user.premium_until if user.premium_until and user.premium_until > now_utc() else now_utc()
    user.is_premium = True
    user.premium_until = base + add
    await session.commit()