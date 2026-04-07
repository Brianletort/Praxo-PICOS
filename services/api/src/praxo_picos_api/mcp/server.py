from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.extractors.calendar import CalendarExtractor
from services.workers.src.praxo_picos_workers.extractors.documents import DocumentsExtractor
from services.workers.src.praxo_picos_workers.extractors.mail import MailExtractor
from services.workers.src.praxo_picos_workers.extractors.screenpipe import ScreenpipeExtractor
from services.workers.src.praxo_picos_workers.extractors.vault import VaultExtractor
from services.workers.src.praxo_picos_workers.generators.daily_brief import DailyBriefGenerator

from ..config.schema import PicosSettings, get_settings
from ..db.engine import get_engine
from ..db.models import DataFlowStatus, SourceType
from ..db.models import ExtractedRecord as DBExtractedRecord
from ..health import health as api_health
from ..search.hybrid import HybridSearch

logger = logging.getLogger(__name__)

VALID_SOURCE_NAMES = frozenset(s.value for s in SourceType)


def _utc_day_bounds(date_str: str) -> tuple[datetime, datetime]:
    day = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    return day, day + timedelta(days=1)


def _db_row_to_extraction(row: DBExtractedRecord) -> ExtractionRecord:
    meta: dict[str, Any] = {}
    raw = row.metadata_json
    if raw:
        try:
            meta = json.loads(raw)
        except json.JSONDecodeError:
            meta = {"_parse_error": True, "preview": raw[:200]}

    src = row.source.value if isinstance(row.source, SourceType) else str(row.source)
    return ExtractionRecord(
        source=src,
        source_id=row.source_id or row.id,
        title=row.title or "",
        body=row.body or "",
        timestamp=row.timestamp,
        metadata=meta,
    )


def _extractor_for_source(source_name: str, settings: PicosSettings) -> MailExtractor | CalendarExtractor | ScreenpipeExtractor | DocumentsExtractor | VaultExtractor | None:
    if source_name == "mail":
        return MailExtractor()
    if source_name == "calendar":
        return CalendarExtractor()
    if source_name == "screen":
        return ScreenpipeExtractor(
            base_url=f"http://127.0.0.1:{settings.screenpipe_port}",
        )
    if source_name == "documents":
        return DocumentsExtractor(watch_path=settings.documents_path)
    if source_name == "vault":
        return VaultExtractor(vault_path=settings.vault_path)
    return None


