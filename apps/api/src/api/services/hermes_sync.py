"""Hermes compatibility wrappers for Wright gateway synchronization."""

from __future__ import annotations

import os

from agent_adapters.hermes_gateway import (
    hermes_config_paths,
    hermes_wright_gateway_profile,
)
from api.services.wright_gateway_sync import (
    sync_mcp_server_to_wright_gateway,
    sync_workspace_tools_to_wright_gateway,
    write_gateway_profile_config,
)
from tool_registry import McpServer

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, *[".."] * 5))


def _write_static_hermes_config() -> bool:
    repo_dir = os.getenv("WRIGHT_REPO_DIR", _REPO_ROOT)
    profile = hermes_wright_gateway_profile(repo_dir)
    return write_gateway_profile_config(profile, hermes_config_paths())


def sync_mcp_server_to_hermes(server: McpServer) -> None:
    sync_mcp_server_to_wright_gateway(server)


def sync_workspace_tools_to_hermes(session_id: str, db_path: str) -> None:
    sync_workspace_tools_to_wright_gateway(session_id, db_path)
