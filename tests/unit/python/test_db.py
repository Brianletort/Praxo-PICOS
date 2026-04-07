from __future__ import annotations

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.api.src.praxo_picos_api.db.models import (
    Base,
    ConfigEntry,
    DataFlowStatus,
    ExtractedRecord,
    SourceType,
)


@pytest_asyncio.fixture
async def in_memory_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_extracted_record(in_memory_session: AsyncSession):
    record = ExtractedRecord(
        source=SourceType.MAIL,
        source_id="msg-001",
        title="Test email",
        body="Hello world",
        timestamp=datetime.now(timezone.utc),
    )
    in_memory_session.add(record)
    await in_memory_session.commit()

    result = await in_memory_session.execute(
        select(ExtractedRecord).where(ExtractedRecord.source_id == "msg-001")
    )
    fetched = result.scalar_one()
    assert fetched.title == "Test email"
    assert fetched.source == SourceType.MAIL


@pytest.mark.unit
@pytest.mark.asyncio
async def test_data_flow_status_tracking(in_memory_session: AsyncSession):
    status = DataFlowStatus(
        source=SourceType.CALENDAR,
        status="ok",
        records_last_interval=42,
    )
    in_memory_session.add(status)
    await in_memory_session.commit()

    result = await in_memory_session.execute(
        select(DataFlowStatus).where(DataFlowStatus.source == SourceType.CALENDAR)
    )
    fetched = result.scalar_one()
    assert fetched.records_last_interval == 42
    assert fetched.status == "ok"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_config_entry_roundtrip(in_memory_session: AsyncSession):
    entry = ConfigEntry(key="llm_provider", value="anthropic")
    in_memory_session.add(entry)
    await in_memory_session.commit()

    result = await in_memory_session.execute(
        select(ConfigEntry).where(ConfigEntry.key == "llm_provider")
    )
    fetched = result.scalar_one()
    assert fetched.value == "anthropic"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_source_types_are_all_defined():
    expected = {"mail", "calendar", "screen", "documents", "vault"}
    actual = {s.value for s in SourceType}
    assert actual == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_records_same_source(in_memory_session: AsyncSession):
    now = datetime.now(timezone.utc)
    for i in range(5):
        in_memory_session.add(
            ExtractedRecord(
                source=SourceType.VAULT,
                source_id=f"note-{i}",
                title=f"Note {i}",
                timestamp=now,
            )
        )
    await in_memory_session.commit()

    result = await in_memory_session.execute(
        select(ExtractedRecord).where(ExtractedRecord.source == SourceType.VAULT)
    )
    records = result.scalars().all()
    assert len(records) == 5
