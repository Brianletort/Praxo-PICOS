"""Entry point for running the MCP server standalone."""
from __future__ import annotations

import argparse

from .server import create_mcp_server, get_mcp_host, get_mcp_port


def main() -> None:
    parser = argparse.ArgumentParser(description="Praxo-PICOS MCP Server")
    parser.add_argument("--port", type=int, default=get_mcp_port())
    parser.add_argument("--host", type=str, default=get_mcp_host())
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse", "stdio"],
        default="streamable-http",
    )
    args = parser.parse_args()

    mcp = create_mcp_server(host=args.host, port=args.port)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
