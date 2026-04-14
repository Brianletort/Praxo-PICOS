#!/usr/bin/env python3
"""Backfill meeting intelligence for past N days.

Usage:
    python scripts/backfill_meeting_intelligence.py --days 30

Runs the full enrichment pipeline (promote, enrich, intelligence)
on historical ExtractedRecord rows. Idempotent -- skips already-processed records.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.src.praxo_picos_api.config.schema import PicosSettings
from services.api.src.praxo_picos_api.db.engine import create_tables, get_engine
from services.workers.src.praxo_picos_workers.enrichment.pipeline import (
    EnrichmentPipeline,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("backfill")


async def main(days: int) -> None:
    settings = PicosSettings()
    settings.ensure_dirs()

    engine = get_engine()
    await create_tables()

    logger.info("Starting backfill for past %d days", days)

    pipeline = EnrichmentPipeline(engine, settings)

    total_promoted = 0
    total_enriched = 0
    total_meetings = 0
    total_people = 0
    passes = 0
    max_passes = 20

    while passes < max_passes:
        passes += 1
        result = await pipeline.run()
        stats = result.get("stats", {})

        promoted = stats.get("promoted", 0)
        enriched = stats.get("enriched", 0)
        meetings = stats.get("meetings_assembled", 0)
        people = stats.get("people_resolved", 0)
        meetings_analyzed = stats.get("meetings_analyzed", 0)

        total_promoted += promoted
        total_enriched += enriched
        total_meetings += meetings
        total_people += people

        logger.info(
            "Pass %d: promoted=%d enriched=%d meetings=%d people=%d analyzed=%d",
            passes, promoted, enriched, meetings, people, meetings_analyzed,
        )

        if promoted == 0 and meetings == 0 and people == 0:
            break

    logger.info(
        "Backfill complete: %d records promoted, %d enriched, "
        "%d meetings assembled, %d people resolved in %d passes",
        total_promoted, total_enriched, total_meetings, total_people, passes,
    )

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill meeting intelligence")
    parser.add_argument("--days", type=int, default=30, help="Days to backfill")
    args = parser.parse_args()
    asyncio.run(main(args.days))
