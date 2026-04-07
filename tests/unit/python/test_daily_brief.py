from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.generators.daily_brief import DailyBriefGenerator


def _make_record(source: str = "mail", title: str = "Test", hour: int = 9) -> ExtractionRecord:
    return ExtractionRecord(
        source=source,
        source_id=f"{source}-001",
        title=title,
        body="Some content",
        timestamp=datetime(2026, 4, 7, hour, 0, tzinfo=UTC),
    )


@pytest.mark.unit
class TestDailyBriefGenerator:
    def test_empty_records_produces_valid_brief(self):
        gen = DailyBriefGenerator()
        brief = gen.generate([], date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "Daily Brief" in brief
        assert "No data available" in brief
        assert brief.startswith("---\n")

    def test_brief_has_frontmatter(self):
        gen = DailyBriefGenerator()
        records = [_make_record()]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "source: picos-generated" in brief
        assert "type: daily-brief" in brief
        assert "date: 2026-04-07" in brief

    def test_brief_groups_by_source(self):
        gen = DailyBriefGenerator()
        records = [
            _make_record(source="mail", title="Email 1"),
            _make_record(source="calendar", title="Meeting"),
            _make_record(source="mail", title="Email 2"),
        ]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "## Email (2 items)" in brief
        assert "## Calendar (1 items)" in brief

    def test_brief_includes_time_and_title(self):
        gen = DailyBriefGenerator()
        records = [_make_record(title="Important Email", hour=14)]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "14:00" in brief
        assert "Important Email" in brief

    def test_brief_limits_items_per_source(self):
        gen = DailyBriefGenerator()
        records = [_make_record(title=f"Email {i}", hour=i) for i in range(15)]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "...and 5 more" in brief

    def test_brief_works_with_single_source(self):
        gen = DailyBriefGenerator()
        records = [_make_record(source="vault", title="My Note")]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "## Vault Notes" in brief
        assert "1 items" in brief

    def test_filename_format(self):
        gen = DailyBriefGenerator()
        name = gen.generate_filename(date=datetime(2026, 4, 7, tzinfo=UTC))
        assert name == "2026-04-07_daily-brief.md"

    def test_record_count_in_summary(self):
        gen = DailyBriefGenerator()
        records = [_make_record() for _ in range(5)]
        brief = gen.generate(records, date=datetime(2026, 4, 7, tzinfo=UTC))
        assert "5 items" in brief
        assert "1 sources" in brief
