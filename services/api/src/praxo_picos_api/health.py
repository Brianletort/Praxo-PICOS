from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter()

_start_time = time.monotonic()


@dataclass
class DependencyStatus:
    name: str
    status: str = "unknown"
    latency_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "status": self.status}
        if self.latency_ms is not None:
            d["latency_ms"] = self.latency_ms
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class HealthResponse:
    status: str
    service: str
    uptime_seconds: float
    dependencies: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "service": self.service,
            "uptime_seconds": round(self.uptime_seconds, 1),
            "dependencies": self.dependencies,
        }


async def check_sqlite() -> DependencyStatus:
    dep = DependencyStatus(name="sqlite")
    try:
        from .db.engine import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            start = time.monotonic()
            await conn.execute(text("SELECT 1"))
            dep.latency_ms = round((time.monotonic() - start) * 1000, 1)
        dep.status = "ok"
    except Exception as e:
        dep.status = "error"
        dep.error = str(e)[:200]
    return dep


@router.get("/health")
async def health() -> dict[str, Any]:
    uptime = time.monotonic() - _start_time
    sqlite_dep = await check_sqlite()
    deps: dict[str, Any] = {"sqlite": sqlite_dep.to_dict()}

    overall = "ok"

    response = HealthResponse(
        status=overall,
        service="praxo-picos-api",
        uptime_seconds=uptime,
        dependencies=deps,
    )
    return response.to_dict()


@router.get("/health/ready")
async def readiness() -> dict[str, str]:
    """Readiness probe -- returns 200 only when all critical deps are available."""
    return {"status": "ready"}
