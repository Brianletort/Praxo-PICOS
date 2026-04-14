"""Layer 3: Vision Analyzer -- body language via vision LLM.

Sends selected meeting frames to gpt-5.4-pro for structured body language
analysis. Results are hypothesis data with confidence ceiling.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from services.api.src.praxo_picos_api.agents.llm_provider import LLMProvider
from services.workers.src.praxo_picos_workers.extractors.screenpipe_deep import (
    ScreenFrame,
)

logger = logging.getLogger(__name__)

VISION_PROMPT = (
    "Analyze this video call screenshot for body language cues. "
    "Focus on the self-view tile (the person using this computer). "
    "Return JSON with:\n"
    '  "facial_expression": one of "engaged"|"neutral"|"confused"|"distracted"|"smiling"|"concerned",\n'
    '  "eye_contact": one of "camera"|"screen"|"down"|"away",\n'
    '  "posture": one of "upright"|"leaning_forward"|"slouched"|"leaning_back",\n'
    '  "gestures": one of "hands_visible"|"gesturing"|"still"|"fidgeting",\n'
    '  "energy_level": one of "high"|"moderate"|"low"|"flat",\n'
    '  "confidence_indicators": list of observed positive signals,\n'
    '  "concern_indicators": list of observed negative signals,\n'
    '  "background_context": one of "home_office"|"office"|"travel"|"other"\n'
    "Be concise. If you cannot see a self-view tile, return {\"no_self_view\": true}."
)

MAX_CONFIDENCE = 0.7


@dataclass
class FrameAnalysisResult:
    timestamp: datetime
    expression: str = "neutral"
    eye_contact: str = "screen"
    posture: str = "upright"
    gestures: str = "still"
    energy: str = "moderate"
    confidence_indicators: list[str] = field(default_factory=list)
    concern_indicators: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class BodyLanguageAnalysis:
    frames_analyzed: int = 0
    eye_contact_pct: float = 0.0
    dominant_expression: str = "neutral"
    energy_trajectory: str = "stable"
    dominant_posture: str = "upright"
    confidence: float = MAX_CONFIDENCE
    frame_results: list[FrameAnalysisResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frames_analyzed": self.frames_analyzed,
            "eye_contact_pct": round(self.eye_contact_pct, 3),
            "dominant_expression": self.dominant_expression,
            "energy_trajectory": self.energy_trajectory,
            "dominant_posture": self.dominant_posture,
            "confidence": self.confidence,
            "per_frame": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "expression": r.expression,
                    "eye_contact": r.eye_contact,
                    "posture": r.posture,
                    "energy": r.energy,
                }
                for r in self.frame_results
            ],
        }


class VisionAnalyzer:
    """Analyzes meeting frames for body language using vision LLM."""

    def __init__(self, llm: LLMProvider, max_frames: int = 30) -> None:
        self._llm = llm
        self._max_frames = max_frames

    async def analyze(self, frames: list[ScreenFrame]) -> BodyLanguageAnalysis:
        """Analyze selected frames for body language signals."""
        with_data = [f for f in frames if f.frame_data]
        selected = with_data[:self._max_frames]

        if not selected:
            return BodyLanguageAnalysis()

        results: list[FrameAnalysisResult] = []
        for frame in selected:
            try:
                raw = await self._llm.complete_vision(
                    VISION_PROMPT,
                    frame.frame_data,
                    max_tokens=512,
                )
                if raw.get("no_self_view"):
                    continue

                results.append(FrameAnalysisResult(
                    timestamp=frame.timestamp,
                    expression=raw.get("facial_expression", "neutral"),
                    eye_contact=raw.get("eye_contact", "screen"),
                    posture=raw.get("posture", "upright"),
                    gestures=raw.get("gestures", "still"),
                    energy=raw.get("energy_level", "moderate"),
                    confidence_indicators=raw.get("confidence_indicators", []),
                    concern_indicators=raw.get("concern_indicators", []),
                    raw=raw,
                ))
            except Exception:
                logger.warning("Vision analysis failed for frame at %s", frame.timestamp)

        return self._aggregate(results)

    def _aggregate(self, results: list[FrameAnalysisResult]) -> BodyLanguageAnalysis:
        if not results:
            return BodyLanguageAnalysis()

        n = len(results)
        eye_contact_count = sum(1 for r in results if r.eye_contact == "camera")

        expressions = [r.expression for r in results]
        dominant_expr = max(set(expressions), key=expressions.count)

        postures = [r.posture for r in results]
        dominant_posture = max(set(postures), key=postures.count)

        energy_order = {"high": 3, "moderate": 2, "low": 1, "flat": 0}
        energies = [energy_order.get(r.energy, 1) for r in results]
        third = max(1, n // 3)
        start_avg = sum(energies[:third]) / third
        end_avg = sum(energies[-third:]) / third
        if end_avg > start_avg + 0.5:
            trajectory = "increasing"
        elif end_avg < start_avg - 0.5:
            trajectory = "decreasing"
        else:
            trajectory = "stable"

        return BodyLanguageAnalysis(
            frames_analyzed=n,
            eye_contact_pct=eye_contact_count / n,
            dominant_expression=dominant_expr,
            energy_trajectory=trajectory,
            dominant_posture=dominant_posture,
            confidence=MAX_CONFIDENCE,
            frame_results=results,
        )
