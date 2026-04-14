from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from services.api.src.praxo_picos_api.db.models import SourceType

from .base import MemoryObject, _utcnow
from .enums import ObjectType, RelationshipType, RetentionBand


class Person(MemoryObject):
    """A person in the user's network, resolved across data sources.

    Intelligence layers store results in attrs under well-known keys:
        attrs["communication_dynamic"]   -- how YOU communicate with this person
        attrs["relationship_dynamics"]   -- warming/cooling, frequency, decay
    """

    object_type: ObjectType = ObjectType.PERSON
    source: SourceType = SourceType.MAIL
    retention_band: RetentionBand = RetentionBand.EVERGREEN

    name: str = ""
    email: str | None = None
    aliases: list[str] = Field(default_factory=list)
    organization: str | None = None
    role: str | None = None
    importance_level: int = Field(default=0, ge=0, le=5)

    @property
    def display_name(self) -> str:
        return self.name or self.email or self.source_id or "Unknown"

    @property
    def relationship_trend(self) -> str | None:
        dynamics = self.attrs.get("relationship_dynamics")
        if isinstance(dynamics, dict):
            return dynamics.get("trend")
        return None

    def matches_name(self, query: str) -> bool:
        """Check if this person matches a name query (case-insensitive)."""
        q = query.lower().strip()
        if q in self.name.lower():
            return True
        if self.email and q in self.email.lower():
            return True
        return any(q in alias.lower() for alias in self.aliases)


class Relationship(BaseModel):
    """An edge between two MemoryObjects (typically Person <-> Person or Person <-> Meeting)."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    attrs: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    model_config = {"extra": "forbid"}
