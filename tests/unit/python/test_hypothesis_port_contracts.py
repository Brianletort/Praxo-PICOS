from hypothesis import given, strategies as st
import pytest

from packages.shared.src.praxo_picos_shared.runtime_contracts import RuntimeContracts


VALID_PORT_RANGE = st.integers(min_value=1024, max_value=65535)


@pytest.mark.unit
def test_all_ports_are_unique():
    c = RuntimeContracts()
    ports = [c.api_port, c.web_dev_port, c.web_runtime_port, c.mcp_port, c.qdrant_http_port, c.qdrant_grpc_port]
    assert len(ports) == len(set(ports)), f"Duplicate ports found: {ports}"


@pytest.mark.unit
def test_all_ports_in_valid_range():
    c = RuntimeContracts()
    for port in [c.api_port, c.web_dev_port, c.web_runtime_port, c.mcp_port, c.qdrant_http_port, c.qdrant_grpc_port]:
        assert 1024 <= port <= 65535, f"Port {port} out of valid range"


@pytest.mark.unit
@given(port=VALID_PORT_RANGE)
def test_valid_ports_are_always_positive(port: int):
    assert port > 0
