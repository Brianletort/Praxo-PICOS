"""Stage 3c: Daily cognitive energy profile.

Generates an Insight object with cognitive energy estimates from
screen activity patterns.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from services.api.src.praxo_picos_api.db.models import SourceType
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import Meeting, ObjectType
from services.api.src.praxo_picos_api.models.episodes import Insight

from ..analytics.attention_tracker import AttentionTracker
from ..analytics.cognitive_energy import CognitiveEnergyTracker
from ..extractors.screenpipe_deep import ScreenpipeDeepConnector
from ..intelligence.operating_optimization import OperatingOptimizationScorer

logger = logging.getLogger(__name__)


class EnergyIntelligenceRunner:
    """Generates daily cognitive energy Insight objects."""

    def __init__(
        self,
        store: ObjectStore,
        screenpipe: ScreenpipeDeepConnector,
    ) -> None:
        self._store = store
        self._screenpipe = screenpipe
        self._tracker = CognitiveEnergyTracker()

    async def run_today(self) -> bool:
        """Generate energy profile for today. Returns True if created."""
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        date_key = day_start.strftime("%Y-%m-%d")
        existing = await self._store.query(object_type=ObjectType.INSIGHT, limit=50)
        for obj in existing:
            if isinstance(obj, Insight) and obj.attrs.get("date") == date_key:
                return False

        try:
            frames = await self._screenpipe.get_frames(day_start, now)
        except Exception:
            logger.warning("Could not get frames for energy analysis")
            return False

        if not frames:
            return False

        meetings = await self._store.query(
            object_type=ObjectType.MEETING, since=day_start, until=day_end, limit=30,
        )
        meeting_windows = []
        for m in meetings:
            if isinstance(m, Meeting) and m.start_time and m.end_time:
                meeting_windows.append((m.start_time, m.end_time))

        profile = self._tracker.analyze_day(frames, meeting_windows)

        attention = AttentionTracker()
        deep_blocks = attention.find_deep_work_blocks(frames)
        deep_work_data = [
            {
                "start": b.start_time.isoformat(),
                "end": b.end_time.isoformat(),
                "app": b.app_name,
                "duration_min": round(b.duration_minutes, 1),
                "break_reason": b.break_reason,
            }
            for b in deep_blocks
        ]

        ops_scorer = OperatingOptimizationScorer()
        ops_attrs = {
            "cognitive_energy": profile.to_dict(),
            "deep_work_blocks": deep_work_data,
            "deep_work_total_min": round(sum(b.duration_minutes for b in deep_blocks), 1),
        }
        ops_profile = ops_scorer.score(ops_attrs)

        insight = Insight(
            title=f"Energy Profile: {date_key}",
            source=SourceType.SCREEN,
            source_id=f"energy_{date_key}",
            timestamp=day_start,
            insight_type="cognitive_energy",
            period_start=day_start,
            period_end=day_end,
            attrs={
                "date": date_key,
                "cognitive_energy": profile.to_dict(),
                "deep_work_blocks": deep_work_data,
                "deep_work_total_min": round(sum(b.duration_minutes for b in deep_blocks), 1),
                "operating_optimization": ops_profile.to_dict(),
            },
        )
        await self._store.put(insight)
        return True
