from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RankedInsight:
    """A single insight scored for display priority."""

    headline: str
    detail: str
    category: str
    score: float
    entity_id: str | None = None
    entity_type: str | None = None
    timestamp: datetime | None = None
    actionable: bool = False
    data: dict[str, Any] | None = None


class InsightRanker:
    """Ranks insights by importance for display in simple mode.

    Scoring factors:
        novelty       -- is this new or a continuation of a known pattern?
        actionability -- can the user do something about this right now?
        magnitude     -- how significant is the change/observation?
        urgency       -- is this time-sensitive?

    The simple-mode UI shows the top N ranked insights.
    """

    NOVELTY_WEIGHT = 0.25
    ACTIONABILITY_WEIGHT = 0.30
    MAGNITUDE_WEIGHT = 0.25
    URGENCY_WEIGHT = 0.20

    def rank(
        self,
        insights: list[RankedInsight],
        max_results: int = 5,
    ) -> list[RankedInsight]:
        """Return the top N insights sorted by composite score."""
        for insight in insights:
            insight.score = self._composite_score(insight)

        ranked = sorted(insights, key=lambda i: i.score, reverse=True)

        seen_categories: dict[str, int] = {}
        diversified: list[RankedInsight] = []
        for insight in ranked:
            cat_count = seen_categories.get(insight.category, 0)
            if cat_count >= 2:
                continue
            seen_categories[insight.category] = cat_count + 1
            diversified.append(insight)
            if len(diversified) >= max_results:
                break

        return diversified

    def from_meeting(self, meeting_data: dict[str, Any]) -> list[RankedInsight]:
        """Extract rankable insights from a meeting's attrs."""
        insights: list[RankedInsight] = []
        title = meeting_data.get("title", "Meeting")
        meeting_id = meeting_data.get("id")

        scorecard = meeting_data.get("scorecard", {})
        if scorecard:
            overall = scorecard.get("overall_score", 0)
            vs_avg = scorecard.get("vs_30d_avg", {})

            if overall >= 0.85:
                insights.append(RankedInsight(
                    headline=f"Great meeting: {title}",
                    detail=f"Overall score {int(overall * 100)} -- above your average",
                    category="meeting_quality",
                    score=0.0,
                    entity_id=meeting_id,
                    entity_type="meeting",
                ))
            elif overall < 0.5:
                insights.append(RankedInsight(
                    headline=f"Rough meeting: {title}",
                    detail="Score below 50 -- check the coaching report for tips",
                    category="meeting_quality",
                    score=0.0,
                    entity_id=meeting_id,
                    entity_type="meeting",
                    actionable=True,
                ))

            delivery_trend = vs_avg.get("delivery_trend")
            if delivery_trend == "improving":
                insights.append(RankedInsight(
                    headline="Your delivery is improving",
                    detail="Trending up over the past 30 days",
                    category="trend",
                    score=0.0,
                ))
            elif delivery_trend == "declining":
                insights.append(RankedInsight(
                    headline="Delivery quality is slipping",
                    detail="Consider reviewing recent coaching reports",
                    category="trend",
                    score=0.0,
                    actionable=True,
                ))

        delivery = meeting_data.get("delivery_metrics", {})
        filler_rate = delivery.get("filler_rate_per_min")
        if filler_rate is not None and filler_rate > 6:
            insights.append(RankedInsight(
                headline=f"High filler word rate in {title}",
                detail=f"{filler_rate:.1f} filler words per minute -- try pausing instead",
                category="delivery",
                score=0.0,
                entity_id=meeting_id,
                entity_type="meeting",
                actionable=True,
            ))

        attention = meeting_data.get("attention", {})
        focus_ratio = attention.get("focus_ratio")
        if focus_ratio is not None and focus_ratio < 0.6:
            insights.append(RankedInsight(
                headline=f"Low focus in {title}",
                detail=f"You were focused {int(focus_ratio * 100)}% of the time",
                category="attention",
                score=0.0,
                entity_id=meeting_id,
                entity_type="meeting",
                actionable=True,
            ))

        return insights

    def from_person(self, person_data: dict[str, Any]) -> list[RankedInsight]:
        """Extract rankable insights from a person's attrs."""
        insights: list[RankedInsight] = []
        name = person_data.get("name", "Someone")
        person_id = person_data.get("id")
        dynamics = person_data.get("relationship_dynamics", {})

        trend = dynamics.get("trend")
        if trend == "cooling":
            insights.append(RankedInsight(
                headline=f"Relationship cooling with {name}",
                detail="Interaction frequency has dropped -- consider a check-in",
                category="relationship",
                score=0.0,
                entity_id=person_id,
                entity_type="person",
                actionable=True,
            ))

        days = dynamics.get("last_interaction_days_ago")
        if days and days > 21:
            insights.append(RankedInsight(
                headline=f"Haven't connected with {name} in {days} days",
                detail="This person may be drifting from your network",
                category="relationship",
                score=0.0,
                entity_id=person_id,
                entity_type="person",
                actionable=True,
            ))

        return insights

    def _composite_score(self, insight: RankedInsight) -> float:
        novelty = 0.7
        actionability = 0.9 if insight.actionable else 0.3
        magnitude = min(1.0, max(0.1, insight.score)) if insight.score > 0 else 0.5
        urgency = 0.8 if insight.actionable else 0.4

        return (
            self.NOVELTY_WEIGHT * novelty
            + self.ACTIONABILITY_WEIGHT * actionability
            + self.MAGNITUDE_WEIGHT * magnitude
            + self.URGENCY_WEIGHT * urgency
        )
