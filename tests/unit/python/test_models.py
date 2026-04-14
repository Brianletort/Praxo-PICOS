"""Tests for the typed object model (Phase 0A)."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from services.api.src.praxo_picos_api.db.models import SourceType
from services.api.src.praxo_picos_api.models import (
    ActionItem,
    Commitment,
    Decision,
    Insight,
    Meeting,
    MemoryObject,
    NarrativeResponse,
    ObjectType,
    Person,
    Relationship,
    RelationshipType,
    RetentionBand,
    SOURCE_TO_OBJECT_TYPE,
    Sensitivity,
    deserialize,
    get_model_class,
    registered_types,
)


class TestEnums:
    def test_object_type_values(self):
        assert ObjectType.MEETING == "meeting"
        assert ObjectType.PERSON == "person"
        assert ObjectType.EMAIL == "email"

    def test_source_to_object_type_mapping(self):
        assert SOURCE_TO_OBJECT_TYPE["mail"] == ObjectType.EMAIL
        assert SOURCE_TO_OBJECT_TYPE["calendar"] == ObjectType.CALENDAR_EVENT
        assert SOURCE_TO_OBJECT_TYPE["screen"] == ObjectType.SCREEN_CAPTURE

    def test_sensitivity_levels(self):
        assert Sensitivity.PUBLIC.value == "public"
        assert Sensitivity.RESTRICTED.value == "restricted"

    def test_retention_bands(self):
        assert RetentionBand.EPHEMERAL.value == "ephemeral"
        assert RetentionBand.EVERGREEN.value == "evergreen"


class TestMemoryObject:
    def test_defaults(self):
        obj = MemoryObject(
            object_type=ObjectType.EMAIL,
            source=SourceType.MAIL,
        )
        assert obj.id
        assert len(obj.id) == 32
        assert obj.sensitivity == Sensitivity.INTERNAL
        assert obj.retention_band == RetentionBand.DURABLE
        assert obj.confidence == 1.0
        assert obj.version == 1
        assert obj.attrs == {}

    def test_bump_version(self):
        obj = MemoryObject(
            object_type=ObjectType.EMAIL,
            source=SourceType.MAIL,
        )
        bumped = obj.bump_version()
        assert bumped.version == 2
        assert bumped.parent_id == obj.id
        assert bumped.updated_at >= obj.updated_at

    def test_attrs_extensible(self):
        obj = MemoryObject(
            object_type=ObjectType.INSIGHT,
            source=SourceType.SCREEN,
            attrs={"cognitive_energy": {"score": 0.82}},
        )
        assert obj.attrs["cognitive_energy"]["score"] == 0.82


class TestMeeting:
    def test_meeting_defaults(self):
        m = Meeting(title="Standup")
        assert m.object_type == ObjectType.MEETING
        assert m.source == SourceType.CALENDAR
        assert m.attendee_ids == []
        assert m.has_intelligence is False

    def test_duration(self):
        m = Meeting(
            start_time=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
            end_time=datetime(2026, 1, 1, 10, 30, tzinfo=UTC),
        )
        assert m.duration_minutes == 30.0

    def test_overall_score(self):
        m = Meeting(attrs={"scorecard": {"overall_score": 0.82}})
        assert m.overall_score == 0.82
        assert m.has_intelligence is True

    def test_no_score(self):
        m = Meeting()
        assert m.overall_score is None


class TestPerson:
    def test_display_name(self):
        p = Person(name="Sarah Chen", email="sarah@example.com")
        assert p.display_name == "Sarah Chen"

    def test_display_name_fallback(self):
        p = Person(email="sarah@example.com")
        assert p.display_name == "sarah@example.com"

    def test_matches_name(self):
        p = Person(name="Sarah Chen", aliases=["S. Chen"])
        assert p.matches_name("sarah")
        assert p.matches_name("S. Chen")
        assert not p.matches_name("bob")

    def test_relationship_trend(self):
        p = Person(attrs={"relationship_dynamics": {"trend": "cooling"}})
        assert p.relationship_trend == "cooling"

    def test_evergreen_retention(self):
        p = Person(name="Test")
        assert p.retention_band == RetentionBand.EVERGREEN


class TestRelationship:
    def test_create_edge(self):
        r = Relationship(
            source_id="abc",
            target_id="def",
            relationship_type=RelationshipType.WORKS_WITH,
            attrs={"tie_strength": 0.8},
        )
        assert r.source_id == "abc"
        assert r.attrs["tie_strength"] == 0.8


class TestRegistry:
    def test_get_model_class(self):
        assert get_model_class(ObjectType.MEETING) is Meeting
        assert get_model_class(ObjectType.PERSON) is Person
        assert get_model_class(ObjectType.EMAIL) is MemoryObject

    def test_registered_types(self):
        types = registered_types()
        assert ObjectType.MEETING in types
        assert ObjectType.PERSON in types

    def test_deserialize_meeting(self):
        data = {
            "object_type": "meeting",
            "source": "calendar",
            "title": "Design Review",
            "start_time": "2026-01-01T10:00:00+00:00",
        }
        obj = deserialize(data)
        assert isinstance(obj, Meeting)
        assert obj.title == "Design Review"

    def test_deserialize_unknown_type(self):
        data = {"object_type": "unknown_future_type", "source": "mail"}
        obj = deserialize(data)
        assert isinstance(obj, MemoryObject)


class TestNarrativeResponse:
    def test_defaults(self):
        n = NarrativeResponse(headline="Test")
        assert n.headline == "Test"
        assert n.trend == "stable"
        assert n.sentiment == "neutral"
        assert n.available_depth == []
