from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .health import router as health_router
from .search.router import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from .db.engine import create_tables
    await create_tables()
    yield


app = FastAPI(title="Praxo-PICOS API", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(search_router)
