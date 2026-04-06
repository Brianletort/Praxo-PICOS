from packages.shared.src.praxo_picos_shared.runtime_contracts import RuntimeContracts


def test_runtime_contracts_are_non_conflicting():
    contracts = RuntimeContracts()
    assert contracts.api_port == 8865
    assert contracts.web_dev_port == 3100
    assert contracts.web_runtime_port == 3777
    assert contracts.mcp_port == 8870


def test_praxo_ports_do_not_reuse_memoryos_defaults():
    contracts = RuntimeContracts()
    assert contracts.api_port != 8765
    assert contracts.web_dev_port != 3000
    assert contracts.web_runtime_port != 7777
