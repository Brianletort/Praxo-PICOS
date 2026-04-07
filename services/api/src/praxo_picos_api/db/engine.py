from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .models import Base

_engine: AsyncEngine | None = None


def _default_db_path() -> Path:
    data_dir = os.environ.get(
        "PRAXO_DATA_DIR",
        os.path.expanduser("~/Library/Application Support/Praxo-PICOS"),
    )
    state_dir = Path(data_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "picos.db"


def get_engine(db_url: str | None = None) -> AsyncEngine:
    global _engine
    if _engine is not None:
        return _engine

    if db_url is None:
        db_path = _default_db_path()
        db_url = f"sqlite+aiosqlite:///{db_path}"

    _engine = create_async_engine(db_url, echo=False)
    return _engine


async def create_tables(engine: AsyncEngine | None = None) -> None:
    engine = engine or get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def reset_engine() -> None:
    """Reset the cached engine (for testing)."""
    global _engine
    _engine = None
