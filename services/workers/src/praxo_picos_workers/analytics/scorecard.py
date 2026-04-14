"""Composite Scorecard -- combines all intelligence layers into a per-meeting score.

Four sub-scores: delivery, engagement, presence, preparation.
Overall weighted composite with 30-day trend comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scorecard:
    delivery_score: float = 0.0
    engagement_score: float = 0.0
    presence_score: float = 0.0
    preparation_score: float = 0.0
    overall_score: float = 0.0
    vs_30d_avg: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery": {"score": round(self.delivery_score, 3)},
            "engagement": {"score": round(self.engagement_score, 3)},
            "presence": {"score": round(self.presence_score, 3)},
            "preparation": {"score": round(self.preparation_score, 3)},
            "overall_score": round(self.overall_score, 3),
            "vs_30d_avg": self.vs_30d_avg,
        }


WEIGHTS = {
    "delivery": 0.30,
    "engagement": 0.30,
    "presence": 0.25,
    "preparation": 0.15,
}


class ScorecardBuilder:
    """Builds a composite scorecard from all intelligence layer attrs."""

    def build(
        self,
        attrs: dict[str, Any],
        historical_scores: list[float] | None = None,
    ) -> Scorecard:
        delivery = self._score_delivery(attrs.get("delivery_metrics", {}))
        engagement = self._score_engagement(attrs.get("attention", {}))
        presence = self._score_presence(attrs.get("body_language", {}))
        preparation = self._score_preparation(attrs.get("attention", {}))

        overall = (
            WEIGHTS["delivery"] * delivery
            + WEIGHTS["engagement"] * engagement
            + WEIGHTS["presence"] * presence
            + WEIGHTS["preparation"] * preparation
        )

        vs_avg: dict[str, str] = {}
        if historical_scores:
            avg = sum(historical_scores) / len(historical_scores)
            diff = overall - avg

            trend_label = "improving" if diff > 0.05 else ("declining" if diff < -0.05 else "stable")
            vs_avg["overall_trend"] = trend_label
            vs_avg["delivery_trend"] = trend_label
            vs_avg["engagement_trend"] = trend_label
            vs_avg["presence_trend"] = trend_label
            vs_avg["avg_30d"] = str(round(avg, 3))

        return Scorecard(
            delivery_score=delivery,
            engagement_score=engagement,
            presence_score=presence,
            preparation_score=preparation,
            overall_score=overall,
            vs_30d_avg=vs_avg,
        )

    @staticmethod
    def _score_delivery(metrics: dict[str, Any]) -> float:
        if not metrics:
            return 0.5

        score = 0.5
        pace = metrics.get("pace_wpm", 0)
        if 120 <= pace <= 160:
            score += 0.2
        elif pace > 0:
            score += 0.1

        filler = metrics.get("filler_rate_per_min", 0)
        if filler < 2:
            score += 0.15
        elif filler < 5:
            score += 0.05

        ratio = metrics.get("talk_listen_ratio", 0.5)
        if 0.3 <= ratio <= 0.6:
            score += 0.15
        elif ratio > 0:
            score += 0.05

        return min(1.0, score)

    @staticmethod
    def _score_engagement(attention: dict[str, Any]) -> float:
        if not attention:
            return 0.5

        focus = attention.get("focus_ratio", 0.5)
        note_bonus = 0.1 if attention.get("note_taking_detected") else 0.0
        switch_penalty = min(0.2, attention.get("app_switch_count", 0) * 0.02)

        return min(1.0, max(0.0, focus + note_bonus - switch_penalty))

    @staticmethod
    def _score_presence(body_lang: dict[str, Any]) -> float:
        if not body_lang:
            return 0.5

        eye = body_lang.get("eye_contact_pct", 0.5)
        expr = body_lang.get("dominant_expression", "neutral")
        posture = body_lang.get("dominant_posture", "upright")

        score = eye * 0.5
        if expr in ("engaged", "smiling"):
            score += 0.3
        elif expr == "neutral":
            score += 0.15

        if posture in ("upright", "leaning_forward"):
            score += 0.2
        elif posture == "slouched":
            score -= 0.1

        return min(1.0, max(0.0, score))

    @staticmethod
    def _score_preparation(attention: dict[str, Any]) -> float:
        if not attention:
            return 0.5

        score = 0.3
        if attention.get("pre_meeting_docs_opened", 0) > 0:
            score += 0.35
        if attention.get("post_meeting_followup"):
            score += 0.35

        return min(1.0, score)
