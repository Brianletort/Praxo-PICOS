"""Stage 3a: Run all L1-L3 intelligence analyzers on a single meeting.

Fetches audio + frames from Screenpipe, runs each analyzer, writes results
into Meeting.attrs, persists via ObjectStore.
"""
from __future__ import annotations

import logging
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import Meeting, ObjectType
from services.api.src.praxo_picos_api.narrative.generator import NarrativeGenerator

from ..analytics.attention_tracker import AttentionTracker
from ..analytics.meeting_delivery import DeliveryAnalyzer
from ..analytics.meeting_frame_analyzer import FrameAnalyzer
from ..analytics.meeting_vision import VisionAnalyzer
from ..analytics.power_dynamics import PowerDynamicsAnalyzer
from ..analytics.scorecard import ScorecardBuilder
from ..extractors.screenpipe_deep import ScreenpipeDeepConnector
from ..intelligence.executive_performance import ExecutivePerformanceScorer
from ..intelligence.meeting_intelligence_scores import MeetingIntelligenceScorer
from ..intelligence.transcript_analysis import TranscriptAnalyzer

logger = logging.getLogger(__name__)


class MeetingIntelligenceRunner:
    """Runs the full intelligence stack on a single meeting."""

    def __init__(
        self,
        store: ObjectStore,
        screenpipe: ScreenpipeDeepConnector,
        llm: LLMProvider | None = None,
    ) -> None:
        self._store = store
        self._screenpipe = screenpipe
        self._llm = llm
        self._delivery = DeliveryAnalyzer()
        self._frames = FrameAnalyzer()
        self._attention = AttentionTracker()
        self._power = PowerDynamicsAnalyzer()
        self._scorecard = ScorecardBuilder()
        self._narrator = NarrativeGenerator(llm)

    async def analyze(self, meeting: Meeting) -> bool:
        """Run all layers on a meeting. Returns True if intelligence was produced."""
        if not meeting.start_time or not meeting.end_time:
            return False

        start = meeting.start_time
        end = meeting.end_time

        try:
            segments = await self._screenpipe.get_meeting_audio(start, end)
        except Exception:
            logger.warning("Could not get audio for meeting %s", meeting.id)
            segments = []

        try:
            frames = await self._screenpipe.get_frames(start, end)
        except Exception:
            logger.warning("Could not get frames for meeting %s", meeting.id)
            frames = []

        if not segments and not frames:
            return False

        if segments:
            delivery = self._delivery.analyze(segments, start, end)
            meeting.attrs["delivery_metrics"] = delivery.to_dict()

            power = self._power.analyze(segments)
            meeting.attrs["power_dynamics"] = power.to_dict()

        if frames:
            visual = self._frames.analyze(frames, start, end)
            meeting.attrs["visual_signals"] = visual.to_dict()

            attention = self._attention.analyze_meeting(
                frames, start, end, meeting.attrs.get("app_name", ""),
            )
            meeting.attrs["attention"] = attention.to_dict()

        if self._llm and frames:
            frames_with_data = [f for f in frames if f.frame_data]
            if frames_with_data:
                try:
                    vision = VisionAnalyzer(self._llm)
                    body = await vision.analyze(frames_with_data)
                    meeting.attrs["body_language"] = body.to_dict()
                except Exception:
                    logger.warning("Vision analysis failed for meeting %s", meeting.id)

        historical = await self._get_historical_scores(meeting)
        scorecard = self._scorecard.build(meeting.attrs, historical)
        meeting.attrs["scorecard"] = scorecard.to_dict()

        exec_scorer = ExecutivePerformanceScorer()
        exec_profile = exec_scorer.score(meeting.attrs)
        meeting.attrs["executive_performance"] = exec_profile.to_dict()

        meeting_scorer = MeetingIntelligenceScorer()
        meeting_intel = meeting_scorer.score(meeting.attrs)
        meeting.attrs["meeting_intelligence"] = meeting_intel.to_dict()

        if self._llm and segments:
            transcript_text = "\n".join(
                f"[{s.speaker}]: {s.text}" for s in segments if s.text
            )
            if transcript_text:
                try:
                    analyzer = TranscriptAnalyzer(self._llm)
                    transcript_intel = await analyzer.analyze_meeting(
                        transcript_text, meeting.attrs,
                    )
                    meeting.attrs["transcript_intelligence"] = transcript_intel.to_dict()
                except Exception:
                    logger.warning("Transcript analysis failed for %s", meeting.id)

        try:
            coaching = await self._narrator.generate_coaching_report(meeting.attrs)
            meeting.attrs["coaching_report"] = coaching
        except Exception:
            logger.warning("Coaching report generation failed for %s", meeting.id)

        await self._store.put(meeting)
        return True

    async def _get_historical_scores(self, meeting: Meeting) -> list[float]:
        from datetime import timedelta
        since = meeting.start_time - timedelta(days=30)
        past = await self._store.query(
            object_type=ObjectType.MEETING, since=since, limit=50,
        )
        scores = []
        for m in past:
            if isinstance(m, Meeting) and m.id != meeting.id:
                sc = m.attrs.get("scorecard", {})
                if isinstance(sc, dict) and "overall_score" in sc:
                    scores.append(sc["overall_score"])
        return scores
