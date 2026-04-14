"""Layer 3: Power Dynamics Analyzer.

Maps influence dynamics from speaker segments: speaking order,
interruptions, talk-time distribution, ghost mode detection.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    SpeakerSegment,
)


@dataclass
class PowerDynamicsMetrics:
    speaking_order: list[str] = field(default_factory=list)
    talk_time_pct: dict[str, float] = field(default_factory=dict)
    gini_coefficient: float = 0.0
    interruptions: dict[str, dict[str, int]] = field(default_factory=dict)
    ghost_speakers: list[str] = field(default_factory=list)
    total_speakers: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaking_order": self.speaking_order,
            "talk_time_pct": {k: round(v, 3) for k, v in self.talk_time_pct.items()},
            "gini_coefficient": round(self.gini_coefficient, 3),
            "interruptions": self.interruptions,
            "ghost_speakers": self.ghost_speakers,
            "total_speakers": self.total_speakers,
        }


class PowerDynamicsAnalyzer:
    """Analyzes power dynamics from diarized speaker segments."""

    def __init__(self, ghost_threshold: float = 0.05) -> None:
        self._ghost_threshold = ghost_threshold

    def analyze(self, segments: list[SpeakerSegment]) -> PowerDynamicsMetrics:
        if not segments:
            return PowerDynamicsMetrics()

        sorted_segs = sorted(segments, key=lambda s: s.start_time)
        speakers = list(dict.fromkeys(s.speaker for s in sorted_segs))

        talk_times: dict[str, float] = defaultdict(float)
        for seg in sorted_segs:
            duration = (seg.end_time - seg.start_time).total_seconds()
            talk_times[seg.speaker] += duration

        total_time = sum(talk_times.values()) or 1.0
        talk_pct = {s: t / total_time for s, t in talk_times.items()}

        speaking_order: list[str] = []
        seen: set[str] = set()
        for seg in sorted_segs:
            if seg.speaker not in seen:
                speaking_order.append(seg.speaker)
                seen.add(seg.speaker)

        interruptions = self._detect_interruptions(sorted_segs)

        ghosts = [s for s, pct in talk_pct.items() if pct < self._ghost_threshold]

        gini = self._gini(list(talk_pct.values()))

        return PowerDynamicsMetrics(
            speaking_order=speaking_order,
            talk_time_pct=talk_pct,
            gini_coefficient=gini,
            interruptions=interruptions,
            ghost_speakers=ghosts,
            total_speakers=len(speakers),
        )

    @staticmethod
    def _detect_interruptions(
        segments: list[SpeakerSegment],
    ) -> dict[str, dict[str, int]]:
        """Who interrupts whom. interruptions[A][B] = count of A interrupting B."""
        interrupts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for i in range(1, len(segments)):
            prev = segments[i - 1]
            curr = segments[i]
            if prev.speaker == curr.speaker:
                continue

            gap = (curr.start_time - prev.end_time).total_seconds()
            if gap < 0.5:
                interrupts[curr.speaker][prev.speaker] += 1

        return {k: dict(v) for k, v in interrupts.items()}

    @staticmethod
    def _gini(values: list[float]) -> float:
        """Compute Gini coefficient. 0 = perfectly equal, 1 = one person dominates."""
        if not values or len(values) < 2:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        total = sum(sorted_vals)
        if total == 0:
            return 0.0
        numerator = sum((2 * i - n + 1) * v for i, v in enumerate(sorted_vals))
        return numerator / (n * total)
