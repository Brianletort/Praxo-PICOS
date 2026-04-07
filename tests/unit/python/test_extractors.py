from datetime import UTC, datetime
from pathlib import Path

import pytest

from services.workers.src.praxo_picos_workers.extractors.base import (
    BaseExtractor,
    ExtractionRecord,
)
from services.workers.src.praxo_picos_workers.extractors.documents import DocumentsExtractor
from services.workers.src.praxo_picos_workers.extractors.vault import VaultExtractor


@pytest.mark.unit
class TestExtractionRecord:
    def test_to_dict_includes_all_fields(self):
        record = ExtractionRecord(
            source="mail",
            source_id="msg-001",
            title="Test",
            body="Hello",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            metadata={"from": "test@example.com"},
        )
        d = record.to_dict()
        assert d["source"] == "mail"
        assert d["source_id"] == "msg-001"
        assert d["title"] == "Test"
        assert d["metadata"]["from"] == "test@example.com"
        assert "2026-01-01" in d["timestamp"]

    def test_to_dict_empty_metadata(self):
        record = ExtractionRecord(
            source="vault",
            source_id="note-1",
            title="Note",
            body="",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert record.to_dict()["metadata"] == {}


@pytest.mark.unit
class TestDocumentsExtractor:
    @pytest.mark.asyncio
    async def test_extracts_txt_files(self, tmp_path):
        (tmp_path / "hello.txt").write_text("Hello world")
        (tmp_path / "data.md").write_text("# Markdown")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")

        ext = DocumentsExtractor(watch_path=tmp_path)
        records = await ext.extract(since=datetime(2020, 1, 1, tzinfo=UTC))

        assert len(records) == 2
        names = {r.title for r in records}
        assert "hello.txt" in names
        assert "data.md" in names

    @pytest.mark.asyncio
    async def test_skips_unsupported_extensions(self, tmp_path):
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "binary.exe").write_bytes(b"\x00\x01")

        ext = DocumentsExtractor(watch_path=tmp_path)
        records = await ext.extract(since=datetime(2020, 1, 1, tzinfo=UTC))
        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_health_check_existing_dir(self, tmp_path):
        ext = DocumentsExtractor(watch_path=tmp_path)
        health = await ext.health_check()
        assert health["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_missing_dir(self):
        ext = DocumentsExtractor(watch_path=Path("/nonexistent/path"))
        health = await ext.health_check()
        assert health["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_returns_empty_for_missing_dir(self):
        ext = DocumentsExtractor(watch_path=Path("/nonexistent/path"))
        records = await ext.extract()
        assert records == []


@pytest.mark.unit
class TestVaultExtractor:
    @pytest.mark.asyncio
    async def test_extracts_markdown_files(self, tmp_path):
        (tmp_path / "note1.md").write_text("# My Note\nContent here")
        (tmp_path / "note2.md").write_text("# Another\nMore content")
        (tmp_path / "readme.txt").write_text("Not markdown")

        ext = VaultExtractor(vault_path=tmp_path)
        records = await ext.extract(since=datetime(2020, 1, 1, tzinfo=UTC))

        assert len(records) == 2
        assert all(r.source == "vault" for r in records)

    @pytest.mark.asyncio
    async def test_skips_generated_folder(self, tmp_path):
        gen_dir = tmp_path / "_picos_generated"
        gen_dir.mkdir()
        (gen_dir / "generated.md").write_text("Auto-generated")
        (tmp_path / "real.md").write_text("User note")

        ext = VaultExtractor(vault_path=tmp_path)
        records = await ext.extract(since=datetime(2020, 1, 1, tzinfo=UTC))

        assert len(records) == 1
        assert records[0].title == "real"

    @pytest.mark.asyncio
    async def test_write_to_vault(self, tmp_path):
        ext = VaultExtractor(vault_path=tmp_path)
        path = await ext.write_to_vault("test-brief.md", "# Daily Brief\n\nContent")

        assert path.exists()
        assert "_picos_generated" in str(path)
        assert path.read_text() == "# Daily Brief\n\nContent"

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self):
        ext = VaultExtractor(vault_path=None)
        health = await ext.health_check()
        assert health["status"] == "not_configured"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_vault(self):
        ext = VaultExtractor(vault_path=None)
        records = await ext.extract()
        assert records == []


@pytest.mark.unit
class TestBaseExtractorSafe:
    @pytest.mark.asyncio
    async def test_extract_safe_catches_permission_error(self):
        class FailExtractor(BaseExtractor):
            @property
            def source_name(self) -> str:
                return "fail"

            async def extract(self, since=None):
                raise PermissionError("no access")

            async def health_check(self):
                return {"status": "error"}

        ext = FailExtractor()
        result = await ext.extract_safe()
        assert result == []
