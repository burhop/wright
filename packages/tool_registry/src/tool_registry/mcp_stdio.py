from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp.server.stdio import stdio_server

from .gateway_service import GatewayService
from .mcp_server import create_mcp_server, initialization_options


@dataclass(frozen=True, slots=True)
class StdioGatewayBinding:
    session_id: str
    principal_id: str
    workspace_id: str


async def run_mcp_streams(
    service: GatewayService,
    binding: StdioGatewayBinding,
    read_stream: Any,
    write_stream: Any,
    *,
    raise_exceptions: bool = False,
) -> None:
    service.open_session(
        session_id=binding.session_id,
        principal_id=binding.principal_id,
        workspace_id=binding.workspace_id,
        transport="stdio",
    )
    server = create_mcp_server(service, binding.session_id)
    try:
        await server.run(
            read_stream,
            write_stream,
            initialization_options(server),
            raise_exceptions=raise_exceptions,
        )
    finally:
        await service.close_session(binding.session_id)


async def serve_stdio(
    service: GatewayService,
    binding: StdioGatewayBinding,
) -> None:
    """Serve one explicitly bound MCP process over official SDK STDIO.

    The SDK owns JSON-RPC framing and serialized stdout writes. Application
    diagnostics must remain on stderr through logging configuration.
    """
    async with stdio_server() as (read_stream, write_stream):
        await run_mcp_streams(service, binding, read_stream, write_stream)
