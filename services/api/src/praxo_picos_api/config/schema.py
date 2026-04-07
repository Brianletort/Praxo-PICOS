from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PicosSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PRAXO_",
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ports
    api_port: int = Field(default=8865)
    web_dev_port: int = Field(default=3100)
    web_runtime_port: int = Field(default=3777)
    mcp_port: int = Field(default=8870)
    qdrant_http_port: int = Field(default=6733)
    qdrant_grpc_port: int = Field(default=6734)

    # Data paths
    data_dir: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "PRAXO_DATA_DIR",
                os.path.expanduser("~/Library/Application Support/Praxo-PICOS"),
            )
        )
    )
    log_dir: Path = Field(
        default_factory=lambda: Path(
            os.environ.get(
                "PRAXO_LOG_DIR",
                os.path.expanduser("~/Library/Logs/Praxo-PICOS"),
            )
        )
    )
    vault_path: Path | None = Field(default=None)

    # Sources
    mail_enabled: bool = Field(default=True)
    calendar_enabled: bool = Field(default=True)
    screen_enabled: bool = Field(default=False)
    documents_enabled: bool = Field(default=False)
    vault_enabled: bool = Field(default=False)
    documents_path: Path | None = Field(default=None)

    # Screenpipe
    screenpipe_port: int = Field(default=3030)

    # LLM provider
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")

    # Agent Zero
    agent_zero_enabled: bool = Field(default=False)
    agent_zero_port: int = Field(default=50001)

    @property
    def state_dir(self) -> Path:
        return self.data_dir / "state"

    @property
    def db_path(self) -> Path:
        return self.state_dir / "picos.db"

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    def ensure_dirs(self) -> None:
        for d in [self.data_dir, self.state_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> PicosSettings:
    return PicosSettings()
