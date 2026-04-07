"""Golden fixture tests: known input produces expected output shape."""
from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.normalizer import normalize_to_markdown


@pytest.mark.regression
class TestGoldenFixtures:
    def test_mail_golden_fixture(self):
        record = ExtractionRecord(
            source="mail",
            source_id="golden-mail-001",
            title="Q2 Budget Review",
            body="Please review the attached Q2 budget spreadsheet.",
            timestamp=datetime(2026, 4, 1, 9, 30, tzinfo=UTC),
            metadata={"from": "cfo@company.com", "to": ["team@company.com"]},
        )
        md = normalize_to_markdown(record)
        assert "source: mail" in md
        assert "Q2 Budget Review" in md
        assert "cfo@company.com" in md
        assert "team@company.com" in md

    def test_calendar_golden_fixture(self):
        record = ExtractionRecord(
            source="calendar",
            source_id="golden-cal-001",
            title="Weekly Standup",
            body="Discuss sprint progress and blockers",
            timestamp=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
            metadata={"location": "Conference Room A", "end_time": "2026-04-07T10:30:00+00:00"},
        )
        md = normalize_to_markdown(record)
        assert "source: calendar" in md
        assert "Weekly Standup" in md
        assert "Conference Room A" in md

    def test_empty_body_golden_fixture(self):
        record = ExtractionRecord(
            source="vault",
            source_id="golden-vault-001",
            title="Empty Note",
            body="",
            timestamp=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
        )
        md = normalize_to_markdown(record)
        assert "source: vault" in md
        assert "Empty Note" in md
        assert md.count("---") >= 2
