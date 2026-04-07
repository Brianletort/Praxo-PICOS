"""Python mirror of self-healing engine for regression tests (see self-healing.js)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supervisor import ServiceSupervisor


class SelfHealingEngine:
    def __init__(self, supervisor: ServiceSupervisor) -> None:
        self._supervisor = supervisor
        self._running = False
        self._log: list[dict[str, str]] = []

    def start(self) -> None:
        self._running = True
        self._log_action("Self-healing engine started")

    def stop(self) -> None:
        self._running = False
        self._log_action("Self-healing engine stopped")

    def getLog(self) -> list[dict[str, str]]:
        return list(self._log)

    def _log_action(self, message: str) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
        }
        self._log.append(entry)
        if len(self._log) > 500:
            self._log = self._log[-250:]
