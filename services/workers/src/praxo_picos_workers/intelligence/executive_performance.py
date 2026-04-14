"""Tier 1: Executive Performance Intelligence.

Derives strategic scores from existing raw metrics:
  executive_presence_score, clarity_score, brevity_efficiency_score,
  confidence_leakage_markers, audience_engagement_curve.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutivePerformanceProfile:
    executive_presence_score: float = 0.5
    clarity_score: float = 0.5
    brevity_efficiency_score: float = 0.5
    confidence_stability_score: float = 0.5
    filler_word_density: float = 0.0
    talk_to_listen_ratio: float = 0.5
    audience_engagement_curve: list[float] = field(default_factory=list)
    confidence_leakage_markers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_presence_score": round(self.executive_presence_score, 3),
            "clarity_score": round(self.clarity_score, 3),
            "brevity_efficiency_score": round(self.brevity_efficiency_score, 3),
            "confidence_stability_score": round(self.confidence_stability_score, 3),
            "filler_word_density": round(self.filler_word_density, 3),
            "talk_to_listen_ratio": round(self.talk_to_listen_ratio, 3),
            "audience_engagement_curve": [round(v, 2) for v in self.audience_engagement_curve],
            "confidence_leakage_markers": self.confidence_leakage_markers,
        }


class ExecutivePerformanceScorer:
    """Computes executive performance scores from existing meeting attrs."""

    def score(self, attrs: dict[str, Any]) -> ExecutivePerformanceProfile:
        delivery = attrs.get("delivery_metrics", {})
        body = attrs.get("body_language", {})
        attention = attrs.get("attention", {})
        power = attrs.get("power_dynamics", {})

        presence = self._executive_presence(delivery, body)
        clarity = self._clarity(delivery)
        brevity = self._brevity(delivery)
        confidence = self._confidence_stability(delivery, body)
        engagement_curve = self._engagement_curve(body)
        leakage = self._confidence_leakage(delivery, body)

        return ExecutivePerformanceProfile(
            executive_presence_score=presence,
            clarity_score=clarity,
            brevity_efficiency_score=brevity,
            confidence_stability_score=confidence,
            filler_word_density=delivery.get("filler_rate_per_min", 0),
            talk_to_listen_ratio=delivery.get("talk_listen_ratio", 0.5),
            audience_engagement_curve=engagement_curve,
            confidence_leakage_markers=leakage,
        )

    def _executive_presence(self, delivery: dict, body: dict) -> float:
        score = 0.0
        weights_used = 0.0

        eye = body.get("eye_contact_pct")
        if eye is not None:
            score += eye * 0.25
            weights_used += 0.25

        posture = body.get("dominant_posture", "")
        if posture in ("upright", "leaning_forward"):
            score += 0.2
        elif posture:
            score += 0.1
        weights_used += 0.2

        pace = delivery.get("pace_wpm", 0)
        if 120 <= pace <= 155:
            score += 0.2
        elif 100 <= pace <= 180:
            score += 0.1
        weights_used += 0.2

        filler = delivery.get("filler_rate_per_min", 0)
        if filler < 2:
            score += 0.15
        elif filler < 4:
            score += 0.08
        weights_used += 0.15

        energy = body.get("energy_trajectory", "stable")
        if energy in ("stable", "increasing"):
            score += 0.2
        else:
            score += 0.05
        weights_used += 0.2

        return min(1.0, score / max(0.01, weights_used) * 1.0) if weights_used > 0 else 0.5

    def _clarity(self, delivery: dict) -> float:
        score = 0.5
        complexity = delivery.get("vocabulary_complexity", 0.5)
        if 0.4 <= complexity <= 0.7:
            score += 0.2
        elif complexity > 0:
            score += 0.1

        monologue = delivery.get("monologue_max_s", 0)
        if monologue < 60:
            score += 0.15
        elif monologue < 90:
            score += 0.05

        questions = delivery.get("question_rate_per_min", 0)
        if questions > 0.5:
            score += 0.15

        return min(1.0, score)

    def _brevity(self, delivery: dict) -> float:
        ratio = delivery.get("talk_listen_ratio", 0.5)
        monologue = delivery.get("monologue_count", 0)
        max_mono = delivery.get("monologue_max_s", 0)

        score = 0.5
        if 0.25 <= ratio <= 0.5:
            score += 0.25
        elif ratio < 0.25:
            score += 0.15

        if monologue == 0:
            score += 0.15
        elif monologue <= 1:
            score += 0.05

        if max_mono < 60:
            score += 0.1

        return min(1.0, score)

    def _confidence_stability(self, delivery: dict, body: dict) -> float:
        score = 0.5
        filler = delivery.get("filler_rate_per_min", 0)
        if filler < 2:
            score += 0.2
        elif filler < 4:
            score += 0.1

        pauses = delivery.get("pause_strategic", 0)
        awkward = delivery.get("pause_awkward", 0)
        if pauses > awkward:
            score += 0.15
        elif awkward == 0:
            score += 0.1

        energy = body.get("energy_trajectory", "stable")
        if energy == "stable":
            score += 0.15
        elif energy == "increasing":
            score += 0.1

        return min(1.0, score)

    def _engagement_curve(self, body: dict) -> list[float]:
        per_frame = body.get("per_frame", [])
        if not per_frame:
            return []

        energy_map = {"high": 1.0, "moderate": 0.6, "low": 0.3, "flat": 0.1}
        expression_bonus = {"engaged": 0.2, "smiling": 0.15, "neutral": 0.0}
        curve = []
        for f in per_frame:
            val = energy_map.get(f.get("energy", "moderate"), 0.5)
            val += expression_bonus.get(f.get("expression", "neutral"), 0.0)
            curve.append(min(1.0, val))
        return curve

    def _confidence_leakage(self, delivery: dict, body: dict) -> list[str]:
        markers = []
        filler = delivery.get("filler_rate_per_min", 0)
        if filler > 5:
            markers.append(f"high filler rate ({filler:.1f}/min)")

        awkward = delivery.get("pause_awkward", 0)
        if awkward > 2:
            markers.append(f"{awkward} awkward pauses detected")

        posture = body.get("dominant_posture", "")
        if posture == "slouched":
            markers.append("slouched posture")

        eye = body.get("eye_contact_pct", 1.0)
        if eye < 0.4:
            markers.append(f"low eye contact ({int(eye * 100)}%)")

        energy = body.get("energy_trajectory", "")
        if energy == "decreasing":
            markers.append("energy declined through meeting")

        return markers
