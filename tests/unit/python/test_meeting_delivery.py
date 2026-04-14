"""Tests for Layer 1: Vocal Intelligence (Phase 1A)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.workers.src.praxo_picos_workers.analytics.communication_style import (
    CommunicationStyleDNA,
)
from services.workers.src.praxo_picos_workers.analytics.meeting_delivery import (
    DeliveryAnalyzer,
    DeliveryMetrics,
)
from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    SpeakerSegment,
)


def _make_segment(
    text: str,
    start_offset_s: float,
    duration_s: float = 10.0,
    is_user: bool = True,
    speaker: str = "you",
) -> SpeakerSegment:
    base = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    return SpeakerSegment(
        speaker=speaker,
        text=text,
        start_time=base + timedelta(seconds=start_offset_s),
        end_time=base + timedelta(seconds=start_offset_s + duration_s),
        is_user=is_user,
        word_count=len(text.split()),
    )


class TestDeliveryAnalyzer:
    def setup_method(self):
        self.analyzer = DeliveryAnalyzer()
        self.start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
        self.end = datetime(2026, 1, 1, 10, 30, 0, tzinfo=UTC)

    def test_empty_segments(self):
        result = self.analyzer.analyze([], self.start, self.end)
        assert result.pace_wpm == 0.0
        assert result.your_word_count == 0

    def test_basic_pace(self):
        segments = [
            _make_segment("word " * 60, 0, duration_s=60.0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert 55 < result.pace_wpm < 65

    def test_filler_detection(self):
        segments = [
            _make_segment("um like basically you know um", 0, duration_s=30.0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert result.filler_counts.get("um", 0) == 2
        assert result.filler_counts.get("like", 0) == 1
        assert result.filler_rate_per_min > 0

    def test_talk_listen_ratio(self):
        segments = [
            _make_segment("hello world", 0, duration_s=300.0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert 0.15 < result.talk_listen_ratio < 0.20

    def test_question_detection(self):
        segments = [
            _make_segment("What do you think? How should we approach this? Let me explain.", 0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert result.question_count == 2

    def test_monologue_detection(self):
        segments = [
            _make_segment("word " * 100, 0, duration_s=120.0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert result.monologue_count == 1
        assert result.monologue_max_s >= 90.0

    def test_pause_classification(self):
        segments = [
            _make_segment("first part", 0, duration_s=5.0),
            _make_segment("interrupted", 5.2, duration_s=5.0),
            _make_segment("strategic pause", 13.0, duration_s=5.0),
            _make_segment("after awkward pause", 26.0, duration_s=5.0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert result.pause_interrupted >= 1
        assert result.pause_strategic >= 1
        assert result.pause_awkward >= 1

    def test_vocabulary_complexity(self):
        segments = [
            _make_segment("the the the the the", 0),
        ]
        result = self.analyzer.analyze(segments, self.start, self.end)
        assert result.vocabulary_complexity < 0.3

        segments2 = [
            _make_segment("architecture design implementation strategy execution", 0),
        ]
        result2 = self.analyzer.analyze(segments2, self.start, self.end)
        assert result2.vocabulary_complexity > 0.8

    def test_to_dict(self):
        metrics = DeliveryMetrics(pace_wpm=145.3, filler_rate_per_min=3.14)
        d = metrics.to_dict()
        assert d["pace_wpm"] == 145.3
        assert d["filler_rate_per_min"] == 3.14


class TestCommunicationStyleDNA:
    def test_profile_below_threshold(self):
        dna = CommunicationStyleDNA(min_meetings=3)
        dna.add_meeting(DeliveryMetrics(pace_wpm=140), ["p1"])
        assert dna.get_profile("p1") is None

    def test_profile_above_threshold(self):
        dna = CommunicationStyleDNA(min_meetings=2)
        dna.add_meeting(DeliveryMetrics(pace_wpm=140, filler_rate_per_min=3.0), ["p1"])
        dna.add_meeting(DeliveryMetrics(pace_wpm=160, filler_rate_per_min=5.0), ["p1"])
        profile = dna.get_profile("p1", "Sarah")
        assert profile is not None
        assert profile.avg_pace_wpm == 150.0
        assert profile.meeting_count == 2

    def test_style_shift(self):
        dna = CommunicationStyleDNA(min_meetings=2)
        dna.add_meeting(DeliveryMetrics(pace_wpm=100), ["p1"])
        dna.add_meeting(DeliveryMetrics(pace_wpm=100), ["p1"])
        dna.add_meeting(DeliveryMetrics(pace_wpm=200), ["p2"])
        dna.add_meeting(DeliveryMetrics(pace_wpm=200), ["p2"])

        shift = dna.compute_style_shift("p1", "Slow Person")
        assert shift is not None
        assert shift.pace_diff_pct < 0

    def test_style_shift_summary(self):
        dna = CommunicationStyleDNA(min_meetings=1)
        dna.add_meeting(
            DeliveryMetrics(pace_wpm=100, question_rate_per_min=1.0), ["p1"]
        )
        dna.add_meeting(
            DeliveryMetrics(pace_wpm=200, question_rate_per_min=5.0), ["p2"]
        )

        shift = dna.compute_style_shift("p2", "Fast Person")
        assert shift is not None
        assert "faster" in shift.summary.lower() or "more questions" in shift.summary.lower()

    def test_get_all_profiles(self):
        dna = CommunicationStyleDNA(min_meetings=2)
        for _ in range(3):
            dna.add_meeting(DeliveryMetrics(pace_wpm=140), ["p1", "p2"])
        profiles = dna.get_all_profiles({"p1": "Alice", "p2": "Bob"})
        assert len(profiles) == 2
