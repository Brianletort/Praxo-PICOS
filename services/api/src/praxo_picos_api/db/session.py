from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .engine import get_engine

AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        engine = get_engine()
        AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    return AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        yield session


def reset_session_factory() -> None:
    """Reset the cached session factory (for testing)."""
    global AsyncSessionLocal
    AsyncSessionLocal = None
