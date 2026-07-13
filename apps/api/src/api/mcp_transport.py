from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import anyio
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from api.config import McpTransportSettings
from tool_registry.gateway_models import GatewayError
from tool_registry.mcp_server import create_mcp_server


@dataclass(frozen=True)
class HttpBinding:
    principal_id: str
    session_id: str
    workspace_id: str


class AuthenticatedMcpTransport:
    def __init__(self, service: Any, settings: McpTransportSettings, security: Any):
        self.service = service
        self.settings = settings
        self.security = security
        self._managers: dict[
            str, tuple[HttpBinding, StreamableHTTPSessionManager, str]
        ] = {}
        self._stop = anyio.Event()
        self._task_group: Any = None
        self._manager_lock = anyio.Lock()
        self._concurrency = anyio.Semaphore(settings.maximum_concurrency)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._rate_lock = anyio.Lock()

    @asynccontextmanager
    async def run(self):
        async with anyio.create_task_group() as group:
            self._task_group = group
            try:
                yield self
            finally:
                self._stop.set()
                group.cancel_scope.cancel()
                self._task_group = None

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self._error(scope, receive, send, 404, "Not found")
            return
        if self._task_group is None:
            await self._error(scope, receive, send, 503, "MCP transport unavailable")
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", ())
        }
        role = getattr(scope.get("state", {}), "principal_role", None)
        if role is None and isinstance(scope.get("state"), dict):
            role = scope["state"].get("principal_role")
        if self.security.enforced and role != "admin":
            await self._error(scope, receive, send, 401, "Authentication required")
            return
        session_id = headers.get("x-wright-session-id", "").strip()
        workspace_id = headers.get("x-wright-workspace-id", "").strip()
        if not session_id or not workspace_id:
            await self._error(
                scope,
                receive,
                send,
                400,
                "X-Wright-Session-Id and X-Wright-Workspace-Id are required",
            )
            return
        length = headers.get("content-length")
        if length and int(length) > self.settings.maximum_body_bytes:
            await self._error(
                scope, receive, send, 413, "MCP request body is too large"
            )
            return
        binding = HttpBinding("local-admin", session_id, workspace_id)
        if not await self._allow(binding.principal_id):
            await self._error(scope, receive, send, 429, "MCP request rate exceeded")
            return
        transport_session_id = headers.get("mcp-session-id")
        gateway_session_id: str
        if transport_session_id:
            record = self._managers.get(transport_session_id)
            if record is None or record[0] != binding:
                await self._error(scope, receive, send, 404, "Session not found")
                return
            _, manager, gateway_session_id = record
        else:
            try:
                manager, gateway_session_id = await self._new_manager(binding)
            except GatewayError as exc:
                await self._error(scope, receive, send, 409, str(exc))
                return
            except Exception:
                await self._error(
                    scope, receive, send, 400, "Invalid MCP workspace binding"
                )
                return
        captured_session_id: str | None = None

        async def bound_send(message) -> None:
            nonlocal captured_session_id
            if message.get("type") == "http.response.start":
                response_headers = {
                    key.decode("latin-1").lower(): value.decode("latin-1")
                    for key, value in message.get("headers", ())
                }
                captured_session_id = response_headers.get("mcp-session-id")
            await send(message)

        async with self._concurrency:
            await manager.handle_request(
                scope, self._bounded_receive(receive), bound_send
            )
        if captured_session_id:
            self._managers[captured_session_id] = (
                binding,
                manager,
                gateway_session_id,
            )
        if scope.get("method") == "DELETE" and transport_session_id:
            self._managers.pop(transport_session_id, None)
            await self.service.close_session(gateway_session_id)

    async def _new_manager(
        self, binding: HttpBinding
    ) -> tuple[StreamableHTTPSessionManager, str]:
        async with self._manager_lock:
            gateway_session_id = f"http:{uuid.uuid4().hex}"
            self.service.open_session(
                session_id=gateway_session_id,
                binding_session_id=binding.session_id,
                principal_id=binding.principal_id,
                workspace_id=binding.workspace_id,
                transport="streamable_http",
            )
            allowed_hosts = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]
            if self.security.bind_host not in {"127.0.0.1", "localhost", "::1"}:
                allowed_hosts.append(f"{self.security.bind_host}:*")
            manager = StreamableHTTPSessionManager(
                create_mcp_server(self.service, gateway_session_id),
                security_settings=TransportSecuritySettings(
                    enable_dns_rebinding_protection=True,
                    allowed_hosts=allowed_hosts,
                    allowed_origins=list(self.security.allowed_origins),
                ),
                session_idle_timeout=self.settings.session_idle_timeout_seconds,
            )
            ready = anyio.Event()

            async def serve() -> None:
                async with manager.run():
                    ready.set()
                    await self._stop.wait()

            assert self._task_group is not None
            self._task_group.start_soon(serve)
            await ready.wait()
            return manager, gateway_session_id

    async def _allow(self, principal: str) -> bool:
        now = time.monotonic()
        async with self._rate_lock:
            values = self._requests[principal]
            while values and values[0] <= now - 60:
                values.popleft()
            if len(values) >= self.settings.requests_per_minute:
                return False
            values.append(now)
            return True

    def _bounded_receive(self, receive):
        consumed = 0

        async def bounded():
            nonlocal consumed
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > self.settings.maximum_body_bytes:
                raise ValueError("MCP request body is too large")
            return message

        return bounded

    async def _error(self, scope, receive, send, status: int, detail: str) -> None:
        await JSONResponse({"detail": detail}, status_code=status)(scope, receive, send)


class McpTransportMount:
    async def __call__(self, scope, receive, send) -> None:
        transport = getattr(scope["app"].state, "mcp_transport", None)
        if transport is None:
            await JSONResponse(
                {"detail": "MCP transport unavailable"}, status_code=503
            )(scope, receive, send)
            return
        await transport(scope, receive, send)
