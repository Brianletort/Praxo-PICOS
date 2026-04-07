from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

router = APIRouter()


@router.get("/api/config")
async def get_config() -> dict[str, Any]:
    from .manager import ConfigManager
    from .schema import PicosSettings

    settings = PicosSettings()
    settings.ensure_dirs()
    mgr = ConfigManager(settings)
    yaml_config = mgr.load_yaml()

    return {
        "config": {
            "vault_path": yaml_config.get("vault_path", str(settings.vault_path or "")),
            "mail_enabled": yaml_config.get("mail_enabled", settings.mail_enabled),
            "calendar_enabled": yaml_config.get("calendar_enabled", settings.calendar_enabled),
            "screen_enabled": yaml_config.get("screen_enabled", settings.screen_enabled),
            "documents_enabled": yaml_config.get("documents_enabled", settings.documents_enabled),
            "vault_enabled": yaml_config.get("vault_enabled", settings.vault_enabled),
            "llm_provider": yaml_config.get("llm_provider", settings.llm_provider),
            "llm_model": yaml_config.get("llm_model", settings.llm_model),
            "agent_zero_enabled": yaml_config.get("agent_zero_enabled", settings.agent_zero_enabled),
            "api_port": yaml_config.get("api_port", settings.api_port),
            "web_dev_port": yaml_config.get("web_dev_port", settings.web_dev_port),
            "mcp_port": yaml_config.get("mcp_port", settings.mcp_port),
            "qdrant_http_port": yaml_config.get("qdrant_http_port", settings.qdrant_http_port),
        }
    }


@router.post("/api/config")
async def save_config(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from .manager import ConfigManager
    from .schema import PicosSettings

    settings = PicosSettings()
    settings.ensure_dirs()
    mgr = ConfigManager(settings)

    existing = mgr.load_yaml()
    existing.update(body)
    mgr.save_yaml(existing)

    return {"status": "saved", "keys": list(body.keys())}


@router.patch("/api/config")
async def patch_config(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from .manager import ConfigManager
    from .schema import PicosSettings

    settings = PicosSettings()
    settings.ensure_dirs()
    mgr = ConfigManager(settings)

    existing = mgr.load_yaml()
    existing.update(body)
    mgr.save_yaml(existing)

    return {"status": "updated", "keys": list(body.keys())}


@router.post("/api/extract/run")
async def trigger_extraction() -> dict[str, Any]:
    """Manually trigger an extraction run."""
    try:
        from services.workers.src.praxo_picos_workers.orchestrator import run_extraction_cycle

        result = await run_extraction_cycle()
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)[:500]}
