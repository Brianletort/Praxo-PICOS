from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
) -> dict[str, Any]:
    from ..db.engine import get_engine
    from .hybrid import HybridSearch

    engine = get_engine()
    search_engine = HybridSearch(engine=engine)
    results = await search_engine.search(query=q, limit=limit)

    return {
        "query": q,
        "results": [r.to_dict() for r in results],
        "total": len(results),
    }
