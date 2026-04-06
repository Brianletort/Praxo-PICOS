from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeContracts:
    api_port: int = 8865
    web_dev_port: int = 3100
    web_runtime_port: int = 3777
    mcp_port: int = 8870
    qdrant_http_port: int = 6733
    qdrant_grpc_port: int = 6734
