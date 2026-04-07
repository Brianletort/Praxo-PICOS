from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import BaseExtractor, ExtractionRecord

MAIL_DB_PATHS = [
    Path.home() / "Library/Mail/V10/MailData/Envelope Index",
    Path.home() / "Library/Mail/V9/MailData/Envelope Index",
    Path.home() / "Library/Mail/V8/MailData/Envelope Index",
]

MAIL_QUERY = """
SELECT 
    m.ROWID,
    m.subject,
    m.date_sent,
    m.date_received,
    a.address as sender_address
FROM messages m
LEFT JOIN addresses a ON m.sender = a.ROWID
WHERE m.date_received > ?
ORDER BY m.date_received DESC
LIMIT 500
"""


class MailExtractor(BaseExtractor):
    source_name = "mail"

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or self._find_mail_db()

    def _find_mail_db(self) -> Path | None:
        for path in MAIL_DB_PATHS:
            if path.exists():
                return path
        return None

    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        if self._db_path is None or not self._db_path.exists():
            raise PermissionError("Mail database not found. Grant Full Disk Access.")

        since_ts = (since or datetime(2024, 1, 1, tzinfo=UTC)).timestamp()
        records: list[ExtractionRecord] = []

        try:
            conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(MAIL_QUERY, (since_ts,))

            for row in cursor.fetchall():
                ts = datetime.fromtimestamp(row["date_received"] or 0, tz=UTC)
                records.append(ExtractionRecord(
                    source="mail",
                    source_id=str(row["ROWID"]),
                    title=row["subject"] or "(no subject)",
                    body="",
                    timestamp=ts,
                    metadata={
                        "from": row["sender_address"] or "",
                        "to": [],
                    },
                ))
            conn.close()
        except sqlite3.OperationalError as e:
            if "unable to open" in str(e).lower():
                raise PermissionError(f"Cannot access Mail database: {e}") from e
            raise

        return records

    async def health_check(self) -> dict[str, Any]:
        if self._db_path is None:
            return {"status": "not_found", "path": None}
        if not self._db_path.exists():
            return {"status": "missing", "path": str(self._db_path)}
        try:
            conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
            conn.execute("SELECT 1")
            conn.close()
            return {"status": "ok", "path": str(self._db_path)}
        except Exception as e:
            return {"status": "error", "path": str(self._db_path), "error": str(e)[:200]}
