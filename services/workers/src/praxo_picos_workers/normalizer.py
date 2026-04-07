from __future__ import annotations

from datetime import datetime

from .extractors.base import ExtractionRecord


def normalize_to_markdown(record: ExtractionRecord) -> str:
    """Convert an extraction record to a markdown document with frontmatter."""
    frontmatter = _build_frontmatter(record)
    body = _clean_body(record.body)
    title_line = f"# {record.title}" if record.title else ""

    parts = [frontmatter]
    if title_line:
        parts.append(title_line)
    if body:
        parts.append(body)

    return "\n\n".join(parts) + "\n"


def _build_frontmatter(record: ExtractionRecord) -> str:
    lines = ["---"]
    lines.append(f"source: {record.source}")
    lines.append(f"source_id: {record.source_id}")
    lines.append(f"timestamp: {record.timestamp.isoformat()}")

    for key, value in sorted(record.metadata.items()):
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, datetime):
            lines.append(f"{key}: {value.isoformat()}")
        else:
            safe_value = str(value).replace("\n", " ")
            lines.append(f"{key}: {safe_value}")

    lines.append("---")
    return "\n".join(lines)


def _clean_body(body: str) -> str:
    if not body:
        return ""
    return body.strip()


def records_to_markdown_batch(records: list[ExtractionRecord]) -> list[tuple[str, str]]:
    """Convert a batch of records to (filename, markdown) tuples."""
    results = []
    for record in records:
        filename = _generate_filename(record)
        markdown = normalize_to_markdown(record)
        results.append((filename, markdown))
    return results


def _generate_filename(record: ExtractionRecord) -> str:
    date_str = record.timestamp.strftime("%Y-%m-%d")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in (record.title or "untitled"))
    safe_title = safe_title.strip().replace(" ", "-")[:80]
    return f"{date_str}_{record.source}_{safe_title}.md"
