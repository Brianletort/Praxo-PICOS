import pytest
from httpx import ASGITransport, AsyncClient

from services.api.src.praxo_picos_api.db import engine as db_engine
from services.api.src.praxo_picos_api.main import app


@pytest.fixture(autouse=True)
def _isolated_praxo_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXO_DATA_DIR", str(tmp_path))
    db_engine.reset_engine()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "praxo-picos-api"
        assert "uptime_seconds" in data
        assert data["dependencies"]["sqlite"]["status"] == "ok"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readiness_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"


@pytest.mark.contract
def test_health_response_schema():
    """Contract: health response must contain required fields."""
    required_fields = {"status", "service", "uptime_seconds", "dependencies"}
    from services.api.src.praxo_picos_api.health import HealthResponse

    hr = HealthResponse(status="ok", service="test", uptime_seconds=1.0)
    result = hr.to_dict()
    assert required_fields.issubset(set(result.keys()))