def create_mcp_server(
    *,
    host: str | None = None,
    port: int | None = None,
) -> FastMCP:
    bind_host = host if host is not None else get_mcp_host()
    bind_port = port if port is not None else get_mcp_port()
    mcp = FastMCP(
        "Praxo-PICOS",
        instructions=(
            "Personal Intelligence Operating System - MCP tools for memory search, "
            "briefs, and source management"
        ),
        host=bind_host,
        port=bind_port,
    )

    @mcp.tool()
    async def health_check() -> dict[str, Any]:
        """Check the health status of Praxo-PICOS services."""
        try:
            return await api_health()
        except Exception as e:
            logger.warning("MCP health_check failed", exc_info=True)
            return {
                "status": "error",
                "service": "praxo-picos-mcp",
                "error": str(e)[:500],
                "timestamp": datetime.now(UTC).isoformat(),
            }

    @mcp.tool()
    async def search_memory(query: str, limit: int = 10) -> dict[str, Any]:
        """Search across all ingested memory sources using hybrid search (keyword + semantic).

        Args:
            query: The search query string
            limit: Maximum number of results to return (default 10)
        """
        try:
            engine = get_engine()
            hybrid = HybridSearch(engine=engine)
            results = await hybrid.search(query=query, limit=limit)
            return {
                "query": query,
                "results": [r.to_dict() for r in results],
                "total": len(results),
            }
        except Exception as e:
            logger.warning("MCP search_memory failed", exc_info=True)
            return {
                "query": query,
                "results": [],
                "total": 0,
                "error": str(e)[:500],
                "degraded": True,
            }

    @mcp.tool()
    async def get_daily_brief(date: str | None = None) -> dict[str, Any]:
        """Get the daily brief/summary for a given date.

        Args:
            date: ISO date string (YYYY-MM-DD). Defaults to today.
        """
        target_date = date or datetime.now(UTC).strftime("%Y-%m-%d")
        try:
            _utc_day_bounds(target_date)
        except ValueError:
            return {
                "date": target_date,
                "brief": None,
                "error": "Invalid date format; use YYYY-MM-DD",
            }

        try:
            day_start, day_end = _utc_day_bounds(target_date)
            engine = get_engine()
            stmt = (
                select(DBExtractedRecord)
                .where(
                    DBExtractedRecord.timestamp >= day_start,
                    DBExtractedRecord.timestamp < day_end,
                )
                .order_by(DBExtractedRecord.timestamp.desc())
                .limit(2000)
            )
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async with factory() as session:
                result = await session.execute(stmt)
                rows = list(result.scalars().all())

            records = [_db_row_to_extraction(r) for r in rows]
            gen = DailyBriefGenerator()
            brief_text = gen.generate(records, date=day_start)
            return {
                "date": target_date,
                "brief": brief_text,
                "record_count": len(records),
            }
        except Exception as e:
            logger.warning("MCP get_daily_brief failed", exc_info=True)
            return {
                "date": target_date,
                "brief": None,
                "error": str(e)[:500],
                "degraded": True,
            }

    @mcp.tool()
    async def list_sources() -> dict[str, Any]:
        """List all configured data sources and their current status."""
        try:
            settings = get_settings()
            specs: list[tuple[str, bool]] = [
                ("mail", settings.mail_enabled),
                ("calendar", settings.calendar_enabled),
                ("screen", settings.screen_enabled),
                ("documents", settings.documents_enabled),
                ("vault", settings.vault_enabled),
            ]
            flow_by_source: dict[str, dict[str, Any]] = {}
            try:
                engine = get_engine()
                factory = async_sessionmaker(engine, expire_on_commit=False)
                async with factory() as session:
                    flow_result = await session.execute(select(DataFlowStatus))
                    for row in flow_result.scalars().all():
                        key = row.source.value if isinstance(row.source, SourceType) else str(row.source)
                        flow_by_source[key] = {
                            "status": row.status or "unknown",
                            "last_record_at": row.last_record_at.isoformat()
                            if row.last_record_at is not None
                            else None,
                            "error_message": (row.error_message or "")[:300]
                            if row.error_message
                            else None,
                        }
            except Exception:
                logger.warning("MCP list_sources: could not load data_flow_status", exc_info=True)

            sources: list[dict[str, Any]] = []
            for name, enabled in specs:
                entry: dict[str, Any] = {
                    "name": name,
                    "enabled": enabled,
                    "status": "unknown",
                }
                flow = flow_by_source.get(name)
                if flow is not None:
                    entry["status"] = flow["status"]
                    if flow["last_record_at"] is not None:
                        entry["last_record_at"] = flow["last_record_at"]
                    if flow["error_message"]:
                        entry["error_message"] = flow["error_message"]
                sources.append(entry)

            return {"sources": sources}
        except Exception as e:
            logger.warning("MCP list_sources failed", exc_info=True)
            return {
                "sources": [],
                "error": str(e)[:500],
                "degraded": True,
            }

    @mcp.tool()
    async def get_source_status(source_name: str) -> dict[str, Any]:
        """Get detailed status for a specific data source.

        Args:
            source_name: Name of the source (mail, calendar, screen, documents, vault)
        """
        if source_name not in VALID_SOURCE_NAMES:
            return {
                "error": (
                    f"Unknown source: {source_name}. "
                    f"Valid: {', '.join(sorted(VALID_SOURCE_NAMES))}"
                )
            }

        try:
            settings = get_settings()
            enabled = {
                "mail": settings.mail_enabled,
                "calendar": settings.calendar_enabled,
                "screen": settings.screen_enabled,
                "documents": settings.documents_enabled,
                "vault": settings.vault_enabled,
            }[source_name]

            last_extraction: str | None = None
            flow_status: str | None = None
            flow_error: str | None = None
            records_count = 0

            try:
                engine = get_engine()
                st = SourceType(source_name)
                factory = async_sessionmaker(engine, expire_on_commit=False)
                async with factory() as session:
                    flow_result = await session.execute(
                        select(DataFlowStatus).where(DataFlowStatus.source == st)
                    )
                    flow = flow_result.scalar_one_or_none()
                    if flow is not None:
                        flow_status = flow.status
                        flow_error = (flow.error_message or "")[:300] or None
                        if flow.last_record_at is not None:
                            last_extraction = flow.last_record_at.isoformat()

                    count_result = await session.execute(
                        select(func.count())
                        .select_from(DBExtractedRecord)
                        .where(DBExtractedRecord.source == st)
                    )
                    records_count = int(count_result.scalar_one() or 0)
            except Exception:
                logger.warning("MCP get_source_status: DB lookup failed", exc_info=True)

            health_info: dict[str, Any] | None = None
            health_error: str | None = None
            try:
                extractor = _extractor_for_source(source_name, settings)
                if extractor is not None:
                    health_info = await extractor.health_check()
            except Exception as e:
                health_error = str(e)[:500]
                logger.warning("MCP get_source_status: health_check failed", exc_info=True)

            status = "unknown"
            if health_info and health_info.get("status") is not None:
                status = str(health_info["status"])
            elif flow_status:
                status = flow_status

            return {
                "source": source_name,
                "enabled": enabled,
                "status": status,
                "last_extraction": last_extraction,
                "records_count": records_count,
                "flow_status": flow_status,
                "flow_error": flow_error,
                "health_check": health_info,
                "health_error": health_error,
            }
        except Exception as e:
            logger.warning("MCP get_source_status failed", exc_info=True)
            return {
                "source": source_name,
                "status": "error",
                "error": str(e)[:500],
                "degraded": True,
            }

    return mcp


def get_mcp_port() -> int:
    return int(os.environ.get("PRAXO_MCP_PORT", "8870"))


def get_mcp_host() -> str:
    return os.environ.get("PRAXO_MCP_HOST", "127.0.0.1")
