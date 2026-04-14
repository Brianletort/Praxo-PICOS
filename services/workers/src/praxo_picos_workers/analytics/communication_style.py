"""Layer 1: Communication Style DNA.

Profiles how the user's verbal behavior shifts per audience.
Requires multiple meetings with the same person (min 3 by default).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .meeting_delivery import DeliveryMetrics


@dataclass
class PersonStyleProfile:
    """How YOU communicate with a specific person."""

    person_id: str
    person_name: str
    meeting_count: int = 0
    avg_pace_wpm: float = 0.0
    avg_filler_rate: float = 0.0
    avg_question_rate: float = 0.0
    avg_talk_listen_ratio: float = 0.0
    avg_monologue_length_s: float = 0.0
    avg_vocabulary_complexity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "meeting_count": self.meeting_count,
            "avg_pace_wpm": round(self.avg_pace_wpm, 1),
            "avg_filler_rate": round(self.avg_filler_rate, 2),
            "avg_question_rate": round(self.avg_question_rate, 2),
            "avg_talk_listen_ratio": round(self.avg_talk_listen_ratio, 3),
            "avg_monologue_length_s": round(self.avg_monologue_length_s, 1),
            "avg_vocabulary_complexity": round(self.avg_vocabulary_complexity, 3),
        }


@dataclass
class StyleShift:
    """Quantified difference in how you communicate with one person vs your baseline."""

    person_id: str
    person_name: str
    pace_diff_pct: float = 0.0
    filler_diff_pct: float = 0.0
    question_diff_pct: float = 0.0
    talk_ratio_diff_pct: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "pace_diff_pct": round(self.pace_diff_pct, 1),
            "filler_diff_pct": round(self.filler_diff_pct, 1),
            "question_diff_pct": round(self.question_diff_pct, 1),
            "talk_ratio_diff_pct": round(self.talk_ratio_diff_pct, 1),
            "summary": self.summary,
        }


class CommunicationStyleDNA:
    """Builds per-person communication style profiles from accumulated delivery metrics."""

    def __init__(self, min_meetings: int = 3) -> None:
        self._min_meetings = min_meetings
        self._profiles: dict[str, list[DeliveryMetrics]] = {}
        self._global_metrics: list[DeliveryMetrics] = []

    def add_meeting(
        self,
        delivery: DeliveryMetrics,
        attendee_ids: list[str],
        attendee_names: dict[str, str] | None = None,
    ) -> None:
        """Record delivery metrics for a meeting with given attendees."""
        self._global_metrics.append(delivery)
        for pid in attendee_ids:
            self._profiles.setdefault(pid, []).append(delivery)

    def get_profile(self, person_id: str, person_name: str = "") -> PersonStyleProfile | None:
        """Get the style profile for a specific person (None if below threshold)."""
        metrics = self._profiles.get(person_id, [])
        if len(metrics) < self._min_meetings:
            return None
        return self._aggregate(person_id, person_name, metrics)

    def get_all_profiles(
        self, names: dict[str, str] | None = None,
    ) -> list[PersonStyleProfile]:
        """Get style profiles for all people above the meeting threshold."""
        names = names or {}
        profiles = []
        for pid, metrics in self._profiles.items():
            if len(metrics) >= self._min_meetings:
                profiles.append(self._aggregate(pid, names.get(pid, ""), metrics))
        return profiles

    def compute_style_shift(
        self, person_id: str, person_name: str = "",
    ) -> StyleShift | None:
        """Quantify how you communicate differently with this person vs your baseline."""
        profile = self.get_profile(person_id, person_name)
        if profile is None:
            return None

        baseline = self._global_baseline()
        if baseline is None:
            return None

        def pct_diff(val: float, base: float) -> float:
            if base == 0:
                return 0.0
            return ((val - base) / base) * 100

        shift = StyleShift(
            person_id=person_id,
            person_name=person_name,
            pace_diff_pct=pct_diff(profile.avg_pace_wpm, baseline.avg_pace_wpm),
            filler_diff_pct=pct_diff(profile.avg_filler_rate, baseline.avg_filler_rate),
            question_diff_pct=pct_diff(profile.avg_question_rate, baseline.avg_question_rate),
            talk_ratio_diff_pct=pct_diff(profile.avg_talk_listen_ratio, baseline.avg_talk_listen_ratio),
        )

        shift.summary = self._generate_summary(shift)
        return shift

    def _aggregate(
        self, person_id: str, person_name: str, metrics: list[DeliveryMetrics],
    ) -> PersonStyleProfile:
        n = len(metrics)
        return PersonStyleProfile(
            person_id=person_id,
            person_name=person_name,
            meeting_count=n,
            avg_pace_wpm=sum(m.pace_wpm for m in metrics) / n,
            avg_filler_rate=sum(m.filler_rate_per_min for m in metrics) / n,
            avg_question_rate=sum(m.question_rate_per_min for m in metrics) / n,
            avg_talk_listen_ratio=sum(m.talk_listen_ratio for m in metrics) / n,
            avg_monologue_length_s=sum(m.monologue_max_s for m in metrics) / n,
            avg_vocabulary_complexity=sum(m.vocabulary_complexity for m in metrics) / n,
        )

    def _global_baseline(self) -> PersonStyleProfile | None:
        if not self._global_metrics:
            return None
        return self._aggregate("_global", "baseline", self._global_metrics)

    @staticmethod
    def _generate_summary(shift: StyleShift) -> str:
        parts: list[str] = []
        name = shift.person_name or "this person"

        if abs(shift.pace_diff_pct) > 10:
            direction = "faster" if shift.pace_diff_pct > 0 else "slower"
            parts.append(f"you speak {abs(int(shift.pace_diff_pct))}% {direction}")

        if abs(shift.question_diff_pct) > 20:
            direction = "more" if shift.question_diff_pct > 0 else "fewer"
            parts.append(f"you ask {direction} questions")

        if abs(shift.filler_diff_pct) > 20:
            direction = "more" if shift.filler_diff_pct > 0 else "fewer"
            parts.append(f"you use {direction} filler words")

        if abs(shift.talk_ratio_diff_pct) > 15:
            direction = "more" if shift.talk_ratio_diff_pct > 0 else "less"
            parts.append(f"you talk {direction}")

        if not parts:
            return f"Your communication style is consistent with {name}"

        joined = ", ".join(parts)
        return f"With {name}: {joined}"
