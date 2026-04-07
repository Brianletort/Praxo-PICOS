import pytest
from httpx import ASGITransport, AsyncClient

from services.api.src.praxo_picos_api.main import app


@pytest.fixture(autouse=True)
def _reset_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXO_DATA_DIR", str(tmp_path))
    from services.api.src.praxo_picos_api.db.engine import reset_engine
    from services.api.src.praxo_picos_api.db.session import reset_session_factory

    reset_engine()
    reset_session_factory()
    yield
    reset_engine()
    reset_session_factory()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_sources_returns_all_five():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        names = {s["name"] for s in data["sources"]}
        assert names == {"mail", "calendar", "screen", "documents", "vault"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_source_status_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sources/mail")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "mail"
        assert "enabled" in data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_source_status_invalid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/sources/invalid")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_data_flow_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/data-flow")
        assert resp.status_code == 200
        data = resp.json()
        assert "data_flow" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_cors_headers_present():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:3100",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers
