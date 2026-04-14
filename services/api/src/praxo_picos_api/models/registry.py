from __future__ import annotations

from typing import Any

from .base import MemoryObject
from .enums import ObjectType
from .episodes import ActionItem, Commitment, Decision, Insight, Meeting
from .people import Person

_REGISTRY: dict[ObjectType, type[MemoryObject]] = {
    ObjectType.MEETING: Meeting,
    ObjectType.PERSON: Person,
    ObjectType.ACTION_ITEM: ActionItem,
    ObjectType.DECISION: Decision,
    ObjectType.COMMITMENT: Commitment,
    ObjectType.INSIGHT: Insight,
}


def get_model_class(object_type: ObjectType) -> type[MemoryObject]:
    """Return the Pydantic model class for an ObjectType, falling back to MemoryObject."""
    return _REGISTRY.get(object_type, MemoryObject)


def register_model(object_type: ObjectType, model_class: type[MemoryObject]) -> None:
    """Register a custom model class for an ObjectType (used by domain extension modules)."""
    _REGISTRY[object_type] = model_class


def deserialize(data: dict[str, Any]) -> MemoryObject:
    """Deserialize a dict into the appropriate typed MemoryObject subclass."""
    raw_type = data.get("object_type", "")
    try:
        obj_type = ObjectType(raw_type)
    except ValueError:
        obj_type = ObjectType.DOCUMENT
        data = {**data, "object_type": obj_type.value}

    cls = get_model_class(obj_type)
    return cls.model_validate(data)


def registered_types() -> list[ObjectType]:
    """Return all ObjectTypes that have a dedicated model class."""
    return list(_REGISTRY.keys())
