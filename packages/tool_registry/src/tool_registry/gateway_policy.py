from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .gateway_models import GatewaySessionContext, GatewayTool


SOLID_EDGE_CREATION_TOOLS = frozenset(
    {
        "cad.validate_recipe",
        "cad.create_part_from_recipe",
        "cad.validate_sheet_metal_recipe",
        "cad.create_sheet_metal_from_recipe",
        "cad.validate_assembly_recipe",
        "cad.create_assembly_from_recipe",
        "cad.rebuild_document",
        "cad.export_document",
        "cad.export_screenshot_views",
    }
)


def _is_solid_edge_tool(tool: GatewayTool) -> bool:
    source = str(tool.provenance.get("source_url") or "").lower()
    return "solidedgemcp" in source or "solid-edge-mcp" in source


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
        if (
            _is_solid_edge_tool(tool)
            and tool.tool_name not in SOLID_EDGE_CREATION_TOOLS
        ):
            return GatewayPolicyDecision(
                False,
                "solid_edge_creation_profile_hidden",
                "Tool is outside the Solid Edge creation profile",
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
        visibility = self.can_list(session, tool)
        if not visibility.allowed:
            return visibility
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
