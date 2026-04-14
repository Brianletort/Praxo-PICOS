from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InsightAvailability:
    """Tracks which insight types are available for an entity."""

    available: list[str] = field(default_factory=list)
    learning: list[LearningPlaceholder] = field(default_factory=list)


@dataclass
class LearningPlaceholder:
    """A placeholder shown while the system builds enough data for an insight."""

    insight_type: str
    message: str
    progress_pct: float = 0.0


@dataclass
class ProgressiveThresholds:
    """Minimum data requirements before each insight type appears."""

    min_meetings_for_delivery: int = 1
    min_meetings_for_style: int = 3
    min_days_for_energy: int = 14
    min_days_for_trends: int = 30
    min_meetings_per_person_for_relationship: int = 5


class ProgressiveDisclosure:
    """Controls what insights are shown based on accumulated data.

    Prevents showing empty or low-confidence cards. The UI feels
    "alive" as new insights progressively appear over time.
    """

    def __init__(self, thresholds: ProgressiveThresholds | None = None) -> None:
        self._thresholds = thresholds or ProgressiveThresholds()

    def meeting_insights(self, total_meetings: int) -> InsightAvailability:
        """What meeting intelligence is available given the number of meetings analyzed."""
        available = []
        learning = []

        if total_meetings >= self._thresholds.min_meetings_for_delivery:
            available.append("delivery_metrics")
            available.append("attention")
        else:
            learning.append(LearningPlaceholder(
                insight_type="delivery_metrics",
                message="After your first meeting, I'll analyze your speaking patterns",
                progress_pct=0.0,
            ))

        if total_meetings >= 3:
            available.append("coaching_report")
        else:
            remaining = 3 - total_meetings
            learning.append(LearningPlaceholder(
                insight_type="coaching_report",
                message=f"{remaining} more meeting{'s' if remaining != 1 else ''} until coaching reports",
                progress_pct=total_meetings / 3 * 100,
            ))

        if total_meetings >= 5:
            available.append("scorecard")
            available.append("trend_comparison")
        else:
            remaining = 5 - total_meetings
            learning.append(LearningPlaceholder(
                insight_type="scorecard",
                message=f"{remaining} more meetings until score trends",
                progress_pct=total_meetings / 5 * 100,
            ))

        return InsightAvailability(available=available, learning=learning)

    def person_insights(
        self,
        meetings_with_person: int,
        total_days_known: int,
    ) -> InsightAvailability:
        """What person intelligence is available given interaction history."""
        available = []
        learning = []

        if meetings_with_person >= 1:
            available.append("basic_profile")

        if meetings_with_person >= self._thresholds.min_meetings_for_style:
            available.append("communication_style")
        elif meetings_with_person >= 1:
            remaining = self._thresholds.min_meetings_for_style - meetings_with_person
            learning.append(LearningPlaceholder(
                insight_type="communication_style",
                message=f"{remaining} more meetings to learn your style with this person",
                progress_pct=meetings_with_person / self._thresholds.min_meetings_for_style * 100,
            ))

        if meetings_with_person >= self._thresholds.min_meetings_per_person_for_relationship:
            available.append("relationship_dynamics")
        elif meetings_with_person >= 1:
            remaining = self._thresholds.min_meetings_per_person_for_relationship - meetings_with_person
            learning.append(LearningPlaceholder(
                insight_type="relationship_dynamics",
                message=f"{remaining} more interactions to track relationship trends",
                progress_pct=(
                    meetings_with_person
                    / self._thresholds.min_meetings_per_person_for_relationship
                    * 100
                ),
            ))

        if total_days_known >= self._thresholds.min_days_for_trends:
            available.append("long_term_trends")

        return InsightAvailability(available=available, learning=learning)

    def energy_insights(self, days_of_data: int) -> InsightAvailability:
        """What cognitive energy insights are available."""
        available = []
        learning = []

        if days_of_data >= 3:
            available.append("daily_energy")

        if days_of_data >= self._thresholds.min_days_for_energy:
            available.append("circadian_map")
            available.append("peak_hours")
        else:
            remaining = self._thresholds.min_days_for_energy - days_of_data
            learning.append(LearningPlaceholder(
                insight_type="circadian_map",
                message=f"{remaining} more days to map your energy patterns",
                progress_pct=days_of_data / self._thresholds.min_days_for_energy * 100,
            ))

        if days_of_data >= self._thresholds.min_days_for_trends:
            available.append("energy_trends")

        return InsightAvailability(available=available, learning=learning)

    def global_readiness(
        self,
        total_meetings: int,
        total_days: int,
        total_people: int,
    ) -> dict[str, InsightAvailability]:
        """Summary of what's ready across all domains."""
        return {
            "meetings": self.meeting_insights(total_meetings),
            "energy": self.energy_insights(total_days),
            "people": InsightAvailability(
                available=["people_list"] if total_people > 0 else [],
                learning=[LearningPlaceholder(
                    insight_type="people_list",
                    message="People will appear as you have meetings and send emails",
                    progress_pct=0.0,
                )] if total_people == 0 else [],
            ),
        }
