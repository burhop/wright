from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any, Mapping, Protocol

from .gateway_models import GatewayResource, GatewaySessionContext, GatewayTool
from .models import McpServer
from .runners.base import ProgressCallback


class GatewayWorkspacePort(Protocol):
    def resolve_binding(
        self, *, session_id: str, principal_id: str, workspace_id: str
    ) -> Mapping[str, str]: ...

    def enabled_server_ids(self, session: GatewaySessionContext) -> set[str] | None: ...


class GatewayCatalogPort(Protocol):
    def servers(self) -> Sequence[McpServer]: ...

    def tools(self, server_id: str) -> Sequence[GatewayTool]: ...

    def resources(
        self, session: GatewaySessionContext
    ) -> Sequence[GatewayResource]: ...


class GatewayAuditPort(Protocol):
    def record(self, event: Mapping[str, Any]) -> None: ...


class GatewayNotifierPort(Protocol):
    def subscribe(self, session: GatewaySessionContext) -> AsyncIterator[str]: ...

    def publish(self, *, workspace_id: str, event: str) -> None: ...


class GatewayLifecyclePort(Protocol):
    def lifecycle_projection(self, server_id: str) -> Mapping[str, Any]: ...

    async def ensure_started(
        self, server_id: str, *, workspace_path: str, approval_context: Any
    ) -> None: ...

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        approval_context: Any,
        progress_callback: ProgressCallback | None = None,
    ) -> Mapping[str, Any]: ...

    async def shutdown(self) -> None: ...


class GatewayCapabilityProvider(Protocol):
    """Provider-neutral dynamic tools executed through GatewayService authority."""

    provider_id: str
    declared_tool_names: frozenset[str]

    def tools(self, session: GatewaySessionContext) -> Sequence[GatewayTool]: ...

    async def call(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        arguments: Mapping[str, Any],
        *,
        request_id: str,
        approval_context: Any,
        progress_callback: ProgressCallback | None,
    ) -> Mapping[str, Any]: ...

    async def cancel(self, session: GatewaySessionContext, request_id: str) -> None: ...

    async def close_session(self, session: GatewaySessionContext) -> None: ...

    async def shutdown(self) -> None: ...


CancellationFactory = Callable[[], Awaitable[None]]
