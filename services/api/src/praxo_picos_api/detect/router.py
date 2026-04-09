"""Auto-detection endpoints for smart onboarding and settings."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter

router = APIRouter()

HOME = Path.home()

OBSIDIAN_SEARCH_PATHS = [
    HOME / "Documents",
    HOME / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents",
    HOME / "Obsidian",
    HOME / "Desktop",
    HOME,
]


def _find_obsidian_vaults() -> list[dict[str, Any]]:
    vaults: list[dict[str, Any]] = []
    seen: set[str] = set()
    for base in OBSIDIAN_SEARCH_PATHS:
        if not base.exists():
            continue
        try:
            for p in base.iterdir():
                if not p.is_dir():
                    continue
                obsidian_dir = p / ".obsidian"
                if obsidian_dir.is_dir() and str(p) not in seen:
                    seen.add(str(p))
                    md_count = sum(1 for _ in p.rglob("*.md"))
                    vaults.append({
                        "path": str(p),
                        "name": p.name,
                        "note_count": md_count,
                    })
        except OSError:
            continue
    return vaults


@router.get("/api/detect/obsidian")
async def detect_obsidian() -> dict[str, Any]:
    try:
        vaults = _find_obsidian_vaults()
    except Exception:
        vaults = []
    suggested = vaults[0]["path"] if vaults else str(HOME / "Documents" / "Praxo-PICOS")
    return {"vaults": vaults, "suggested": suggested, "found": len(vaults) > 0}


@router.get("/api/detect/documents")
async def detect_documents() -> dict[str, Any]:
    docs = HOME / "Documents"
    exists = docs.exists()
    file_count = 0
    if exists:
        try:
            file_count = sum(1 for f in docs.iterdir() if f.is_file())
        except OSError:
            pass
    return {
        "path": str(docs),
        "exists": exists,
        "file_count": file_count,
        "suggested": str(docs),
    }


@router.get("/api/detect/screenpipe")
async def detect_screenpipe() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://127.0.0.1:3030/health")
            return {"installed": True, "running": resp.status_code < 400, "port": 3030}
    except Exception:
        installed = shutil.which("screenpipe") is not None
        return {"installed": installed, "running": False, "port": 3030}


@router.get("/api/detect/docker")
async def detect_docker() -> dict[str, Any]:
    docker_path = shutil.which("docker")
    if not docker_path:
        return {"installed": False, "running": False}
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5, text=True
        )
        return {"installed": True, "running": result.returncode == 0}
    except Exception:
        return {"installed": True, "running": False}


@router.get("/api/detect/agent-zero")
async def detect_agent_zero() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://127.0.0.1:50001")
            return {"running": resp.status_code < 400, "port": 50001, "url": "http://127.0.0.1:50001"}
    except Exception:
        return {"running": False, "port": 50001, "url": "http://127.0.0.1:50001"}


@router.get("/api/detect/all")
async def detect_all() -> dict[str, Any]:
    try:
        obsidian = _find_obsidian_vaults()
    except Exception:
        obsidian = []
    docs_path = HOME / "Documents"

    docker_installed = shutil.which("docker") is not None
    docker_running = False
    if docker_installed:
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            docker_running = r.returncode == 0
        except Exception:
            pass

    screenpipe_installed = shutil.which("screenpipe") is not None
    screenpipe_running = False
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get("http://127.0.0.1:3030/health")
            screenpipe_running = resp.status_code < 400
    except Exception:
        pass

    agent_zero_running = False
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get("http://127.0.0.1:50001")
            agent_zero_running = resp.status_code < 400
    except Exception:
        pass

    suggested_vault = obsidian[0]["path"] if obsidian else str(HOME / "Documents" / "Praxo-PICOS")

    return {
        "obsidian": {"vaults": obsidian, "found": len(obsidian) > 0},
        "documents": {"path": str(docs_path), "exists": docs_path.exists()},
        "screenpipe": {"installed": screenpipe_installed, "running": screenpipe_running},
        "docker": {"installed": docker_installed, "running": docker_running},
        "agent_zero": {"running": agent_zero_running},
        "suggestions": {
            "vault_path": suggested_vault,
            "documents_path": str(docs_path),
        },
    }
