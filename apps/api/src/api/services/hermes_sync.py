"""
Hermes config.yaml synchronization service.

Extracted from workspace.py and mcp.py routers to eliminate duplicate sync logic.
Handles syncing MCP server state and workspace tool enablement to Hermes config files.
"""

import os
import sys
import shlex
import subprocess
from typing import Any

import structlog
import yaml

from core.workspace import get_workspace_by_session, get_workspace_enabled_tools
from tool_registry import McpServer

logger = structlog.get_logger(__name__)

# Resolve repository root dynamically for local and container installs.
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, *[".."] * 5))


def _write_static_hermes_config() -> bool:
    """Writes the static wright-gateway configuration to config.yaml.
    Returns True if config changed or was newly created, False otherwise.
    """
    repo_dir = os.getenv("WRIGHT_REPO_DIR", _REPO_ROOT)
    new_mcp_servers = {
        "wrightgateway": {
            "command": "uv",
            "args": [
                "run",
                "--project",
                repo_dir,
                "python",
                "-m",
                "tool_registry.gateway"
            ]
        }
    }
    
    paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]
    
    config_changed = False
    for path in paths:
        if not os.path.exists(path):
            config_changed = True
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    yaml.safe_dump({
                        "mcp_servers": new_mcp_servers,
                        "terminal": {
                            "cwd": repo_dir
                        }
                    }, f, default_flow_style=False)
            except Exception as e:
                logger.error("Failed to write initial config", path=path, error=str(e))
            continue
            
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
            
            import copy
            new_config = copy.deepcopy(config)
            new_config["mcp_servers"] = new_mcp_servers
            
            if "terminal" not in new_config:
                new_config["terminal"] = {}
            new_config["terminal"]["cwd"] = repo_dir
            
            if config != new_config:
                config_changed = True
                with open(path, "w") as f:
                    yaml.safe_dump(new_config, f, default_flow_style=False)
        except Exception as e:
            logger.error("Failed to sync static config to Hermes", path=path, error=str(e))
            config_changed = True
            
    return config_changed


def sync_mcp_server_to_hermes(server: McpServer) -> None:
    """Sync an MCP server's active/inactive state.
    
    Under the gateway architecture, this writes the static gateway config
    and notifies connected gateways to refresh tools, avoiding process restarts.
    """
    if "pytest" in sys.modules:
        return
    _write_static_hermes_config()
    logger.info("notifying_gateway_tool_change")
    from api.routers.gateway import notify_gateway_tool_change
    notify_gateway_tool_change()


def sync_workspace_tools_to_hermes(session_id: str, db_path: str) -> None:
    """Sync a workspace's enabled tools.
    
    Under the gateway architecture, this writes the static gateway config,
    sets up workspace directory .gitignore / metadata, and notifies gateways of changes.
    """
    if "pytest" in sys.modules:
        return

    workspace = get_workspace_by_session(db_path, session_id)
    if not workspace:
        return

    workspace_path = workspace["local_path"]
    tmp_dir = os.path.join(workspace_path, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # Ensure tmp/ and /tmp/ are in .gitignore
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
        logger.warning("Failed to update .gitignore: %s", e)

    try:
        from core.workspace import write_workspace_hermes_md
        write_workspace_hermes_md(db_path, workspace_path)
    except Exception as e:
        logger.warning("Failed to write workspace .hermes.md during sync: %s", e)

    _write_static_hermes_config()
    logger.info("notifying_gateway_tool_change")
    from api.routers.gateway import notify_gateway_tool_change
    notify_gateway_tool_change()

