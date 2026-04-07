from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .base import BaseExtractor, ExtractionRecord

CALENDAR_DB_PATHS = [
    Path.home() / "Library/Calendars/Calendar.sqlitedb",
    Path.home() / "Library/Group Containers/group.com.apple.calendar/Calendar.sqlitedb",
]

CALENDAR_QUERY = """
SELECT 
    ci.ROWID,
    ci.summary,
    ci.description,
    ci.start_date,
    ci.end_date,
    ci.location
FROM CalendarItem ci
WHERE ci.start_date > ?
ORDER BY ci.start_date ASC
LIMIT 500
"""

CORE_DATA_EPOCH = 978307200


class CalendarExtractor(BaseExtractor):
    source_name = "calendar"

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or self._find_calendar_db()

    def _find_calendar_db(self) -> Path | None:
        for path in CALENDAR_DB_PATHS:
            if path.exists():
                return path
        return None

    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        if self._db_path is None or not self._db_path.exists():
            raise PermissionError("Calendar database not found. Grant Full Disk Access.")

        since_core = (since or datetime(2024, 1, 1, tzinfo=UTC)).timestamp() - CORE_DATA_EPOCH
        records: list[ExtractionRecord] = []

        try:
            conn = sqlite3.connect(f"file:{self._db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(CALENDAR_QUERY, (since_core,))

            for row in cursor.fetchall():
                start_ts = datetime.fromtimestamp(
                    (row["start_date"] or 0) + CORE_DATA_EPOCH, tz=UTC
                )
                end_ts = datetime.fromtimestamp(
                    (row["end_date"] or 0) + CORE_DATA_EPOCH, tz=UTC
                ) if row["end_date"] else None

                records.append(ExtractionRecord(
                    source="calendar",
                    source_id=str(row["ROWID"]),
                    title=row["summary"] or "(no title)",
                    body=row["description"] or "",
                    timestamp=start_ts,
                    metadata={
                        "location": row["location"] or "",
                        "end_time": end_ts.isoformat() if end_ts else None,
                    },
                ))
            conn.close()
        except sqlite3.OperationalError as e:
            if "unable to open" in str(e).lower():
                raise PermissionError(f"Cannot access Calendar database: {e}") from e
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
