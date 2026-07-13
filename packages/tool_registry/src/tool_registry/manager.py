import time
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, Set
from core.logging import get_logger
from core.redaction import redact_command, redact_mapping, redact_text
from .models import McpServer, McpTool
from .db import get_server, get_servers, update_server, insert_tools, clear_server_tools
from .runners.base import BaseRunner
from .runners.stdio import StdioRunner
from .runners.sse import SseRunner
from .safety import ApprovalContext, McpSafetyPolicy, required_credentials
from .secrets import has_credentials
from .lifecycle import McpLifecycleCoordinator
from .lifecycle_adapters import DatabaseLifecycleAdapter

logger = get_logger(__name__)


class McpEngine:
    """Manager class coordinating the lifecycle, database status, and JSON-RPC dispatch of active MCP servers."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._active_runners: Dict[str, BaseRunner] = {}
        self._lifecycle_adapter = DatabaseLifecycleAdapter(db_path)
        self.lifecycle = McpLifecycleCoordinator(
            self._lifecycle_adapter.build_runner,
            publish_tools=self._lifecycle_adapter.publish_tools,
            publish_status=self._lifecycle_adapter.publish_status,
        )
        self._webmcp_connections: Set[Any] = set()
        self._pending_webmcp_calls: Dict[str, asyncio.Future] = {}

    async def register_webmcp_connection(self, websocket: Any) -> None:
        """Register a new WebMCP WebSocket connection from the client browser."""
        self._webmcp_connections.add(websocket)
        logger.info(
            "webmcp_connection_registered",
            total=len(self._webmcp_connections),
        )

    async def unregister_webmcp_connection(self, websocket: Any) -> None:
        """Unregister a WebMCP WebSocket connection on disconnect."""
        self._webmcp_connections.discard(websocket)
        logger.info(
            "webmcp_connection_unregistered",
            total=len(self._webmcp_connections),
        )

    async def handle_webmcp_message(self, message_str: str) -> None:
        """Process incoming WebSocket JSON-RPC messages and resolve pending tool call futures."""
        try:
            payload = json.loads(message_str)
            if not isinstance(payload, dict):
                return
            call_id = payload.get("id")
            if call_id and call_id in self._pending_webmcp_calls:
                future = self._pending_webmcp_calls[call_id]
                if not future.done():
                    future.set_result(payload)
        except Exception as e:
            logger.error("webmcp_message_process_failed", error=redact_text(e))

    async def start_server(
        self,
        server_id: str,
        workspace_dir: Optional[str] = None,
        *,
        approval_context: ApprovalContext | None = None,
    ) -> McpServer:
        server = get_server(self.db_path, server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} does not exist.")
        if server.type == "webmcp":
            return await self._start_server_legacy(
                server_id,
                workspace_dir,
                approval_context=approval_context,
            )
        try:
            await self.lifecycle.start(
                server_id,
                workspace_path=workspace_dir,
                approval_context=approval_context,
            )
            runner = self.lifecycle.runner_for(server_id)
            if runner is not None:
                self._active_runners[server_id] = runner
            return get_server(self.db_path, server_id)
        except Exception:
            updated = get_server(self.db_path, server_id)
            if updated is not None and updated.status == "error":
                return updated
            raise

    async def _start_server_legacy(
        self,
        server_id: str,
        workspace_dir: Optional[str] = None,
        *,
        approval_context: ApprovalContext | None = None,
    ) -> McpServer:
        """Start an MCP server subprocess or remote SSE connection, query its tools, and sync with database."""
        server = get_server(self.db_path, server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} does not exist.")

        credential_names = required_credentials(server)
        decision = McpSafetyPolicy().can_start(
            server,
            approval_context,
            credentials_configured=(
                has_credentials(server.server_id, credential_names)
                if credential_names
                else {}
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

        # If already running, stop first to restart cleanly
        if server_id in self._active_runners:
            await self.stop_server(server_id)

        runner: Optional[BaseRunner] = None
        import os

        if os.getenv("WRIGHT_TESTING") == "1":

            class MockRunner(BaseRunner):
                def __init__(self, command=None):
                    self.command = command
                    self._running = False

                async def start(self) -> None:
                    self._running = True

                async def stop(self) -> None:
                    self._running = False

                async def list_tools(self) -> list:
                    return []

                async def call_tool(
                    self, tool_name: str, arguments: Dict[str, Any]
                ) -> Dict[str, Any]:
                    return {}

                def is_running(self) -> bool:
                    return self._running

            runner = MockRunner(server.command)
        elif server.type == "stdio":
            if not server.command:
                raise ValueError("Command configuration is required for stdio server.")

            # Build env_vars: merge structured definitions with saved credentials
            from .secrets import read_secrets
            from .models import EnvVarDefinition

            env_vars: Dict[str, str] = {}

            if server.env_vars:
                if isinstance(server.env_vars, list):
                    # New format: list of EnvVarDefinition — load values from secrets store
                    from .secrets import value_for_credential

                    saved_creds = read_secrets(server_id)
                    for var_def in server.env_vars:
                        if isinstance(var_def, EnvVarDefinition):
                            value = value_for_credential(saved_creds, var_def.name)
                            if value:
                                env_vars[var_def.name] = value
                elif isinstance(server.env_vars, dict):
                    # Old format: dict[str, str] — use directly
                    env_vars = server.env_vars.copy()

            # Get workspace directory as a fallback if not provided
            if not workspace_dir:
                try:
                    import sqlite3

                    with sqlite3.connect(self.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT local_path FROM engineering_workspaces ORDER BY updated_at DESC LIMIT 1"
                        )
                        row = cursor.fetchone()
                        if row:
                            workspace_dir = row["local_path"]
                except Exception as e:
                    logger.warning(
                        "mcp_workspace_lookup_failed",
                        server_id=server_id,
                        error=redact_text(e),
                    )

            key_name = "".join(c.lower() for c in server.name if c.isalnum())
            if not key_name:
                key_name = server.server_id
            if key_name == "freecadengineering" or "freecad" in key_name:
                if "FREECAD_PATH" not in env_vars:
                    default_fc = os.environ.get("FREECAD_PATH")
                    if not default_fc:
                        if os.path.exists("/snap/bin/freecad.cmd"):
                            default_fc = "/snap/bin/freecad.cmd"
                        else:
                            default_fc = "/usr/local/bin/freecadcmd"
                    env_vars["FREECAD_PATH"] = default_fc
                if workspace_dir and "FREECAD_MCP_WORK_DIR" not in env_vars:
                    env_vars["FREECAD_MCP_WORK_DIR"] = os.path.join(
                        workspace_dir, "freecad_mcp_work"
                    )

            # Wrap with xvfb-run if we are headless, xvfb-run is available, and it is a CAD server
            import shutil

            is_headless = not os.environ.get("DISPLAY")
            xvfb_path = shutil.which("xvfb-run")
            is_cad_server = server.category == "cad" or any(
                x in key_name for x in ["cad", "openscad", "freecad", "blender"]
            )

            command = server.command
            if is_headless and xvfb_path and is_cad_server:
                logger.info(
                    "mcp_command_wrapped_with_xvfb",
                    server_name=server.name,
                )
                if isinstance(server.command, list):
                    command = [xvfb_path, "-a"] + server.command
                else:
                    import shlex

                    command = [xvfb_path, "-a"] + shlex.split(server.command)

            runner = StdioRunner(command, env=env_vars, cwd=workspace_dir)
        elif server.type == "sse":
            if not server.command or not isinstance(server.command, str):
                raise ValueError("Valid SSE URL string is required for sse server.")
            runner = SseRunner(server.command)
        elif server.type == "webmcp":
            # webmcp servers represent client-side DOM connections managed via websockets in apps/web.
            # They do not use a backend subprocess runner, but we update status to active.
            logger.info(
                "Initializing WebMCP server placeholder state for %s", server.name
            )
            updated = update_server(
                self.db_path,
                server_id,
                {
                    "is_active": True,
                    "status": "active",
                    "error_message": None,
                    "updated_at": int(time.time()),
                },
            )
            return updated
        else:
            raise ValueError(f"Unsupported server type: {server.type}")

        try:
            # Start runner
            await runner.start()
            self._active_runners[server_id] = runner

            # Retrieve tools list
            logger.info(
                "mcp_tools_list_query", server_id=server_id, server_name=server.name
            )
            tools_list = await runner.list_tools()

            # Format and insert tools into DB
            mcp_tools = []
            now = int(time.time())
            for t in tools_list:
                name = t.get("name")
                if not name:
                    continue
                mcp_tools.append(
                    McpTool(
                        tool_id=f"{server_id}:{name}",
                        server_id=server_id,
                        name=name,
                        description=t.get("description"),
                        input_schema=t.get("inputSchema", {}),
                        is_enabled=True,
                        created_at=now,
                    )
                )

            # Clear old tools and insert fresh discovered tools
            clear_server_tools(self.db_path, server_id)
            if mcp_tools:
                insert_tools(self.db_path, mcp_tools)

            # Update DB status
            updated = update_server(
                self.db_path,
                server_id,
                {
                    "is_active": True,
                    "status": "active",
                    "error_message": None,
                    "updated_at": int(time.time()),
                },
            )
            return updated

        except Exception as e:
            logger.exception(
                "mcp_server_start_failed",
                server_id=server_id,
                server_name=server.name,
                command=redact_command(server.command or []),
                error=redact_text(e),
            )
            if runner:
                try:
                    await runner.stop()
                except Exception:
                    pass
            self._active_runners.pop(server_id, None)

            # Clear discovered tools on failure
            clear_server_tools(self.db_path, server_id)

            # Update DB status with error message
            updated = update_server(
                self.db_path,
                server_id,
                {
                    "is_active": False,
                    "status": "error",
                    "error_message": str(e),
                    "updated_at": int(time.time()),
                },
            )
            return updated

    async def stop_server(self, server_id: str, update_db: bool = True) -> McpServer:
        server = get_server(self.db_path, server_id)
        if server and server.type == "webmcp":
            return await self._stop_server_legacy(server_id, update_db=update_db)
        await self.lifecycle.stop(server_id)
        self._active_runners.pop(server_id, None)
        return get_server(self.db_path, server_id)

    async def _stop_server_legacy(
        self, server_id: str, update_db: bool = True
    ) -> McpServer:
        """Stop an active MCP server runner and update DB state."""
        runner = self._active_runners.pop(server_id, None)
        if runner:
            try:
                await runner.stop()
            except Exception as e:
                logger.error(
                    "mcp_runner_stop_failed",
                    server_id=server_id,
                    error=redact_text(e),
                )

        if update_db:
            # Clear active tools from database
            clear_server_tools(self.db_path, server_id)

            updated = update_server(
                self.db_path,
                server_id,
                {
                    "is_active": False,
                    "status": "inactive",
                    "error_message": None,
                    "updated_at": int(time.time()),
                },
            )
            return updated
        return get_server(self.db_path, server_id)

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        approval_context: ApprovalContext | None = None,
    ) -> Dict[str, Any]:
        """Invoke a tool on an active MCP server."""
        server = get_server(self.db_path, server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} does not exist.")

        credential_names = required_credentials(server)
        decision = McpSafetyPolicy().can_call_tool(
            server,
            tool_name,
            approval_context,
            credentials_configured=(
                has_credentials(server.server_id, credential_names)
                if credential_names
                else {}
            ),
        )
        logger.info(
            "mcp_safety_evaluate",
            server_id=server_id,
            operation="call",
            tool_name=tool_name,
            allowed=decision.allowed,
            reason=decision.reason,
            arguments=redact_mapping(arguments),
        )
        if not decision.allowed:
            raise RuntimeError(decision.reason)

        if server.type == "webmcp":
            if not self._webmcp_connections:
                raise RuntimeError(
                    "No active browser WebSocket connection found for WebMCP tool invocation."
                )

            call_id = f"webmcp-call-{uuid.uuid4()}"
            future = asyncio.get_running_loop().create_future()
            self._pending_webmcp_calls[call_id] = future

            payload = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": tool_name,
                "params": arguments,
            }

            send_payload = json.dumps(payload)
            # Broadcast the tool call to all connected client WebMCP sockets
            for conn in list(self._webmcp_connections):
                try:
                    await conn.send_text(send_payload)
                except Exception as e:
                    logger.warning(
                        "webmcp_payload_send_failed",
                        server_id=server_id,
                        tool_name=tool_name,
                        error=redact_text(e),
                    )

            try:
                # Wait for client response over WebSocket with a 30-second timeout
                response = await asyncio.wait_for(future, timeout=30.0)
                if "error" in response:
                    raise RuntimeError(
                        f"WebMCP tool invocation failed: {response['error']}"
                    )
                return response.get("result", {})
            finally:
                self._pending_webmcp_calls.pop(call_id, None)

        return await self.lifecycle.call_tool(
            server_id,
            tool_name,
            arguments,
        )

    async def sync_active_servers(self) -> None:
        """Sync and restart all servers configured as active in the database."""
        servers = get_servers(self.db_path)
        for server in servers:
            if server.is_active:
                logger.info(
                    "mcp_sync_starting_active_server",
                    server_id=server.server_id,
                    server_name=server.name,
                )
                try:
                    await self.start_server(server.server_id)
                except Exception as e:
                    logger.error(
                        "mcp_sync_start_failed",
                        server_id=server.server_id,
                        server_name=server.name,
                        error=redact_text(e),
                    )

    async def shutdown(self) -> None:
        """Shutdown all active runners on cleanup."""
        await self.lifecycle.shutdown()
        self._active_runners.clear()
