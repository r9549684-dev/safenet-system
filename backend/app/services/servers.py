from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.server import Server

async def list_active_servers(session: AsyncSession) -> list[Server]:
    q = await session.execute(
        select(Server).where(Server.is_active == True).order_by(Server.country, Server.priority.asc())
    )
    return q.scalars().all()