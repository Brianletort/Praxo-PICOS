from __future__ import annotations

import logging
from typing import Any

from ..extractors.base import ExtractionRecord
from .chunker import TextChunk, chunk_text

logger = logging.getLogger(__name__)


class IndexingPipeline:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_fn: Any | None = None,
    ):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._embedding_fn = embedding_fn

    def chunk_record(self, record: ExtractionRecord) -> list[TextChunk]:
        full_text = ""
        if record.title:
            full_text += record.title + "\n\n"
        if record.body:
            full_text += record.body

        chunks = chunk_text(
            full_text,
            chunk_size=self._chunk_size,
            overlap=self._chunk_overlap,
        )
        stripped = full_text.strip()
        if stripped and not chunks:
            chunks = [
                TextChunk(
                    text=stripped,
                    index=0,
                    start_char=0,
                    end_char=len(full_text),
                )
            ]

        for chunk in chunks:
            chunk.metadata = {
                "source": record.source,
                "source_id": record.source_id,
                "timestamp": record.timestamp.isoformat(),
            }

        return chunks

    def chunk_batch(
        self, records: list[ExtractionRecord]
    ) -> list[tuple[ExtractionRecord, list[TextChunk]]]:
        results = []
        for record in records:
            chunks = self.chunk_record(record)
            if chunks:
                results.append((record, chunks))
        return results

    async def index_record(self, record: ExtractionRecord) -> int:
        chunks = self.chunk_record(record)
        indexed = 0
        for chunk in chunks:
            try:
                if self._embedding_fn:
                    await self._embedding_fn(chunk.text)
                indexed += 1
            except Exception:
                logger.warning(
                    "Failed to index chunk %d for %s", chunk.index, record.source_id
                )
        return indexed

    async def index_batch(self, records: list[ExtractionRecord]) -> dict[str, int]:
        total_records = 0
        total_chunks = 0
        failed = 0

        for record in records:
            try:
                count = await self.index_record(record)
                total_records += 1
                total_chunks += count
            except Exception:
                failed += 1
                logger.warning("Failed to index record %s", record.source_id)

        return {
            "records_processed": total_records,
            "chunks_indexed": total_chunks,
            "failed": failed,
        }
