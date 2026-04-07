from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.src.praxo_picos_api.db.models import (
    DataFlowStatus,
    ExtractedRecord,
    SourceType,
)

logger = logging.getLogger(__name__)

FRESHNESS_SLAS: dict[str, timedelta] = {
    "mail": timedelta(minutes=30),
    "calendar": timedelta(minutes=30),
    "screen": timedelta(minutes=5),
    "documents": timedelta(hours=1),
    "vault": timedelta(hours=1),
}


def _ensure_utc(dt: datetime) -> datetime:
    """SQLite often returns naive datetimes; treat them as UTC for comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def compute_status(
    last_record_at: datetime | None,
    sla: timedelta,
    now: datetime | None = None,
) -> str:
    if last_record_at is None:
        return "unknown"
    now = now or datetime.now(UTC)
    last = _ensure_utc(last_record_at)
    now_utc = _ensure_utc(now)
    age = now_utc - last
    if age <= sla:
        return "ok"
    if age <= sla * 2:
        return "warning"
    return "error"


class DataFlowMonitor:
    def __init__(self, enabled_sources: set[str] | None = None):
        self._enabled_sources = enabled_sources or {s.value for s in SourceType}

    async def check_all(self, session: AsyncSession) -> dict[str, dict[str, Any]]:
        now = datetime.now(UTC)
        results: dict[str, dict[str, Any]] = {}

        for source_name in self._enabled_sources:
            try:
                source_enum = SourceType(source_name)
            except ValueError:
                continue

            result = await self._check_source(session, source_enum, now)
            results[source_name] = result

        return results

    async def _check_source(
        self,
        session: AsyncSession,
        source: SourceType,
        now: datetime,
    ) -> dict[str, Any]:
        sla = FRESHNESS_SLAS.get(source.value, timedelta(hours=1))

        latest_row = await session.execute(
            select(ExtractedRecord.timestamp)
            .where(ExtractedRecord.source == source)
            .order_by(ExtractedRecord.timestamp.desc())
            .limit(1)
        )
        latest = latest_row.scalar_one_or_none()

        count_row = await session.execute(
            select(func.count())
            .select_from(ExtractedRecord)
            .where(
                ExtractedRecord.source == source,
                ExtractedRecord.created_at >= now - sla,
            )
        )
        recent_count = count_row.scalar_one()

        status = compute_status(latest, sla, now)

        flow_status = DataFlowStatus(
            source=source,
            last_record_at=_ensure_utc(latest) if latest is not None else None,
            last_check_at=now,
            records_last_interval=recent_count,
            status=status,
            error_message=None,
        )
        await session.merge(flow_status)
        await session.commit()

        return {
            "source": source.value,
            "status": status,
            "last_record_at": _ensure_utc(latest).isoformat() if latest else None,
            "records_last_interval": recent_count,
            "sla_minutes": int(sla.total_seconds() / 60),
            "checked_at": now.isoformat(),
        }

    async def check_source(
        self, session: AsyncSession, source_name: str
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        source = SourceType(source_name)
        return await self._check_source(session, source, now)
