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

# Resolve repository root and default OpenSCAD path dynamically
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, *[".."] * 5))
_DEFAULT_OPENSCAD_PATH = os.path.join(_REPO_ROOT, "scripts", "openscad-headless.sh")


def sync_mcp_server_to_hermes(server: McpServer) -> None:
    """Sync an MCP server's active/inactive state to Hermes config.yaml files.

    Used when a server is toggled active/inactive or deleted.
    Skips execution during pytest runs.
    """
    if "pytest" in sys.modules:
        return

    # Try to get active workspace path to inject localized env variables
    workspace_path = None
    try:
        from api.config import DATABASE_PATH
        import sqlite3
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT local_path FROM engineering_workspaces ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            workspace_path = row["local_path"]
        conn.close()
    except Exception:
        pass

    tmp_dir = None
    if workspace_path:
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

    key_name = "".join(c.lower() for c in server.name if c.isalnum())
    if not key_name:
        key_name = server.server_id

    paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]

    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}

            if "mcp_servers" not in config:
                config["mcp_servers"] = {}

            if server.is_active:
                if server.type == "stdio":
                    if not server.command:
                        continue
                    args = []
                    if isinstance(server.command, list):
                        cmd = server.command[0]
                        if len(server.command) > 1:
                            args = server.command[1:]
                    else:
                        parsed = shlex.split(server.command)
                        cmd = parsed[0] if parsed else "echo"
                        args = parsed[1:] if len(parsed) > 1 else []

                    custom_env = server.env_vars or {}
                    srv_config: dict[str, Any] = {"command": cmd, "args": args}
                    
                    if tmp_dir:
                        srv_config["env"] = {
                            "TMPDIR": tmp_dir,
                            "TEMP": tmp_dir,
                            "TMP": tmp_dir,
                        }
                    else:
                        srv_config["env"] = {}

                    if key_name == "openscadgeometry" or "openscad" in key_name:
                        if "OPENSCAD_PATH" not in custom_env:
                            srv_config["env"]["OPENSCAD_PATH"] = os.environ.get(
                                "OPENSCAD_PATH", _DEFAULT_OPENSCAD_PATH
                            )
                        if tmp_dir and "MCP_TEMP_DIR" not in custom_env:
                            scad_temp_dir = os.path.join(tmp_dir, "openscad-mcp")
                            os.makedirs(scad_temp_dir, exist_ok=True)
                            srv_config["env"]["MCP_TEMP_DIR"] = scad_temp_dir

                    srv_config["env"].update(custom_env)
                    config["mcp_servers"][key_name] = srv_config

                elif server.type == "sse":
                    if not server.command or not isinstance(server.command, str):
                        continue
                    config["mcp_servers"][key_name] = {
                        "url": server.command,
                        "transport": "sse",
                    }
            else:
                for k in list(config["mcp_servers"].keys()):
                    if k == key_name or (
                        key_name == "openscadgeometry" and k == "openscad"
                    ):
                        del config["mcp_servers"][k]

            with open(path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

        except Exception as e:
            logger.error(
                "hermes_config_sync_failed", path=path, server=server.name, error=str(e)
            )


def sync_workspace_tools_to_hermes(session_id: str, db_path: str) -> None:
    """Sync a workspace's enabled tools to Hermes config.yaml.

    Rebuilds the mcp_servers section with only the tools enabled for this workspace.
    Used when workspace tools are toggled or workspace is activated.
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

    enabled_tools = get_workspace_enabled_tools(db_path, session_id)

    from tool_registry.db import get_servers

    all_servers = get_servers(db_path)

    paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]

    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}

            if "mcp_servers" not in config:
                config["mcp_servers"] = {}

            # Rebuild the mcp_servers section
            new_mcp_servers = {}
            for server in all_servers:
                key_name = "".join(c.lower() for c in server.name if c.isalnum())
                if not key_name:
                    key_name = server.server_id

                # Check if this server is globally active
                if not server.is_active:
                    continue

                # Check if this server is enabled in the workspace session
                is_enabled = True
                if enabled_tools is not None:
                    is_enabled = (server.name in enabled_tools) or (
                        server.server_id in enabled_tools
                    )

                if is_enabled:
                    if server.type == "stdio":
                        if not server.command:
                            continue
                        args = []
                        if isinstance(server.command, list):
                            cmd = server.command[0]
                            if len(server.command) > 1:
                                args = server.command[1:]
                        else:
                            parsed = shlex.split(server.command)
                            cmd = parsed[0] if parsed else "echo"
                            args = parsed[1:] if len(parsed) > 1 else []

                        custom_env = server.env_vars or {}
                        srv_config: dict[str, Any] = {"command": cmd, "args": args}
                        
                        # Set standard temp directory environment variables for all stdio servers
                        srv_config["env"] = {
                            "TMPDIR": tmp_dir,
                            "TEMP": tmp_dir,
                            "TMP": tmp_dir,
                        }

                        if key_name == "openscadgeometry" or "openscad" in key_name:
                            if "OPENSCAD_PATH" not in custom_env:
                                srv_config["env"]["OPENSCAD_PATH"] = os.environ.get(
                                    "OPENSCAD_PATH", _DEFAULT_OPENSCAD_PATH
                                )
                            if "MCP_TEMP_DIR" not in custom_env:
                                scad_temp_dir = os.path.join(tmp_dir, "openscad-mcp")
                                os.makedirs(scad_temp_dir, exist_ok=True)
                                srv_config["env"]["MCP_TEMP_DIR"] = scad_temp_dir

                        srv_config["env"].update(custom_env)
                        new_mcp_servers[key_name] = srv_config
                    elif server.type == "sse":
                        if not server.command or not isinstance(server.command, str):
                            continue
                        new_mcp_servers[key_name] = {
                            "url": server.command,
                            "transport": "sse",
                        }

            config["mcp_servers"] = new_mcp_servers
            with open(path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

        except Exception as e:
            logger.error(
                "hermes_workspace_sync_failed",
                path=path,
                session_id=session_id,
                error=str(e),
            )


def restart_hermes_background(workspace_path: str | None = None) -> None:
    """Restart Hermes WebUI in background to reload config.

    Non-blocking subprocess call. Failures are silently ignored.
    """
    if "pytest" in sys.modules:
        return

    # Try to resolve active workspace path dynamically if not passed
    if not workspace_path:
        try:
            from api.config import DATABASE_PATH
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT local_path FROM engineering_workspaces ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                workspace_path = row["local_path"]
            conn.close()
        except Exception:
            pass

    env_str = 'export HERMES_HOME="$HOME/.hermes/profiles/wright"'
    if workspace_path:
        tmp_dir = os.path.join(workspace_path, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        env_str += f' && export TMPDIR="{tmp_dir}" && export TEMP="{tmp_dir}" && export TMP="{tmp_dir}"'

    try:
        # Preemptively terminate any running process bound to port 8788
        # and wait a short duration to ensure the socket is fully released.
        kill_cmd = "fuser -k -n tcp 8788 || true"
        subprocess.run(kill_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0)
        import time
        time.sleep(0.5)
    except Exception:
        pass

    try:
        subprocess.Popen(
            f'{env_str} && $HOME/hermes-webui/ctl.sh stop && $HOME/hermes-webui/ctl.sh start 8788',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

