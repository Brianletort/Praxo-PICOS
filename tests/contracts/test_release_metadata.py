import json
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def release_version() -> str:
    return load_json(ROOT / "apps" / "desktop" / "package.json")["version"]


@pytest.mark.contract
def test_release_versions_are_aligned():
    desktop_version = release_version()
    root_version = load_json(ROOT / "package.json")["version"]
    pyproject_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]

    assert desktop_version == root_version == pyproject_version


@pytest.mark.contract
def test_install_script_pins_installs_to_the_release_version():
    install_script = (ROOT / "scripts" / "install.sh").read_text()
    version = release_version()

    assert f'PICOS_GIT_REF="${{PICOS_GIT_REF:-v{version}}}"' in install_script
    assert 'git checkout "$PICOS_GIT_REF"' in install_script


@pytest.mark.contract
def test_readme_uses_the_versioned_installer_url():
    readme = (ROOT / "README.md").read_text()
    version = release_version()
    installer_url = (
        f"https://raw.githubusercontent.com/Brianletort/Praxo-PICOS/v{version}/scripts/install.sh"
    )

    assert installer_url in readme
    assert re.search(r"curl -fsSL .*?/scripts/install\.sh \| bash", readme)
