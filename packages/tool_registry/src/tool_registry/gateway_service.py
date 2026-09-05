from __future__ import annotations

import asyncio
import re
import time
import uuid
from collections.abc import Callable, Mapping
from typing import Any
from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

from .gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayLifecycleError,
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
    GatewayCapabilityProvider,
    GatewayCatalogPort,
    GatewayLifecyclePort,
    GatewayNotifierPort,
    GatewayWorkspacePort,
)
from .runners.base import ProgressCallback
from .ui.policy import McpUiPolicy
from .ui.resources import McpUiBinding, McpUiResourceStore
from .wright_managed_servers import (
    RIVET_WORKFLOW_MUTATION_APPROVAL,
    RIVET_WORKFLOWS_SERVER_ID,
)

SUPPORTED_PROTOCOL_VERSION = "2025-11-25"
_BREP_APPLICATION_STATUS_TOOL = "brep.app.status"
_URL_SECRET_PATTERN = re.compile(
    r"(?i)([?&](?:token|access_token|api_key)=)[^&\s\"'\\]+"
)


def _redact_url_secrets(value: Any) -> Any:
    """Remove URL credentials before a child result crosses the model boundary."""

    if isinstance(value, str):
        return _URL_SECRET_PATTERN.sub(r"\1[redacted]", value)
    if isinstance(value, Mapping):
        return {str(key): _redact_url_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_url_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_url_secrets(item) for item in value)
    return value


def _sanitize_model_result(
    tool: GatewayTool, result: GatewayToolResult
) -> GatewayToolResult:
    """Keep BREP's panel token inside Wright instead of exposing it to an LLM."""

    if tool.tool_name != _BREP_APPLICATION_STATUS_TOOL:
        return result
    structured = (
        _redact_url_secrets(result.structured_content)
        if result.structured_content is not None
        else None
    )
    return GatewayToolResult(
        content=tuple(_redact_url_secrets(item) for item in result.content),
        structured_content=structured,
        meta=_redact_url_secrets(result.meta),
        is_error=result.is_error,
        error_code=result.error_code,
    )


def _schema_allows_null(schema: object) -> bool:
    if not isinstance(schema, Mapping):
        return False
    declared_type = schema.get("type")
    if declared_type == "null":
        return True
    if isinstance(declared_type, list) and "null" in declared_type:
        return True
    if isinstance(schema.get("enum"), list) and None in schema["enum"]:
        return True
    return any(
        _schema_allows_null(option)
        for keyword in ("anyOf", "oneOf")
        for option in (
            schema.get(keyword) if isinstance(schema.get(keyword), list) else []
        )
    )


def _supply_missing_nullable_fields(value: Any, schema: object) -> Any:
    """Repair a common MCP omission without weakening output validation."""

    if not isinstance(schema, Mapping):
        return value
    if isinstance(value, Mapping):
        repaired = {str(key): item for key, item in value.items()}
        properties = schema.get("properties")
        properties = properties if isinstance(properties, Mapping) else {}
        required = schema.get("required")
        required = required if isinstance(required, list) else []
        for name in required:
            property_schema = properties.get(name)
            if (
                isinstance(name, str)
                and name not in repaired
                and _schema_allows_null(property_schema)
            ):
                repaired[name] = None
        for name, property_schema in properties.items():
            if isinstance(name, str) and name in repaired:
                repaired[name] = _supply_missing_nullable_fields(
                    repaired[name], property_schema
                )
        return repaired
    if isinstance(value, list) and isinstance(schema.get("items"), Mapping):
        return [
            _supply_missing_nullable_fields(item, schema["items"]) for item in value
        ]
    return value


