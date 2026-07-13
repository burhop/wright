from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .db import get_servers, get_tools
from .gateway_models import GatewayResource, GatewaySessionContext, GatewayTool
from .manager import McpEngine
from .safety import ApprovalContext


class DatabaseGatewayWorkspace:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def resolve_binding(
        self, *, session_id: str, principal_id: str, workspace_id: str
    ) -> dict[str, Any]:
        return self.repository.resolve_binding(
            session_id=session_id,
            principal_id=principal_id,
            workspace_id=workspace_id,
        )

    def enabled_server_ids(self, session: GatewaySessionContext) -> set[str] | None:
        return self.repository.enabled_server_ids(session.workspace_id)


class DatabaseGatewayAudit:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def record(self, event: Mapping[str, Any]) -> None:
        self.repository.record_audit(event)


class DatabaseGatewayCatalog:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def servers(self) -> Sequence[Any]:
        return get_servers(self.db_path)

    def tools(self, server_id: str) -> Sequence[GatewayTool]:
        server = next(
            (item for item in get_servers(self.db_path) if item.server_id == server_id),
            None,
        )
        if server is None:
            return ()
        annotations = {
            "readOnlyHint": server.risk_level == "low",
            "destructiveHint": server.risk_level in {"high", "critical"},
            "idempotentHint": False,
            "openWorldHint": bool(server.credentials_required),
            "approval_gates": list(server.approval_gates),
        }
        return tuple(
            GatewayTool(
                name=f"{server_id}__{tool.name}",
                server_id=server_id,
                tool_name=tool.name,
                description=tool.description or "",
                input_schema=tool.input_schema,
                output_schema={"type": "object"},
                annotations=annotations,
                provenance={
                    "server_id": server.server_id,
                    "source_url": server.source_url,
                    "installed_version": server.installed_version,
                    "validation_status": server.validation_result.status,
                },
            )
            for tool in get_tools(self.db_path, server_id)
            if tool.is_enabled
        )

    def resources(self, session: GatewaySessionContext) -> Sequence[GatewayResource]:
        return ()


class EngineGatewayLifecycle:
    def __init__(self, engine: McpEngine) -> None:
        self.engine = engine

    async def ensure_started(
        self, server_id: str, *, workspace_path: str, approval_context: Any
    ) -> None:
        context = _approval_context(approval_context)
        if self.engine.lifecycle.runner_for(server_id) is None:
            await self.engine.start_server(
                server_id, workspace_path, approval_context=context
            )

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        approval_context: Any,
    ) -> Mapping[str, Any]:
        return await self.engine.call_tool(
            server_id,
            tool_name,
            dict(arguments),
            approval_context=_approval_context(approval_context),
        )

    async def shutdown(self) -> None:
        await self.engine.shutdown()


def _approval_context(value: Any) -> ApprovalContext:
    if isinstance(value, ApprovalContext):
        return value
    if isinstance(value, Mapping):
        return ApprovalContext(
            workspace_id=str(value.get("workspace_id") or "") or None,
            workspace_approvals=set(value.get("workspace_approvals") or ()),
        )
    return ApprovalContext()
