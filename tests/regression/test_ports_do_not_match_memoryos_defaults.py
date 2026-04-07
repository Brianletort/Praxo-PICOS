import pytest

from packages.shared.src.praxo_picos_shared.runtime_contracts import RuntimeContracts


MEMORYOS_PORTS = {8765, 3000, 7777}


@pytest.mark.regression
def test_praxo_ports_do_not_reuse_memoryos_defaults():
    contracts = RuntimeContracts()
    praxo_ports = {
        contracts.api_port,
        contracts.web_dev_port,
        contracts.web_runtime_port,
        contracts.mcp_port,
        contracts.qdrant_http_port,
        contracts.qdrant_grpc_port,
    }
    overlap = praxo_ports & MEMORYOS_PORTS
    assert not overlap, f"Port conflict with MemoryOS: {overlap}"
