"""Contract tests verifying extraction output shapes."""
from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.normalizer import normalize_to_markdown

REQUIRED_RECORD_FIELDS = {"source", "source_id", "title", "body", "timestamp", "metadata"}


@pytest.mark.regression
class TestExtractionContracts:
    def _make_record(self, source: str) -> ExtractionRecord:
        return ExtractionRecord(
            source=source,
            source_id=f"{source}-test-001",
            title=f"Test {source} record",
            body=f"Body content for {source}",
            timestamp=datetime(2026, 4, 7, 12, 0, tzinfo=UTC),
            metadata={"test": True},
        )

    def test_extraction_record_has_required_fields(self):
        record = self._make_record("mail")
        d = record.to_dict()
        assert REQUIRED_RECORD_FIELDS.issubset(set(d.keys()))

    @pytest.mark.parametrize("source", ["mail", "calendar", "screen", "documents", "vault"])
    def test_each_source_normalizes_to_valid_markdown(self, source):
        record = self._make_record(source)
        md = normalize_to_markdown(record)
        assert md.startswith("---\n"), f"{source}: markdown must start with frontmatter"
        assert f"source: {source}" in md
        assert "---" in md[4:]

    @pytest.mark.parametrize("source", ["mail", "calendar", "screen", "documents", "vault"])
    def test_each_source_produces_filename(self, source):
        from services.workers.src.praxo_picos_workers.normalizer import records_to_markdown_batch

        record = self._make_record(source)
        batch = records_to_markdown_batch([record])
        assert len(batch) == 1
        filename, _ = batch[0]
        assert filename.endswith(".md")
        assert source in filename
