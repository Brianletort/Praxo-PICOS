from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .schema import PicosSettings

logger = logging.getLogger(__name__)

SECRET_KEYS = frozenset({
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "admin_key",
    "telegram_bot_token",
})


class ConfigManager:
    def __init__(self, settings: PicosSettings | None = None):
        self.settings = settings or PicosSettings()
        self._yaml_path = self.settings.state_dir / "config.yaml"

    def load_yaml(self) -> dict[str, Any]:
        if not self._yaml_path.exists():
            return {}
        with open(self._yaml_path) as f:
            data = yaml.safe_load(f) or {}
        return data

    def save_yaml(self, data: dict[str, Any]) -> None:
        filtered = {k: v for k, v in data.items() if k not in SECRET_KEYS}
        self.settings.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self._yaml_path, "w") as f:
            yaml.safe_dump(filtered, f, default_flow_style=False)

    def parse_env_file(self, path: Path) -> tuple[dict[str, str], dict[str, str]]:
        """Parse a .env file and separate secrets from normal config.

        Returns (normal_config, secrets).
        """
        normal: dict[str, str] = {}
        secrets: dict[str, str] = {}

        if not path.exists():
            return normal, secrets

        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip().strip("'\"")

            if key in SECRET_KEYS or key.endswith("_key") or key.endswith("_token"):
                secrets[key] = value
            else:
                normal[key] = value

        return normal, secrets

    def import_env_file(self, path: Path) -> dict[str, Any]:
        """Import a .env.local file: save normal config to YAML, return secrets for Keychain."""
        normal, secrets = self.parse_env_file(path)
        if normal:
            existing = self.load_yaml()
            existing.update(normal)
            self.save_yaml(existing)
        return {
            "imported_config_keys": list(normal.keys()),
            "secrets_for_keychain": list(secrets.keys()),
            "secrets": secrets,
        }
