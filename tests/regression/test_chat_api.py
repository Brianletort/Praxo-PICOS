import pytest
from httpx import ASGITransport, AsyncClient

from services.api.src.praxo_picos_api.main import app
from services.api.src.praxo_picos_api.search.hybrid import SearchResult


@pytest.fixture(autouse=True)
def _reset_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXO_DATA_DIR", str(tmp_path))
    from services.api.src.praxo_picos_api.db.engine import reset_engine

    reset_engine()
    yield
    reset_engine()


@pytest.mark.regression
@pytest.mark.asyncio
async def test_chat_retries_with_keyword_query_when_question_prompt_is_too_broad(mocker):
    queries: list[str] = []

    async def fake_search(self, query: str, limit: int = 5):
        queries.append(query)
        if query == "release verification document":
            return [
                SearchResult(
                    record_id="doc-1",
                    title="installer-check.txt",
                    snippet="Praxo release verification document",
                    source="documents",
                    timestamp="",
                    score=1.0,
                    match_type="fts",
                )
            ]
        return []

    mocker.patch("services.api.src.praxo_picos_api.search.hybrid.HybridSearch.search", new=fake_search)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/chat",
            json={"message": "What do you know about the release verification document?"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) == 1
    assert queries == [
        "What do you know about the release verification document?",
        "release verification document",
    ]
