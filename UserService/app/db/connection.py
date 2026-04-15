import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import USER_DATABASE_URL


def make_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


_sessionmakers = {}


def get_sessionmaker():
    loop = asyncio.get_running_loop()
    loop_key = id(loop)

    if loop_key not in _sessionmakers:
        engine = create_async_engine(
            make_async_database_url(USER_DATABASE_URL),
            pool_pre_ping=True,
        )
        _sessionmakers[loop_key] = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
        )

    return _sessionmakers[loop_key]


@asynccontextmanager
async def get_db_session():
    AsyncSessionLocal = get_sessionmaker()
    async with AsyncSessionLocal() as session:
        yield session