def _safe_lifecycle_projection(
    lifecycle: GatewayLifecyclePort, server_id: str
) -> dict[str, Any]:
    """Return the bounded lifecycle facts allowed across the gateway boundary."""

    ordinary = {
        "kind": "ordinary",
        "visible_application": False,
        "cancellation_supported": True,
        "recovery_action": None,
    }
    resolver = getattr(lifecycle, "lifecycle_projection", None)
    if not callable(resolver):
        return ordinary
    try:
        raw = resolver(server_id)
    except Exception:
        return ordinary
    if not isinstance(raw, Mapping):
        return ordinary
    kind = str(raw.get("kind") or "ordinary")
    if kind not in {"ordinary", "panel", "host_bridge"}:
        kind = "ordinary"
    recovery = raw.get("recovery_action")
    return {
        "kind": kind,
        "visible_application": bool(raw.get("visible_application", False)),
        "cancellation_supported": bool(raw.get("cancellation_supported", True)),
        "recovery_action": (
            str(recovery)[:128] if isinstance(recovery, str) and recovery else None
        ),
    }


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
        ui_policy: McpUiPolicy | None = None,
        mcp_ui_resources: McpUiResourceStore | None = None,
        capability_providers: tuple[GatewayCapabilityProvider, ...] = (),
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
        self.ui_policy = ui_policy or McpUiPolicy()
        self.mcp_ui_resources = mcp_ui_resources
        self.operation_timeout = operation_timeout
        self.maximum_timeout = maximum_timeout
        self._sessions: dict[str, GatewaySessionContext] = {}
        self._requests: dict[
            tuple[str, str], tuple[GatewayRequest, asyncio.Task[Any]]
        ] = {}
        self._request_providers: dict[tuple[str, str], GatewayCapabilityProvider] = {}
        self._provider_cancellations: set[tuple[str, str]] = set()
        self._capability_providers: dict[str, GatewayCapabilityProvider] = {}
        self._closing = False
        for provider in capability_providers:
            self.add_capability_provider(provider)

    def add_capability_provider(self, provider: GatewayCapabilityProvider) -> None:
        """Register one provider while failing closed on every stable collision."""

        provider_id = str(provider.provider_id).strip()
        if not provider_id or provider_id in self._capability_providers:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Gateway capability provider identity is missing or duplicated",
            )
        declared = frozenset(str(item) for item in provider.declared_tool_names)
        if not declared or any(not item for item in declared):
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Gateway capability provider declared no valid tool identities",
            )
        occupied: set[str] = set()
        for server in self.catalog.servers():
            occupied.update(tool.name for tool in self.catalog.tools(server.server_id))
        if self.management is not None:
            occupied.update(tool.name for tool in self.management.tools())
        for existing in self._capability_providers.values():
            occupied.update(existing.declared_tool_names)
        if occupied.intersection(declared):
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Gateway capability tool name collision",
            )
        self._capability_providers[provider_id] = provider

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
                or existing.binding_session_id != str(resolved_binding["session_id"])
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
            binding_session_id=str(resolved_binding["session_id"]),
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
        names = {tool.name for tool in result}
        for provider in self._capability_providers.values():
            for tool in provider.tools(session):
                if tool.name not in provider.declared_tool_names:
                    raise GatewayError(
                        GatewayErrorCode.INVALID_BINDING,
                        "Gateway capability provider returned an undeclared tool",
                    )
                if tool.name in names:
                    raise GatewayError(
                        GatewayErrorCode.INVALID_BINDING,
                        "Gateway capability tool name collision",
                    )
                names.add(tool.name)
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

    def _provider_for_tool(
        self, session: GatewaySessionContext, tool: GatewayTool
    ) -> GatewayCapabilityProvider | None:
        matches = [
            provider
            for provider in self._capability_providers.values()
            if tool.name in provider.declared_tool_names
        ]
        if len(matches) > 1:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Gateway capability tool name collision",
            )
        return matches[0] if matches else None

    def workspace_approvals_for_model_call(
        self, session_id: str, name: str
    ) -> set[str]:
        """Project the operator grant represented by workspace enablement.

        Model-visible tools from installed catalog servers have already been
        filtered to the servers enabled for this workspace. Their declared
        call gates therefore travel with the model call instead of prompting
        for a second, unavailable approval. Wright management tools remain
        narrowly scoped to the built-in Rivet mutation grant.
        """

        session = self._session(session_id)
        tool = next(
            (item for item in self.list_tools(session_id) if item.name == name), None
        )
        if tool is None:
            return set()
        if tool.server_id != "wright":
            return set(tool.required_approvals)
        if RIVET_WORKFLOW_MUTATION_APPROVAL not in tool.required_approvals:
            return set()
        is_rivet_tool = tool.server_id == RIVET_WORKFLOWS_SERVER_ID or (
            tool.server_id == "wright" and tool.name.startswith("wright__rivet_")
        )
        if not is_rivet_tool:
            return set()
        enabled = self.workspaces.enabled_server_ids(session)
        if enabled is not None and not {
            RIVET_WORKFLOWS_SERVER_ID,
            "Rivet Workflows",
        }.intersection(enabled):
            return set()
        return {RIVET_WORKFLOW_MUTATION_APPROVAL}

    def list_app_tools(
        self,
        session_id: str,
        app_server_id: str,
    ) -> tuple[GatewayTool, ...]:
        session = self._session(session_id)
        enabled = self.workspaces.enabled_server_ids(session)
        server = next(
            (
                item
                for item in self.catalog.servers()
                if item.server_id == app_server_id and item.is_installed
            ),
            None,
        )
        if server is None or (
            enabled is not None
            and app_server_id not in enabled
            and server.name not in enabled
        ):
            return ()
        visible: list[GatewayTool] = []
        for tool in self.catalog.tools(app_server_id):
            decision = self.ui_policy.can_list_tool(
                session,
                tool,
                app_server_id=app_server_id,
            )
            self._audit(
                session,
                "",
                tool,
                decision.allowed,
                decision.reason_code,
                "listed" if decision.allowed else "hidden",
                0,
                operation="app.tool.list",
            )
            if decision.allowed:
                visible.append(tool)
        return tuple(visible)

    async def call_app_tool(
        self,
        session_id: str,
        request_id: str,
        app_server_id: str,
        name: str,
        arguments: Mapping[str, Any],
        *,
        timeout: float | None = None,
        workspace_approvals: set[str] | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> GatewayToolResult:
        return await self.call_tool(
            session_id,
            request_id,
            name,
            arguments,
            timeout=timeout,
            workspace_approvals=workspace_approvals,
            progress_callback=progress_callback,
            _app_server_id=app_server_id,
        )

    async def read_app_resource(
        self,
        session_id: str,
        request_id: str,
        app_server_id: str,
        resource_server_id: str,
        uri: str,
        *,
        timeout: float | None = None,
    ) -> McpUiBinding:
        session = self._session(session_id)
        decision = self.ui_policy.can_read_resource(
            app_server_id=app_server_id,
            resource_server_id=resource_server_id,
        )
        target = GatewayTool(
            name=uri,
            server_id=resource_server_id,
            tool_name=uri,
            description="MCP App resource read",
            input_schema={},
        )
        if not decision.allowed:
            self._audit(
                session,
                request_id,
                target,
                False,
                decision.reason_code,
                "denied",
                0,
                operation="app.resource.read",
            )
            raise GatewayError(GatewayErrorCode.POLICY_DENIED, decision.message)
        if self.mcp_ui_resources is None:
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE,
                "MCP UI resource service is unavailable",
            )
        enabled = self.workspaces.enabled_server_ids(session)
        server = next(
            (
                item
                for item in self.catalog.servers()
                if item.server_id == resource_server_id and item.is_installed
            ),
            None,
        )
        if server is None or (
            enabled is not None
            and resource_server_id not in enabled
            and server.name not in enabled
        ):
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND,
                "MCP UI resource server is not enabled in this workspace",
            )
        now = time.monotonic()
        bounded = min(timeout or self.operation_timeout, self.maximum_timeout)
        request = GatewayRequest(
            session_id,
            request_id,
            "resources/read",
            str(uuid.uuid4()),
            now + bounded,
            now + self.maximum_timeout,
        )
        request.transition(RequestState.RUNNING)
        self._audit(
            session,
            request_id,
            target,
            True,
            decision.reason_code,
            "started",
            now,
            operation="app.resource.read",
        )

        async def execute() -> McpUiBinding:
            await self.lifecycle.ensure_started(
                resource_server_id,
                workspace_path=session.workspace_path,
                approval_context={
                    "workspace_id": session.workspace_id,
                    "session_id": session.session_id,
                },
            )
            return await self.mcp_ui_resources.read(
                session,
                resource_server_id,
                uri,
            )

        task = asyncio.create_task(execute())
        key = (session_id, request_id)
        self._requests[key] = (request, task)
        try:
            binding = await asyncio.wait_for(task, bounded)
            request.transition(RequestState.SUCCEEDED)
            self._audit(
                session,
                request_id,
                target,
                True,
                decision.reason_code,
                "succeeded",
                now,
                operation="app.resource.read",
                metadata={"content_hash": binding.content_hash},
            )
            return binding
        except TimeoutError:
            request.transition(RequestState.TIMED_OUT)
            self._audit(
                session,
                request_id,
                target,
                True,
                "timeout",
                "timed_out",
                now,
                operation="app.resource.read",
            )
            raise GatewayError(
                GatewayErrorCode.TIMEOUT,
                "MCP UI resource read timed out",
            ) from None
        except asyncio.CancelledError:
            if not request.state.terminal:
                request.cancel("cancelled")
            self._audit(
                session,
                request_id,
                target,
                True,
                "cancelled",
                "cancelled",
                now,
                operation="app.resource.read",
            )
            raise
        finally:
            self._requests.pop(key, None)

    async def list_app_resources(
        self,
        session_id: str,
        request_id: str,
        app_server_id: str,
        *,
        timeout: float | None = None,
    ) -> Mapping[str, Any]:
        return await self._list_app_resource_collection(
            session_id,
            request_id,
            app_server_id,
            collection="resources",
            timeout=timeout,
        )

    async def list_app_resource_templates(
        self,
        session_id: str,
        request_id: str,
        app_server_id: str,
        *,
        timeout: float | None = None,
    ) -> Mapping[str, Any]:
        return await self._list_app_resource_collection(
            session_id,
            request_id,
            app_server_id,
            collection="resource_templates",
            timeout=timeout,
        )

    async def _list_app_resource_collection(
        self,
        session_id: str,
        request_id: str,
        app_server_id: str,
        *,
        collection: str,
        timeout: float | None,
    ) -> Mapping[str, Any]:
        session = self._session(session_id)
        operation = f"app.{collection}.list"
        target = GatewayTool(
            name=collection,
            server_id=app_server_id,
            tool_name=collection,
            description="MCP App resource discovery",
            input_schema={},
        )
        if self.mcp_ui_resources is None:
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE,
                "MCP UI resource service is unavailable",
            )
        enabled = self.workspaces.enabled_server_ids(session)
        server = next(
            (
                item
                for item in self.catalog.servers()
                if item.server_id == app_server_id and item.is_installed
            ),
            None,
        )
        if server is None or (
            enabled is not None
            and app_server_id not in enabled
            and server.name not in enabled
        ):
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND,
                "MCP UI resource server is not enabled in this workspace",
            )
        now = time.monotonic()
        bounded = min(timeout or self.operation_timeout, self.maximum_timeout)
        request = GatewayRequest(
            session_id,
            request_id,
            f"{collection}/list",
            str(uuid.uuid4()),
            now + bounded,
            now + self.maximum_timeout,
        )
        request.transition(RequestState.RUNNING)
        self._audit(
            session,
            request_id,
            target,
            True,
            "same_server",
            "started",
            now,
            operation=operation,
        )

        async def execute() -> Mapping[str, Any]:
            await self.lifecycle.ensure_started(
                app_server_id,
                workspace_path=session.workspace_path,
                approval_context={
                    "workspace_id": session.workspace_id,
                    "session_id": session.session_id,
                },
            )
            reader = self.mcp_ui_resources.reader
            if collection == "resources":
                return await reader.list_resources(app_server_id)
            return await reader.list_resource_templates(app_server_id)

        task = asyncio.create_task(execute())
        key = (session_id, request_id)
        self._requests[key] = (request, task)
        try:
            result = await asyncio.wait_for(task, bounded)
            request.transition(RequestState.SUCCEEDED)
            self._audit(
                session,
                request_id,
                target,
                True,
                "same_server",
                "succeeded",
                now,
                operation=operation,
            )
            return result
        except TimeoutError:
            request.transition(RequestState.TIMED_OUT)
            self._audit(
                session,
                request_id,
                target,
                True,
                "timeout",
                "timed_out",
                now,
                operation=operation,
            )
            raise GatewayError(
                GatewayErrorCode.TIMEOUT,
                "MCP UI resource discovery timed out",
            ) from None
        except asyncio.CancelledError:
            if not request.state.terminal:
                request.cancel("cancelled")
            self._audit(
                session,
                request_id,
                target,
                True,
                "cancelled",
                "cancelled",
                now,
                operation=operation,
            )
            raise
        finally:
            self._requests.pop(key, None)

    async def call_tool(
        self,
        session_id: str,
        request_id: str,
        name: str,
        arguments: Mapping[str, Any],
        *,
        timeout: float | None = None,
        client_approval_hint: bool = False,
        workspace_approvals: set[str] | None = None,
        progress_callback: ProgressCallback | None = None,
        _app_server_id: str | None = None,
        before_dispatch: Callable[[GatewayTool], None] | None = None,
        trace_id: str | None = None,
    ) -> GatewayToolResult:
        session = self._session(session_id)
        available_tools = (
            self.list_app_tools(session_id, _app_server_id)
            if _app_server_id is not None
            else self.list_tools(session_id)
        )
        tool = next((item for item in available_tools if item.name == name), None)
        if tool is None:
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND, f"Unknown or disabled tool: {name}"
            )
        decision = (
            self.ui_policy.can_call_tool(
                session,
                tool,
                arguments,
                app_server_id=_app_server_id,
                workspace_approvals=workspace_approvals,
                client_approval_hint=client_approval_hint,
            )
            if _app_server_id is not None
            else self.policy.can_call(
                session,
                tool,
                arguments,
                workspace_approvals=workspace_approvals,
                client_approval_hint=client_approval_hint,
            )
        )
        audit_operation = "app.tool.call" if _app_server_id else "tool.call"
        if not decision.allowed:
            self._audit(
                session,
                request_id,
                tool,
                decision.allowed,
                decision.reason_code,
                "denied",
                0,
                operation=audit_operation,
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
        capability_provider = (
            None
            if _app_server_id is not None
            else self._provider_for_tool(session, tool)
        )
        lifecycle_projection = _safe_lifecycle_projection(
            self.lifecycle, tool.server_id
        )
        audit_metadata = {
            "timeout_ms": int(bounded * 1000),
            "argument_count": len(arguments),
            "lifecycle_kind": lifecycle_projection["kind"],
        }
        if trace_id is not None:
            audit_metadata["trace_id"] = trace_id
        self._audit(
            session,
            request_id,
            tool,
            True,
            decision.reason_code,
            "started",
            now,
            metadata=audit_metadata,
            operation=audit_operation,
        )

        approval_context: dict[str, Any] = {
            "workspace_id": session.workspace_id,
            "session_id": session.session_id,
        }
        if workspace_approvals:
            approval_context["workspace_approvals"] = sorted(workspace_approvals)

        async def forward_progress(update: Mapping[str, Any]) -> None:
            if progress_callback is None:
                return
            event = {
                **dict(update),
                "server": tool.server_id,
                "tool": tool.name,
                "title": (
                    update.get("title")
                    or tool.title
                    or tool.description
                    or tool.tool_name
                ),
                "correlationId": request.correlation_id,
                "status": update.get("status") or "running",
            }
            if lifecycle_projection["kind"] != "ordinary":
                event["lifecycle"] = lifecycle_projection
            callback_result = progress_callback(event)
            if callback_result is not None:
                await callback_result

        async def execute() -> Mapping[str, Any]:
            if tool.server_id == "wright" and self.management is not None:
                if before_dispatch is not None:
                    before_dispatch(tool)
                return await self.management.call(session, tool.name, dict(arguments))
            if capability_provider is not None:
                if before_dispatch is not None:
                    before_dispatch(tool)
                return await capability_provider.call(
                    session,
                    tool,
                    arguments,
                    request_id=request_id,
                    approval_context=approval_context,
                    progress_callback=(
                        forward_progress if progress_callback is not None else None
                    ),
                )
            specialized = lifecycle_projection["kind"] != "ordinary"
            try:
                if specialized:
                    await forward_progress(
                        {
                            "phase": "lifecycle-starting",
                            "message": "Wright is preparing the required application.",
                        }
                    )
                await self.lifecycle.ensure_started(
                    tool.server_id,
                    workspace_path=session.workspace_path,
                    approval_context=approval_context,
                )
                if specialized:
                    await forward_progress(
                        {
                            "phase": "lifecycle-ready",
                            "message": "The required application is ready.",
                        }
                    )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                if not specialized:
                    raise
                raise GatewayLifecycleError(
                    lifecycle_kind=str(lifecycle_projection["kind"]),
                    recovery_action=(
                        str(lifecycle_projection["recovery_action"])
                        if lifecycle_projection["recovery_action"]
                        else None
                    ),
                ) from error
            # Exact-binding callers revalidate after startup may refresh the
            # catalog, and before any child invocation. Legacy calls retain
            # their existing behavior when no guard is supplied.
            if before_dispatch is not None:
                before_dispatch(tool)
            try:
                if progress_callback is None:
                    return await self.lifecycle.call_tool(
                        tool.server_id,
                        tool.tool_name,
                        arguments,
                        approval_context=approval_context,
                    )

                return await self.lifecycle.call_tool(
                    tool.server_id,
                    tool.tool_name,
                    arguments,
                    approval_context=approval_context,
                    progress_callback=forward_progress,
                )
            except asyncio.CancelledError:
                raise
            except GatewayLifecycleError:
                raise
            except Exception as error:
                if not specialized:
                    raise
                raise GatewayLifecycleError(
                    lifecycle_kind=str(lifecycle_projection["kind"]),
                    recovery_action=(
                        str(lifecycle_projection["recovery_action"])
                        if lifecycle_projection["recovery_action"]
                        else None
                    ),
                ) from error

        task = asyncio.create_task(execute())
        key = (session_id, request_id)
        self._requests[key] = (request, task)
        if capability_provider is not None:
            self._request_providers[key] = capability_provider
        try:
            raw_result = dict(await asyncio.wait_for(task, bounded))
            normalized = GatewayToolResult.from_upstream(raw_result)
            structured = normalized.structured_content
            # A child's advertised output schema describes successful structured
            # results. MCP error results commonly carry provider-authored text and
            # either omit structuredContent or use a small error envelope. Preserve
            # those results so callers can act on the real provider failure instead
            # of replacing it with Wright's INVALID_OUTPUT error.
            if tool.output_schema is not None and not normalized.is_error:
                try:
                    if structured is None:
                        raise ValidationError(
                            "Child omitted structuredContent required by outputSchema"
                        )
                    structured = _supply_missing_nullable_fields(
                        structured, tool.output_schema
                    )
                    validate(instance=structured, schema=dict(tool.output_schema))
                except ValidationError as exc:
                    raise GatewayError(
                        GatewayErrorCode.INVALID_OUTPUT,
                        f"Invalid output from tool: {name}",
                    ) from exc
                normalized = GatewayToolResult(
                    content=normalized.content,
                    structured_content=structured,
                    meta=normalized.meta,
                    is_error=normalized.is_error,
                    error_code=normalized.error_code,
                )
            normalized = _sanitize_model_result(tool, normalized)
            structured = normalized.structured_content
            request.transition(RequestState.SUCCEEDED)
            result_text = _result_text(structured or raw_result)
            self._audit(
                session,
                request_id,
                tool,
                True,
                decision.reason_code,
                "succeeded",
                now,
                metadata={
                    **audit_metadata,
                    "response_bytes": len(result_text.encode("utf-8")),
                    "result_key_count": len(structured or {}),
                },
                operation=audit_operation,
            )
            return GatewayToolResult(
                content=normalized.content or ({"type": "text", "text": result_text},),
                structured_content=structured,
                meta=normalized.meta,
                is_error=normalized.is_error,
            )
        except TimeoutError:
            if capability_provider is not None:
                await self._cancel_provider_once(
                    key, capability_provider, session, request_id
                )
            request.transition(RequestState.TIMED_OUT)
            self._audit(
                session,
                request_id,
                tool,
                True,
                "timeout",
                "timed_out",
                now,
                metadata=audit_metadata,
                operation=audit_operation,
            )
            raise GatewayError(
                GatewayErrorCode.TIMEOUT, f"Tool call timed out: {name}"
            ) from None
        except asyncio.CancelledError:
            if not request.state.terminal:
                request.cancel("cancelled")
            self._audit(
                session,
                request_id,
                tool,
                True,
                "cancelled",
                "cancelled",
                now,
                metadata=audit_metadata if trace_id is not None else None,
                operation=audit_operation,
            )
            raise
        except GatewayError as exc:
            request.transition(RequestState.FAILED)
            self._audit(
                session,
                request_id,
                tool,
                not (
                    before_dispatch is not None
                    and exc.code is GatewayErrorCode.POLICY_DENIED
                ),
                str(exc.code) if before_dispatch is not None else "invalid_output",
                "failed",
                now,
                metadata=audit_metadata,
                operation=audit_operation,
            )
            raise
        except Exception as exc:
            request.transition(RequestState.FAILED)
            self._audit(
                session,
                request_id,
                tool,
                True,
                "child_error",
                "failed",
                now,
                metadata=audit_metadata,
                operation=audit_operation,
            )
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE, "Tool execution failed"
            ) from exc
        finally:
            self._requests.pop(key, None)
            self._request_providers.pop(key, None)
            self._provider_cancellations.discard(key)

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
        provider = self._request_providers.get((session_id, request_id))
        if provider is not None:
            self._provider_cancellations.add((session_id, request_id))
            asyncio.create_task(provider.cancel(self._session(session_id), request_id))
        task.cancel()
        return True

    async def _cancel_provider_once(
        self,
        key: tuple[str, str],
        provider: GatewayCapabilityProvider,
        session: GatewaySessionContext,
        request_id: str,
    ) -> None:
        if key in self._provider_cancellations:
            return
        self._provider_cancellations.add(key)
        await provider.cancel(session, request_id)

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        owned = [item for key, item in self._requests.items() if key[0] == session_id]
        for _, task in owned:
            task.cancel()
        if owned:
            await asyncio.gather(*(task for _, task in owned), return_exceptions=True)
        if self.mcp_ui_resources is not None:
            self.mcp_ui_resources.close_session(session)
        await asyncio.gather(
            *(
                provider.close_session(session)
                for provider in self._capability_providers.values()
            ),
            return_exceptions=True,
        )
        self._sessions[session_id] = session.close()

    async def shutdown(self) -> None:
        self._closing = True
        await asyncio.gather(
            *(self.close_session(session_id) for session_id in list(self._sessions)),
            return_exceptions=True,
        )
        await self.lifecycle.shutdown()
        await asyncio.gather(
            *(provider.shutdown() for provider in self._capability_providers.values()),
            return_exceptions=True,
        )

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
        metadata: Mapping[str, Any] | None = None,
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
                "metadata": dict(metadata or {}),
            }
        )


def _result_text(result: Mapping[str, Any]) -> str:
    import json

    return json.dumps(result, sort_keys=True, default=str)
