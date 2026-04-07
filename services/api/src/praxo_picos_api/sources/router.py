from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/sources")
async def list_sources() -> dict[str, Any]:
    from ..config.schema import get_settings

    settings = get_settings()

    sources = [
        {"name": "mail", "enabled": settings.mail_enabled, "status": "not_checked", "records_count": 0},
        {"name": "calendar", "enabled": settings.calendar_enabled, "status": "not_checked", "records_count": 0},
        {"name": "screen", "enabled": settings.screen_enabled, "status": "not_checked", "records_count": 0},
        {"name": "documents", "enabled": settings.documents_enabled, "status": "not_checked", "records_count": 0},
        {"name": "vault", "enabled": settings.vault_enabled, "status": "not_checked", "records_count": 0},
    ]

    try:
        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from ..db.engine import get_engine
        from ..db.models import DataFlowStatus, ExtractedRecord, SourceType

        engine = get_engine()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            for src in sources:
                try:
                    source_enum = SourceType(src["name"])
                    count_row = await session.execute(
                        select(func.count()).select_from(ExtractedRecord).where(ExtractedRecord.source == source_enum)
                    )
                    src["records_count"] = count_row.scalar_one()

                    flow_row = await session.execute(
                        select(DataFlowStatus).where(DataFlowStatus.source == source_enum)
                    )
                    flow = flow_row.scalar_one_or_none()
                    if flow:
                        src["status"] = flow.status or "unknown"
                        src["last_extraction"] = flow.last_record_at.isoformat() if flow.last_record_at else None
                except Exception:
                    pass
    except Exception:
        pass

    return {"sources": sources}


@router.get("/api/sources/{source_name}")
async def get_source_status(source_name: str) -> dict[str, Any]:
    valid = {"mail", "calendar", "screen", "documents", "vault"}
    if source_name not in valid:
        return {"error": f"Unknown source: {source_name}. Valid: {', '.join(sorted(valid))}"}

    from ..config.schema import get_settings

    settings = get_settings()

    enabled_map = {
        "mail": settings.mail_enabled,
        "calendar": settings.calendar_enabled,
        "screen": settings.screen_enabled,
        "documents": settings.documents_enabled,
        "vault": settings.vault_enabled,
    }

    result: dict[str, Any] = {
        "name": source_name,
        "enabled": enabled_map.get(source_name, False),
        "status": "not_checked",
        "records_count": 0,
        "last_extraction": None,
    }

    try:
        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from ..db.engine import get_engine
        from ..db.models import DataFlowStatus, ExtractedRecord, SourceType

        source_enum = SourceType(source_name)
        engine = get_engine()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            count_row = await session.execute(
                select(func.count()).select_from(ExtractedRecord).where(ExtractedRecord.source == source_enum)
            )
            result["records_count"] = count_row.scalar_one()

            flow_row = await session.execute(
                select(DataFlowStatus).where(DataFlowStatus.source == source_enum)
            )
            flow = flow_row.scalar_one_or_none()
            if flow:
                result["status"] = flow.status or "unknown"
                result["last_extraction"] = flow.last_record_at.isoformat() if flow.last_record_at else None
    except Exception:
        pass

    return result


@router.get("/api/data-flow")
async def get_data_flow_status() -> dict[str, Any]:
    """Get data flow status for all sources (used by Health Center)."""
    try:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from ..db.engine import get_engine
        from ..db.models import DataFlowStatus

        engine = get_engine()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            rows = await session.execute(select(DataFlowStatus))
            statuses = []
            for row in rows.scalars().all():
                statuses.append(
                    {
                        "source": row.source.value if hasattr(row.source, "value") else str(row.source),
                        "status": row.status,
                        "last_record_at": row.last_record_at.isoformat() if row.last_record_at else None,
                        "last_check_at": row.last_check_at.isoformat() if row.last_check_at else None,
                        "records_last_interval": row.records_last_interval,
                        "error_message": row.error_message,
                    }
                )
            return {"data_flow": statuses}
    except Exception as e:
        return {"data_flow": [], "error": str(e)[:200]}
