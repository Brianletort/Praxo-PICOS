from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.src.praxo_picos_api.db.models import SourceType

from .enums import ObjectType, RetentionBand, Sensitivity


def _new_id() -> str:
    return uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MemoryObject(BaseModel):
    """Base class for all typed objects in the second brain.

    The user never sees or interacts with this layer directly.
    It exists to power the narrative and analytics surfaces.
    """

    id: str = Field(default_factory=_new_id)
    object_type: ObjectType
    source: SourceType
    source_id: str = ""

    title: str | None = None
    body: str | None = None
    timestamp: datetime = Field(default_factory=_utcnow)

    attrs: dict[str, Any] = Field(default_factory=dict)

    sensitivity: Sensitivity = Sensitivity.INTERNAL
    retention_band: RetentionBand = RetentionBand.DURABLE
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    version: int = 1
    parent_id: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    model_config = {"extra": "forbid"}

    def bump_version(self) -> MemoryObject:
        """Return a copy with incremented version and fresh updated_at."""
        return self.model_copy(
            update={
                "version": self.version + 1,
                "parent_id": self.id,
                "updated_at": _utcnow(),
            }
        )


class NarrativeResponse(BaseModel):
    """Standard narrative shape returned by all analytics endpoints.

    Simple-mode UI reads only this. If you cannot write a clear headline
    for a feature, the feature is not ready for the UI.
    """

    headline: str
    bullets: list[str] = Field(default_factory=list)
    trend: str = "stable"
    sentiment: str = "neutral"
    available_depth: list[str] = Field(default_factory=list)


class AnalyticsResponse(BaseModel):
    """Dual-response envelope: narrative (always) + detail (opt-in)."""

    narrative: NarrativeResponse
    detail: dict[str, Any] | None = None
