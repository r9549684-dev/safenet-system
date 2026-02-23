import json
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.profile import Profile

async def get_profiles_map(session: AsyncSession) -> dict:
    q = await session.execute(select(Profile))
    items = q.scalars().all()
    out = {}
    for p in items:
        out[p.country] = {"version": p.version, "payload": p.payload}
    return out

def compute_etag(profiles_map: dict) -> str:
    raw = json.dumps(profiles_map, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()