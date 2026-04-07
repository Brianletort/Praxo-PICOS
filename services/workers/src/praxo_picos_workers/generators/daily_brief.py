from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..extractors.base import ExtractionRecord


class DailyBriefGenerator:
    """Generates a daily summary brief from extracted records.

    The generator collects recent records from all sources and
    produces a structured markdown brief. When an LLM is available,
    it synthesizes a narrative summary. Without an LLM, it produces
    a structured list-based brief.
    """

    def __init__(self, llm_fn: Any | None = None):
        self._llm_fn = llm_fn

    def generate(
        self,
        records: list[ExtractionRecord],
        date: datetime | None = None,
    ) -> str:
        target_date = date or datetime.now(timezone.utc)
        date_str = target_date.strftime("%Y-%m-%d")
        day_name = target_date.strftime("%A")

        by_source = self._group_by_source(records)
        sections = self._build_sections(by_source)

        brief_parts = [
            f"---",
            f"source: picos-generated",
            f"type: daily-brief",
            f"date: {date_str}",
            f"generated_at: {datetime.now(timezone.utc).isoformat()}",
            f"record_count: {len(records)}",
            f"---",
            f"",
            f"# Daily Brief — {day_name}, {date_str}",
            f"",
        ]

        if not records:
            brief_parts.append("*No data available for this period.*\n")
            return "\n".join(brief_parts)

        brief_parts.append(f"**{len(records)} items** across {len(by_source)} sources.\n")

        for section in sections:
            brief_parts.append(section)

        return "\n".join(brief_parts)

    def _group_by_source(
        self, records: list[ExtractionRecord]
    ) -> dict[str, list[ExtractionRecord]]:
        groups: dict[str, list[ExtractionRecord]] = {}
        for record in records:
            groups.setdefault(record.source, []).append(record)
        for key in groups:
            groups[key].sort(key=lambda r: r.timestamp, reverse=True)
        return groups

    def _build_sections(
        self, by_source: dict[str, list[ExtractionRecord]]
    ) -> list[str]:
        section_order = ["mail", "calendar", "screen", "documents", "vault"]
        source_titles = {
            "mail": "Email",
            "calendar": "Calendar",
            "screen": "Screen Activity",
            "documents": "Documents",
            "vault": "Vault Notes",
        }

        sections = []
        for source in section_order:
            if source not in by_source:
                continue
            items = by_source[source]
            title = source_titles.get(source, source.title())
            section = f"## {title} ({len(items)} items)\n\n"

            for item in items[:10]:
                time_str = item.timestamp.strftime("%H:%M")
                title_text = item.title or "(untitled)"
                section += f"- **{time_str}** — {title_text}\n"

            if len(items) > 10:
                section += f"- *...and {len(items) - 10} more*\n"

            section += "\n"
            sections.append(section)

        return sections

    def generate_filename(self, date: datetime | None = None) -> str:
        target_date = date or datetime.now(timezone.utc)
        return target_date.strftime("%Y-%m-%d_daily-brief.md")
