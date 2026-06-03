import time
import logging
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, Set
from .models import McpServer, McpTool
from .db import (
    get_server,
    get_servers,
    update_server,
    insert_tools,
    clear_server_tools
)
from .runners.base import BaseRunner
from .runners.stdio import StdioRunner
from .runners.sse import SseRunner

logger = logging.getLogger(__name__)

class McpEngine:
    """Manager class coordinating the lifecycle, database status, and JSON-RPC dispatch of active MCP servers."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._active_runners: Dict[str, BaseRunner] = {}
        self._webmcp_connections: Set[Any] = set()
        self._pending_webmcp_calls: Dict[str, asyncio.Future] = {}

    async def register_webmcp_connection(self, websocket: Any) -> None:
        """Register a new WebMCP WebSocket connection from the client browser."""
        self._webmcp_connections.add(websocket)
        logger.info("Registered WebMCP WebSocket connection. Total: %d", len(self._webmcp_connections))

    async def unregister_webmcp_connection(self, websocket: Any) -> None:
        """Unregister a WebMCP WebSocket connection on disconnect."""
        self._webmcp_connections.discard(websocket)
        logger.info("Unregistered WebMCP WebSocket connection. Total: %d", len(self._webmcp_connections))

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
            logger.error("Failed to process WebMCP WebSocket message: %s", e)


    async def start_server(self, server_id: str) -> McpServer:
        """Start an MCP server subprocess or remote SSE connection, query its tools, and sync with database."""
        server = get_server(self.db_path, server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} does not exist.")

        # If already running, stop first to restart cleanly
        if server_id in self._active_runners:
            await self.stop_server(server_id)

        runner: Optional[BaseRunner] = None
        if server.type == "stdio":
            if not server.command:
                raise ValueError("Command configuration is required for stdio server.")
            runner = StdioRunner(server.command)
        elif server.type == "sse":
            if not server.command or not isinstance(server.command, str):
                raise ValueError("Valid SSE URL string is required for sse server.")
            runner = SseRunner(server.command)
        elif server.type == "webmcp":
            # webmcp servers represent client-side DOM connections managed via websockets in apps/web.
            # They do not use a backend subprocess runner, but we update status to active.
            logger.info("Initializing WebMCP server placeholder state for %s", server.name)
            updated = update_server(
                self.db_path,
                server_id,
                {
                    "is_active": True,
                    "status": "active",
                    "error_message": None,
                    "updated_at": int(time.time())
                }
            )
            return updated
        else:
            raise ValueError(f"Unsupported server type: {server.type}")

        try:
            # Start runner
            await runner.start()
            self._active_runners[server_id] = runner

            # Retrieve tools list
            logger.info("Querying tools list from MCP server: %s", server.name)
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
                        created_at=now
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
                    "updated_at": int(time.time())
                }
            )
            return updated

        except Exception as e:
            logger.exception("Failed to start MCP server %s", server.name)
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
                    "updated_at": int(time.time())
                }
            )
            return updated

    async def stop_server(self, server_id: str) -> McpServer:
        """Stop an active MCP server runner and update DB state."""
        runner = self._active_runners.pop(server_id, None)
        if runner:
            try:
                await runner.stop()
            except Exception as e:
                logger.error("Error stopping runner for %s: %s", server_id, e)

        # Clear active tools from database
        clear_server_tools(self.db_path, server_id)

        updated = update_server(
            self.db_path,
            server_id,
            {
                "is_active": False,
                "status": "inactive",
                "error_message": None,
                "updated_at": int(time.time())
            }
        )
        return updated

    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool on an active MCP server."""
        server = get_server(self.db_path, server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} does not exist.")

        if server.type == "webmcp":
            if not self._webmcp_connections:
                raise RuntimeError("No active browser WebSocket connection found for WebMCP tool invocation.")
            
            call_id = f"webmcp-call-{uuid.uuid4()}"
            future = asyncio.get_running_loop().create_future()
            self._pending_webmcp_calls[call_id] = future
            
            payload = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": tool_name,
                "params": arguments
            }
            
            send_payload = json.dumps(payload)
            # Broadcast the tool call to all connected client WebMCP sockets
            for conn in list(self._webmcp_connections):
                try:
                    await conn.send_text(send_payload)
                except Exception as e:
                    logger.warning("Failed to send WebMCP payload to connection: %s", e)
                    
            try:
                # Wait for client response over WebSocket with a 30-second timeout
                response = await asyncio.wait_for(future, timeout=30.0)
                if "error" in response:
                    raise RuntimeError(f"WebMCP tool invocation failed: {response['error']}")
                return response.get("result", {})
            finally:
                self._pending_webmcp_calls.pop(call_id, None)

        runner = self._active_runners.get(server_id)
        if not runner or not runner.is_running():
            raise RuntimeError(f"MCP server '{server.name}' is not currently active.")

        return await runner.call_tool(tool_name, arguments)

    async def sync_active_servers(self) -> None:
        """Sync and restart all servers configured as active in the database."""
        servers = get_servers(self.db_path)
        for server in servers:
            if server.is_active:
                logger.info("Sync starting configured active server: %s", server.name)
                try:
                    await self.start_server(server.server_id)
                except Exception as e:
                    logger.error("Failed to automatically start server %s on sync: %s", server.name, e)

    async def shutdown(self) -> None:
        """Shutdown all active runners on cleanup."""
        active_ids = list(self._active_runners.keys())
        for sid in active_ids:
            try:
                await self.stop_server(sid)
            except Exception as e:
                logger.error("Error shutting down server %s: %s", sid, e)
