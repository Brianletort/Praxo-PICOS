"""Tests for AttentionTracker and CognitiveEnergyTracker."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.workers.src.praxo_picos_workers.analytics.attention_tracker import (
    AttentionTracker,
    DeepWorkBlock,
)
from services.workers.src.praxo_picos_workers.analytics.cognitive_energy import (
    CognitiveEnergyTracker,
    DailyEnergyProfile,
    HourlyEnergy,
)
from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
)


def _frame(hour: int, minute: int, app: str = "zoom.us", window: str = "meeting") -> ScreenFrame:
    return ScreenFrame(
        timestamp=datetime(2026, 1, 1, hour, minute, tzinfo=UTC),
        app_name=app,
        window_name=window,
    )


class TestAttentionTracker:
    def setup_method(self):
        self.tracker = AttentionTracker()
        self.start = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
        self.end = datetime(2026, 1, 1, 10, 30, tzinfo=UTC)

    def test_empty_frames(self):
        result = self.tracker.analyze_meeting([], self.start, self.end)
        assert result.total_frames_analyzed == 0

    def test_full_focus(self):
        frames = [_frame(10, i) for i in range(10)]
        result = self.tracker.analyze_meeting(frames, self.start, self.end)
        assert result.focus_ratio == 1.0
        assert result.app_switch_count == 0

    def test_distraction_detection(self):
        frames = [
            _frame(10, 0, "zoom.us"),
            _frame(10, 5, "Mail"),
            _frame(10, 10, "zoom.us"),
            _frame(10, 15, "Slack"),
            _frame(10, 20, "zoom.us"),
        ]
        result = self.tracker.analyze_meeting(frames, self.start, self.end)
        assert result.focus_ratio < 1.0
        assert result.app_switch_count >= 3
        assert "Mail" in result.distraction_apps or "Slack" in result.distraction_apps

    def test_note_taking_detection(self):
        frames = [
            _frame(10, 0, "zoom.us"),
            _frame(10, 5, "Notes"),
            _frame(10, 10, "zoom.us"),
        ]
        result = self.tracker.analyze_meeting(frames, self.start, self.end)
        assert result.note_taking_detected is True

    def test_to_dict(self):
        result = self.tracker.analyze_meeting([_frame(10, 0)], self.start, self.end)
        d = result.to_dict()
        assert "focus_ratio" in d
        assert "app_switch_count" in d
        assert "distraction_apps" in d

    def test_deep_work_blocks(self):
        frames = [
            _frame(9, i, "VS Code", "main.py") for i in range(30)
        ]
        blocks = self.tracker.find_deep_work_blocks(frames)
        assert len(blocks) >= 1
        assert blocks[0].duration_minutes >= 25
        assert blocks[0].app_name == "VS Code"

    def test_no_deep_work_with_switching(self):
        frames = []
        for i in range(20):
            app = "VS Code" if i % 2 == 0 else "Slack"
            frames.append(_frame(9, i, app))
        blocks = self.tracker.find_deep_work_blocks(frames)
        assert len(blocks) == 0


class TestCognitiveEnergyTracker:
    def test_empty_frames(self):
        tracker = CognitiveEnergyTracker()
        profile = tracker.analyze_day([])
        assert profile.date == ""

    def test_single_hour(self):
        tracker = CognitiveEnergyTracker()
        frames = [_frame(10, i, "VS Code") for i in range(10)]
        profile = tracker.analyze_day(frames)
        assert len(profile.hourly) == 1
        assert profile.hourly[0].hour == 10

    def test_peak_hours_detected(self):
        tracker = CognitiveEnergyTracker()
        frames = [_frame(10, i, "VS Code") for i in range(20)]
        frames += [_frame(14, i, "Slack") for i in range(5)]
        profile = tracker.analyze_day(frames)
        assert "10:" in profile.peak_hours

    def test_consecutive_meetings(self):
        tracker = CognitiveEnergyTracker()
        meetings = [
            (datetime(2026, 1, 1, 10, 0, tzinfo=UTC), datetime(2026, 1, 1, 10, 30, tzinfo=UTC)),
            (datetime(2026, 1, 1, 10, 35, tzinfo=UTC), datetime(2026, 1, 1, 11, 0, tzinfo=UTC)),
            (datetime(2026, 1, 1, 11, 5, tzinfo=UTC), datetime(2026, 1, 1, 11, 30, tzinfo=UTC)),
        ]
        frames = [_frame(10, i) for i in range(30)]
        profile = tracker.analyze_day(frames, meetings)
        assert profile.consecutive_meeting_max >= 2

    def test_to_dict(self):
        profile = DailyEnergyProfile(date="2026-01-01", avg_energy=0.7)
        d = profile.to_dict()
        assert d["date"] == "2026-01-01"
        assert d["avg_energy"] == 0.7

    def test_hourly_to_dict(self):
        h = HourlyEnergy(hour=10, estimated_energy=0.8)
        d = h.to_dict()
        assert d["hour"] == 10
        assert d["estimated_energy"] == 0.8
