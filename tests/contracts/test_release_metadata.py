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


@pytest.mark.contract
def test_desktop_internal_build_includes_standalone_next_runtime():
    desktop_package = load_json(ROOT / "apps" / "desktop" / "package.json")
    build_script = desktop_package["scripts"]["build"]
    extra_resources = desktop_package["build"]["extraResources"]

    assert "-c.mac.hardenedRuntime=false" in build_script
    assert any(
        resource.get("from") == "../../apps/web/.next/standalone/node_modules"
        and resource.get("to") == "app/web-standalone/node_modules"
        for resource in extra_resources
    )


@pytest.mark.contract
def test_macos_release_workflow_attaches_installer_assets():
    workflow = (ROOT / ".github" / "workflows" / "macos-release.yml").read_text()

    assert "gh release upload" in workflow
    assert "dist/Praxo-PICOS.pkg" in workflow
    assert "dist/desktop/*.dmg" in workflow


@pytest.mark.contract
def test_mac_target_does_not_include_zip():
    desktop_package = load_json(ROOT / "apps" / "desktop" / "package.json")
    targets = desktop_package["build"]["mac"]["target"]

    assert "zip" not in targets, "zip target enables Squirrel auto-update distribution"
    assert "dmg" in targets


@pytest.mark.contract
def test_rebrand_frameworks_script_exists():
    script = ROOT / "packaging" / "rebrand_frameworks.sh"
    assert script.exists(), "rebrand_frameworks.sh needed to fix Squirrel identity in System Settings"
    text = script.read_text()
    assert "Praxo-PICOS Updater" in text
    assert "com.praxo.picos.updater" in text
