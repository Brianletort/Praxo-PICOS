import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.router import router as config_router
from .detect.router import router as detect_router
from .health import router as health_router
from .search.router import router as search_router
from .sources.router import router as sources_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from .db.engine import create_tables

    await create_tables()

    from services.workers.src.praxo_picos_workers.orchestrator import extraction_loop

    task = asyncio.create_task(extraction_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Praxo-PICOS API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3100",
        "http://localhost:3100",
        "http://127.0.0.1:3777",
        "http://localhost:3777",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(search_router)
app.include_router(sources_router)
app.include_router(config_router)
app.include_router(detect_router)
