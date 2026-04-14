"""Tier 1: Relationship Intelligence.

Derives strategic relationship scores from existing metrics:
  trust_trend, response_reliability_score, friction_index,
  follow_through_probability, relationship_decay_velocity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RelationshipIntelligenceProfile:
    stakeholder_alignment_score: float = 0.5
    trust_trend: str = "stable"
    response_reliability_score: float = 0.5
    follow_through_probability: float = 0.5
    friction_index: float = 0.0
    relationship_decay_velocity: float = 0.0
    sponsorship_potential: float = 0.5
    political_sensitivity: float = 0.0
    influence_dependency: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stakeholder_alignment_score": round(self.stakeholder_alignment_score, 3),
            "trust_trend": self.trust_trend,
            "response_reliability_score": round(self.response_reliability_score, 3),
            "follow_through_probability": round(self.follow_through_probability, 3),
            "friction_index": round(self.friction_index, 3),
            "relationship_decay_velocity": round(self.relationship_decay_velocity, 3),
            "sponsorship_potential": round(self.sponsorship_potential, 3),
            "political_sensitivity": round(self.political_sensitivity, 3),
            "influence_dependency": round(self.influence_dependency, 3),
        }


class RelationshipIntelligenceScorer:
    """Computes strategic relationship scores from existing person attrs."""

    def score(self, person_attrs: dict[str, Any]) -> RelationshipIntelligenceProfile:
        dynamics = person_attrs.get("relationship_dynamics", {})
        style = person_attrs.get("communication_dynamic", {})
        profile = person_attrs.get("style_profile", {})

        trend = dynamics.get("trend", "stable")
        interaction_count = dynamics.get("interaction_count", 0)
        days_ago = dynamics.get("last_interaction_days_ago")
        one_on_one = dynamics.get("one_on_one_ratio", 0.0)
        initiated = dynamics.get("initiated_by_you_ratio", 0.5)
        completion = dynamics.get("commitment_completion_rate")

        alignment = self._alignment(trend, one_on_one, interaction_count)
        trust = self._trust_trend(trend, completion, days_ago)
        reliability = self._reliability(completion, interaction_count)
        follow_through = self._follow_through(completion)
        friction = self._friction(style, trend, days_ago)
        decay = self._decay_velocity(days_ago, trend)
        sponsorship = self._sponsorship(one_on_one, interaction_count, trend)
        sensitivity = self._political_sensitivity(style)
        dependency = self._influence_dependency(initiated, interaction_count)

        return RelationshipIntelligenceProfile(
            stakeholder_alignment_score=alignment,
            trust_trend=trust,
            response_reliability_score=reliability,
            follow_through_probability=follow_through,
            friction_index=friction,
            relationship_decay_velocity=decay,
            sponsorship_potential=sponsorship,
            political_sensitivity=sensitivity,
            influence_dependency=dependency,
        )

    def _alignment(self, trend: str, one_on_one: float, count: int) -> float:
        score = 0.5
        if trend == "warming":
            score += 0.2
        elif trend == "cooling":
            score -= 0.2

        score += one_on_one * 0.15
        score += min(0.15, count * 0.01)
        return max(0.0, min(1.0, score))

    def _trust_trend(self, trend: str, completion: float | None, days_ago: int | None) -> str:
        if completion is not None and completion > 0.8 and trend == "warming":
            return "strengthening"
        if completion is not None and completion < 0.5:
            return "weakening"
        if days_ago and days_ago > 30:
            return "at_risk"
        return trend

    def _reliability(self, completion: float | None, count: int) -> float:
        if completion is None or count < 3:
            return 0.5
        return completion

    def _follow_through(self, completion: float | None) -> float:
        if completion is None:
            return 0.5
        return completion

    def _friction(self, style: dict, trend: str, days_ago: int | None) -> float:
        friction = 0.0
        pace_diff = abs(style.get("pace_diff_pct", 0))
        if pace_diff > 20:
            friction += 0.2

        if trend == "cooling":
            friction += 0.3

        if days_ago and days_ago > 21:
            friction += 0.2

        return min(1.0, friction)

    def _decay_velocity(self, days_ago: int | None, trend: str) -> float:
        if days_ago is None:
            return 0.0
        if trend == "cooling":
            return min(1.0, days_ago / 60.0)
        return min(0.5, days_ago / 90.0)

    def _sponsorship(self, one_on_one: float, count: int, trend: str) -> float:
        score = 0.3
        score += one_on_one * 0.3
        score += min(0.2, count * 0.01)
        if trend == "warming":
            score += 0.2
        elif trend == "cooling":
            score -= 0.15
        return max(0.0, min(1.0, score))

    def _political_sensitivity(self, style: dict) -> float:
        pace_diff = abs(style.get("pace_diff_pct", 0))
        talk_diff = abs(style.get("talk_ratio_diff_pct", 0))

        sensitivity = 0.0
        if pace_diff > 15:
            sensitivity += 0.3
        if talk_diff > 20:
            sensitivity += 0.3
        return min(1.0, sensitivity)

    def _influence_dependency(self, initiated: float, count: int) -> float:
        if count < 3:
            return 0.0
        return max(0.0, min(1.0, initiated * 0.8 + min(0.2, count * 0.005)))
