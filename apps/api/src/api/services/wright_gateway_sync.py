"""Agent-neutral Wright gateway synchronization helpers."""

from __future__ import annotations

import os
import sys

import structlog

from agent_adapters.config_merge import atomic_merge_yaml
from agent_adapters.gateway import WrightGatewayProfile
from agent_adapters.hermes_gateway import (
    hermes_config_paths,
    hermes_wright_gateway_profile,
)
from core.workspace import (
    get_workspace_by_session,
    set_active_gateway_session,
)
from tool_registry import McpServer

logger = structlog.get_logger(__name__)

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, *[".."] * 5))


def default_hermes_gateway_profile(repo_dir: str | None = None) -> WrightGatewayProfile:
    return hermes_wright_gateway_profile(
        repo_dir or os.getenv("WRIGHT_REPO_DIR", _REPO_ROOT)
    )


def write_gateway_profile_config(
    profile: WrightGatewayProfile, config_paths: list[str]
) -> bool:
    config_changed = False

    for path in config_paths:
        try:

            def update(config: dict) -> None:
                servers = config.get("mcp_servers")
                if not isinstance(servers, dict):
                    servers = {}
                config["mcp_servers"] = {
                    **servers,
                    profile.server_name: profile.mcp_server_config(),
                }
                terminal = config.get("terminal")
                if not isinstance(terminal, dict):
                    terminal = {}
                config["terminal"] = {**terminal, **profile.terminal_config()}

            config_changed = atomic_merge_yaml(path, update) or config_changed
        except Exception as e:
            logger.error("failed_to_sync_gateway_config", path=path, error=str(e))
            config_changed = True

    return config_changed


def write_static_gateway_config(
    profile: WrightGatewayProfile | None = None,
    config_paths: list[str] | None = None,
) -> bool:
    active_profile = profile or default_hermes_gateway_profile()
    paths = config_paths or hermes_config_paths()
    return write_gateway_profile_config(active_profile, paths)


def notify_gateway_tool_change() -> None:
    logger.info("notifying_gateway_tool_change")
    from api.routers.gateway import notify_gateway_tool_change as notify

    notify()


def write_workspace_gateway_context(
    db_path: str, workspace_path: str, profile: WrightGatewayProfile | None = None
) -> None:
    active_profile = profile or default_hermes_gateway_profile()
    if not active_profile.workspace_context_filename:
        return

    from core.workspace import write_workspace_agent_context

    write_workspace_agent_context(
        db_path, workspace_path, active_profile.workspace_context_filename
    )


def sync_mcp_server_to_wright_gateway(
    server: McpServer, profile: WrightGatewayProfile | None = None
) -> None:
    if "pytest" in sys.modules:
        return
    write_static_gateway_config(profile)
    notify_gateway_tool_change()


def sync_workspace_tools_to_wright_gateway(
    session_id: str,
    db_path: str,
    profile: WrightGatewayProfile | None = None,
) -> None:
    if "pytest" in sys.modules:
        return

    workspace = get_workspace_by_session(db_path, session_id)
    if not workspace:
        return
    set_active_gateway_session(db_path, session_id)

    workspace_path = workspace["local_path"]
    tmp_dir = os.path.join(workspace_path, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    gitignore_path = os.path.join(workspace_path, ".gitignore")
    try:
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                lines = f.readlines()
            cleaned_lines = [line.strip() for line in lines]
            to_append = []
            if "tmp/" not in cleaned_lines and "/tmp/" not in cleaned_lines:
                to_append.append("tmp/")
                to_append.append("/tmp/")
            elif "tmp/" not in cleaned_lines:
                to_append.append("tmp/")
            elif "/tmp/" not in cleaned_lines:
                to_append.append("/tmp/")

            if to_append:
                with open(gitignore_path, "a") as f:
                    if lines and not lines[-1].endswith("\n"):
                        f.write("\n")
                    for item in to_append:
                        f.write(f"{item}\n")
        else:
            with open(gitignore_path, "w") as f:
                f.write("tmp/\n/tmp/\n")
    except Exception as e:
        logger.warning("failed_to_update_gateway_gitignore", error=str(e))

    active_profile = profile or default_hermes_gateway_profile()

    try:
        write_workspace_gateway_context(db_path, workspace_path, active_profile)
    except Exception as e:
        logger.warning("failed_to_write_workspace_context", error=str(e))

    write_static_gateway_config(active_profile)
    notify_gateway_tool_change()
