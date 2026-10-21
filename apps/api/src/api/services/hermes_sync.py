"""Hermes compatibility wrappers for Wright gateway synchronization."""

from __future__ import annotations

from api.services.wright_gateway_sync import (
    sync_mcp_server_to_wright_gateway,
    sync_workspace_tools_to_wright_gateway,
    write_static_gateway_config,
)
from tool_registry import McpServer


def _write_static_hermes_config() -> bool:
    return write_static_gateway_config()


def sync_mcp_server_to_hermes(server: McpServer) -> None:
    sync_mcp_server_to_wright_gateway(server)


def sync_workspace_tools_to_hermes(session_id: str, db_path: str) -> None:
    sync_workspace_tools_to_wright_gateway(session_id, db_path)
