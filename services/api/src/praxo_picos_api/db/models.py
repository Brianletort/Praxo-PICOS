from __future__ import annotations

import enum
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex


class Base(DeclarativeBase):
    pass


class SourceType(enum.StrEnum):
    MAIL = "mail"
    CALENDAR = "calendar"
    SCREEN = "screen"
    DOCUMENTS = "documents"
    VAULT = "vault"


class ExtractedRecord(Base):
    __tablename__ = "extracted_records"

    id = Column(String(32), primary_key=True, default=_new_id)
    source: Column[SourceType] = Column(Enum(SourceType), nullable=False, index=True)
    source_id = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_extracted_source_ts", "source", "timestamp"),
    )


class DataFlowStatus(Base):
    """Tracks freshness and health per data source."""

    __tablename__ = "data_flow_status"

    source: Column[SourceType] = Column(Enum(SourceType), primary_key=True)
    last_record_at = Column(DateTime(timezone=True), nullable=True)
    last_check_at = Column(DateTime(timezone=True), nullable=True)
    records_last_interval = Column(Integer, default=0)
    status = Column(String(20), default="unknown")
    error_message = Column(Text, nullable=True)


class ConfigEntry(Base):
    """Non-secret configuration stored in SQLite."""

    __tablename__ = "config_entries"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class SearchIndex(Base):
    """FTS5 shadow table for keyword search."""

    __tablename__ = "search_index"

    rowid = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(32), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)


class PerfBaseline(Base):
    """Stores performance baselines for regression detection."""

    __tablename__ = "perf_baselines"

    metric_name = Column(String(255), primary_key=True)
    p50_ms = Column(Float, nullable=False)
    p95_ms = Column(Float, nullable=False)
    p99_ms = Column(Float, nullable=True)
    measured_at = Column(DateTime(timezone=True), default=_utcnow)
    sample_count = Column(Integer, default=0)


class MemoryObjectRecord(Base):
    """Typed object store -- the interpreted layer above raw ExtractedRecord."""

    __tablename__ = "memory_objects"

    id = Column(String(32), primary_key=True, default=_new_id)
    object_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255), nullable=True)

    title = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)

    attrs_json = Column(Text, nullable=True)

    sensitivity = Column(String(20), default="internal", nullable=False)
    retention_band = Column(String(20), default="durable", nullable=False)
    confidence = Column(Float, default=1.0)

    version = Column(Integer, default=1)
    parent_id = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_memobj_type_ts", "object_type", "timestamp"),
        Index("ix_memobj_source_id", "source", "source_id"),
    )


class RelationshipRecord(Base):
    """Edge table connecting MemoryObjects."""

    __tablename__ = "relationships"

    id = Column(String(32), primary_key=True, default=_new_id)
    source_id = Column(String(32), nullable=False, index=True)
    target_id = Column(String(32), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False)
    attrs_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_rel_source_target", "source_id", "target_id"),
        Index("ix_rel_type", "relationship_type"),
    )


class ConsentRecord(Base):
    """Per-domain consent state managed via UI toggles."""

    __tablename__ = "consent_records"

    domain = Column(String(50), primary_key=True)
    status = Column(String(20), nullable=False, default="not_asked")
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ProcessingStatus(Base):
    """Tracks where each extracted record is in the enrichment pipeline."""

    __tablename__ = "processing_status"

    record_id = Column(String(32), primary_key=True)
    source = Column(String(50), nullable=False, index=True)
    promoted_at = Column(DateTime(timezone=True), nullable=True)
    enriched_at = Column(DateTime(timezone=True), nullable=True)
    intelligence_at = Column(DateTime(timezone=True), nullable=True)
    memory_object_id = Column(String(32), nullable=True)
    error = Column(Text, nullable=True)
