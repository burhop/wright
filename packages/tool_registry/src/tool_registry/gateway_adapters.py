from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
import os
from typing import Any

from .db import get_server, get_servers, get_tools
from .gateway_models import (
    GatewayResource,
    GatewaySessionContext,
    GatewayTool,
    GatewayWorkspaceScopeError,
)
from .manager import McpEngine
from .safety import ApprovalContext, McpSafetyPolicy
from .runners.base import ProgressCallback
from .runners.stdio import StdioRunner
from .wright_managed_servers import (
    RIVET_WORKFLOW_MUTATION_APPROVAL,
    RIVET_WORKFLOWS_SERVER_ID,
)


def _server_authority_revision(server: Any) -> str:
    """Digest executable authority without including mutable runtime health."""

    env_vars = server.env_vars
    if isinstance(env_vars, list):
        env_vars = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in env_vars
        ]
    material = {
        "type": server.type,
        "transport_variant": server.transport_variant,
        "command": server.command,
        "source_url": server.source_url,
        "installed_version": server.installed_version,
        "env_vars": env_vars,
        "launch_env": server.launch_env,
    }
    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"config-{hashlib.sha256(encoded).hexdigest()}"


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
        policy = McpSafetyPolicy()

        def approvals(tool_name: str) -> frozenset[str]:
            required = set(
                policy.can_call_tool(
                    server, tool_name, ApprovalContext()
                ).required_approvals
            )
            if server.server_id == RIVET_WORKFLOWS_SERVER_ID and tool_name in {
                "create_workflow",
                "run_workflow",
            }:
                required.add(RIVET_WORKFLOW_MUTATION_APPROVAL)
            return frozenset(required)

        return tuple(
            GatewayTool(
                name=f"{server_id}__{tool.name}",
                server_id=server_id,
                tool_name=tool.name,
                description=tool.description or "",
                input_schema=tool.input_schema,
                title=tool.title,
                output_schema=tool.output_schema,
                annotations=tool.annotations,
                upstream_meta=tool.meta,
                ui=tool.ui,
                required_approvals=approvals(tool.name),
                provenance={
                    "server_id": server.server_id,
                    "source_url": server.source_url,
                    "installed_version": server.installed_version,
                    "server_revision": _server_authority_revision(server),
                    "validation_status": server.validation_result.status,
                    "validation_evidence_id": (
                        f"gateway-validation:{server.server_id}:"
                        f"{server.updated_at}:{server.validation_result.status}"
                    ),
                },
            )
            for tool in get_tools(self.db_path, server_id)
            if tool.is_enabled
        )

    def resources(self, session: GatewaySessionContext) -> Sequence[GatewayResource]:
        return ()


class EngineGatewayLifecycle:
    def __init__(
        self,
        engine: McpEngine,
        *,
        projection_resolver: Callable[[str], Mapping[str, Any]] | None = None,
        tools_changed: Callable[[str], None] | None = None,
    ) -> None:
        self.engine = engine
        self._projection_resolver = projection_resolver
        self._tools_changed = tools_changed

    def lifecycle_projection(self, server_id: str) -> Mapping[str, Any]:
        if self._projection_resolver is None:
            return {
                "kind": "ordinary",
                "visible_application": False,
                "cancellation_supported": True,
                "recovery_action": None,
            }
        return dict(self._projection_resolver(server_id))

    async def ensure_started(
        self, server_id: str, *, workspace_path: str, approval_context: Any
    ) -> None:
        context = _approval_context(approval_context)
        runner = self.engine.lifecycle.runner_for(server_id)
        if runner is not None:
            self._check_browser_workspace(server_id, runner, workspace_path)
        if runner is None:
            await self.engine.start_server(
                server_id, workspace_path, approval_context=context
            )
            runner = self.engine.lifecycle.runner_for(server_id)
            if runner is not None:
                # start_server may reuse a runner published by a concurrent
                # activation; check that winning instance's actual file root.
                self._check_browser_workspace(server_id, runner, workspace_path)
            if runner is not None and self._tools_changed is not None:
                self._tools_changed(server_id)

    def _check_browser_workspace(
        self, server_id: str, runner: Any, workspace_path: str
    ) -> None:
        if not isinstance(runner, StdioRunner):
            return
        server = get_server(self.engine.db_path, server_id)
        if server is None or (server.source_url or "").rstrip("/") != (
            "https://github.com/microsoft/playwright-mcp"
        ):
            return
        # Playwright's file tools resolve against the process cwd when the
        # client does not supply MCP roots. A cached child must never silently
        # substitute another workspace. Do not restart it: it may own live calls.
        def normalize(path: str) -> str:
            return os.path.normcase(os.path.realpath(path))

        if runner.cwd and normalize(runner.cwd) == normalize(workspace_path):
            return
        raise GatewayWorkspaceScopeError()

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        approval_context: Any,
        progress_callback: ProgressCallback | None = None,
    ) -> Mapping[str, Any]:
        if progress_callback is None:
            return await self.engine.call_tool(
                server_id,
                tool_name,
                dict(arguments),
                approval_context=_approval_context(approval_context),
            )
        return await self.engine.call_tool(
            server_id,
            tool_name,
            dict(arguments),
            approval_context=_approval_context(approval_context),
            progress_callback=progress_callback,
        )

    async def shutdown(self) -> None:
        await self.engine.shutdown()


def _approval_context(value: Any) -> ApprovalContext:
    if isinstance(value, ApprovalContext):
        return value
    if isinstance(value, Mapping):
        return ApprovalContext(
            workspace_id=str(value.get("workspace_id") or "") or None,
            session_id=str(value.get("session_id") or "") or None,
            workspace_approvals=set(value.get("workspace_approvals") or ()),
        )
    return ApprovalContext()
