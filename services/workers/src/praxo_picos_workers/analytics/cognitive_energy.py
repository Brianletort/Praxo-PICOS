"""Layer 2: Cognitive Energy Tracker.

Derives cognitive energy estimates from screen activity patterns.
App-switch velocity, meeting-debt, recovery time, circadian mapping.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
)


@dataclass
class HourlyEnergy:
    hour: int
    switch_rate: float = 0.0
    frame_count: int = 0
    unique_apps: int = 0
    estimated_energy: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "hour": self.hour,
            "switch_rate": round(self.switch_rate, 2),
            "frame_count": self.frame_count,
            "unique_apps": self.unique_apps,
            "estimated_energy": round(self.estimated_energy, 3),
        }


@dataclass
class DailyEnergyProfile:
    date: str
    hourly: list[HourlyEnergy] = field(default_factory=list)
    peak_hours: str = ""
    low_hours: str = ""
    meeting_count: int = 0
    consecutive_meeting_max: int = 0
    avg_energy: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "hourly": [h.to_dict() for h in self.hourly],
            "peak_hours": self.peak_hours,
            "low_hours": self.low_hours,
            "meeting_count": self.meeting_count,
            "consecutive_meeting_max": self.consecutive_meeting_max,
            "avg_energy": round(self.avg_energy, 3),
        }


class CognitiveEnergyTracker:
    """Estimates cognitive energy from screen activity patterns.

    Lower app-switch rates and fewer unique apps = higher focus = higher energy.
    This is a proxy, not a measurement. Stored with appropriate confidence.
    """

    def analyze_day(
        self,
        frames: list[ScreenFrame],
        meeting_windows: list[tuple[datetime, datetime]] | None = None,
    ) -> DailyEnergyProfile:
        """Build a daily energy profile from screen frames."""
        if not frames:
            return DailyEnergyProfile(date="")

        sorted_frames = sorted(frames, key=lambda f: f.timestamp)
        date_str = sorted_frames[0].timestamp.strftime("%Y-%m-%d")

        by_hour: dict[int, list[ScreenFrame]] = defaultdict(list)
        for f in sorted_frames:
            by_hour[f.timestamp.hour].append(f)

        hourly: list[HourlyEnergy] = []
        for hour in range(24):
            hour_frames = by_hour.get(hour, [])
            if not hour_frames:
                continue

            switches = self._count_switches(hour_frames)
            unique = len({f.app_name for f in hour_frames})
            energy = self._estimate_energy(switches, unique, len(hour_frames))

            hourly.append(HourlyEnergy(
                hour=hour,
                switch_rate=switches / max(1, len(hour_frames)),
                frame_count=len(hour_frames),
                unique_apps=unique,
                estimated_energy=energy,
            ))

        peak_hours = ""
        low_hours = ""
        if hourly:
            best = max(hourly, key=lambda h: h.estimated_energy)
            worst = min(hourly, key=lambda h: h.estimated_energy)
            peak_hours = f"{best.hour}:00-{best.hour + 1}:00"
            low_hours = f"{worst.hour}:00-{worst.hour + 1}:00"

        meetings = meeting_windows or []
        consec = self._consecutive_meetings(meetings)

        avg_energy = (
            sum(h.estimated_energy for h in hourly) / len(hourly) if hourly else 0.5
        )

        return DailyEnergyProfile(
            date=date_str,
            hourly=hourly,
            peak_hours=peak_hours,
            low_hours=low_hours,
            meeting_count=len(meetings),
            consecutive_meeting_max=consec,
            avg_energy=avg_energy,
        )

    @staticmethod
    def _count_switches(frames: list[ScreenFrame]) -> int:
        switches = 0
        prev = ""
        for f in frames:
            if f.app_name != prev and prev:
                switches += 1
            prev = f.app_name
        return switches

    @staticmethod
    def _estimate_energy(switches: int, unique_apps: int, frame_count: int) -> float:
        if frame_count == 0:
            return 0.5

        switch_rate = switches / frame_count
        norm_unique = min(1.0, unique_apps / 10.0)

        energy = 1.0 - (0.5 * switch_rate + 0.3 * norm_unique)
        return max(0.1, min(1.0, energy))

    @staticmethod
    def _consecutive_meetings(
        meetings: list[tuple[datetime, datetime]],
    ) -> int:
        if not meetings:
            return 0

        sorted_m = sorted(meetings, key=lambda m: m[0])
        max_consec = 1
        current = 1

        for i in range(1, len(sorted_m)):
            gap = (sorted_m[i][0] - sorted_m[i - 1][1]).total_seconds()
            if gap < 600:
                current += 1
                max_consec = max(max_consec, current)
            else:
                current = 1

        return max_consec
