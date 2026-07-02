from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

from pydantic import BaseModel, Field

from .mcp_catalog import is_install_blocked
from .models import EnvVarDefinition, McpServer

PolicyOperation = Literal["install", "start", "call"]


class PolicyDecision(BaseModel):
    allowed: bool
    operation: PolicyOperation
    reason: str
    required_approvals: list[str] = Field(default_factory=list)
    missing_credentials: list[str] = Field(default_factory=list)
    network_required: bool = False
    blocked_by_catalog: bool = False
    diagnostics: dict[str, object] = Field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalContext:
    machine_approvals: set[str] = field(default_factory=set)
    workspace_approvals: set[str] = field(default_factory=set)
    workspace_id: str | None = None

    def approvals_for(self, operation: PolicyOperation) -> set[str]:
        if operation == "install":
            return set(self.machine_approvals)
        return set(self.machine_approvals) | set(self.workspace_approvals)


def required_credentials(server: McpServer) -> list[str]:
    names = list(server.credentials_required)
    if server.env_vars and isinstance(server.env_vars, list):
        for var in server.env_vars:
            if isinstance(var, EnvVarDefinition) and var.required:
                names.append(var.name)
    return sorted(set(names))


def server_requires_network(server: McpServer) -> bool:
    if server.type in {"sse", "webmcp"}:
        return True
    if isinstance(server.command, str):
        return server.command.startswith(("http://", "https://"))
    return False


class McpSafetyPolicy:
    def can_install(
        self,
        server: McpServer,
        approval_context: ApprovalContext | None = None,
    ) -> PolicyDecision:
        return self._evaluate(server, "install", approval_context)

    def can_start(
        self,
        server: McpServer,
        approval_context: ApprovalContext | None = None,
        *,
        credentials_configured: Mapping[str, bool] | None = None,
    ) -> PolicyDecision:
        return self._evaluate(
            server,
            "start",
            approval_context,
            credentials_configured=credentials_configured,
        )

    def can_call_tool(
        self,
        server: McpServer,
        tool_name: str,
        approval_context: ApprovalContext | None = None,
        *,
        credentials_configured: Mapping[str, bool] | None = None,
    ) -> PolicyDecision:
        decision = self._evaluate(
            server,
            "call",
            approval_context,
            credentials_configured=credentials_configured,
        )
        decision.diagnostics["tool_name"] = tool_name
        return decision

    def _evaluate(
        self,
        server: McpServer,
        operation: PolicyOperation,
        approval_context: ApprovalContext | None,
        *,
        credentials_configured: Mapping[str, bool] | None = None,
    ) -> PolicyDecision:
        context = approval_context or ApprovalContext()
        network_required = server_requires_network(server)
        diagnostics = {
            "server_id": server.server_id,
            "risk_level": server.risk_level,
            "installability_tier": server.installability_tier,
        }

        if is_install_blocked(server):
            reason = server.install_blocked_reason or (
                f"Server '{server.name}' is marked {server.installability_tier}."
            )
            return PolicyDecision(
                allowed=False,
                operation=operation,
                reason=reason,
                network_required=network_required,
                blocked_by_catalog=True,
                diagnostics=diagnostics,
            )

        required = self._required_approvals(server)
        missing_approvals = sorted(required - context.approvals_for(operation))
        if missing_approvals:
            return PolicyDecision(
                allowed=False,
                operation=operation,
                reason=(
                    f"MCP server '{server.name}' requires approval before {operation}."
                ),
                required_approvals=missing_approvals,
                network_required=network_required,
                diagnostics=diagnostics,
            )

        if operation in {"start", "call"}:
            missing_credentials = self._missing_credentials(
                server, credentials_configured
            )
            if missing_credentials:
                return PolicyDecision(
                    allowed=False,
                    operation=operation,
                    reason=(
                        f"MCP server '{server.name}' is missing required credentials."
                    ),
                    missing_credentials=missing_credentials,
                    network_required=network_required,
                    diagnostics=diagnostics,
                )

        return PolicyDecision(
            allowed=True,
            operation=operation,
            reason="allowed",
            network_required=network_required,
            diagnostics=diagnostics,
        )

    def _required_approvals(self, server: McpServer) -> set[str]:
        if not server.approval_gates:
            return set()
        if server.risk_level in {"high", "safety-critical"}:
            return set(server.approval_gates)
        if server.credentials_required or server_requires_network(server):
            return set(server.approval_gates)
        return set()

    def _missing_credentials(
        self,
        server: McpServer,
        credentials_configured: Mapping[str, bool] | None,
    ) -> list[str]:
        required = required_credentials(server)
        if not required:
            return []
        configured = credentials_configured or {}
        return [name for name in required if not configured.get(name, False)]
