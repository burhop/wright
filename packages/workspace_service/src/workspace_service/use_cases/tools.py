from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

import yaml
from tool_registry import ApprovalContext

from data_vault import WorkspaceRepository

from ..models import WorkspaceToolState


class WorkspaceToolUseCases:
    def __init__(
        self,
        repository: WorkspaceRepository,
        installed_names: Callable[[], list[str]],
        default_for_session: Callable[[str], list[str] | None],
        servers: Callable[[], list[Any]],
    ) -> None:
        self.repository = repository
        self.installed_names = installed_names
        self.default_for_session = default_for_session
        self.servers = servers

    def list_by_workspace(self, workspace_id: str) -> WorkspaceToolState:
        enabled = self.repository.enabled_tools(workspace_id)
        if enabled is None:
            enabled = self.installed_names()
        workspace = self.repository.get_by_id(workspace_id)
        session_id = (
            str(workspace.get("session_id") or workspace_id)
            if workspace
            else workspace_id
        )
        return WorkspaceToolState(session_id=session_id, enabled_tools=enabled)

    def set_by_workspace(
        self, workspace_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        state = self.list_by_workspace(workspace_id)
        current = list(state.enabled_tools)
        if is_enabled and server_id not in current:
            current.append(server_id)
        elif not is_enabled and server_id in current:
            current.remove(server_id)
        self.repository.set_enabled_tools(workspace_id, current)
        return WorkspaceToolState(session_id=state.session_id, enabled_tools=current)

    def list_by_session(self, session_id: str) -> WorkspaceToolState:
        enabled = self.default_for_session(session_id)
        return WorkspaceToolState(
            session_id=session_id,
            enabled_tools=enabled if enabled is not None else self.installed_names(),
        )

    def set_by_session(
        self, session_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        state = self.list_by_session(session_id)
        current = list(state.enabled_tools)
        if is_enabled and server_id not in current:
            current.append(server_id)
        elif not is_enabled and server_id in current:
            current.remove(server_id)
        workspace = self.repository.get_by_session(session_id)
        if workspace:
            self.repository.set_enabled_tools(workspace["workspace_id"], current)
        return WorkspaceToolState(session_id=session_id, enabled_tools=current)

    async def status(
        self,
        workspace: dict[str, Any],
        *,
        mcp_engine: Any | None,
        config_paths: list[str],
    ) -> dict[str, Any]:
        workspace_id = workspace["workspace_id"]
        enabled = self.list_by_session(workspace["session_id"]).enabled_tools
        expected = [
            server
            for server in self.servers()
            if server.is_installed
            and (server.name in enabled or server.server_id in enabled)
        ]
        running: list[dict[str, Any]] = []
        failures: list[str] = []
        for server in expected:
            effective = server.status
            error_message = server.error_message
            runner = (
                getattr(mcp_engine, "_active_runners", {}).get(server.server_id)
                if mcp_engine
                else None
            )
            if runner and runner.is_running():
                effective, error_message = "active", None
            elif mcp_engine and server.status != "error":
                try:
                    await mcp_engine.start_server(
                        server.server_id,
                        workspace_dir=workspace["local_path"],
                        approval_context=ApprovalContext(
                            workspace_id=workspace_id,
                            workspace_approvals=set(server.approval_gates or []),
                        ),
                    )
                    runner = getattr(mcp_engine, "_active_runners", {}).get(
                        server.server_id
                    )
                    if runner and runner.is_running():
                        effective, error_message = "active", None
                except Exception as error:
                    effective, error_message = "error", str(error)
                    failures.append(f"{server.name}: {error}")
            running.append(
                {
                    "name": server.name,
                    "status": effective,
                    "error_message": error_message,
                }
            )

        config_loaded = False
        configured: set[str] = set()
        for path in config_paths:
            if not os.path.exists(path):
                continue
            try:
                with open(path, encoding="utf-8") as stream:
                    config = yaml.safe_load(stream) or {}
                configured = set((config.get("mcp_servers") or {}).keys())
                config_loaded = True
                break
            except (OSError, yaml.YAMLError):
                continue

        if expected and (not config_loaded or "wrightgateway" not in configured):
            return {
                "status": "mismatch",
                "message": "Workspace MCP tools are not connected through Wright gateway.",
                "running_mcps": running,
            }
        if failures:
            return {
                "status": "error",
                "message": "Failed to start workspace MCP server(s): "
                + "; ".join(failures),
                "running_mcps": running,
            }
        errors = [item for item in running if item["status"] == "error"]
        if errors:
            item = errors[0]
            return {
                "status": "error",
                "message": f"Cannot connect to MCP Server: {item['name']} ({item['error_message'] or 'Unknown error'})",
                "running_mcps": running,
            }
        inactive = [item["name"] for item in running if item["status"] != "active"]
        if inactive:
            return {
                "status": "warning",
                "message": "MCP server installed but not active: "
                + ", ".join(inactive),
                "running_mcps": running,
            }
        return {
            "status": "ok",
            "message": "MCP configuration is active and healthy.",
            "running_mcps": running,
        }
