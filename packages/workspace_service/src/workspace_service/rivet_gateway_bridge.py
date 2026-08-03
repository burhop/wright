"""Narrow governed bridge from a Rivet run to Wright's gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RivetNodeInvocation:
    run_id: str
    node_id: str
    workspace_id: str
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    request_id: str


class GatewayPort(Protocol):
    async def call_tool(
        self,
        session_id: str,
        request_id: str,
        name: str,
        arguments: dict[str, Any],
        *,
        workspace_approvals: set[str] | None = None,
        client_approval_hint: bool = False,
    ) -> Any: ...


class RivetGatewayBridge:
    """Never trusts graph-provided workspace/session or approval authority."""

    def __init__(
        self, gateway: GatewayPort, *, run_scope: dict[str, tuple[str, str]]
    ) -> None:
        self._gateway = gateway
        self._run_scope = run_scope

    async def invoke(
        self,
        invocation: RivetNodeInvocation,
        *,
        workspace_approvals: set[str] | None = None,
    ) -> Any:
        scope = self._run_scope.get(invocation.run_id)
        if scope != (invocation.workspace_id, invocation.session_id):
            raise PermissionError("Rivet node run scope is unavailable")
        return await self._gateway.call_tool(
            invocation.session_id,
            invocation.request_id,
            invocation.tool_name,
            invocation.arguments,
            workspace_approvals=workspace_approvals,
            client_approval_hint=False,
        )
