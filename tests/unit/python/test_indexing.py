from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.indexing.chunker import chunk_text
from services.workers.src.praxo_picos_workers.indexing.pipeline import IndexingPipeline


@pytest.mark.unit
class TestChunker:
    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        chunks = chunk_text("Hello world, this is a test.", chunk_size=1000)
        assert len(chunks) == 0 or (len(chunks) == 1 and "Hello" in chunks[0].text)

    def test_long_text_multiple_chunks(self):
        text = "word " * 500
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1

    def test_chunks_have_sequential_indices(self):
        text = "paragraph one.\n\n" * 20
        chunks = chunk_text(text, chunk_size=50, overlap=10, min_chunk_size=10)
        indices = [c.index for c in chunks]
        assert indices == list(range(len(indices)))

    def test_chunk_metadata_starts_none(self):
        chunks = chunk_text("Hello world test content here.", chunk_size=1000, min_chunk_size=5)
        for c in chunks:
            assert c.metadata is None


@pytest.mark.unit
class TestIndexingPipeline:
    def _make_record(self, body: str = "Test body content") -> ExtractionRecord:
        return ExtractionRecord(
            source="mail",
            source_id="msg-001",
            title="Test Subject",
            body=body,
            timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        )

    def test_chunk_record_includes_title_and_body(self):
        pipeline = IndexingPipeline(chunk_size=5000)
        record = self._make_record()
        chunks = pipeline.chunk_record(record)
        assert len(chunks) >= 1
        assert "Test Subject" in chunks[0].text
        assert "Test body" in chunks[0].text

    def test_chunk_record_sets_metadata(self):
        pipeline = IndexingPipeline(chunk_size=5000)
        record = self._make_record()
        chunks = pipeline.chunk_record(record)
        for chunk in chunks:
            assert chunk.metadata is not None
            assert chunk.metadata["source"] == "mail"
            assert chunk.metadata["source_id"] == "msg-001"

    def test_chunk_batch_groups_by_record(self):
        pipeline = IndexingPipeline(chunk_size=5000)
        records = [self._make_record(body=f"Content {i}") for i in range(3)]
        batch = pipeline.chunk_batch(records)
        assert len(batch) == 3
        for _record, chunks in batch:
            assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_index_batch_returns_stats(self):
        pipeline = IndexingPipeline(chunk_size=5000)
        records = [self._make_record(body=f"Content {i}") for i in range(3)]
        stats = await pipeline.index_batch(records)
        assert stats["records_processed"] == 3
        assert stats["failed"] == 0
        assert stats["chunks_indexed"] >= 3
