"""Layer 2: Frame Analyzer -- slide transitions, screen share, demo mode.

Pure OCR/metadata analysis, no LLM. Classifies meeting visual state
from screen frame data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
)


@dataclass
class SlideTransition:
    timestamp: datetime
    from_text_hash: str
    to_text_hash: str
    text_change_ratio: float


@dataclass
class VisualSignals:
    slide_count: int = 0
    transitions: list[SlideTransition] = field(default_factory=list)
    avg_time_per_slide_s: float = 0.0
    screen_share_detected: bool = False
    screen_share_start: datetime | None = None
    demo_mode_detected: bool = False
    meeting_app_frames: int = 0
    other_app_frames: int = 0
    total_frames: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_count": self.slide_count,
            "avg_time_per_slide_s": round(self.avg_time_per_slide_s, 1),
            "screen_share_detected": self.screen_share_detected,
            "screen_share_start": self.screen_share_start.isoformat() if self.screen_share_start else None,
            "demo_mode_detected": self.demo_mode_detected,
            "meeting_app_frames": self.meeting_app_frames,
            "other_app_frames": self.other_app_frames,
            "total_frames": self.total_frames,
            "transition_count": len(self.transitions),
            "transition_timestamps": [
                t.timestamp.isoformat() for t in self.transitions
            ],
        }


MEETING_APPS = frozenset({
    "zoom.us", "zoom", "microsoft teams", "teams",
    "google meet", "webex", "facetime", "slack",
})

SLIDE_APPS = frozenset({
    "keynote", "powerpoint", "google slides", "impress",
})


class FrameAnalyzer:
    """Analyzes screen frames during a meeting for visual state changes."""

    def __init__(self, text_change_threshold: float = 0.6) -> None:
        self._threshold = text_change_threshold

    def analyze(
        self,
        frames: list[ScreenFrame],
        meeting_start: datetime,
        meeting_end: datetime,
    ) -> VisualSignals:
        if not frames:
            return VisualSignals()

        during = [f for f in frames if meeting_start <= f.timestamp <= meeting_end]
        during.sort(key=lambda f: f.timestamp)

        if not during:
            return VisualSignals()

        meeting_frames = sum(
            1 for f in during if f.app_name.lower() in MEETING_APPS
        )

        transitions: list[SlideTransition] = []
        prev_text = ""
        for f in during:
            if prev_text and f.ocr_text:
                ratio = 1.0 - SequenceMatcher(None, prev_text, f.ocr_text).ratio()
                if ratio >= self._threshold:
                    transitions.append(SlideTransition(
                        timestamp=f.timestamp,
                        from_text_hash=str(hash(prev_text))[:8],
                        to_text_hash=str(hash(f.ocr_text))[:8],
                        text_change_ratio=ratio,
                    ))
            prev_text = f.ocr_text

        slide_count = len(transitions) + (1 if transitions else 0)
        duration_s = (meeting_end - meeting_start).total_seconds()
        avg_per_slide = duration_s / max(1, slide_count)

        screen_share = any(f.app_name.lower() in SLIDE_APPS for f in during)
        screen_share_start = None
        if screen_share:
            for f in during:
                if f.app_name.lower() in SLIDE_APPS:
                    screen_share_start = f.timestamp
                    break

        demo_mode = False
        if screen_share:
            for i, f in enumerate(during):
                if f.app_name.lower() in SLIDE_APPS:
                    remaining = during[i + 1:]
                    if any(
                        r.app_name.lower() not in SLIDE_APPS
                        and r.app_name.lower() not in MEETING_APPS
                        for r in remaining[:5]
                    ):
                        demo_mode = True
                        break

        return VisualSignals(
            slide_count=slide_count,
            transitions=transitions,
            avg_time_per_slide_s=avg_per_slide,
            screen_share_detected=screen_share,
            screen_share_start=screen_share_start,
            demo_mode_detected=demo_mode,
            meeting_app_frames=meeting_frames,
            other_app_frames=len(during) - meeting_frames,
            total_frames=len(during),
        )
