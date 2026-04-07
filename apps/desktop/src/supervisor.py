"""Python mirror of desktop service graph for regression tests (see supervisor.js)."""

from __future__ import annotations

from typing import Any

SERVICE_GRAPH: list[dict[str, Any]] = [
    {
        "name": "qdrant",
        "command": None,
        "healthUrl": "http://127.0.0.1:6733/healthz",
        "healthInterval": 10000,
        "dependsOn": [],
        "managed": False,
    },
    {
        "name": "api",
        "command": None,
        "healthUrl": "http://127.0.0.1:8865/health",
        "healthInterval": 10000,
        "dependsOn": ["qdrant"],
        "managed": True,
    },
    {
        "name": "workers",
        "command": None,
        "healthUrl": None,
        "healthInterval": 30000,
        "dependsOn": ["api", "qdrant"],
        "managed": True,
    },
    {
        "name": "web",
        "command": None,
        "healthUrl": "http://127.0.0.1:3777",
        "healthInterval": 15000,
        "dependsOn": ["api"],
        "managed": True,
    },
    {
        "name": "mcp",
        "command": None,
        "healthUrl": "http://127.0.0.1:8870/health",
        "healthInterval": 15000,
        "dependsOn": ["api"],
        "managed": True,
    },
    {
        "name": "agent-zero",
        "command": None,
        "healthUrl": "http://127.0.0.1:50001",
        "healthInterval": 30000,
        "dependsOn": ["api", "mcp"],
        "managed": False,
    },
]


class ServiceSupervisor:
    def __init__(self) -> None:
        self._services: dict[str, dict[str, Any]] = {}
        for svc in SERVICE_GRAPH:
            name = svc["name"]
            self._services[name] = {
                **svc,
                "status": "stopped",
                "pid": None,
                "lastHealthCheck": None,
                "restartCount": 0,
            }

    def getStatus(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name, svc in self._services.items():
            result[name] = {
                "name": svc["name"],
                "status": svc["status"],
                "pid": svc["pid"],
                "lastHealthCheck": svc["lastHealthCheck"],
                "restartCount": svc["restartCount"],
                "managed": svc["managed"],
            }
        return result

    def getStartOrder(self) -> list[str]:
        resolved: list[str] = []
        visited: set[str] = set()

        def resolve(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            svc = self._services.get(name)
            if not svc:
                return
            for dep in svc["dependsOn"]:
                resolve(dep)
            resolved.append(name)

        for name in self._services:
            resolve(name)
        return resolved
