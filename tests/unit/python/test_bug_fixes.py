"""Tests for the 4 bug fixes from the vision gap analysis."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.workers.src.praxo_picos_workers.analytics.meeting_frame_analyzer import (
    FrameAnalyzer,
    SlideTransition,
    VisualSignals,
)
from services.workers.src.praxo_picos_workers.analytics.meeting_vision import (
    BodyLanguageAnalysis,
    FrameAnalysisResult,
)
from services.workers.src.praxo_picos_workers.analytics.relationship_dynamics import (
    InteractionRecord,
    RelationshipDynamicsTracker,
    RelationshipMetrics,
)
from services.workers.src.praxo_picos_workers.analytics.scorecard import (
    ScorecardBuilder,
)


class TestBug1CommitmentCompletionRate:
    """commitment_completion_rate was never populated in get_metrics."""

    def test_completion_rate_computed_from_interactions(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)

        tracker.add_interaction(InteractionRecord(
            person_id="p1", timestamp=base, interaction_type="meeting",
            has_commitment=True, commitment_completed=True,
        ))
        tracker.add_interaction(InteractionRecord(
            person_id="p1", timestamp=base + timedelta(days=1), interaction_type="meeting",
            has_commitment=True, commitment_completed=False,
        ))
        tracker.add_interaction(InteractionRecord(
            person_id="p1", timestamp=base + timedelta(days=2), interaction_type="meeting",
            has_commitment=False,
        ))

        metrics = tracker.get_metrics("p1", "Alice", base + timedelta(days=3))
        assert metrics.commitment_completion_rate == 0.5

    def test_no_commitments_returns_none(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord(
            person_id="p1", timestamp=base, interaction_type="meeting",
        ))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=1))
        assert metrics.commitment_completion_rate is None

    def test_to_dict_includes_completion_rate(self):
        m = RelationshipMetrics(person_id="p1", commitment_completion_rate=0.85)
        d = m.to_dict()
        assert d["commitment_completion_rate"] == 0.85

    def test_to_dict_none_completion_rate(self):
        m = RelationshipMetrics(person_id="p1")
        d = m.to_dict()
        assert d["commitment_completion_rate"] is None


class TestBug2DeliveryTrend:
    """delivery_trend was not emitted by ScorecardBuilder."""

    def test_scorecard_emits_delivery_trend(self):
        builder = ScorecardBuilder()
        sc = builder.build(
            {"delivery_metrics": {"pace_wpm": 140, "filler_rate_per_min": 1, "talk_listen_ratio": 0.4}},
            historical_scores=[0.3, 0.3, 0.3],
        )
        d = sc.to_dict()
        assert "delivery_trend" in d["vs_30d_avg"]
        assert "engagement_trend" in d["vs_30d_avg"]
        assert "presence_trend" in d["vs_30d_avg"]

    def test_no_historical_no_trends(self):
        builder = ScorecardBuilder()
        sc = builder.build({})
        d = sc.to_dict()
        assert d["vs_30d_avg"] == {}


class TestBug3DeepWorkPersistence:
    """Deep work blocks were computed but never persisted."""

    def test_visual_signals_includes_transition_timestamps(self):
        ts = datetime(2026, 1, 1, 10, 5, tzinfo=UTC)
        vs = VisualSignals(
            slide_count=3,
            transitions=[
                SlideTransition(timestamp=ts, from_text_hash="a", to_text_hash="b", text_change_ratio=0.8),
            ],
        )
        d = vs.to_dict()
        assert "transition_timestamps" in d
        assert len(d["transition_timestamps"]) == 1
        assert ts.isoformat() in d["transition_timestamps"][0]

    def test_visual_signals_includes_screen_share_start(self):
        ts = datetime(2026, 1, 1, 10, 10, tzinfo=UTC)
        vs = VisualSignals(screen_share_detected=True, screen_share_start=ts)
        d = vs.to_dict()
        assert d["screen_share_start"] is not None


class TestBug4ToDict:
    """Per-frame vision details and slide timestamps dropped by to_dict."""

    def test_body_language_includes_per_frame(self):
        ts = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        bl = BodyLanguageAnalysis(
            frames_analyzed=2,
            frame_results=[
                FrameAnalysisResult(timestamp=ts, expression="engaged", eye_contact="camera", posture="upright", energy="high"),
                FrameAnalysisResult(timestamp=ts + timedelta(minutes=5), expression="neutral", eye_contact="screen", posture="slouched", energy="low"),
            ],
        )
        d = bl.to_dict()
        assert "per_frame" in d
        assert len(d["per_frame"]) == 2
        assert d["per_frame"][0]["expression"] == "engaged"
        assert d["per_frame"][1]["posture"] == "slouched"

    def test_body_language_empty_per_frame(self):
        bl = BodyLanguageAnalysis()
        d = bl.to_dict()
        assert d["per_frame"] == []
