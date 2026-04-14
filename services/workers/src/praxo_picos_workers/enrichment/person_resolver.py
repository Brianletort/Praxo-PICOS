"""Stage 2b: Cross-source person discovery and deduplication.

Discovers people from email headers, calendar attendees, transcript speakers,
and document mentions. Merges across sources using name/email matching.
"""
from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.src.praxo_picos_api.db.models import SourceType
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import (
    ObjectType,
    Person,
    Relationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


class PersonResolver:
    """Discovers and merges Person objects across data sources."""

    def __init__(self, store: ObjectStore) -> None:
        self._store = store
        self._cache: dict[str, Person] = {}

    async def resolve_from_recent(self, session: AsyncSession) -> int:
        """Scan recently promoted objects and discover people. Returns count of new people."""
        existing = await self._store.query(object_type=ObjectType.PERSON, limit=1000)
        for p in existing:
            if isinstance(p, Person):
                self._index_person(p)

        objects = await self._store.query(limit=500)
        new_count = 0

        for obj in objects:
            people_found = self._extract_people(obj)
            for name, email in people_found:
                person = self._find_match(name, email)
                if person is None:
                    person = Person(
                        name=name,
                        email=email,
                        source=obj.source,
                        source_id=email or name,
                        timestamp=obj.timestamp,
                    )
                    await self._store.put(person)
                    self._index_person(person)
                    new_count += 1

                    await self._store.put_relationship(Relationship(
                        source_id=obj.id,
                        target_id=person.id,
                        relationship_type=self._rel_type_for(obj.object_type),
                    ))

        return new_count

    def _extract_people(self, obj: Any) -> list[tuple[str, str]]:
        """Extract (name, email) pairs from an object's attrs and body."""
        people: list[tuple[str, str]] = []
        attrs = getattr(obj, "attrs", {}) or {}

        enrichment = attrs.get("llm_enrichment", {})
        for name in enrichment.get("people_mentioned", []):
            if isinstance(name, str) and len(name) > 1:
                people.append((name.strip(), ""))

        for field in ("sender", "from"):
            val = attrs.get(field, "")
            if val:
                name, email = self._parse_email_field(str(val))
                if name or email:
                    people.append((name, email))

        for field in ("recipients", "to", "cc", "attendees"):
            val = attrs.get(field, [])
            if isinstance(val, str):
                val = [v.strip() for v in val.split(",")]
            if isinstance(val, list):
                for entry in val:
                    name, email = self._parse_email_field(str(entry))
                    if name or email:
                        people.append((name, email))

        return people

    def _find_match(self, name: str, email: str) -> Person | None:
        if email:
            key = email.lower().strip()
            if key in self._cache:
                return self._cache[key]

        if name:
            key = name.lower().strip()
            if key in self._cache:
                return self._cache[key]

            for person in self._cache.values():
                if person.matches_name(name):
                    return person

        return None

    def _index_person(self, person: Person) -> None:
        if person.email:
            self._cache[person.email.lower().strip()] = person
        if person.name:
            self._cache[person.name.lower().strip()] = person
        for alias in person.aliases:
            self._cache[alias.lower().strip()] = person

    @staticmethod
    def _parse_email_field(raw: str) -> tuple[str, str]:
        emails = EMAIL_PATTERN.findall(raw)
        email = emails[0] if emails else ""
        name = EMAIL_PATTERN.sub("", raw).strip(" <>,\"'")
        return name, email

    @staticmethod
    def _rel_type_for(obj_type: ObjectType) -> RelationshipType:
        if obj_type == ObjectType.EMAIL:
            return RelationshipType.COMMUNICATES_WITH
        if obj_type in (ObjectType.CALENDAR_EVENT, ObjectType.MEETING):
            return RelationshipType.ATTENDED
        return RelationshipType.MENTIONED_IN
