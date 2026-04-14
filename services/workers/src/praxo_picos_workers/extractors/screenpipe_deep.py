"""Deep Screenpipe integration for meeting intelligence.

Goes beyond text extraction to access frames, audio transcriptions
with speaker diarization, UI events, and meeting detection.
Runs automatically in the background -- the user never triggers it.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MEETING_APPS = frozenset({
    "zoom.us", "zoom", "microsoft teams", "teams",
    "google meet", "meet.google.com", "webex",
    "slack huddle", "discord", "facetime",
})

MEETING_WINDOW_KEYWORDS = frozenset({
    "meeting", "call", "huddle", "standup", "sync",
    "zoom", "teams", "webex", "google meet",
})


@dataclass
class SpeakerSegment:
    speaker: str
    text: str
    start_time: datetime
    end_time: datetime
    is_user: bool = False
    word_count: int = 0


@dataclass
class ScreenFrame:
    timestamp: datetime
    app_name: str
    window_name: str
    ocr_text: str = ""
    frame_data: str = ""
    content_hash: str = ""


@dataclass
class DetectedMeeting:
    """A meeting detected from Screenpipe activity, not from calendar."""
    start_time: datetime
    end_time: datetime
    app_name: str
    window_title: str
    speaker_segments: list[SpeakerSegment] = field(default_factory=list)
    frames: list[ScreenFrame] = field(default_factory=list)
    detected_attendees: list[str] = field(default_factory=list)


class ScreenpipeDeepConnector:
    """Deep integration with Screenpipe for frame-level and audio intelligence."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3030",
        frame_sample_interval_s: int = 20,
        max_frames_per_meeting: int = 30,
    ) -> None:
        self._base_url = base_url
        self._frame_interval = frame_sample_interval_s
        self._max_frames = max_frames_per_meeting

    async def get_meeting_audio(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[SpeakerSegment]:
        """Get diarized audio transcriptions for a time range."""
        params: dict[str, Any] = {
            "content_type": "audio",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "limit": 500,
        }

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=30) as client:
                resp = await client.get("/search", params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            logger.warning("Failed to fetch audio from Screenpipe")
            return []

        segments: list[SpeakerSegment] = []
        for item in data.get("data", []):
            content = item.get("content", {})
            transcript = content.get("transcription", "")
            if not transcript:
                continue

            ts_str = item.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue

            speaker = content.get("speaker_id", "unknown")
            is_input = content.get("is_input_device", False)
            words = transcript.split()

            segments.append(SpeakerSegment(
                speaker=speaker,
                text=transcript,
                start_time=ts,
                end_time=ts + timedelta(seconds=len(words) / 2.5),
                is_user=is_input,
                word_count=len(words),
            ))

        return segments

    async def get_frames(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        include_frame_data: bool = False,
        app_filter: str | None = None,
    ) -> list[ScreenFrame]:
        """Get screen frames for a time range with configurable sampling."""
        params: dict[str, Any] = {
            "content_type": "ocr",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "limit": 500,
        }
        if include_frame_data:
            params["include_frames"] = True
        if app_filter:
            params["app_name"] = app_filter

        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=30) as client:
                resp = await client.get("/search", params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            logger.warning("Failed to fetch frames from Screenpipe")
            return []

        raw_frames: list[ScreenFrame] = []
        for item in data.get("data", []):
            content = item.get("content", {})
            ts_str = item.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue

            raw_frames.append(ScreenFrame(
                timestamp=ts,
                app_name=content.get("app_name", ""),
                window_name=content.get("window_name", ""),
                ocr_text=content.get("text", ""),
                frame_data=content.get("frame", ""),
                content_hash=str(item.get("content_hash", "")),
            ))

        return self._sample_frames(raw_frames)

    async def detect_meetings(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[DetectedMeeting]:
        """Auto-detect meetings from app usage patterns."""
        frames = await self.get_frames(start_time, end_time)

        meetings: list[DetectedMeeting] = []
        current: DetectedMeeting | None = None

        for frame in sorted(frames, key=lambda f: f.timestamp):
            is_meeting_app = self._is_meeting_app(frame.app_name, frame.window_name)

            if is_meeting_app:
                if current is None:
                    current = DetectedMeeting(
                        start_time=frame.timestamp,
                        end_time=frame.timestamp,
                        app_name=frame.app_name,
                        window_title=frame.window_name,
                    )
                else:
                    current.end_time = frame.timestamp
                    current.frames.append(frame)
            else:
                if current is not None:
                    duration = (current.end_time - current.start_time).total_seconds()
                    if duration >= 120:
                        meetings.append(current)
                    current = None

        if current is not None:
            duration = (current.end_time - current.start_time).total_seconds()
            if duration >= 120:
                meetings.append(current)

        return meetings

    def _sample_frames(self, frames: list[ScreenFrame]) -> list[ScreenFrame]:
        """Deduplicate and sample frames at configured interval."""
        if not frames:
            return []

        sorted_frames = sorted(frames, key=lambda f: f.timestamp)
        sampled: list[ScreenFrame] = []
        seen_hashes: set[str] = set()
        last_ts: datetime | None = None

        for frame in sorted_frames:
            if frame.content_hash and frame.content_hash in seen_hashes:
                continue

            if last_ts is not None:
                gap = (frame.timestamp - last_ts).total_seconds()
                if gap < self._frame_interval:
                    continue

            sampled.append(frame)
            if frame.content_hash:
                seen_hashes.add(frame.content_hash)
            last_ts = frame.timestamp

            if len(sampled) >= self._max_frames:
                break

        return sampled

    @staticmethod
    def _is_meeting_app(app_name: str, window_name: str) -> bool:
        app_lower = app_name.lower().strip()
        window_lower = window_name.lower().strip()

        if app_lower in MEETING_APPS:
            return True

        return any(kw in window_lower for kw in MEETING_WINDOW_KEYWORDS)
