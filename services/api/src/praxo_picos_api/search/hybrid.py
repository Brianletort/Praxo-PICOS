from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    record_id: str
    title: str
    snippet: str
    source: str
    timestamp: str
    score: float
    match_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "title": self.title,
            "snippet": self.snippet,
            "source": self.source,
            "timestamp": self.timestamp,
            "score": self.score,
            "match_type": self.match_type,
        }


class HybridSearch:
    def __init__(self, engine: AsyncEngine, qdrant_client: Any | None = None):
        self._engine = engine
        self._qdrant = qdrant_client

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        fts_results = await self._fts_search(query, limit)

        if self._qdrant is not None:
            try:
                vector_results = await self._vector_search(query, limit)
                return self._merge_results(fts_results, vector_results, limit)
            except Exception:
                logger.warning("Qdrant unavailable, falling back to FTS-only")

        return fts_results[:limit]

    async def _fts_search(self, query: str, limit: int) -> list[SearchResult]:
        sql = text("""
            SELECT record_id, content, source,
                   bm25(search_fts) as score
            FROM search_fts
            WHERE search_fts MATCH :query
            ORDER BY bm25(search_fts)
            LIMIT :limit
        """)

        results: list[SearchResult] = []
        try:
            async with self._engine.connect() as conn:
                rows = await conn.execute(sql, {"query": query, "limit": limit})
                for row in rows:
                    results.append(
                        SearchResult(
                            record_id=row.record_id,
                            title="",
                            snippet=row.content[:200] if row.content else "",
                            source=row.source,
                            timestamp="",
                            score=abs(float(row.score)) if row.score else 0.0,
                            match_type="fts",
                        )
                    )
        except Exception:
            logger.warning("FTS search failed", exc_info=True)

        return results

    async def _vector_search(self, query: str, limit: int) -> list[SearchResult]:
        return []

    def _merge_results(
        self,
        fts: list[SearchResult],
        vector: list[SearchResult],
        limit: int,
    ) -> list[SearchResult]:
        seen: set[str] = set()
        merged: list[SearchResult] = []

        all_results = sorted(fts + vector, key=lambda r: r.score, reverse=True)
        for r in all_results:
            if r.record_id not in seen:
                seen.add(r.record_id)
                merged.append(r)
            if len(merged) >= limit:
                break

        return merged
