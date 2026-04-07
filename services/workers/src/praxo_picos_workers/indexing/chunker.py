from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    index: int
    start_char: int
    end_char: int
    metadata: dict | None = None

    @property
    def char_count(self) -> int:
        return len(self.text)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 50,
) -> list[TextChunk]:
    if not text or not text.strip():
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            for sep in ["\n\n", "\n", ". ", " "]:
                boundary = text.rfind(sep, start, end)
                if boundary > start + min_chunk_size:
                    end = boundary + len(sep)
                    break

        chunk_text_str = text[start:end].strip()
        if len(chunk_text_str) >= min_chunk_size:
            chunks.append(
                TextChunk(
                    text=chunk_text_str,
                    index=index,
                    start_char=start,
                    end_char=end,
                )
            )
            index += 1

        if end >= len(text):
            break

        next_start = max(0, end - overlap)
        if chunks and next_start <= chunks[-1].start_char:
            next_start = chunks[-1].start_char + max(1, min_chunk_size // 2)
        if next_start <= start:
            next_start = start + max(1, min_chunk_size // 2)
        start = min(next_start, len(text))
        if start >= len(text):
            break

    return chunks
