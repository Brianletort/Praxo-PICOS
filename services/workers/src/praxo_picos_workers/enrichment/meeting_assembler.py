"""Stage 2c: Meeting assembly from calendar + screenpipe data.

Merges calendar events with screen-detected meetings by time overlap.
Creates Meeting objects with attendees, transcript refs, and relationships.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.src.praxo_picos_api.db.models import SourceType
from services.api.src.praxo_picos_api.db.object_store import ObjectStore
from services.api.src.praxo_picos_api.models import (
    Meeting,
    ObjectType,
    Person,
    Relationship,
    RelationshipType,
)

from ..extractors.screenpipe_deep import ScreenpipeDeepConnector

logger = logging.getLogger(__name__)


class MeetingAssembler:
    """Combines calendar events and screen activity into Meeting objects."""

    def __init__(
        self,
        store: ObjectStore,
        screenpipe: ScreenpipeDeepConnector,
    ) -> None:
        self._store = store
        self._screenpipe = screenpipe

    async def assemble_recent(self, session: AsyncSession) -> int:
        """Find calendar events not yet assembled into meetings. Returns new meeting count."""
        cal_events = await self._store.query(
            object_type=ObjectType.CALENDAR_EVENT,
            since=datetime.now(UTC) - timedelta(days=7),
            limit=100,
        )

        existing_meetings = await self._store.query(
            object_type=ObjectType.MEETING,
            since=datetime.now(UTC) - timedelta(days=7),
            limit=200,
        )
        existing_source_ids = {m.source_id for m in existing_meetings if m.source_id}

        new_count = 0
        for event in cal_events:
            if event.source_id in existing_source_ids:
                continue

            meeting = await self._assemble_one(event)
            if meeting:
                await self._store.put(meeting)
                await self._link_attendees(meeting)
                new_count += 1

        try:
            screen_meetings = await self._screenpipe.detect_meetings(
                datetime.now(UTC) - timedelta(days=1),
                datetime.now(UTC),
            )
            for sm in screen_meetings:
                key = f"screen_{sm.start_time.isoformat()}"
                if key not in existing_source_ids and not self._overlaps_existing(
                    sm.start_time, sm.end_time, existing_meetings
                ):
                    meeting = Meeting(
                        title=f"{sm.app_name} meeting",
                        source=SourceType.SCREEN,
                        source_id=key,
                        start_time=sm.start_time,
                        end_time=sm.end_time,
                        timestamp=sm.start_time,
                    )
                    await self._store.put(meeting)
                    new_count += 1
        except Exception:
            logger.warning("Screen meeting detection failed", exc_info=True)

        return new_count

    async def _assemble_one(self, event: Any) -> Meeting | None:
        """Create a Meeting from a calendar event."""
        attrs = event.attrs or {}
        start = event.timestamp
        end_str = attrs.get("end_time") or attrs.get("end")
        end = None
        if end_str:
            try:
                end = datetime.fromisoformat(str(end_str))
            except (ValueError, TypeError):
                pass
        if end is None:
            end = start + timedelta(hours=1)

        attendees_raw = attrs.get("attendees", [])
        if isinstance(attendees_raw, str):
            attendees_raw = [a.strip() for a in attendees_raw.split(",") if a.strip()]

        attendee_ids: list[str] = []
        people = await self._store.query(object_type=ObjectType.PERSON, limit=500)
        person_map = {p.id: p for p in people if isinstance(p, Person)}

        for name_or_email in attendees_raw:
            for person in person_map.values():
                if person.matches_name(str(name_or_email)):
                    attendee_ids.append(person.id)
                    break

        return Meeting(
            title=event.title or "Meeting",
            source=SourceType.CALENDAR,
            source_id=event.source_id,
            start_time=start,
            end_time=end,
            timestamp=start,
            attendee_ids=attendee_ids,
            location=attrs.get("location"),
        )

    async def _link_attendees(self, meeting: Meeting) -> None:
        for pid in meeting.attendee_ids:
            await self._store.put_relationship(Relationship(
                source_id=pid,
                target_id=meeting.id,
                relationship_type=RelationshipType.ATTENDED,
            ))

    @staticmethod
    def _overlaps_existing(
        start: datetime,
        end: datetime,
        existing: list[Any],
    ) -> bool:
        for m in existing:
            if not isinstance(m, Meeting):
                continue
            m_start = m.start_time
            m_end = m.end_time or (m_start + timedelta(hours=1))
            if start < m_end and end > m_start:
                return True
        return False
