from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import BaseExtractor, ExtractionRecord

SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log"}
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentsExtractor(BaseExtractor):
    source_name = "documents"

    def __init__(self, watch_path: Path | None = None, extensions: set[str] | None = None):
        self._watch_path = watch_path or Path.home() / "Documents"
        self._extensions = extensions or SUPPORTED_EXTENSIONS

    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        if not self._watch_path.exists():
            return []

        since_ts = (since or datetime(2024, 1, 1, tzinfo=UTC)).timestamp()
        records: list[ExtractionRecord] = []

        for path in self._watch_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in self._extensions:
                continue
            if path.stat().st_size > MAX_FILE_SIZE:
                continue
            if path.stat().st_mtime < since_ts:
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            records.append(ExtractionRecord(
                source="documents",
                source_id=str(path),
                title=path.name,
                body=content[:50000],
                timestamp=mtime,
                metadata={
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "extension": path.suffix,
                },
            ))

        return records

    async def health_check(self) -> dict[str, Any]:
        exists = self._watch_path.exists()
        return {
            "status": "ok" if exists else "not_found",
            "path": str(self._watch_path),
            "exists": exists,
        }
