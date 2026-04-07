from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExtractionRecord:
    source: str
    source_id: str
    title: str
    body: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "title": self.title,
            "body": self.body,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BaseExtractor(abc.ABC):
    """Base class for all data source extractors."""

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        ...

    @abc.abstractmethod
    async def extract(self, since: datetime | None = None) -> list[ExtractionRecord]:
        """Extract records from the source, optionally since a given timestamp."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check whether the source is accessible and return status info."""
        ...

    async def extract_safe(self, since: datetime | None = None) -> list[ExtractionRecord]:
        """Extract with error handling -- returns empty list on failure."""
        try:
            return await self.extract(since)
        except PermissionError:
            return []
        except Exception:
            return []
