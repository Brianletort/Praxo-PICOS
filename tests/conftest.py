from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    path = Path(tempfile.mkdtemp(prefix="praxo-picos-test-"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_data_dir(temp_dir: Path) -> Path:
    data_dir = temp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def temp_vault(temp_dir: Path) -> Path:
    vault = temp_dir / "vault"
    for sub in ["00_inbox", "10_meetings", "20_teams-chat", "40_slides", "50_knowledge", "_context"]:
        (vault / sub).mkdir(parents=True, exist_ok=True)
    return vault
