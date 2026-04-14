"""Enrichment pipeline engine -- the three-stage post-extraction processor.

Runs automatically after every extraction cycle:
  Stage 1: Promote raw ExtractionRecords into typed MemoryObjects
  Stage 2: LLM enrichment + entity resolution + meeting assembly
  Stage 3: Intelligence analysis (meeting, person, energy)
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider
from services.api.src.praxo_picos_api.config.schema import PicosSettings
from services.api.src.praxo_picos_api.db.models import (
    ExtractedRecord,
    ProcessingStatus,
)
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import (
    Meeting,
    MemoryObject,
    ObjectType,
    Person,
    SOURCE_TO_OBJECT_TYPE,
)
from services.api.src.praxo_picos_api.models.enums import Sensitivity

from ..extractors.screenpipe_deep import ScreenpipeDeepConnector
from .energy_intelligence import EnergyIntelligenceRunner
from .llm_enricher import LLMEnricher
from .meeting_assembler import MeetingAssembler
from .meeting_intelligence import MeetingIntelligenceRunner
from .person_intelligence import PersonIntelligenceRunner
from .person_resolver import PersonResolver

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """Orchestrates all post-extraction processing."""

    def __init__(
        self,
        engine: AsyncEngine,
        settings: PicosSettings | None = None,
        llm: LLMProvider | None = None,
    ) -> None:
        self._engine = engine
        self._settings = settings or PicosSettings()
        self._llm = llm
        self._factory = async_sessionmaker(engine, expire_on_commit=False)

        port = self._settings.screenpipe_port
        self._screenpipe = ScreenpipeDeepConnector(
            base_url=f"http://127.0.0.1:{port}",
            max_frames_per_meeting=self._settings.max_frames_per_meeting,
        )

    async def run(self, records: list[Any] | None = None) -> dict[str, Any]:
        """Run the full enrichment pipeline. Idempotent."""
        if not self._settings.intelligence_enabled:
            return {"status": "disabled"}

        stats: dict[str, int] = {
            "promoted": 0, "enriched": 0, "meetings_assembled": 0,
            "people_resolved": 0, "meetings_analyzed": 0, "people_analyzed": 0,
        }

        async with self._factory() as session:
            store = ObjectStore(session)

            promoted = await self._stage1_promote(session, store, records)
            stats["promoted"] = promoted

            enriched = await self._stage2_enrich(session, store)
            stats["enriched"] = enriched["enriched"]
            stats["meetings_assembled"] = enriched["meetings"]
            stats["people_resolved"] = enriched["people"]

            intel = await self._stage3_intelligence(session, store)
            stats["meetings_analyzed"] = intel["meetings"]
            stats["people_analyzed"] = intel["people"]

            await session.commit()

        logger.info("Enrichment pipeline completed: %s", stats)
        return {"status": "completed", "stats": stats}

    async def _stage1_promote(
        self,
        session: AsyncSession,
        store: ObjectStore,
        records: list[Any] | None,
    ) -> int:
        """Promote raw ExtractedRecords into typed MemoryObjects."""
        stmt = (
            select(ExtractedRecord)
            .outerjoin(
                ProcessingStatus,
                ExtractedRecord.id == ProcessingStatus.record_id,
            )
            .where(ProcessingStatus.record_id.is_(None))
            .limit(500)
        )
        result = await session.execute(stmt)
        unprocessed = list(result.scalars())

        promoted = 0
        for row in unprocessed:
            try:
                obj = self._record_to_memory_object(row)
                obj_id = await store.put(obj)

                status = ProcessingStatus(
                    record_id=row.id,
                    source=row.source.value if hasattr(row.source, "value") else str(row.source),
                    promoted_at=datetime.now(UTC),
                    memory_object_id=obj_id,
                )
                session.add(status)
                promoted += 1
            except Exception:
                logger.warning("Failed to promote record %s", row.id, exc_info=True)
                status = ProcessingStatus(
                    record_id=row.id,
                    source=row.source.value if hasattr(row.source, "value") else str(row.source),
                    error="promotion_failed",
                )
                session.add(status)

        if promoted:
            await session.flush()
        return promoted

    async def _stage2_enrich(
        self,
        session: AsyncSession,
        store: ObjectStore,
    ) -> dict[str, int]:
        """LLM enrichment, person resolution, meeting assembly."""
        stats = {"enriched": 0, "meetings": 0, "people": 0}

        unenriched = await session.execute(
            select(ProcessingStatus)
            .where(ProcessingStatus.promoted_at.isnot(None))
            .where(ProcessingStatus.enriched_at.is_(None))
            .where(ProcessingStatus.error.is_(None))
            .limit(200)
        )
        to_enrich = list(unenriched.scalars())

        if self._llm and to_enrich:
            enricher = LLMEnricher(self._llm)
            for ps in to_enrich:
                if ps.memory_object_id:
                    obj = await store.get(ps.memory_object_id)
                    if obj:
                        enriched = await enricher.enrich(obj)
                        if enriched:
                            obj.attrs.update(enriched)
                            await store.put(obj)
                            stats["enriched"] += 1
                ps.enriched_at = datetime.now(UTC)
            await session.flush()

        resolver = PersonResolver(store)
        new_people = await resolver.resolve_from_recent(session)
        stats["people"] = new_people

        assembler = MeetingAssembler(store, self._screenpipe)
        new_meetings = await assembler.assemble_recent(session)
        stats["meetings"] = new_meetings

        return stats

    async def _stage3_intelligence(
        self,
        session: AsyncSession,
        store: ObjectStore,
    ) -> dict[str, int]:
        """Run intelligence analyzers on meetings and people."""
        stats = {"meetings": 0, "people": 0}

        unanalyzed = await session.execute(
            select(ProcessingStatus)
            .where(ProcessingStatus.enriched_at.isnot(None))
            .where(ProcessingStatus.intelligence_at.is_(None))
            .where(ProcessingStatus.error.is_(None))
            .limit(100)
        )
        to_analyze = list(unanalyzed.scalars())

        meeting_runner = MeetingIntelligenceRunner(
            store, self._screenpipe, self._llm,
        )

        meetings = await store.query(object_type=ObjectType.MEETING, limit=50)
        for m in meetings:
            if isinstance(m, Meeting) and not m.has_intelligence:
                analyzed = await meeting_runner.analyze(m)
                if analyzed:
                    stats["meetings"] += 1

        for ps in to_analyze:
            ps.intelligence_at = datetime.now(UTC)
        if to_analyze:
            await session.flush()

        person_runner = PersonIntelligenceRunner(store, self._llm)
        people_updated = await person_runner.update_all()
        stats["people"] = people_updated

        if self._settings.screen_enabled:
            energy_runner = EnergyIntelligenceRunner(store, self._screenpipe)
            await energy_runner.run_today()

        return stats

    @staticmethod
    def _record_to_memory_object(row: ExtractedRecord) -> MemoryObject:
        source_str = row.source.value if hasattr(row.source, "value") else str(row.source)
        obj_type = SOURCE_TO_OBJECT_TYPE.get(source_str, ObjectType.DOCUMENT)

        attrs: dict[str, Any] = {}
        if row.metadata_json:
            try:
                raw = row.metadata_json
                if raw.startswith("{"):
                    attrs = json.loads(raw)
                else:
                    import ast
                    attrs = ast.literal_eval(raw)
            except Exception:
                attrs = {"raw_metadata": row.metadata_json}

        from services.api.src.praxo_picos_api.db.models import SourceType
        source_enum = SourceType(source_str)

        return MemoryObject(
            object_type=obj_type,
            source=source_enum,
            source_id=row.source_id or "",
            title=row.title,
            body=row.body,
            timestamp=row.timestamp,
            attrs=attrs,
            sensitivity=Sensitivity.INTERNAL,
        )
