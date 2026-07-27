"""Agent-neutral Wright gateway synchronization helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import structlog
import yaml

from agent_adapters.config_merge import atomic_merge_yaml
from agent_adapters.gateway import WrightGatewayProfile
from agent_adapters.hermes_gateway import (
    hermes_config_paths,
    hermes_wright_gateway_profile,
)
from workspace_service.adapters.runtime import (
    get_active_gateway_session,
    get_workspace_by_session,
    set_active_gateway_session,
)
from tool_registry import McpServer

logger = structlog.get_logger(__name__)

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, *[".."] * 5))
_PRESERVED_GATEWAY_CONFIG_KEYS = (
    "env",
    "enabled",
    "tools",
    "timeout",
    "connect_timeout",
)


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
                existing_gateway = servers.get(profile.server_name)
                preserved_gateway = (
                    {
                        key: existing_gateway[key]
                        for key in _PRESERVED_GATEWAY_CONFIG_KEYS
                        if key in existing_gateway
                    }
                    if isinstance(existing_gateway, dict)
                    else {}
                )
                config["mcp_servers"] = {
                    **servers,
                    profile.server_name: {
                        **preserved_gateway,
                        **profile.mcp_server_config(),
                    },
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
    from api.notifications import notify_gateway_tool_change as notify

    notify()


def _configured_gateway_binding(config_path: str) -> tuple[str, str] | None:
    """Read an exact Wright gateway session/workspace binding from Hermes config."""
    path = Path(config_path).expanduser()
    if not path.exists():
        return None
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        gateway = config.get("mcp_servers", {}).get("wrightgateway", {})
        args = gateway.get("args", [])
        if not isinstance(args, list):
            return None
        session_index = args.index("--session-id") + 1
        workspace_index = args.index("--workspace-id") + 1
        session_id = str(args[session_index]).strip()
        workspace_id = str(args[workspace_index]).strip()
        if session_id and workspace_id:
            return session_id, workspace_id
    except (OSError, ValueError, IndexError, TypeError, AttributeError, yaml.YAMLError):
        return None
    return None


def _gateway_binding_session(
    db_path: str,
    requested_session_id: str,
    workspace_id: str,
    config_paths: list[str],
) -> str:
    """Keep a live gateway binding stable across chats in the same workspace."""
    candidates = [
        binding[0]
        for path in config_paths
        if (binding := _configured_gateway_binding(path)) and binding[1] == workspace_id
    ]
    persisted_session_id = get_active_gateway_session(db_path)
    if persisted_session_id:
        candidates.append(persisted_session_id)

    for candidate_session_id in candidates:
        candidate_workspace = get_workspace_by_session(db_path, candidate_session_id)
        if (
            candidate_workspace
            and str(candidate_workspace.get("workspace_id")) == workspace_id
        ):
            return candidate_session_id
    return requested_session_id


def write_workspace_gateway_context(
    db_path: str, workspace_path: str, profile: WrightGatewayProfile | None = None
) -> None:
    active_profile = profile or default_hermes_gateway_profile()
    if not active_profile.workspace_context_filename:
        return

    from workspace_service.adapters.runtime import write_workspace_agent_context

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
    config_paths: list[str] | None = None,
) -> bool:
    if "pytest" in sys.modules and config_paths is None:
        return False

    workspace = get_workspace_by_session(db_path, session_id)
    if not workspace:
        return False
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
    active_config_paths = config_paths or hermes_config_paths()
    if active_profile.provider_name == "hermes":
        gateway_project_dir = (
            active_profile.gateway_project_dir or active_profile.terminal_cwd
        )
        binding_session_id = _gateway_binding_session(
            db_path,
            session_id,
            str(workspace["workspace_id"]),
            active_config_paths,
        )
        active_profile = hermes_wright_gateway_profile(
            gateway_project_dir,
            session_id=binding_session_id,
            workspace_id=str(workspace["workspace_id"]),
            terminal_cwd=workspace_path,
        )
        set_active_gateway_session(db_path, binding_session_id)

    try:
        write_workspace_gateway_context(db_path, workspace_path, active_profile)
    except Exception as e:
        logger.warning("failed_to_write_workspace_context", error=str(e))

    changed = write_gateway_profile_config(active_profile, active_config_paths)
    notify_gateway_tool_change()
    return changed
