"""Database session management with SQLAlchemy async."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

db_url = settings.DATABASE_URL
if "asyncpg" in db_url and "?" in db_url:
    base_url, query_str = db_url.split("?", 1)
    params = [p for p in query_str.split("&") if not p.startswith("sslmode=") and not p.startswith("channel_binding=")]
    db_url = base_url + ("?" + "&".join(params) if params else "")

connect_args = {}
if "neon.tech" in db_url:
    connect_args["ssl"] = True

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: get a database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
