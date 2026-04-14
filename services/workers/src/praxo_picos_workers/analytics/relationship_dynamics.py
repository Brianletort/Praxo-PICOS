"""Layer 2: Relationship Dynamics Tracker.

Interaction frequency decay, warming/cooling detection, commitment tracking.
Built from accumulated meeting and communication data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class RelationshipMetrics:
    person_id: str
    person_name: str = ""
    interaction_count: int = 0
    last_interaction: datetime | None = None
    last_interaction_days_ago: int | None = None
    interaction_frequency: str = ""
    trend: str = "stable"
    one_on_one_ratio: float = 0.0
    initiated_by_you_ratio: float = 0.0
    commitment_completion_rate: float | None = None
    topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "interaction_count": self.interaction_count,
            "last_interaction_days_ago": self.last_interaction_days_ago,
            "interaction_frequency": self.interaction_frequency,
            "trend": self.trend,
            "one_on_one_ratio": round(self.one_on_one_ratio, 3),
            "initiated_by_you_ratio": round(self.initiated_by_you_ratio, 3),
            "commitment_completion_rate": (
                round(self.commitment_completion_rate, 3)
                if self.commitment_completion_rate is not None
                else None
            ),
            "topics": self.topics[:10],
        }


@dataclass
class InteractionRecord:
    person_id: str
    timestamp: datetime
    interaction_type: str
    is_one_on_one: bool = False
    initiated_by_you: bool = False
    attendee_count: int = 0
    topics: list[str] = field(default_factory=list)
    has_commitment: bool = False
    commitment_completed: bool = False


class RelationshipDynamicsTracker:
    """Tracks relationship trends from accumulated interaction data."""

    def __init__(
        self,
        cooling_threshold_days: int = 21,
        warming_window_days: int = 14,
    ) -> None:
        self._cooling_threshold = timedelta(days=cooling_threshold_days)
        self._warming_window = timedelta(days=warming_window_days)
        self._interactions: dict[str, list[InteractionRecord]] = {}

    def add_interaction(self, record: InteractionRecord) -> None:
        self._interactions.setdefault(record.person_id, []).append(record)

    def get_metrics(
        self,
        person_id: str,
        person_name: str = "",
        now: datetime | None = None,
    ) -> RelationshipMetrics:
        records = self._interactions.get(person_id, [])
        if not records:
            return RelationshipMetrics(person_id=person_id, person_name=person_name)

        now = now or datetime.now()
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        last = sorted_records[-1]

        days_ago = (now - last.timestamp).days
        frequency = self._compute_frequency(sorted_records, now)
        trend = self._compute_trend(sorted_records, now)

        one_on_one_count = sum(1 for r in records if r.is_one_on_one)
        one_on_one_ratio = one_on_one_count / len(records) if records else 0.0

        initiated = sum(1 for r in records if r.initiated_by_you)
        init_ratio = initiated / len(records) if records else 0.0

        all_topics: list[str] = []
        for r in sorted_records[-10:]:
            all_topics.extend(r.topics)
        unique_topics = list(dict.fromkeys(all_topics))

        with_commitment = [r for r in records if r.has_commitment]
        completion_rate = None
        if with_commitment:
            completed = sum(1 for r in with_commitment if r.commitment_completed)
            completion_rate = completed / len(with_commitment)

        return RelationshipMetrics(
            person_id=person_id,
            person_name=person_name,
            interaction_count=len(records),
            last_interaction=last.timestamp,
            last_interaction_days_ago=days_ago,
            interaction_frequency=frequency,
            trend=trend,
            one_on_one_ratio=one_on_one_ratio,
            initiated_by_you_ratio=init_ratio,
            commitment_completion_rate=completion_rate,
            topics=unique_topics,
        )

    def get_people_needing_attention(
        self,
        now: datetime | None = None,
    ) -> list[RelationshipMetrics]:
        """Find people whose relationships are cooling or stale."""
        now = now or datetime.now()
        attention: list[RelationshipMetrics] = []

        for pid in self._interactions:
            metrics = self.get_metrics(pid, now=now)
            if metrics.trend == "cooling" or (
                metrics.last_interaction_days_ago is not None
                and metrics.last_interaction_days_ago > self._cooling_threshold.days
            ):
                attention.append(metrics)

        return sorted(
            attention,
            key=lambda m: m.last_interaction_days_ago or 999,
            reverse=True,
        )

    def _compute_frequency(
        self,
        records: list[InteractionRecord],
        now: datetime,
    ) -> str:
        if len(records) < 2:
            return "too few interactions"

        span_days = max(1, (now - records[0].timestamp).days)
        rate = len(records) / (span_days / 7)

        if rate >= 3:
            return "multiple times per week"
        if rate >= 1:
            return "weekly"
        if rate >= 0.25:
            return "monthly"
        return "infrequent"

    def _compute_trend(
        self,
        records: list[InteractionRecord],
        now: datetime,
    ) -> str:
        if len(records) < 3:
            return "stable"

        recent_window = now - self._warming_window
        recent = [r for r in records if r.timestamp >= recent_window]
        older = [r for r in records if r.timestamp < recent_window]

        if not older:
            return "stable"

        older_span_days = max(1, (recent_window - records[0].timestamp).days)
        older_rate = len(older) / (older_span_days / 7)

        recent_span_days = max(1, self._warming_window.days)
        recent_rate = len(recent) / (recent_span_days / 7)

        if older_rate == 0:
            return "warming" if recent_rate > 0 else "stable"

        change = (recent_rate - older_rate) / older_rate
        if change > 0.3:
            return "warming"
        if change < -0.3:
            return "cooling"
        return "stable"
