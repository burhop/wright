"""Hermes compatibility wrappers for Wright gateway synchronization."""

from __future__ import annotations

from agent_adapters.hermes_gateway import (
    hermes_config_paths,
)
from api.services.wright_gateway_sync import (
    default_hermes_gateway_profile,
    sync_mcp_server_to_wright_gateway,
    sync_workspace_tools_to_wright_gateway,
    write_gateway_profile_config,
)
from tool_registry import McpServer


def _write_static_hermes_config() -> bool:
    profile = default_hermes_gateway_profile()
    return write_gateway_profile_config(profile, hermes_config_paths())


def sync_mcp_server_to_hermes(server: McpServer) -> None:
    sync_mcp_server_to_wright_gateway(server)


def sync_workspace_tools_to_hermes(session_id: str, db_path: str) -> None:
    sync_workspace_tools_to_wright_gateway(session_id, db_path)
