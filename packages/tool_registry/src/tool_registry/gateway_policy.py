from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .gateway_models import GatewaySessionContext, GatewayTool


@dataclass(frozen=True, slots=True)
class GatewayPolicyDecision:
    allowed: bool
    reason_code: str
    message: str


class GatewayPolicy:
    """Authoritative gateway projection and call policy.

    MCP annotations and client approval hints are descriptive inputs only. They never
    grant workspace access or satisfy Wright approval gates.
    """

    def can_list(
        self, session: GatewaySessionContext, tool: GatewayTool
    ) -> GatewayPolicyDecision:
        if session.workspace_id.strip() == "":
            return GatewayPolicyDecision(
                False, "missing_workspace", "Workspace required"
            )
        return GatewayPolicyDecision(True, "workspace_authorized", "Tool is visible")

    def can_call(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        arguments: Mapping[str, Any],
        *,
        workspace_approvals: set[str] | None = None,
        client_approval_hint: bool = False,
    ) -> GatewayPolicyDecision:
        annotations = dict(tool.annotations)
        required = {str(value) for value in annotations.get("approval_gates", [])}
        granted = workspace_approvals or set()
        missing = sorted(required - granted)
        if missing:
            return GatewayPolicyDecision(
                False,
                "approval_required",
                "Workspace approval required: " + ", ".join(missing),
            )
        return GatewayPolicyDecision(True, "policy_allowed", "Tool call allowed")
