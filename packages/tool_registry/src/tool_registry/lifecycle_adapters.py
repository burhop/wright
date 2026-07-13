from __future__ import annotations

import os
import shlex
import shutil
import time
from collections.abc import Mapping, Sequence
from typing import Any

from core.logging import get_logger  # type: ignore[import-untyped]

from .db import clear_server_tools, get_server, insert_tools, update_server
from .models import EnvVarDefinition, McpTool
from .runners.base import BaseRunner
from .runners.sse import SseRunner
from .runners.stdio import StdioRunner
from .safety import ApprovalContext, McpSafetyPolicy, required_credentials
from .secrets import has_credentials, read_secrets, value_for_credential

logger = get_logger(__name__)


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
        self, tool_name: str, arguments: Mapping[str, Any]
    ) -> dict[str, Any]:
        return {}

    def is_running(self) -> bool:
        return self._running


class DatabaseLifecycleAdapter:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

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
            env = self._environment(server_id, server.env_vars)
            command = self._headless_command(server, server.command)
            return StdioRunner(command, env=env, cwd=workspace_path)
        if server.type == "sse":
            if not server.command or not isinstance(server.command, str):
                raise ValueError("Valid SSE URL string is required for sse server.")
            return SseRunner(server.command)
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
                description=tool.get("description"),
                input_schema=tool.get("inputSchema", {}),
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
