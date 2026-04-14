from __future__ import annotations

from datetime import datetime

from pydantic import Field

from services.api.src.praxo_picos_api.db.models import SourceType

from .base import MemoryObject, _utcnow
from .enums import ObjectType, RetentionBand


class Meeting(MemoryObject):
    """A meeting episode derived from calendar + screenpipe data.

    Intelligence layers store results in attrs under well-known keys:
        attrs["delivery_metrics"]  -- Layer 1 vocal intelligence
        attrs["visual_signals"]    -- Layer 2 frame analysis
        attrs["attention"]         -- Layer 2 attention tracking
        attrs["body_language"]     -- Layer 3 vision analysis
        attrs["coaching_report"]   -- Layer 3 presentation coaching
        attrs["power_dynamics"]    -- Layer 3 power dynamics
        attrs["scorecard"]         -- composite scorecard
    """

    object_type: ObjectType = ObjectType.MEETING
    source: SourceType = SourceType.CALENDAR

    start_time: datetime = Field(default_factory=_utcnow)
    end_time: datetime | None = None
    attendee_ids: list[str] = Field(default_factory=list)
    transcript_ref: str | None = None
    summary: str | None = None
    location: str | None = None

    @property
    def duration_minutes(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60.0

    @property
    def has_intelligence(self) -> bool:
        return bool(self.attrs.get("scorecard") or self.attrs.get("delivery_metrics"))

    @property
    def overall_score(self) -> float | None:
        scorecard = self.attrs.get("scorecard")
        if isinstance(scorecard, dict):
            return scorecard.get("overall_score")
        return None


class ActionItem(MemoryObject):
    """A tracked action item from a meeting or communication."""

    object_type: ObjectType = ObjectType.ACTION_ITEM
    retention_band: RetentionBand = RetentionBand.DURABLE

    owner_id: str | None = None
    due_date: datetime | None = None
    status: str = "open"
    meeting_id: str | None = None
    dependency_ids: list[str] = Field(default_factory=list)


class Decision(MemoryObject):
    """A recorded decision with rationale and alternatives."""

    object_type: ObjectType = ObjectType.DECISION
    retention_band: RetentionBand = RetentionBand.EVERGREEN

    decision_text: str = ""
    rationale: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    decided_by: list[str] = Field(default_factory=list)
    meeting_id: str | None = None


class Commitment(MemoryObject):
    """A promise or obligation tracked across time."""

    object_type: ObjectType = ObjectType.COMMITMENT
    retention_band: RetentionBand = RetentionBand.DURABLE

    promise: str = ""
    owner_id: str | None = None
    audience_ids: list[str] = Field(default_factory=list)
    due_date: datetime | None = None
    status: str = "open"
    completion_evidence: str | None = None
    meeting_id: str | None = None


class Insight(MemoryObject):
    """A system-generated insight (cognitive energy, trend, pattern)."""

    object_type: ObjectType = ObjectType.INSIGHT
    retention_band: RetentionBand = RetentionBand.DURABLE

    insight_type: str = ""
    score: float | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    related_ids: list[str] = Field(default_factory=list)
