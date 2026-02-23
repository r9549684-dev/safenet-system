from datetime import datetime
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.profile import Profile
from app.models.server import Server

DEFAULT_PROFILES = {
    "TR": {
        "modes": ["byedpi", "amneziawg", "hybrid"],
        "byedpi": {"split": 2, "desync": "fake"},
        "amneziawg": {"junk_packet_count": 3, "junk_packet_min_size": 50},
        "fallback": {"max_attempts": 3}
    },
    "EG": {
        "modes": ["amneziawg", "byedpi"],
        "amneziawg": {"junk_packet_count": 4, "junk_packet_min_size": 60},
        "byedpi": {"split": 1, "desync": "disorder"},
        "fallback": {"max_attempts": 2}
    },
    "AE": {
        "modes": ["amneziawg"],
        "amneziawg": {"junk_packet_count": 5, "junk_packet_min_size": 70},
        "fallback": {"max_attempts": 2}
    },
}

DEFAULT_SERVERS = [
    # MVP: один сервер (тот же), позже добавишь реальные VPN-ноды/локации
    {"country": "TR", "name": "TR-1", "host": "89.208.107.67", "port": 51820, "priority": 10, "meta": {"type": "mvp-single"}},
    {"country": "EG", "name": "EG-1", "host": "89.208.107.67", "port": 51820, "priority": 10, "meta": {"type": "mvp-single"}},
    {"country": "AE", "name": "AE-1", "host": "89.208.107.67", "port": 51820, "priority": 10, "meta": {"type": "mvp-single"}},
]

async def main():
    async with AsyncSessionLocal() as session:
        # profiles
        for country, payload in DEFAULT_PROFILES.items():
            q = await session.execute(select(Profile).where(Profile.country == country))
            p = q.scalar_one_or_none()
            if not p:
                p = Profile(country=country, version=1, payload=payload, updated_at=datetime.utcnow())
                session.add(p)
            else:
                # do not overwrite in seed (idempotent)
                pass

        # servers
        for s in DEFAULT_SERVERS:
            q = await session.execute(
                select(Server).where(Server.country == s["country"], Server.name == s["name"])
            )
            existing = q.scalar_one_or_none()
            if not existing:
                session.add(Server(**s))

        await session.commit()

if __name__ == "__main__":
    asyncio.run(main())