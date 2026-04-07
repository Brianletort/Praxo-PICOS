from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import BaseExtractor, ExtractionRecord

GENERATED_FOLDER = "_picos_generated"


class VaultExtractor(BaseExtractor):
    source_name = "vault"

    def __init__(self, vault_path: Path | None = None):
        self._vault_path = vault_path

    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        if self._vault_path is None or not self._vault_path.exists():
            return []

        since_ts = (since or datetime(2024, 1, 1, tzinfo=UTC)).timestamp()
        records: list[ExtractionRecord] = []

        for path in self._vault_path.rglob("*.md"):
            if GENERATED_FOLDER in path.parts:
                continue
            if not path.is_file():
                continue
            if path.stat().st_mtime < since_ts:
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            rel_path = path.relative_to(self._vault_path)
            records.append(ExtractionRecord(
                source="vault",
                source_id=str(rel_path),
                title=path.stem,
                body=content[:100000],
                timestamp=mtime,
                metadata={"path": str(rel_path), "folder": str(rel_path.parent)},
            ))

        return records

    async def write_to_vault(self, filename: str, content: str) -> Path:
        if self._vault_path is None:
            raise ValueError("Vault path not configured")
        output_dir = self._vault_path / GENERATED_FOLDER
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        output_path.write_text(content, encoding="utf-8")
        return output_path

    async def health_check(self) -> dict[str, Any]:
        if self._vault_path is None:
            return {"status": "not_configured", "path": None}
        exists = self._vault_path.exists()
        return {
            "status": "ok" if exists else "not_found",
            "path": str(self._vault_path),
            "exists": exists,
        }
