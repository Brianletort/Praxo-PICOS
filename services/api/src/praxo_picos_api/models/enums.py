from __future__ import annotations

import enum


class ObjectType(enum.StrEnum):
    # Phase 0: raw capture types (mapped from ExtractedRecord)
    EMAIL = "email"
    CALENDAR_EVENT = "calendar_event"
    SCREEN_CAPTURE = "screen_capture"
    DOCUMENT = "document"
    VAULT_NOTE = "vault_note"

    # Phase 1: interpreted types (derived from enrichment)
    MEETING = "meeting"
    PERSON = "person"
    ACTION_ITEM = "action_item"
    DECISION = "decision"
    COMMITMENT = "commitment"
    INSIGHT = "insight"
    COGNITIVE_ENERGY = "cognitive_energy"

    # Phase 2+: extended domains (added as sources arrive)
    CONTENT_CONSUMED = "content_consumed"
    READING_SESSION = "reading_session"
    LEARNING_OBJECTIVE = "learning_objective"
    SLEEP_SESSION = "sleep_session"
    VITAL_SAMPLE = "vital_sample"
    WORKOUT = "workout"
    LOCATION_EVENT = "location_event"
    VISIT = "visit"
    TRANSACTION = "transaction"
    SUBSCRIPTION = "subscription"
    BILL = "bill"

    # Cross-cutting meta types
    NEGATIVE_EVIDENCE = "negative_evidence"
    CHANGE_EVENT = "change_event"
    INTERVENTION_RECORD = "intervention_record"


class Sensitivity(enum.StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class RetentionBand(enum.StrEnum):
    EPHEMERAL = "ephemeral"
    DURABLE = "durable"
    EVERGREEN = "evergreen"


class RelationshipType(enum.StrEnum):
    WORKS_WITH = "works_with"
    REPORTS_TO = "reports_to"
    MANAGES = "manages"
    COMMUNICATES_WITH = "communicates_with"
    PARTICIPATES_IN = "participates_in"
    ATTENDED = "attended"
    MENTIONED_IN = "mentioned_in"
    RELATED_TO = "related_to"


# Map legacy SourceType values to ObjectType for migration
SOURCE_TO_OBJECT_TYPE: dict[str, ObjectType] = {
    "mail": ObjectType.EMAIL,
    "calendar": ObjectType.CALENDAR_EVENT,
    "screen": ObjectType.SCREEN_CAPTURE,
    "documents": ObjectType.DOCUMENT,
    "vault": ObjectType.VAULT_NOTE,
}
