from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from .base import BaseExtractor, ExtractionRecord


class ScreenpipeExtractor(BaseExtractor):
    source_name = "screen"

    def __init__(self, base_url: str = "http://127.0.0.1:3030"):
        self._base_url = base_url

    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        records: list[ExtractionRecord] = []
        params: dict[str, Any] = {"limit": 100}
        if since:
            params["start_time"] = since.isoformat()

        async with httpx.AsyncClient(base_url=self._base_url, timeout=10) as client:
            resp = await client.get("/search", params=params)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("data", []):
            content = item.get("content", {})
            text = content.get("text", "") or content.get("transcription", "")
            ts_str = item.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue

            records.append(ExtractionRecord(
                source="screen",
                source_id=str(item.get("id", "")),
                title=content.get("app_name", "Screen capture"),
                body=text,
                timestamp=ts,
                metadata={
                    "app_name": content.get("app_name", ""),
                    "window_name": content.get("window_name", ""),
                    "content_type": item.get("type", ""),
                },
            ))

        return records

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=5) as client:
                resp = await client.get("/health")
                if resp.status_code == 200:
                    return {"status": "ok", "url": self._base_url}
                return {"status": "degraded", "url": self._base_url, "code": resp.status_code}
        except Exception as e:
            return {"status": "unavailable", "url": self._base_url, "error": str(e)[:200]}
