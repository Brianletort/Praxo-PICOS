from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from services.api.src.praxo_picos_api.db.engine import reset_engine
from services.api.src.praxo_picos_api.db.models import Base, ExtractedRecord, SourceType
from services.api.src.praxo_picos_api.mcp.server import create_mcp_server
from services.api.src.praxo_picos_api.search.hybrid import SearchResult


def _tool_fn(mcp, name: str):
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    return tools[name].fn


@pytest.fixture(autouse=True)
def _reset_engine_singleton():
    yield
    reset_engine()


@pytest.mark.unit
class TestMCPServer:
    def test_server_creates_successfully(self):
        mcp = create_mcp_server()
        assert mcp is not None
        assert mcp.name == "Praxo-PICOS"

    def test_server_has_required_tools(self):
        mcp = create_mcp_server()
        tool_names = {t.name for t in mcp._tool_manager.list_tools()}
        expected = {
            "health_check",
            "search_memory",
            "get_daily_brief",
            "list_sources",
            "get_source_status",
        }
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


@pytest.mark.contract
class TestMCPToolSchemas:
    def test_search_memory_has_query_param(self):
        mcp = create_mcp_server()
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        search = tools["search_memory"]
        schema = search.parameters
        assert "query" in schema.get("properties", {}), "search_memory must have 'query' parameter"

    def test_get_daily_brief_has_optional_date(self):
        mcp = create_mcp_server()
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        brief = tools["get_daily_brief"]
        schema = brief.parameters
        props = schema.get("properties", {})
        assert "date" in props, "get_daily_brief must have 'date' parameter"

    def test_all_tools_have_descriptions(self):
        mcp = create_mcp_server()
        for tool in mcp._tool_manager.list_tools():
            assert tool.description, f"Tool {tool.name} missing description"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_uses_api_health(mocker):
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.api_health",
        new_callable=AsyncMock,
        return_value={"status": "ok", "service": "praxo-picos-api"},
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "health_check")()
    assert out["status"] == "ok"
    assert out["service"] == "praxo-picos-api"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_degrades_on_error(mocker):
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.api_health",
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "health_check")()
    assert out["status"] == "error"
    assert "db down" in out["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_memory_returns_results(mocker):
    fake = SearchResult(
        record_id="r1",
        title="T",
        snippet="snip",
        source="mail",
        timestamp="",
        score=0.5,
        match_type="fts",
    )
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.HybridSearch.search",
        new_callable=AsyncMock,
        return_value=[fake],
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "search_memory")(query="hello", limit=5)
    assert out["total"] == 1
    assert out["results"][0]["record_id"] == "r1"
    assert out["query"] == "hello"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_memory_degrades_on_error(mocker):
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.HybridSearch.search",
        new_callable=AsyncMock,
        side_effect=Exception("fts failed"),
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "search_memory")(query="q")
    assert out["total"] == 0
    assert out.get("degraded") is True
    assert "fts failed" in out["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_daily_brief_invalid_date():
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "get_daily_brief")(date="bad-date")
    assert out.get("brief") is None
    assert "error" in out


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_daily_brief_from_db(mocker):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        at = datetime(2026, 1, 15, 14, 30, tzinfo=UTC)
        session.add(
            ExtractedRecord(
                source=SourceType.MAIL,
                source_id="m1",
                title="Meeting",
                body="Notes",
                timestamp=at,
            )
        )
        await session.commit()

    mocker.patch("services.api.src.praxo_picos_api.mcp.server.get_engine", return_value=engine)
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "get_daily_brief")(date="2026-01-15")
    assert out.get("record_count") == 1
    assert out.get("brief")
    assert "Meeting" in out["brief"]

    await engine.dispose()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_sources_reflects_settings(mocker):
    class _Settings:
        mail_enabled = True
        calendar_enabled = False
        screen_enabled = False
        documents_enabled = True
        vault_enabled = False

    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.get_settings",
        return_value=_Settings(),
    )
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.get_engine",
        side_effect=RuntimeError("no engine"),
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "list_sources")()
    assert len(out["sources"]) == 5
    by_name = {s["name"]: s for s in out["sources"]}
    assert by_name["mail"]["enabled"] is True
    assert by_name["calendar"]["enabled"] is False
    assert by_name["documents"]["enabled"] is True
    assert by_name["mail"]["status"] == "unknown"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_source_status_unknown_source():
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "get_source_status")(source_name="nope")
    assert "error" in out


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_source_status_uses_extractor_health(mocker):
    class _Settings:
        mail_enabled = True
        calendar_enabled = False
        screen_enabled = False
        documents_enabled = False
        vault_enabled = False
        screenpipe_port = 3030
        documents_path = None
        vault_path = None

    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.get_settings",
        return_value=_Settings(),
    )
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server.get_engine",
        side_effect=RuntimeError("no db"),
    )
    mock_ex = mocker.MagicMock()
    mock_ex.health_check = AsyncMock(return_value={"status": "ok", "path": "/mail"})
    mocker.patch(
        "services.api.src.praxo_picos_api.mcp.server._extractor_for_source",
        return_value=mock_ex,
    )
    mcp = create_mcp_server()
    out = await _tool_fn(mcp, "get_source_status")(source_name="mail")
    assert out["source"] == "mail"
    assert out["enabled"] is True
    assert out["status"] == "ok"
    assert out["health_check"]["path"] == "/mail"
