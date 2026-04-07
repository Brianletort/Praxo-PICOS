"""Performance baseline tests."""
import time
from datetime import UTC, datetime

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import ExtractionRecord
from services.workers.src.praxo_picos_workers.indexing.chunker import chunk_text
from services.workers.src.praxo_picos_workers.normalizer import normalize_to_markdown


@pytest.mark.performance
class TestPerformanceBaselines:
    def test_chunker_throughput(self):
        text = "word " * 10000
        start = time.perf_counter()
        for _ in range(100):
            chunk_text(text, chunk_size=500, overlap=100)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"Chunking 100x 50k chars took {elapsed:.2f}s (budget: 5s)"

    def test_normalizer_throughput(self):
        records = [
            ExtractionRecord(
                source="mail",
                source_id=f"perf-{i}",
                title=f"Email {i}",
                body="Body " * 200,
                timestamp=datetime(2026, 4, 7, tzinfo=UTC),
                metadata={"from": "test@example.com"},
            )
            for i in range(1000)
        ]
        start = time.perf_counter()
        for r in records:
            normalize_to_markdown(r)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Normalizing 1000 records took {elapsed:.2f}s (budget: 2s)"

    def test_search_result_serialization_throughput(self):
        from services.api.src.praxo_picos_api.search.hybrid import SearchResult

        results = [
            SearchResult(f"r{i}", f"Title {i}", "snippet", "mail", "2026-04-07", 0.9, "fts")
            for i in range(10000)
        ]
        start = time.perf_counter()
        for r in results:
            r.to_dict()
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Serializing 10k results took {elapsed:.2f}s (budget: 1s)"
