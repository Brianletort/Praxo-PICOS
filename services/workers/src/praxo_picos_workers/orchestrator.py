"""Extraction orchestrator -- the data pipeline that makes PICOS work.

Runs enabled extractors on a schedule, normalizes records, inserts into
SQLite, indexes into FTS5, and updates DataFlowStatus.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.src.praxo_picos_api.config.manager import ConfigManager
from services.api.src.praxo_picos_api.config.schema import PicosSettings
from services.api.src.praxo_picos_api.db.models import (
    DataFlowStatus,
    ExtractedRecord,
    SourceType,
)

from .extractors.base import BaseExtractor, ExtractionRecord
from .extractors.calendar import CalendarExtractor
from .extractors.documents import DocumentsExtractor
from .extractors.mail import MailExtractor
from .extractors.screenpipe import ScreenpipeExtractor
from .extractors.vault import VaultExtractor

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 900  # 15 minutes


def _load_effective_config(settings: PicosSettings) -> dict:
    """Merge saved YAML config over PicosSettings defaults."""
    mgr = ConfigManager(settings)
    yaml_cfg = mgr.load_yaml()
    return {
        "mail_enabled": yaml_cfg.get("mail_enabled", settings.mail_enabled),
        "calendar_enabled": yaml_cfg.get("calendar_enabled", settings.calendar_enabled),
        "screen_enabled": yaml_cfg.get("screen_enabled", settings.screen_enabled),
        "documents_enabled": yaml_cfg.get("documents_enabled", settings.documents_enabled),
        "vault_enabled": yaml_cfg.get("vault_enabled", settings.vault_enabled),
        "vault_path": yaml_cfg.get("vault_path", str(settings.vault_path or "")),
        "documents_path": yaml_cfg.get("documents_path", str(settings.documents_path or "")),
        "screenpipe_port": yaml_cfg.get("screenpipe_port", settings.screenpipe_port),
    }


def _build_extractors(settings: PicosSettings) -> list[BaseExtractor]:
    cfg = _load_effective_config(settings)
    extractors: list[BaseExtractor] = []
    if cfg["mail_enabled"]:
        extractors.append(MailExtractor())
    if cfg["calendar_enabled"]:
        extractors.append(CalendarExtractor())
    if cfg["screen_enabled"]:
        extractors.append(
            ScreenpipeExtractor(base_url=f"http://127.0.0.1:{cfg['screenpipe_port']}")
        )
    if cfg["documents_enabled"] and cfg["documents_path"]:
        extractors.append(DocumentsExtractor(watch_path=Path(cfg["documents_path"])))
    if cfg["vault_enabled"] and cfg["vault_path"]:
        extractors.append(VaultExtractor(vault_path=Path(cfg["vault_path"])))
    return extractors


async def _insert_records(
    session: AsyncSession,
    records: list[ExtractionRecord],
) -> int:
    inserted = 0
    for record in records:
        try:
            source_enum = SourceType(record.source)
        except ValueError:
            logger.warning("Unknown source type: %s", record.source)
            continue

        db_record = ExtractedRecord(
            source=source_enum,
            source_id=record.source_id,
            title=record.title,
            body=record.body,
            timestamp=record.timestamp,
            metadata_json=str(record.metadata) if record.metadata else None,
        )
        session.add(db_record)
        inserted += 1

    if inserted:
        await session.flush()
    return inserted


async def _index_records_fts(
    session: AsyncSession,
    records: list[ExtractionRecord],
) -> int:
    indexed = 0
    for record in records:
        content = ""
        if record.title:
            content += record.title + " "
        if record.body:
            content += record.body[:5000]

        if not content.strip():
            continue

        await session.execute(
            text("DELETE FROM search_fts WHERE record_id = :record_id"),
            {"record_id": record.source_id},
        )
        await session.execute(
            text(
                "INSERT INTO search_fts (record_id, content, source) "
                "VALUES (:record_id, :content, :source)"
            ),
            {
                "record_id": record.source_id,
                "content": content.strip(),
                "source": record.source,
            },
        )
        indexed += 1
    return indexed


async def _update_flow_status(
    session: AsyncSession,
    source: SourceType,
    record_count: int,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    status_val = "ok" if record_count > 0 else ("error" if error else "empty")

    flow = DataFlowStatus(
        source=source,
        last_record_at=now if record_count > 0 else None,
        last_check_at=now,
        records_last_interval=record_count,
        status=status_val,
        error_message=error,
    )
    await session.merge(flow)


async def run_extraction_cycle(
    engine: AsyncEngine | None = None,
    settings: PicosSettings | None = None,
) -> dict[str, Any]:
    """Run one full extraction cycle across all enabled sources."""
    if engine is None:
        from services.api.src.praxo_picos_api.db.engine import get_engine
        engine = get_engine()

    if settings is None:
        settings = PicosSettings()

    extractors = _build_extractors(settings)
    if not extractors:
        return {"status": "no_sources_enabled", "sources": {}}

    factory = async_sessionmaker(engine, expire_on_commit=False)
    results: dict[str, Any] = {}
    since = datetime.now(UTC) - timedelta(hours=24)

    for extractor in extractors:
        source_name = extractor.source_name
        try:
            records = await extractor.extract(since=since)
            logger.info("Extracted %d records from %s", len(records), source_name)

            async with factory() as session:
                inserted = await _insert_records(session, records)
                indexed = await _index_records_fts(session, records)
                source_enum = SourceType(source_name)
                await _update_flow_status(session, source_enum, len(records))
                await session.commit()

            results[source_name] = {
                "extracted": len(records),
                "inserted": inserted,
                "indexed": indexed,
                "status": "ok",
            }
        except PermissionError as e:
            logger.warning("Permission denied for %s: %s", source_name, e)
            try:
                source_enum = SourceType(source_name)
                async with factory() as session:
                    await _update_flow_status(session, source_enum, 0, str(e))
                    await session.commit()
            except Exception:
                pass
            results[source_name] = {"status": "permission_denied", "error": str(e)}
        except Exception as e:
            logger.warning("Extraction failed for %s: %s", source_name, e)
            try:
                source_enum = SourceType(source_name)
                async with factory() as session:
                    await _update_flow_status(session, source_enum, 0, str(e))
                    await session.commit()
            except Exception:
                pass
            results[source_name] = {"status": "error", "error": str(e)[:500]}

    return {"status": "completed", "sources": results}


async def extraction_loop(
    engine: AsyncEngine | None = None,
    interval: int = DEFAULT_INTERVAL_SECONDS,
) -> None:
    """Background loop that runs extraction cycles on a schedule."""
    logger.info("Extraction loop started (interval=%ds)", interval)
    while True:
        try:
            result = await run_extraction_cycle(engine=engine)
            logger.info("Extraction cycle completed: %s", result.get("status"))
        except Exception:
            logger.exception("Extraction cycle failed")
        await asyncio.sleep(interval)
