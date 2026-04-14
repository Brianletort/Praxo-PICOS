"""Tests for RelationshipDynamicsTracker -- covering the untested module."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.workers.src.praxo_picos_workers.analytics.relationship_dynamics import (
    InteractionRecord,
    RelationshipDynamicsTracker,
    RelationshipMetrics,
)


class TestRelationshipDynamicsTracker:
    def test_empty_interactions(self):
        tracker = RelationshipDynamicsTracker()
        metrics = tracker.get_metrics("p1")
        assert metrics.interaction_count == 0
        assert metrics.trend == "stable"

    def test_single_interaction(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting"))
        metrics = tracker.get_metrics("p1", "Alice", base + timedelta(days=1))
        assert metrics.interaction_count == 1
        assert metrics.last_interaction_days_ago == 1

    def test_frequency_weekly(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, tzinfo=UTC)
        for i in range(4):
            tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=i * 7), "meeting"))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=28))
        assert "weekly" in metrics.interaction_frequency

    def test_warming_trend(self):
        tracker = RelationshipDynamicsTracker(warming_window_days=14)
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting"))
        tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=1), "meeting"))
        for i in range(10):
            tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=20 + i), "meeting"))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=30))
        assert metrics.trend == "warming"

    def test_cooling_trend(self):
        tracker = RelationshipDynamicsTracker(warming_window_days=14)
        base = datetime(2026, 1, 1, tzinfo=UTC)
        for i in range(10):
            tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=i), "meeting"))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=30))
        assert metrics.trend == "cooling"

    def test_one_on_one_ratio(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting", is_one_on_one=True))
        tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=1), "meeting", is_one_on_one=False))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=2))
        assert metrics.one_on_one_ratio == 0.5

    def test_initiated_by_you_ratio(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting", initiated_by_you=True))
        tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=1), "meeting", initiated_by_you=False))
        tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=2), "meeting", initiated_by_you=True))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=3))
        assert abs(metrics.initiated_by_you_ratio - 0.667) < 0.01

    def test_topics_deduplication(self):
        tracker = RelationshipDynamicsTracker()
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting", topics=["budget", "timeline"]))
        tracker.add_interaction(InteractionRecord("p1", base + timedelta(days=1), "meeting", topics=["budget", "hiring"]))
        metrics = tracker.get_metrics("p1", now=base + timedelta(days=2))
        assert "budget" in metrics.topics
        assert metrics.topics.count("budget") == 1

    def test_people_needing_attention(self):
        tracker = RelationshipDynamicsTracker(cooling_threshold_days=10)
        base = datetime(2026, 1, 1, tzinfo=UTC)
        tracker.add_interaction(InteractionRecord("p1", base, "meeting"))
        tracker.add_interaction(InteractionRecord("p2", base + timedelta(days=9), "meeting"))
        people = tracker.get_people_needing_attention(base + timedelta(days=15))
        ids = [p.person_id for p in people]
        assert "p1" in ids


class TestRelationshipMetricsToDict:
    def test_full_to_dict(self):
        m = RelationshipMetrics(
            person_id="p1",
            person_name="Alice",
            interaction_count=10,
            last_interaction_days_ago=3,
            interaction_frequency="weekly",
            trend="warming",
            one_on_one_ratio=0.5,
            initiated_by_you_ratio=0.6,
            commitment_completion_rate=0.85,
            topics=["budget", "hiring"],
        )
        d = m.to_dict()
        assert d["person_id"] == "p1"
        assert d["trend"] == "warming"
        assert d["commitment_completion_rate"] == 0.85
        assert len(d["topics"]) == 2
