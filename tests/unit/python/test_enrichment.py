"""Tests for the enrichment pipeline and intelligence modules."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.api.src.praxo_picos_api.db.models import SourceType
from services.api.src.praxo_picos_api.models import (
    Meeting,
    MemoryObject,
    ObjectType,
    Person,
    SOURCE_TO_OBJECT_TYPE,
)
from services.api.src.praxo_picos_api.models.enums import Sensitivity
from services.workers.src.praxo_picos_workers.analytics.meeting_frame_analyzer import (
    FrameAnalyzer,
    VisualSignals,
)
from services.workers.src.praxo_picos_workers.analytics.power_dynamics import (
    PowerDynamicsAnalyzer,
)
from services.workers.src.praxo_picos_workers.analytics.scorecard import (
    ScorecardBuilder,
)
from services.workers.src.praxo_picos_workers.enrichment.llm_enricher import (
    LLMEnricher,
)
from services.workers.src.praxo_picos_workers.enrichment.person_resolver import (
    PersonResolver,
)
from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
    SpeakerSegment,
)


class TestSourceToObjectTypeMapping:
    def test_all_sources_mapped(self):
        for source in ("mail", "calendar", "screen", "documents", "vault"):
            assert source in SOURCE_TO_OBJECT_TYPE

    def test_mail_maps_to_email(self):
        assert SOURCE_TO_OBJECT_TYPE["mail"] == ObjectType.EMAIL

    def test_calendar_maps_to_calendar_event(self):
        assert SOURCE_TO_OBJECT_TYPE["calendar"] == ObjectType.CALENDAR_EVENT


class TestFrameAnalyzer:
    def setup_method(self):
        self.analyzer = FrameAnalyzer()
        self.start = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        self.end = datetime(2026, 1, 1, 10, 30, tzinfo=UTC)

    def test_empty_frames(self):
        result = self.analyzer.analyze([], self.start, self.end)
        assert result.total_frames == 0

    def test_slide_transition_detection(self):
        frames = [
            ScreenFrame(
                timestamp=self.start + timedelta(minutes=i),
                app_name="zoom.us",
                window_name="meeting",
                ocr_text=f"Completely different slide content number {i}" if i % 2 == 0
                else "This is a totally unique page with fresh text",
            )
            for i in range(6)
        ]
        result = self.analyzer.analyze(frames, self.start, self.end)
        assert result.total_frames == 6
        assert result.meeting_app_frames > 0

    def test_screen_share_detection(self):
        frames = [
            ScreenFrame(
                timestamp=self.start + timedelta(minutes=i),
                app_name="keynote",
                window_name="presentation.key",
                ocr_text="slide content",
            )
            for i in range(3)
        ]
        result = self.analyzer.analyze(frames, self.start, self.end)
        assert result.screen_share_detected is True

    def test_to_dict(self):
        vs = VisualSignals(slide_count=5, total_frames=10)
        d = vs.to_dict()
        assert d["slide_count"] == 5
        assert d["total_frames"] == 10


class TestPowerDynamicsAnalyzer:
    def setup_method(self):
        self.analyzer = PowerDynamicsAnalyzer()

    def test_empty_segments(self):
        result = self.analyzer.analyze([])
        assert result.total_speakers == 0

    def test_speaking_order(self):
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        segments = [
            SpeakerSegment("Alice", "hello", base, base + timedelta(seconds=5), False),
            SpeakerSegment("Bob", "hi", base + timedelta(seconds=6), base + timedelta(seconds=10), False),
            SpeakerSegment("Alice", "continuing", base + timedelta(seconds=11), base + timedelta(seconds=15), False),
        ]
        result = self.analyzer.analyze(segments)
        assert result.speaking_order == ["Alice", "Bob"]
        assert result.total_speakers == 2

    def test_interruption_detection(self):
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        segments = [
            SpeakerSegment("Alice", "talking", base, base + timedelta(seconds=10), False),
            SpeakerSegment("Bob", "interrupting", base + timedelta(seconds=10, milliseconds=200), base + timedelta(seconds=15), False),
        ]
        result = self.analyzer.analyze(segments)
        assert "Bob" in result.interruptions
        assert result.interruptions["Bob"].get("Alice", 0) >= 1

    def test_gini_coefficient(self):
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        segments = [
            SpeakerSegment("Alice", "word " * 100, base, base + timedelta(seconds=60), False),
            SpeakerSegment("Bob", "hi", base + timedelta(seconds=61), base + timedelta(seconds=62), False),
        ]
        result = self.analyzer.analyze(segments)
        assert result.gini_coefficient > 0.3

    def test_ghost_detection(self):
        base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        segments = [
            SpeakerSegment("Alice", "word " * 50, base, base + timedelta(seconds=60), False),
            SpeakerSegment("Ghost", "ok", base + timedelta(seconds=61), base + timedelta(seconds=62), False),
        ]
        result = self.analyzer.analyze(segments)
        assert "Ghost" in result.ghost_speakers

    def test_to_dict(self):
        result = self.analyzer.analyze([])
        d = result.to_dict()
        assert "gini_coefficient" in d
        assert "speaking_order" in d


class TestScorecardBuilder:
    def setup_method(self):
        self.builder = ScorecardBuilder()

    def test_empty_attrs(self):
        sc = self.builder.build({})
        assert 0.0 < sc.overall_score <= 1.0

    def test_good_delivery(self):
        attrs = {
            "delivery_metrics": {
                "pace_wpm": 140,
                "filler_rate_per_min": 1.5,
                "talk_listen_ratio": 0.45,
            },
        }
        sc = self.builder.build(attrs)
        assert sc.delivery_score > 0.7

    def test_good_engagement(self):
        attrs = {
            "attention": {
                "focus_ratio": 0.9,
                "note_taking_detected": True,
                "app_switch_count": 2,
            },
        }
        sc = self.builder.build(attrs)
        assert sc.engagement_score > 0.8

    def test_trend_comparison(self):
        sc = self.builder.build(
            {"delivery_metrics": {"pace_wpm": 140, "filler_rate_per_min": 1, "talk_listen_ratio": 0.4}},
            historical_scores=[0.5, 0.5, 0.5],
        )
        assert sc.vs_30d_avg.get("overall_trend") in ("improving", "stable", "declining")

    def test_to_dict(self):
        sc = self.builder.build({})
        d = sc.to_dict()
        assert "overall_score" in d
        assert "delivery" in d
        assert "engagement" in d


class TestPersonResolverEmailParsing:
    def test_parse_email_field(self):
        name, email = PersonResolver._parse_email_field("John Doe <john@example.com>")
        assert email == "john@example.com"
        assert "John" in name

    def test_parse_plain_email(self):
        name, email = PersonResolver._parse_email_field("alice@example.com")
        assert email == "alice@example.com"

    def test_parse_name_only(self):
        name, email = PersonResolver._parse_email_field("Bob Smith")
        assert name == "Bob Smith"
        assert email == ""


class TestLLMEnricherSystemPrompts:
    def test_email_has_system(self):
        system = LLMEnricher._system_for_type(ObjectType.EMAIL)
        assert system is not None
        assert "topics" in system

    def test_calendar_has_system(self):
        system = LLMEnricher._system_for_type(ObjectType.CALENDAR_EVENT)
        assert system is not None
        assert "meeting_type" in system

    def test_meeting_has_no_system(self):
        system = LLMEnricher._system_for_type(ObjectType.MEETING)
        assert system is None

    def test_build_text(self):
        obj = MemoryObject(
            object_type=ObjectType.EMAIL,
            source=SourceType.MAIL,
            title="Test Subject",
            body="Hello world",
        )
        text = LLMEnricher._build_text(obj)
        assert "Test Subject" in text
        assert "Hello world" in text
