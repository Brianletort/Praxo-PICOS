import pytest
from httpx import ASGITransport, AsyncClient

from services.api.src.praxo_picos_api.main import app


@pytest.fixture(autouse=True)
def _reset_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXO_DATA_DIR", str(tmp_path))
    from services.api.src.praxo_picos_api.db.engine import reset_engine

    reset_engine()
    yield
    reset_engine()


@pytest.mark.regression
@pytest.mark.asyncio
async def test_detect_all_never_returns_500(monkeypatch):
    monkeypatch.setattr(
        "services.api.src.praxo_picos_api.detect.router._find_obsidian_vaults",
        lambda: [],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/detect/all")

    assert resp.status_code == 200
    data = resp.json()
    assert "obsidian" in data
    assert "documents" in data
    assert "suggestions" in data


@pytest.mark.regression
@pytest.mark.asyncio
async def test_detect_obsidian_handles_oserror(monkeypatch):
    def broken_find():
        raise OSError("Simulated filesystem error")

    monkeypatch.setattr(
        "services.api.src.praxo_picos_api.detect.router._find_obsidian_vaults",
        broken_find,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/detect/obsidian")

    assert resp.status_code != 500
