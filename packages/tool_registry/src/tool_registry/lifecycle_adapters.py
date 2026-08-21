from __future__ import annotations

import os
import shlex
import shutil
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from core.logging import get_logger  # type: ignore[import-untyped]

from .db import clear_server_tools, get_server, insert_tools, update_server
from .launch_templates import render_launch_configuration
from .models import EnvVarDefinition, McpTool
from .runners.base import BaseRunner, ProgressCallback
from .runners.sse import SseRunner
from .runners.stdio import StdioRunner
from .safety import ApprovalContext, McpSafetyPolicy, required_credentials
from .secrets import has_credentials, read_secrets, value_for_credential
from .wright_managed_servers import trusted_managed_launch_environment

logger = get_logger(__name__)


class EngineMcpUiResourceReader:
    def __init__(
        self,
        engine: Any,
        *,
        invalidate: Callable[..., int] | None = None,
    ) -> None:
        self.engine = engine
        self._invalidate = invalidate
        self._attached: set[str] = set()

    def set_invalidator(self, invalidate: Callable[..., int]) -> None:
        self._invalidate = invalidate

    def connection_id(self, server_id: str) -> str:
        return self.engine.child_connection_id(server_id)

    async def list_resources(self, server_id: str) -> Mapping[str, Any]:
        self._attach_notifications(server_id)
        return await self.engine.list_child_resources(server_id)

    async def list_resource_templates(self, server_id: str) -> Mapping[str, Any]:
        self._attach_notifications(server_id)
        return await self.engine.list_child_resource_templates(server_id)

    async def read_resource(self, server_id: str, uri: str) -> Mapping[str, Any]:
        self._attach_notifications(server_id)
        return await self.engine.read_child_resource(server_id, uri)

    async def subscribe_resource(self, server_id: str, uri: str) -> None:
        self._attach_notifications(server_id)
        await self.engine.subscribe_child_resource(server_id, uri)

    def _attach_notifications(self, server_id: str) -> None:
        connection_id = self.connection_id(server_id)
        if not connection_id or connection_id in self._attached:
            return
        runner = self.engine.lifecycle.runner_for(server_id)
        add_handler = getattr(runner, "add_notification_handler", None)
        if not callable(add_handler):
            return

        async def handle(method: str, params: Mapping[str, Any]) -> None:
            if self._invalidate is None:
                return
            if method == "notifications/resources/updated":
                uri = params.get("uri")
                self._invalidate(
                    server_connection_id=connection_id,
                    uri=str(uri) if isinstance(uri, str) else None,
                )
            elif method == "notifications/resources/list_changed":
                self._invalidate(server_connection_id=connection_id, uri=None)

        add_handler(handle)
        self._attached.add(connection_id)


class MockRunner(BaseRunner):
    def __init__(self, command: Any = None) -> None:
        self.command = command
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def list_tools(self) -> list[dict[str, Any]]:
        return []

    async def call_tool(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        return {}

    def is_running(self) -> bool:
        return self._running


class DatabaseLifecycleAdapter:
    def __init__(self, db_path: str, *, operation_timeout: float = 30.0) -> None:
        if operation_timeout <= 0:
            raise ValueError("operation_timeout must be positive")
        self.db_path = db_path
        self.operation_timeout = operation_timeout

    def build_runner(
        self,
        server_id: str,
        workspace_path: str | None,
        approval_context: ApprovalContext | None,
    ) -> BaseRunner:
        server = get_server(self.db_path, server_id)
        if server is None:
            raise ValueError(f"Server with ID {server_id} does not exist.")
        credentials = required_credentials(server)
        decision = McpSafetyPolicy().can_start(
            server,
            approval_context,
            credentials_configured=(
                has_credentials(server_id, credentials) if credentials else {}
            ),
        )
        logger.info(
            "mcp_safety_evaluate",
            server_id=server_id,
            operation="start",
            allowed=decision.allowed,
            reason=decision.reason,
        )
        if not decision.allowed:
            raise RuntimeError(decision.reason)
        if os.getenv("WRIGHT_TESTING") == "1":
            return MockRunner(server.command)
        if server.type == "stdio":
            if not server.command:
                raise ValueError("Command configuration is required for stdio server.")
            command, launch_env = render_launch_configuration(
                server.command,
                server.launch_env,
                workspace_path,
                server_id=server_id,
            )
            trusted_env = trusted_managed_launch_environment(
                server_id,
                workspace_path=workspace_path,
                database_path=self.db_path,
                binding={
                    "workspace_id": approval_context.workspace_id
                    if approval_context
                    else None,
                    "session_id": approval_context.session_id
                    if approval_context
                    else None,
                },
            )
            env = {
                **self._environment(server_id, server.env_vars),
                **launch_env,
                **trusted_env,
            }
            command = self._headless_command(server, command)
            return StdioRunner(
                command,
                env=env,
                cwd=workspace_path,
                operation_timeout=self.operation_timeout,
                ui_enabled=os.getenv("WRIGHT_SURFACES_MCP_APPS_ENABLED") == "1",
            )
        if server.type == "sse":
            if not server.command or not isinstance(server.command, str):
                raise ValueError("Valid SSE URL string is required for sse server.")
            return SseRunner(
                server.command,
                ui_enabled=os.getenv("WRIGHT_SURFACES_MCP_APPS_ENABLED") == "1",
                server_id=server_id,
            )
        raise ValueError(f"Unsupported coordinated server type: {server.type}")

    async def publish_tools(
        self, server_id: str, tools: Sequence[dict[str, Any]], generation: int
    ) -> None:
        clear_server_tools(self.db_path, server_id)
        now = int(time.time())
        records = [
            McpTool(
                tool_id=f"{server_id}:{tool['name']}",
                server_id=server_id,
                name=str(tool["name"]),
                title=tool.get("title") or (tool.get("annotations") or {}).get("title"),
                description=tool.get("description"),
                input_schema=tool.get("inputSchema", {}),
                output_schema=tool.get("outputSchema"),
                annotations=tool.get("annotations") or {},
                meta=tool.get("_meta") or {},
                is_enabled=True,
                created_at=now,
            )
            for tool in tools
            if tool.get("name")
        ]
        if records:
            insert_tools(self.db_path, records)

    async def publish_status(
        self, server_id: str, status: str, error: str | None, generation: int
    ) -> None:
        update_server(
            self.db_path,
            server_id,
            {
                "is_active": status == "active",
                "status": status,
                "error_message": error,
                "updated_at": int(time.time()),
            },
        )

    def _environment(self, server_id: str, definitions: Any) -> dict[str, str]:
        if isinstance(definitions, dict):
            return {str(key): str(value) for key, value in definitions.items()}
        if not isinstance(definitions, list):
            return {}
        saved = read_secrets(server_id)
        result: dict[str, str] = {}
        for definition in definitions:
            if isinstance(definition, EnvVarDefinition):
                value = value_for_credential(saved, definition.name)
                if value:
                    result[definition.name] = value
        return result

    def _headless_command(self, server: Any, command: Any) -> Any:
        key = "".join(
            character.lower() for character in server.name if character.isalnum()
        )
        is_cad = server.category == "cad" or any(
            token in key for token in ("cad", "openscad", "freecad", "blender")
        )
        xvfb = shutil.which("xvfb-run") if not os.environ.get("DISPLAY") else None
        if not xvfb or not is_cad:
            return command
        arguments = command if isinstance(command, list) else shlex.split(command)
        return [xvfb, "-a", *arguments]
