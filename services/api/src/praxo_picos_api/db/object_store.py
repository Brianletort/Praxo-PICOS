from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.src.praxo_picos_api.models import (
    MemoryObject,
    ObjectType,
    Relationship,
    RelationshipType,
    deserialize,
)

from .models import MemoryObjectRecord, RelationshipRecord

logger = logging.getLogger(__name__)


class ObjectStore:
    """Typed CRUD for MemoryObjects backed by the memory_objects table.

    The user never interacts with this directly. It powers analytics,
    narrative generation, and the intelligence pipeline.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Object CRUD ──────────────────────────────────────────────

    async def put(self, obj: MemoryObject) -> str:
        """Insert or update a MemoryObject. Returns the object id."""
        row = self._to_row(obj)
        existing = await self._session.get(MemoryObjectRecord, obj.id)

        if existing is not None:
            for col in (
                "object_type", "source", "source_id", "title", "body",
                "timestamp", "attrs_json", "sensitivity", "retention_band",
                "confidence", "version", "parent_id", "updated_at",
            ):
                setattr(existing, col, getattr(row, col))
        else:
            self._session.add(row)

        await self._session.flush()
        return obj.id

    async def get(self, object_id: str) -> MemoryObject | None:
        """Retrieve a single MemoryObject by id."""
        row = await self._session.get(MemoryObjectRecord, object_id)
        if row is None:
            return None
        return self._from_row(row)

    async def query(
        self,
        object_type: ObjectType | None = None,
        source: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryObject]:
        """Query MemoryObjects with optional filters."""
        stmt = select(MemoryObjectRecord)

        if object_type is not None:
            stmt = stmt.where(MemoryObjectRecord.object_type == object_type.value)
        if source is not None:
            stmt = stmt.where(MemoryObjectRecord.source == source)
        if since is not None:
            stmt = stmt.where(MemoryObjectRecord.timestamp >= since)
        if until is not None:
            stmt = stmt.where(MemoryObjectRecord.timestamp <= until)

        stmt = stmt.order_by(MemoryObjectRecord.timestamp.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return [self._from_row(row) for row in result.scalars()]

    async def count(
        self,
        object_type: ObjectType | None = None,
        since: datetime | None = None,
    ) -> int:
        """Count MemoryObjects matching filters."""
        stmt = select(text("COUNT(*)")).select_from(MemoryObjectRecord)  # type: ignore[arg-type]
        if object_type is not None:
            stmt = stmt.where(MemoryObjectRecord.object_type == object_type.value)
        if since is not None:
            stmt = stmt.where(MemoryObjectRecord.timestamp >= since)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, object_id: str) -> bool:
        """Delete a MemoryObject. Returns True if it existed."""
        result = await self._session.execute(
            delete(MemoryObjectRecord).where(MemoryObjectRecord.id == object_id)
        )
        return (result.rowcount or 0) > 0

    # ── Relationship CRUD ────────────────────────────────────────

    async def put_relationship(self, rel: Relationship) -> str:
        """Insert or update a Relationship edge."""
        row = RelationshipRecord(
            id=rel.id,
            source_id=rel.source_id,
            target_id=rel.target_id,
            relationship_type=rel.relationship_type.value,
            attrs_json=json.dumps(rel.attrs) if rel.attrs else None,
            created_at=rel.created_at,
            updated_at=rel.updated_at,
        )
        existing = await self._session.get(RelationshipRecord, rel.id)
        if existing is not None:
            existing.attrs_json = row.attrs_json
            existing.updated_at = datetime.now(UTC)
        else:
            self._session.add(row)

        await self._session.flush()
        return rel.id

    async def get_relationships(
        self,
        object_id: str,
        relationship_type: RelationshipType | None = None,
        direction: str = "both",
    ) -> list[Relationship]:
        """Get relationships for an object. direction: 'outgoing', 'incoming', or 'both'."""
        conditions = []
        if direction in ("outgoing", "both"):
            conditions.append(RelationshipRecord.source_id == object_id)
        if direction in ("incoming", "both"):
            conditions.append(RelationshipRecord.target_id == object_id)

        from sqlalchemy import or_
        stmt = select(RelationshipRecord).where(or_(*conditions))

        if relationship_type is not None:
            stmt = stmt.where(
                RelationshipRecord.relationship_type == relationship_type.value
            )

        result = await self._session.execute(stmt)
        return [self._rel_from_row(row) for row in result.scalars()]

    # ── Conversion helpers ───────────────────────────────────────

    @staticmethod
    def _to_row(obj: MemoryObject) -> MemoryObjectRecord:
        return MemoryObjectRecord(
            id=obj.id,
            object_type=obj.object_type.value,
            source=obj.source.value,
            source_id=obj.source_id,
            title=obj.title,
            body=obj.body,
            timestamp=obj.timestamp,
            attrs_json=json.dumps(obj.attrs) if obj.attrs else None,
            sensitivity=obj.sensitivity.value,
            retention_band=obj.retention_band.value,
            confidence=obj.confidence,
            version=obj.version,
            parent_id=obj.parent_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    @staticmethod
    def _from_row(row: MemoryObjectRecord) -> MemoryObject:
        attrs = {}
        if row.attrs_json:
            try:
                attrs = json.loads(row.attrs_json)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse attrs_json for %s", row.id)

        data: dict[str, Any] = {
            "id": row.id,
            "object_type": row.object_type,
            "source": row.source,
            "source_id": row.source_id or "",
            "title": row.title,
            "body": row.body,
            "timestamp": row.timestamp,
            "attrs": attrs,
            "sensitivity": row.sensitivity,
            "retention_band": row.retention_band,
            "confidence": row.confidence or 1.0,
            "version": row.version or 1,
            "parent_id": row.parent_id,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        return deserialize(data)

    @staticmethod
    def _rel_from_row(row: RelationshipRecord) -> Relationship:
        attrs = {}
        if row.attrs_json:
            import contextlib

            with contextlib.suppress(json.JSONDecodeError, TypeError):
                attrs = json.loads(row.attrs_json)

        return Relationship(
            id=row.id,
            source_id=row.source_id,
            target_id=row.target_id,
            relationship_type=RelationshipType(row.relationship_type),
            attrs=attrs,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
