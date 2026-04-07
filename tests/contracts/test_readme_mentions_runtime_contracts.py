from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.contract
def test_readme_mentions_praxo_ports():
    text = (ROOT / "README.md").read_text()
    assert "8865" in text, "README must mention API port 8865"
    assert "3100" in text, "README must mention web dev port 3100"
    assert "3777" in text, "README must mention web runtime port 3777"


@pytest.mark.contract
def test_readme_mentions_mcp_port():
    text = (ROOT / "README.md").read_text()
    assert "8870" in text, "README must mention MCP port 8870"


@pytest.mark.contract
def test_standards_docs_exist():
    standards = ROOT / "docs" / "standards"
    required = [
        "runtime-contracts.md",
        "testing-strategy.md",
        "data-quality-standards.md",
        "performance-budgets.md",
        "self-healing-policy.md",
    ]
    for doc in required:
        assert (standards / doc).exists(), f"Missing required doc: docs/standards/{doc}"
