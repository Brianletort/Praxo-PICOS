"""Layer 1: Vocal Intelligence -- DeliveryAnalyzer.

Analyzes audio transcription data to produce speaking pace, filler word rate,
talk-to-listen ratio, pause patterns, question frequency, and monologue detection.
No LLM needed -- pure text analysis on existing Screenpipe data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    SpeakerSegment,
)

FILLER_WORDS = frozenset({
    "um", "uh", "like", "you know", "basically", "right",
    "so", "actually", "i mean", "sort of", "kind of",
})

QUESTION_PATTERN = re.compile(r"\?")
SENTENCE_END_PATTERN = re.compile(r"[.!?]\s*$", re.MULTILINE)


@dataclass
class DeliveryMetrics:
    pace_wpm: float = 0.0
    filler_rate_per_min: float = 0.0
    filler_counts: dict[str, int] = field(default_factory=dict)
    talk_listen_ratio: float = 0.0
    question_count: int = 0
    question_rate_per_min: float = 0.0
    monologue_count: int = 0
    monologue_max_s: float = 0.0
    pause_strategic: int = 0
    pause_awkward: int = 0
    pause_interrupted: int = 0
    vocabulary_complexity: float = 0.0
    total_speaking_time_s: float = 0.0
    total_meeting_time_s: float = 0.0
    your_word_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pace_wpm": round(self.pace_wpm, 1),
            "filler_rate_per_min": round(self.filler_rate_per_min, 2),
            "filler_counts": self.filler_counts,
            "talk_listen_ratio": round(self.talk_listen_ratio, 3),
            "question_count": self.question_count,
            "question_rate_per_min": round(self.question_rate_per_min, 2),
            "monologue_count": self.monologue_count,
            "monologue_max_s": round(self.monologue_max_s, 1),
            "pause_strategic": self.pause_strategic,
            "pause_awkward": self.pause_awkward,
            "pause_interrupted": self.pause_interrupted,
            "vocabulary_complexity": round(self.vocabulary_complexity, 3),
            "total_speaking_time_s": round(self.total_speaking_time_s, 1),
            "total_meeting_time_s": round(self.total_meeting_time_s, 1),
            "your_word_count": self.your_word_count,
        }


class DeliveryAnalyzer:
    """Analyzes vocal delivery from diarized audio transcriptions."""

    def __init__(
        self,
        filler_words: frozenset[str] | None = None,
        monologue_threshold_s: float = 90.0,
    ) -> None:
        self._fillers = filler_words or FILLER_WORDS
        self._monologue_threshold = monologue_threshold_s

    def analyze(
        self,
        segments: list[SpeakerSegment],
        meeting_start: datetime,
        meeting_end: datetime,
    ) -> DeliveryMetrics:
        if not segments:
            return DeliveryMetrics()

        your_segments = [s for s in segments if s.is_user]
        all_text_yours = " ".join(s.text for s in your_segments)
        total_meeting_s = max(1.0, (meeting_end - meeting_start).total_seconds())

        your_words = all_text_yours.split()
        your_word_count = len(your_words)
        your_speaking_s = sum(
            (s.end_time - s.start_time).total_seconds() for s in your_segments
        )
        your_speaking_s = max(0.01, your_speaking_s)

        pace_wpm = (your_word_count / your_speaking_s) * 60
        talk_listen_ratio = your_speaking_s / total_meeting_s

        filler_counts = self._count_fillers(all_text_yours)
        total_fillers = sum(filler_counts.values())
        speaking_min = your_speaking_s / 60
        filler_rate = total_fillers / max(0.01, speaking_min)

        question_count = len(QUESTION_PATTERN.findall(all_text_yours))
        question_rate = question_count / max(0.01, speaking_min)

        monologues = self._detect_monologues(your_segments)
        monologue_count = len(monologues)
        monologue_max_s = max(monologues) if monologues else 0.0

        pauses = self._classify_pauses(segments, your_segments)

        vocab_complexity = self._vocabulary_complexity(your_words)

        return DeliveryMetrics(
            pace_wpm=pace_wpm,
            filler_rate_per_min=filler_rate,
            filler_counts=filler_counts,
            talk_listen_ratio=talk_listen_ratio,
            question_count=question_count,
            question_rate_per_min=question_rate,
            monologue_count=monologue_count,
            monologue_max_s=monologue_max_s,
            pause_strategic=pauses["strategic"],
            pause_awkward=pauses["awkward"],
            pause_interrupted=pauses["interrupted"],
            vocabulary_complexity=vocab_complexity,
            total_speaking_time_s=your_speaking_s,
            total_meeting_time_s=total_meeting_s,
            your_word_count=your_word_count,
        )

    def _count_fillers(self, text: str) -> dict[str, int]:
        text_lower = text.lower()
        counts: dict[str, int] = {}
        for filler in self._fillers:
            if " " in filler:
                count = text_lower.count(filler)
            else:
                count = sum(
                    1 for word in text_lower.split() if word.strip(",.!?;:") == filler
                )
            if count > 0:
                counts[filler] = count
        return counts

    def _detect_monologues(self, your_segments: list[SpeakerSegment]) -> list[float]:
        """Find consecutive speaking streaks above the monologue threshold."""
        if not your_segments:
            return []

        sorted_segs = sorted(your_segments, key=lambda s: s.start_time)
        monologues: list[float] = []
        streak_start = sorted_segs[0].start_time
        streak_end = sorted_segs[0].end_time

        for seg in sorted_segs[1:]:
            gap = (seg.start_time - streak_end).total_seconds()
            if gap < 3.0:
                streak_end = seg.end_time
            else:
                duration = (streak_end - streak_start).total_seconds()
                if duration >= self._monologue_threshold:
                    monologues.append(duration)
                streak_start = seg.start_time
                streak_end = seg.end_time

        duration = (streak_end - streak_start).total_seconds()
        if duration >= self._monologue_threshold:
            monologues.append(duration)

        return monologues

    def _classify_pauses(
        self,
        all_segments: list[SpeakerSegment],
        your_segments: list[SpeakerSegment],
    ) -> dict[str, int]:
        """Classify gaps between your speaking segments."""
        pauses = {"strategic": 0, "awkward": 0, "interrupted": 0}

        sorted_yours = sorted(your_segments, key=lambda s: s.start_time)
        for i in range(1, len(sorted_yours)):
            gap = (sorted_yours[i].start_time - sorted_yours[i - 1].end_time).total_seconds()
            if gap < 0.5:
                pauses["interrupted"] += 1
            elif 2.0 <= gap <= 4.0:
                pauses["strategic"] += 1
            elif gap > 6.0:
                pauses["awkward"] += 1

        return pauses

    @staticmethod
    def _vocabulary_complexity(words: list[str]) -> float:
        """Type-token ratio as a simple vocabulary complexity proxy."""
        if not words:
            return 0.0
        cleaned = [w.lower().strip(",.!?;:\"'()") for w in words if len(w) > 1]
        if not cleaned:
            return 0.0
        unique = len(set(cleaned))
        return unique / len(cleaned)
