from pathlib import Path

import pytest

from services.api.src.praxo_picos_api.config.manager import ConfigManager
from services.api.src.praxo_picos_api.config.schema import PicosSettings


@pytest.mark.unit
class TestPicosSettings:
    def test_defaults_load_without_env(self):
        settings = PicosSettings(
            _env_file=None,
            data_dir=Path("/tmp/picos-test"),
            log_dir=Path("/tmp/picos-test/logs"),
        )
        assert settings.api_port == 8865
        assert settings.web_dev_port == 3100
        assert settings.mcp_port == 8870
        assert settings.mail_enabled is True
        assert settings.screen_enabled is False

    def test_db_url_uses_state_dir(self):
        settings = PicosSettings(
            _env_file=None,
            data_dir=Path("/tmp/picos-test"),
            log_dir=Path("/tmp/picos-test/logs"),
        )
        assert "picos.db" in settings.db_url
        assert "/tmp/picos-test/state/" in settings.db_url

    def test_ensure_dirs_creates_directories(self, tmp_path):
        settings = PicosSettings(
            _env_file=None,
            data_dir=tmp_path / "data",
            log_dir=tmp_path / "logs",
        )
        settings.ensure_dirs()
        assert settings.data_dir.exists()
        assert settings.state_dir.exists()
        assert settings.log_dir.exists()


@pytest.mark.unit
class TestConfigManager:
    def test_yaml_roundtrip(self, tmp_path):
        settings = PicosSettings(
            _env_file=None,
            data_dir=tmp_path / "data",
            log_dir=tmp_path / "logs",
        )
        settings.ensure_dirs()
        mgr = ConfigManager(settings)

        mgr.save_yaml({"llm_provider": "anthropic", "vault_path": "/my/vault"})
        loaded = mgr.load_yaml()
        assert loaded["llm_provider"] == "anthropic"
        assert loaded["vault_path"] == "/my/vault"

    def test_secrets_never_written_to_yaml(self, tmp_path):
        settings = PicosSettings(
            _env_file=None,
            data_dir=tmp_path / "data",
            log_dir=tmp_path / "logs",
        )
        settings.ensure_dirs()
        mgr = ConfigManager(settings)

        mgr.save_yaml({
            "llm_provider": "openai",
            "openai_api_key": "sk-secret-123",
            "anthropic_api_key": "ant-secret-456",
        })
        loaded = mgr.load_yaml()
        assert "openai_api_key" not in loaded
        assert "anthropic_api_key" not in loaded
        assert loaded["llm_provider"] == "openai"

    def test_parse_env_file_separates_secrets(self, tmp_path):
        env_file = tmp_path / ".env.local"
        env_file.write_text(
            "OPENAI_API_KEY=sk-test-123\n"
            "LLM_PROVIDER=anthropic\n"
            "PRAXO_API_PORT=9000\n"
            "CUSTOM_TOKEN=secret-tok\n"
            "# comment\n"
            "\n"
        )
        settings = PicosSettings(
            _env_file=None,
            data_dir=tmp_path / "data",
            log_dir=tmp_path / "logs",
        )
        mgr = ConfigManager(settings)
        normal, secrets = mgr.parse_env_file(env_file)

        assert "openai_api_key" in secrets
        assert "custom_token" in secrets
        assert "llm_provider" in normal
        assert "praxo_api_port" in normal

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        settings = PicosSettings(
            _env_file=None,
            data_dir=tmp_path / "data",
            log_dir=tmp_path / "logs",
        )
        mgr = ConfigManager(settings)
        assert mgr.load_yaml() == {}
