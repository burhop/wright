from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..gateway_models import GatewaySessionContext, GatewayTool
from ..gateway_policy import GatewayPolicyDecision


class McpUiPolicy:
    """Fail-closed policy for privileged operations initiated by an MCP App."""

    def can_list_tool(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        *,
        app_server_id: str,
    ) -> GatewayPolicyDecision:
        if not session.workspace_id:
            return GatewayPolicyDecision(
                False, "missing_workspace", "Workspace required"
            )
        if tool.server_id != app_server_id:
            return GatewayPolicyDecision(
                False,
                "cross_server_denied",
                "MCP Apps may access tools from their own server only",
            )
        if not tool.ui.app_visible:
            return GatewayPolicyDecision(
                False,
                "model_only",
                "Tool is not visible to MCP Apps",
            )
        return GatewayPolicyDecision(
            True,
            "same_server_app_visible",
            "Tool is visible to this MCP App",
        )

    def can_call_tool(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        arguments: Mapping[str, Any],
        *,
        app_server_id: str,
        workspace_approvals: set[str] | None = None,
        client_approval_hint: bool = False,
    ) -> GatewayPolicyDecision:
        del arguments, client_approval_hint
        visibility = self.can_list_tool(
            session,
            tool,
            app_server_id=app_server_id,
        )
        if not visibility.allowed:
            return visibility
        missing = sorted(
            set(tool.required_approvals) - set(workspace_approvals or ())
        )
        if missing:
            return GatewayPolicyDecision(
                False,
                "approval_required",
                "Workspace approval required: " + ", ".join(missing),
            )
        return GatewayPolicyDecision(
            True,
            "same_server_policy_allowed",
            "MCP App tool call allowed",
        )

    def can_read_resource(
        self,
        *,
        app_server_id: str,
        resource_server_id: str,
    ) -> GatewayPolicyDecision:
        if app_server_id != resource_server_id:
            return GatewayPolicyDecision(
                False,
                "cross_server_denied",
                "MCP Apps may read resources from their own server only",
            )
        return GatewayPolicyDecision(
            True,
            "same_server_resource_allowed",
            "MCP App resource read allowed",
        )

    def can_host_operation(
        self,
        operation: str,
        *,
        declared_capabilities: set[str],
        granted_capabilities: set[str],
    ) -> GatewayPolicyDecision:
        known = {"context.update", "user.message"}
        if operation not in known:
            return GatewayPolicyDecision(
                False,
                "unsupported_operation",
                "Unsupported MCP App host operation",
            )
        if operation not in declared_capabilities:
            return GatewayPolicyDecision(
                False,
                "capability_not_declared",
                "MCP App did not declare this host capability",
            )
        if operation not in granted_capabilities:
            return GatewayPolicyDecision(
                False,
                "grant_required",
                "User or workspace grant required",
            )
        return GatewayPolicyDecision(True, "grant_allowed", "Host operation allowed")
