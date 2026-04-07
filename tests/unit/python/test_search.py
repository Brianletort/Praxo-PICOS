import pytest

from services.api.src.praxo_picos_api.search.hybrid import HybridSearch, SearchResult


@pytest.mark.unit
class TestSearchResult:
    def test_to_dict(self):
        r = SearchResult(
            record_id="abc123",
            title="Test",
            snippet="Hello world",
            source="mail",
            timestamp="2026-01-01T00:00:00",
            score=0.95,
            match_type="fts",
        )
        d = r.to_dict()
        assert d["record_id"] == "abc123"
        assert d["score"] == 0.95
        assert d["match_type"] == "fts"


@pytest.mark.unit
class TestHybridSearchMerge:
    def test_merge_deduplicates_by_record_id(self):
        hs = HybridSearch.__new__(HybridSearch)
        fts = [
            SearchResult("a", "T1", "S1", "mail", "", 0.9, "fts"),
            SearchResult("b", "T2", "S2", "mail", "", 0.8, "fts"),
        ]
        vector = [
            SearchResult("a", "T1", "S1", "mail", "", 0.95, "vector"),
            SearchResult("c", "T3", "S3", "vault", "", 0.7, "vector"),
        ]
        merged = hs._merge_results(fts, vector, limit=10)
        ids = [r.record_id for r in merged]
        assert len(ids) == 3
        assert len(set(ids)) == 3

    def test_merge_respects_limit(self):
        hs = HybridSearch.__new__(HybridSearch)
        fts = [
            SearchResult(f"r{i}", f"T{i}", "", "mail", "", 1.0 - i * 0.1, "fts")
            for i in range(10)
        ]
        merged = hs._merge_results(fts, [], limit=3)
        assert len(merged) == 3
