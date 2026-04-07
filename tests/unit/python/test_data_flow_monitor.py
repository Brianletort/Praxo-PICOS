from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from services.api.src.praxo_picos_api.db.models import (
    Base,
    DataFlowStatus,
    ExtractedRecord,
    SourceType,
)
from services.workers.src.praxo_picos_workers.data_flow_monitor import (
    FRESHNESS_SLAS,
    DataFlowMonitor,
    compute_status,
)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


@pytest.mark.unit
class TestComputeStatus:
    def test_none_returns_unknown(self):
        assert compute_status(None, timedelta(minutes=30)) == "unknown"

    def test_fresh_returns_ok(self):
        now = datetime(2026, 4, 7, 12, 0, tzinfo=UTC)
        last = now - timedelta(minutes=10)
        assert compute_status(last, timedelta(minutes=30), now) == "ok"

    def test_stale_returns_warning(self):
        now = datetime(2026, 4, 7, 12, 0, tzinfo=UTC)
        last = now - timedelta(minutes=45)
        assert compute_status(last, timedelta(minutes=30), now) == "warning"

    def test_very_stale_returns_error(self):
        now = datetime(2026, 4, 7, 12, 0, tzinfo=UTC)
        last = now - timedelta(hours=2)
        assert compute_status(last, timedelta(minutes=30), now) == "error"

    def test_naive_last_record_treated_as_utc(self):
        """SQLite returns naive datetimes; compare consistently against aware *now*."""
        now = datetime(2026, 4, 7, 12, 0, tzinfo=UTC)
        last_naive = datetime(2026, 4, 7, 11, 50)
        assert compute_status(last_naive, timedelta(minutes=30), now) == "ok"


@pytest.mark.unit
class TestDataFlowMonitor:
    @pytest.mark.asyncio
    async def test_check_all_with_no_records(self, session):
        monitor = DataFlowMonitor(enabled_sources={"mail", "calendar"})
        results = await monitor.check_all(session)
        assert "mail" in results
        assert "calendar" in results
        assert results["mail"]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_check_source_with_fresh_records(self, session):
        now = datetime.now(UTC)
        session.add(
            ExtractedRecord(
                source=SourceType.MAIL,
                source_id="msg-1",
                title="Test",
                body="Hello",
                timestamp=now - timedelta(minutes=5),
            )
        )
        await session.commit()

        monitor = DataFlowMonitor()
        result = await monitor.check_source(session, "mail")
        assert result["status"] == "ok"
        assert result["records_last_interval"] >= 1

    @pytest.mark.asyncio
    async def test_check_updates_data_flow_status_table(self, session):
        now = datetime.now(UTC)
        session.add(
            ExtractedRecord(
                source=SourceType.VAULT,
                source_id="note-1",
                title="Note",
                body="Content",
                timestamp=now - timedelta(minutes=10),
            )
        )
        await session.commit()

        monitor = DataFlowMonitor()
        await monitor.check_source(session, "vault")

        row = await session.execute(
            select(DataFlowStatus).where(DataFlowStatus.source == SourceType.VAULT)
        )
        status = row.scalar_one()
        assert status.status == "ok"
        assert status.records_last_interval >= 1

    def test_freshness_slas_defined_for_all_sources(self):
        for source in SourceType:
            assert source.value in FRESHNESS_SLAS, f"Missing SLA for {source.value}"
