"""Layer 2: Attention Tracker.

Measures focus during meetings and general screen activity.
Focus ratio, app-switch count, distraction profile, pre/post-meeting behavior.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
)

MEETING_APPS = frozenset({
    "zoom.us", "zoom", "microsoft teams", "teams",
    "google meet", "facetime", "webex", "slack",
})

NOTE_APPS = frozenset({
    "notes", "notion", "obsidian", "bear", "apple notes",
    "google docs", "microsoft word", "textedit",
})


@dataclass
class AttentionMetrics:
    focus_ratio: float = 0.0
    app_switch_count: int = 0
    distraction_apps: dict[str, float] = field(default_factory=dict)
    note_taking_detected: bool = False
    pre_meeting_docs_opened: int = 0
    post_meeting_followup: bool = False
    total_frames_analyzed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "focus_ratio": round(self.focus_ratio, 3),
            "app_switch_count": self.app_switch_count,
            "distraction_apps": {
                k: round(v, 1) for k, v in sorted(
                    self.distraction_apps.items(), key=lambda x: x[1], reverse=True
                )[:5]
            },
            "note_taking_detected": self.note_taking_detected,
            "pre_meeting_docs_opened": self.pre_meeting_docs_opened,
            "post_meeting_followup": self.post_meeting_followup,
            "total_frames_analyzed": self.total_frames_analyzed,
        }


@dataclass
class DeepWorkBlock:
    start_time: datetime
    end_time: datetime
    app_name: str
    duration_minutes: float = 0.0
    break_reason: str = ""


class AttentionTracker:
    """Tracks attention patterns from screen frame data."""

    def __init__(
        self,
        deep_work_min_minutes: int = 25,
        pre_meeting_window_m: int = 15,
        post_meeting_window_m: int = 30,
    ) -> None:
        self._deep_work_min = deep_work_min_minutes
        self._pre_window = timedelta(minutes=pre_meeting_window_m)
        self._post_window = timedelta(minutes=post_meeting_window_m)

    def analyze_meeting(
        self,
        frames: list[ScreenFrame],
        meeting_start: datetime,
        meeting_end: datetime,
        meeting_app: str = "",
    ) -> AttentionMetrics:
        """Analyze attention during a meeting time window."""
        if not frames:
            return AttentionMetrics()

        during = [f for f in frames if meeting_start <= f.timestamp <= meeting_end]
        before = [
            f for f in frames
            if (meeting_start - self._pre_window) <= f.timestamp < meeting_start
        ]
        after = [
            f for f in frames
            if meeting_end < f.timestamp <= (meeting_end + self._post_window)
        ]

        total = len(during)
        if total == 0:
            return AttentionMetrics()

        focused = sum(
            1 for f in during if self._is_meeting_focused(f.app_name, meeting_app)
        )
        focus_ratio = focused / total

        app_switches = self._count_switches(during)

        distractions: dict[str, float] = {}
        for f in during:
            if not self._is_meeting_focused(f.app_name, meeting_app):
                app = f.app_name or "Unknown"
                distractions[app] = distractions.get(app, 0) + 1

        note_taking = any(
            f.app_name.lower() in NOTE_APPS for f in during
        )

        pre_docs = len({
            f.window_name for f in before
            if f.app_name.lower() in NOTE_APPS or "doc" in f.window_name.lower()
        })

        post_followup = any(
            "mail" in f.app_name.lower() or "doc" in f.window_name.lower()
            for f in after
        )

        return AttentionMetrics(
            focus_ratio=focus_ratio,
            app_switch_count=app_switches,
            distraction_apps=distractions,
            note_taking_detected=note_taking,
            pre_meeting_docs_opened=pre_docs,
            post_meeting_followup=post_followup,
            total_frames_analyzed=total,
        )

    def find_deep_work_blocks(
        self,
        frames: list[ScreenFrame],
    ) -> list[DeepWorkBlock]:
        """Find uninterrupted single-app focus periods in general screen activity."""
        if not frames:
            return []

        sorted_frames = sorted(frames, key=lambda f: f.timestamp)
        blocks: list[DeepWorkBlock] = []
        streak_app = sorted_frames[0].app_name
        streak_start = sorted_frames[0].timestamp
        streak_end = sorted_frames[0].timestamp

        for frame in sorted_frames[1:]:
            if frame.app_name == streak_app:
                streak_end = frame.timestamp
            else:
                duration = (streak_end - streak_start).total_seconds() / 60
                if duration >= self._deep_work_min:
                    blocks.append(DeepWorkBlock(
                        start_time=streak_start,
                        end_time=streak_end,
                        app_name=streak_app,
                        duration_minutes=duration,
                        break_reason=frame.app_name,
                    ))
                streak_app = frame.app_name
                streak_start = frame.timestamp
                streak_end = frame.timestamp

        duration = (streak_end - streak_start).total_seconds() / 60
        if duration >= self._deep_work_min:
            blocks.append(DeepWorkBlock(
                start_time=streak_start,
                end_time=streak_end,
                app_name=streak_app,
                duration_minutes=duration,
            ))

        return blocks

    @staticmethod
    def _is_meeting_focused(app_name: str, meeting_app: str) -> bool:
        app_lower = app_name.lower()
        if meeting_app and meeting_app.lower() in app_lower:
            return True
        return app_lower in MEETING_APPS or any(
            kw in app_lower for kw in ("zoom", "teams", "meet", "webex")
        )

    @staticmethod
    def _count_switches(frames: list[ScreenFrame]) -> int:
        switches = 0
        prev_app = ""
        for f in frames:
            if f.app_name != prev_app and prev_app:
                switches += 1
            prev_app = f.app_name
        return switches
