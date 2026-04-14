"""Tests for ScreenpipeDeepConnector (Phase 0F)."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    MEETING_APPS,
    ScreenFrame,
    ScreenpipeDeepConnector,
)


class TestMeetingDetection:
    def test_known_meeting_apps(self):
        connector = ScreenpipeDeepConnector()
        assert connector._is_meeting_app("zoom.us", "")
        assert connector._is_meeting_app("Microsoft Teams", "")
        assert connector._is_meeting_app("Google Meet", "")

    def test_meeting_window_keywords(self):
        connector = ScreenpipeDeepConnector()
        assert connector._is_meeting_app("Chrome", "Google Meet - Team Standup")
        assert connector._is_meeting_app("Firefox", "Zoom Meeting")

    def test_non_meeting_app(self):
        connector = ScreenpipeDeepConnector()
        assert not connector._is_meeting_app("Visual Studio Code", "main.py")
        assert not connector._is_meeting_app("Finder", "Documents")


class TestFrameSampling:
    def test_dedup_by_content_hash(self):
        connector = ScreenpipeDeepConnector(frame_sample_interval_s=0)
        frames = [
            ScreenFrame(
                timestamp=datetime(2026, 1, 1, 10, i, tzinfo=UTC),
                app_name="zoom",
                window_name="meeting",
                content_hash="same_hash",
            )
            for i in range(5)
        ]
        sampled = connector._sample_frames(frames)
        assert len(sampled) == 1

    def test_interval_sampling(self):
        connector = ScreenpipeDeepConnector(frame_sample_interval_s=30)
        from datetime import timedelta
        base = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
        frames = [
            ScreenFrame(
                timestamp=base + timedelta(seconds=i * 10),
                app_name="zoom",
                window_name="meeting",
                content_hash=f"hash_{i}",
            )
            for i in range(10)
        ]
        sampled = connector._sample_frames(frames)
        assert len(sampled) < len(frames)

    def test_max_frames_cap(self):
        connector = ScreenpipeDeepConnector(
            frame_sample_interval_s=0, max_frames_per_meeting=3
        )
        frames = [
            ScreenFrame(
                timestamp=datetime(2026, 1, 1, 10, i, tzinfo=UTC),
                app_name="zoom",
                window_name="meeting",
                content_hash=f"hash_{i}",
            )
            for i in range(10)
        ]
        sampled = connector._sample_frames(frames)
        assert len(sampled) == 3

    def test_empty_frames(self):
        connector = ScreenpipeDeepConnector()
        assert connector._sample_frames([]) == []
