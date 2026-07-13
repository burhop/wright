from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Mapping
from typing import Any
from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

from .gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayRequest,
    GatewayResource,
    GatewaySessionContext,
    GatewayTool,
    GatewayToolResult,
    RequestState,
    SessionState,
)
from .gateway_policy import GatewayPolicy
from .gateway_management import GatewayManagementTools
from .gateway_resources import GatewayResourceProvider, ResourceContent
from .gateway_ports import (
    GatewayAuditPort,
    GatewayCatalogPort,
    GatewayLifecyclePort,
    GatewayNotifierPort,
    GatewayWorkspacePort,
)

SUPPORTED_PROTOCOL_VERSION = "2025-11-25"


class GatewayService:
    def __init__(
        self,
        *,
        workspaces: GatewayWorkspacePort,
        catalog: GatewayCatalogPort,
        lifecycle: GatewayLifecyclePort,
        audit: GatewayAuditPort,
        notifier: GatewayNotifierPort,
        resources: GatewayResourceProvider | None = None,
        management: GatewayManagementTools | None = None,
        policy: GatewayPolicy | None = None,
        operation_timeout: float = 30.0,
        maximum_timeout: float = 120.0,
    ) -> None:
        self.workspaces = workspaces
        self.catalog = catalog
        self.lifecycle = lifecycle
        self.audit = audit
        self.notifier = notifier
        self.resources = resources
        self.management = management
        self.policy = policy or GatewayPolicy()
        self.operation_timeout = operation_timeout
        self.maximum_timeout = maximum_timeout
        self._sessions: dict[str, GatewaySessionContext] = {}
        self._requests: dict[
            tuple[str, str], tuple[GatewayRequest, asyncio.Task[Any]]
        ] = {}
        self._closing = False

    def open_session(
        self,
        *,
        session_id: str,
        principal_id: str,
        workspace_id: str,
        transport: str,
        binding_session_id: str | None = None,
    ) -> GatewaySessionContext:
        if self._closing:
            raise GatewayError(GatewayErrorCode.INTERNAL, "Gateway is shutting down")
        resolved_binding = self.workspaces.resolve_binding(
            session_id=binding_session_id or session_id,
            principal_id=principal_id,
            workspace_id=workspace_id,
        )
        existing = self._sessions.get(session_id)
        if existing is not None:
            if (
                existing.principal_id != principal_id
                or existing.workspace_id != workspace_id
                or existing.transport != transport
            ):
                raise GatewayError(
                    GatewayErrorCode.INVALID_BINDING,
                    "Gateway session binding is immutable",
                )
            return existing
        context = GatewaySessionContext(
            session_id=session_id,
            principal_id=str(resolved_binding["principal_id"]),
            workspace_id=str(resolved_binding["workspace_id"]),
            workspace_path=str(resolved_binding["workspace_path"]),
            transport=transport,
        )
        self._sessions[session_id] = context
        return context

    def initialize_session(
        self,
        session_id: str,
        *,
        protocol_version: str,
        client_name: str,
        client_version: str,
        client_capabilities: Mapping[str, Any],
    ) -> GatewaySessionContext:
        if protocol_version != SUPPORTED_PROTOCOL_VERSION:
            raise GatewayError(
                GatewayErrorCode.UNSUPPORTED_PROTOCOL,
                f"Unsupported MCP protocol version: {protocol_version}",
            )
        session = self._session(session_id, allow_created=True)
        active = session.initialized(
            protocol_version=protocol_version,
            client_name=client_name,
            client_version=client_version,
            client_capabilities=client_capabilities,
        ).activate()
        self._sessions[session_id] = active
        return active

    def list_tools(self, session_id: str) -> tuple[GatewayTool, ...]:
        session = self._session(session_id)
        enabled = self.workspaces.enabled_server_ids(session)
        result: list[GatewayTool] = []
        for server in self.catalog.servers():
            if not server.is_installed:
                continue
            if (
                enabled is not None
                and server.server_id not in enabled
                and server.name not in enabled
            ):
                continue
            for tool in self.catalog.tools(server.server_id):
                decision = self.policy.can_list(session, tool)
                self._audit(
                    session,
                    "",
                    tool,
                    decision.allowed,
                    decision.reason_code,
                    "listed" if decision.allowed else "hidden",
                    0,
                    operation="tool.list",
                )
                if decision.allowed:
                    result.append(tool)
        if self.management is not None:
            for tool in self.management.tools():
                decision = self.policy.can_list(session, tool)
                self._audit(
                    session,
                    "",
                    tool,
                    decision.allowed,
                    decision.reason_code,
                    "listed" if decision.allowed else "hidden",
                    0,
                    operation="tool.list",
                )
                if decision.allowed:
                    result.append(tool)
        return tuple(result)

    async def call_tool(
        self,
        session_id: str,
        request_id: str,
        name: str,
        arguments: Mapping[str, Any],
        *,
        timeout: float | None = None,
        client_approval_hint: bool = False,
    ) -> GatewayToolResult:
        session = self._session(session_id)
        tool = next(
            (item for item in self.list_tools(session_id) if item.name == name), None
        )
        if tool is None:
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND, f"Unknown or disabled tool: {name}"
            )
        decision = self.policy.can_call(
            session,
            tool,
            arguments,
            workspace_approvals=set(),
            client_approval_hint=client_approval_hint,
        )
        if not decision.allowed:
            self._audit(
                session,
                request_id,
                tool,
                decision.allowed,
                decision.reason_code,
                "denied",
                0,
            )
            return GatewayToolResult(
                content=({"type": "text", "text": decision.message},),
                structured_content={"error": decision.reason_code},
                is_error=True,
                error_code=GatewayErrorCode.POLICY_DENIED,
            )
        try:
            validate(instance=dict(arguments), schema=dict(tool.input_schema))
        except ValidationError as exc:
            raise GatewayError(
                GatewayErrorCode.INVALID_INPUT,
                f"Invalid input for tool: {name}",
            ) from exc
        now = time.monotonic()
        bounded = min(timeout or self.operation_timeout, self.maximum_timeout)
        request = GatewayRequest(
            session_id,
            request_id,
            "tools/call",
            str(uuid.uuid4()),
            now + bounded,
            now + self.maximum_timeout,
        )
        request.transition(RequestState.RUNNING)

        async def execute() -> Mapping[str, Any]:
            if tool.server_id == "wright" and self.management is not None:
                return self.management.call(session, tool.name)
            await self.lifecycle.ensure_started(
                tool.server_id,
                workspace_path=session.workspace_path,
                approval_context={"workspace_id": session.workspace_id},
            )
            return await self.lifecycle.call_tool(
                tool.server_id,
                tool.tool_name,
                arguments,
                approval_context={"workspace_id": session.workspace_id},
            )

        task = asyncio.create_task(execute())
        key = (session_id, request_id)
        self._requests[key] = (request, task)
        try:
            result = await asyncio.wait_for(task, bounded)
            structured = dict(result)
            if tool.output_schema is not None:
                try:
                    validate(instance=structured, schema=dict(tool.output_schema))
                except ValidationError as exc:
                    raise GatewayError(
                        GatewayErrorCode.INVALID_OUTPUT,
                        f"Invalid output from tool: {name}",
                    ) from exc
            request.transition(RequestState.SUCCEEDED)
            self._audit(
                session, request_id, tool, True, decision.reason_code, "succeeded", now
            )
            return GatewayToolResult(
                content=({"type": "text", "text": _result_text(structured)},),
                structured_content=structured,
            )
        except TimeoutError:
            request.transition(RequestState.TIMED_OUT)
            self._audit(session, request_id, tool, True, "timeout", "timed_out", now)
            raise GatewayError(
                GatewayErrorCode.TIMEOUT, f"Tool call timed out: {name}"
            ) from None
        except asyncio.CancelledError:
            if not request.state.terminal:
                request.cancel("cancelled")
            self._audit(session, request_id, tool, True, "cancelled", "cancelled", now)
            raise
        except GatewayError:
            request.transition(RequestState.FAILED)
            self._audit(
                session, request_id, tool, True, "invalid_output", "failed", now
            )
            raise
        except Exception as exc:
            request.transition(RequestState.FAILED)
            self._audit(session, request_id, tool, True, "child_error", "failed", now)
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE, "Tool execution failed"
            ) from exc
        finally:
            self._requests.pop(key, None)

    def list_resources(self, session_id: str) -> tuple[GatewayResource, ...]:
        session = self._session(session_id)
        if self.resources is not None:
            return self.resources.list(session)
        return tuple(self.catalog.resources(session))

    def read_resource(self, session_id: str, uri: str) -> ResourceContent:
        session = self._session(session_id)
        if self.resources is None:
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND, "Resource reader unavailable"
            )
        return self.resources.read(session, uri)

    def cancel(
        self, session_id: str, request_id: str, reason: str | None = None
    ) -> bool:
        self._session(session_id)
        item = self._requests.get((session_id, request_id))
        if item is None:
            return False
        request, task = item
        if request.state.terminal:
            return False
        request.cancellation_reason = reason
        task.cancel()
        return True

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        owned = [item for key, item in self._requests.items() if key[0] == session_id]
        for _, task in owned:
            task.cancel()
        if owned:
            await asyncio.gather(*(task for _, task in owned), return_exceptions=True)
        self._sessions[session_id] = session.close()

    async def shutdown(self) -> None:
        self._closing = True
        await asyncio.gather(
            *(self.close_session(session_id) for session_id in list(self._sessions)),
            return_exceptions=True,
        )
        await self.lifecycle.shutdown()

    def publish_list_changes(
        self,
        *,
        workspace_id: str | None = None,
        tools: bool = True,
        resources: bool = True,
    ) -> None:
        targets = {
            session.workspace_id
            for session in self._sessions.values()
            if session.state is not SessionState.CLOSED
            and (workspace_id is None or session.workspace_id == workspace_id)
        }
        for target in targets:
            if tools:
                self.notifier.publish(workspace_id=target, event="tools/list_changed")
            if resources:
                self.notifier.publish(
                    workspace_id=target, event="resources/list_changed"
                )

    def _session(
        self, session_id: str, *, allow_created: bool = False
    ) -> GatewaySessionContext:
        session = self._sessions.get(session_id)
        if session is None or session.state is SessionState.CLOSED:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING, "Unknown gateway session"
            )
        if not allow_created and session.state is not SessionState.ACTIVE:
            raise GatewayError(
                GatewayErrorCode.INVALID_LIFECYCLE, "Gateway session is not active"
            )
        return session

    def _audit(
        self,
        session: GatewaySessionContext,
        request_id: str,
        tool: GatewayTool,
        allowed: bool,
        reason_code: str,
        outcome: str,
        started: float,
        *,
        operation: str = "tool.call",
    ) -> None:
        duration = 0 if started == 0 else int((time.monotonic() - started) * 1000)
        self.audit.record(
            {
                "correlation_id": str(uuid.uuid4()),
                "request_id": request_id,
                "session_id": session.session_id,
                "principal_id": session.principal_id,
                "workspace_id": session.workspace_id,
                "operation": operation,
                "server_id": tool.server_id,
                "target_name": tool.tool_name,
                "allowed": allowed,
                "reason_code": reason_code,
                "outcome": outcome,
                "duration_ms": duration,
            }
        )


def _result_text(result: Mapping[str, Any]) -> str:
    import json

    return json.dumps(result, sort_keys=True, default=str)
