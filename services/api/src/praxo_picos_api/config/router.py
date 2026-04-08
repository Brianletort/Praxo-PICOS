from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body

router = APIRouter()

VALID_PROVIDERS = {"openai", "anthropic", "openrouter", "ollama", "gemini"}


def _validate_config(body: dict[str, Any]) -> list[str]:
    errors = []

    if "vault_path" in body and body["vault_path"]:
        p = Path(body["vault_path"]).expanduser()
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"Cannot create vault path: {body['vault_path']}")

    if "documents_path" in body and body["documents_path"]:
        p = Path(body["documents_path"]).expanduser()
        if not p.exists():
            errors.append(f"Documents path does not exist: {body['documents_path']}")

    for port_key in ["api_port", "web_dev_port", "mcp_port", "qdrant_http_port"]:
        if port_key in body:
            try:
                port = int(body[port_key])
                if not (1024 <= port <= 65535):
                    errors.append(f"{port_key} must be between 1024 and 65535")
            except (TypeError, ValueError):
                errors.append(f"{port_key} must be a number")

    if "llm_provider" in body and body["llm_provider"] not in VALID_PROVIDERS:
        errors.append(f"Unknown provider: {body['llm_provider']}. Valid: {', '.join(sorted(VALID_PROVIDERS))}")

    return errors


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
            "documents_path": yaml_config.get("documents_path", str(settings.documents_path or "")),
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

    errors = _validate_config(body)
    if errors:
        return {"status": "validation_error", "errors": errors}

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

    errors = _validate_config(body)
    if errors:
        return {"status": "validation_error", "errors": errors}

    settings = PicosSettings()
    settings.ensure_dirs()
    mgr = ConfigManager(settings)

    existing = mgr.load_yaml()
    existing.update(body)
    mgr.save_yaml(existing)

    return {"status": "updated", "keys": list(body.keys())}


@router.post("/api/extract/run")
async def trigger_extraction() -> dict[str, Any]:
    try:
        from services.workers.src.praxo_picos_workers.orchestrator import run_extraction_cycle
        result = await run_extraction_cycle()
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)[:500]}


@router.post("/api/chat")
async def chat(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Simple chat endpoint that searches memory and returns a context-aware response."""
    query = body.get("message", "")
    if not query:
        return {"response": "Please ask me something about your work.", "sources": []}

    try:
        from ..db.engine import get_engine
        from ..search.hybrid import HybridSearch

        engine = get_engine()
        search = HybridSearch(engine=engine)
        results = await search.search(query=query, limit=5)

        if results:
            context_parts = [f"- {r.snippet[:200]}" for r in results]
            context = "\n".join(context_parts)
            response = f"Based on your data, here's what I found about \"{query}\":\n\n{context}"
            sources = [r.to_dict() for r in results]
        else:
            response = f"I don't have any information about \"{query}\" yet. Try enabling more data sources in Settings, or wait for the next extraction cycle."
            sources = []

        return {"response": response, "sources": sources}
    except Exception as e:
        return {"response": f"Search is temporarily unavailable: {str(e)[:200]}", "sources": []}
