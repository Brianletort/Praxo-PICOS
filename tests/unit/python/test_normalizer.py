from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.normalizer import (
    normalize_to_markdown,
    records_to_markdown_batch,
)


@pytest.mark.unit
class TestNormalizer:
    def _make_record(self, **kwargs) -> ExtractionRecord:
        defaults = {
            "source": "mail",
            "source_id": "msg-001",
            "title": "Test Email",
            "body": "Hello world",
            "timestamp": datetime(2026, 4, 1, 10, 30, tzinfo=UTC),
            "metadata": {"from": "alice@example.com"},
        }
        defaults.update(kwargs)
        return ExtractionRecord(**defaults)

    def test_markdown_has_frontmatter(self):
        md = normalize_to_markdown(self._make_record())
        assert md.startswith("---\n")
        assert "source: mail" in md
        assert "source_id: msg-001" in md

    def test_markdown_has_title(self):
        md = normalize_to_markdown(self._make_record())
        assert "# Test Email" in md

    def test_markdown_has_body(self):
        md = normalize_to_markdown(self._make_record())
        assert "Hello world" in md

    def test_empty_body_produces_valid_markdown(self):
        md = normalize_to_markdown(self._make_record(body=""))
        assert md.startswith("---\n")
        assert "# Test Email" in md

    def test_empty_title_omits_heading(self):
        md = normalize_to_markdown(self._make_record(title=""))
        assert "# " not in md

    def test_metadata_list_values(self):
        record = self._make_record(metadata={"to": ["bob@example.com", "carol@example.com"]})
        md = normalize_to_markdown(record)
        assert "- bob@example.com" in md
        assert "- carol@example.com" in md

    def test_batch_produces_filenames(self):
        records = [self._make_record(), self._make_record(source="calendar", title="Meeting")]
        batch = records_to_markdown_batch(records)
        assert len(batch) == 2
        assert all(fn.endswith(".md") for fn, _ in batch)
        assert "mail" in batch[0][0]
        assert "calendar" in batch[1][0]

    def test_filename_sanitizes_special_chars(self):
        record = self._make_record(title="Re: Hello / World <test>")
        batch = records_to_markdown_batch([record])
        filename = batch[0][0]
        assert "/" not in filename.split("_", 2)[-1]
        assert "<" not in filename
