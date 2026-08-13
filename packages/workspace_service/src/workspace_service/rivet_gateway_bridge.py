"""Narrow governed bridge from a Rivet run to Wright's gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, Protocol

import structlog
from core.rivet_mcp import ApprovalState, CapabilityBinding, canonical_digest
from core.tracing import traced
from tool_registry.gateway_models import GatewayToolResult

from .rivet_authority import RivetRunAuthorityService
from .rivet_approvals import RivetApprovalError, RivetApprovalService
from .rivet_evidence import sanitize_gateway_result


logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RivetNodeInvocation:
    run_id: str
    node_id: str
    workspace_id: str
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    request_id: str
    generation: int = 1
    authority_id: str | None = None
    node_handle: str | None = None
    binding_digest: str | None = None


@dataclass(frozen=True, slots=True)
class RivetBoundInvocation:
    run_id: str
    generation: int
    authority_id: str
    node_handle: str
    binding_digest: str
    request_id: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RivetBridgeResult:
    result: GatewayToolResult
    binding: CapabilityBinding
    artifacts: tuple[Any, ...]
    redaction_count: int


class GatewayPort(Protocol):
    async def call_tool(
        self,
        session_id: str,
        request_id: str,
        name: str,
        arguments: Mapping[str, Any],
        *,
        workspace_approvals: set[str] | None = None,
        client_approval_hint: bool = False,
        progress_callback: Callable[[Mapping[str, Any]], Awaitable[None] | None]
        | None = None,
    ) -> GatewayToolResult: ...

    def cancel(
        self, session_id: str, request_id: str, reason: str | None = None
    ) -> bool: ...


BindingResolver = Callable[[str], CapabilityBinding | None]
CurrentBindingValidator = Callable[[CapabilityBinding, str, str], tuple[str, ...]]
ProgressCallback = Callable[[Mapping[str, Any]], Awaitable[None] | None]


class RivetGatewayBridge:
    """Resolve runner handles to reviewed bindings and delegate to GatewayService."""

    def __init__(
        self,
        gateway: GatewayPort,
        *,
        run_scope: dict[str, tuple[str, str]] | None = None,
        authorities: RivetRunAuthorityService | None = None,
        resolve_binding: BindingResolver | None = None,
        validate_current: CurrentBindingValidator | None = None,
        approvals: RivetApprovalService | None = None,
        approval_ttl_seconds: float = 300.0,
    ) -> None:
        self._gateway = gateway
        self._run_scope = run_scope or {}
        self._authorities = authorities
        self._resolve_binding = resolve_binding
        self._validate_current = validate_current or (
            lambda binding, session_id, workspace_id: ()
        )
        self._approvals = approvals
        self._approval_ttl_seconds = max(1.0, approval_ttl_seconds)
        self._active: dict[tuple[str, str], tuple[str, str]] = {}

    async def invoke(
        self,
        invocation: RivetNodeInvocation,
        *,
        workspace_approvals: set[str] | None = None,
    ) -> Any:
        """Compatibility path for existing tests and pre-v2 non-runner callers."""

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

    @traced("rivet.gateway.bound_call")
    async def invoke_bound(
        self,
        token: str,
        audience: str,
        invocation: RivetBoundInvocation,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> RivetBridgeResult:
        if self._authorities is None or self._resolve_binding is None:
            raise PermissionError("Rivet MCP authority bridge is unavailable")
        authority = self._authorities.validate(
            token,
            audience=audience,
            run_id=invocation.run_id,
            generation=invocation.generation,
            node_handle=invocation.node_handle,
            binding_digest=invocation.binding_digest,
        )
        if authority.authority_id != invocation.authority_id:
            raise PermissionError("Rivet MCP authority identity is unavailable")
        binding = self._resolve_binding(invocation.binding_digest)
        if binding is None or binding.node_handle != invocation.node_handle:
            raise PermissionError("Rivet MCP binding is unavailable")
        if (
            binding.workspace_id != authority.claims.workspace_id
            or binding.workflow_id != authority.claims.workflow_id
            or binding.workflow_digest != authority.claims.workflow_digest
            or binding.graph_id != authority.claims.graph_id
        ):
            raise PermissionError("Rivet MCP binding scope changed")
        stale = self._validate_current(
            binding, authority.claims.session_id, authority.claims.workspace_id
        )
        if stale:
            raise PermissionError("Rivet MCP binding is stale: " + ", ".join(stale))

        async def project_progress(update: Mapping[str, Any]) -> None:
            if progress_callback is None:
                return
            event = {
                **dict(update),
                "runId": invocation.run_id,
                "nodeId": binding.node_id,
                "requestId": invocation.request_id,
                "bindingDigest": binding.binding_digest,
            }
            callback_result = progress_callback(event)
            if callback_result is not None:
                await callback_result

        active_key = (invocation.authority_id, invocation.request_id)
        self._active[active_key] = (
            authority.claims.session_id,
            invocation.request_id,
        )
        logger.info(
            "rivet_gateway_call_started",
            run_id=invocation.run_id,
            node_id=binding.node_id,
            request_id=invocation.request_id,
            binding_digest=binding.binding_digest,
            tool=binding.qualified_tool_name,
        )
        try:
            required_gates = tuple(
                sorted(set(binding.risk.get("required_approvals") or ()))
            )
            workspace_approvals: set[str] | None = None
            if required_gates:
                if self._approvals is None:
                    raise RivetApprovalError(
                        "RIVET_CALL_APPROVAL_REQUIRED",
                        "This exact tool call requires Wright approval",
                    )
                approval = self._approvals.request(
                    run_id=invocation.run_id,
                    authority_id=invocation.authority_id,
                    node_id=binding.node_id,
                    binding_digest=binding.binding_digest,
                    session_id=authority.claims.session_id,
                    server_id=binding.server_id,
                    qualified_tool_name=binding.qualified_tool_name,
                    request_id=invocation.request_id,
                    arguments=invocation.arguments,
                    required_gates=required_gates,
                    requested_by=f"runner:{invocation.run_id}",
                    ttl_seconds=self._approval_ttl_seconds,
                )
                await project_progress(
                    {
                        "type": "approval_required",
                        "phase": "approval-required",
                        "approvalId": approval.approval_id,
                        "approvalDigest": approval.approval_digest,
                    }
                )
                decision = await self._approvals.wait(approval.approval_id)
                if decision.state is not ApprovalState.APPROVED:
                    raise RivetApprovalError(
                        "RIVET_CALL_APPROVAL_DENIED",
                        "This exact tool call was not approved",
                    )
                self._approvals.consume(
                    approval.approval_id,
                    argument_digest=canonical_digest(invocation.arguments),
                )
                workspace_approvals = set(required_gates)
            result = await self._gateway.call_tool(
                authority.claims.session_id,
                invocation.request_id,
                binding.qualified_tool_name,
                invocation.arguments,
                workspace_approvals=workspace_approvals,
                client_approval_hint=False,
                progress_callback=project_progress,
            )
            sanitized, artifacts, redactions = sanitize_gateway_result(
                result, workspace_id=authority.claims.workspace_id
            )
            logger.info(
                "rivet_gateway_call_finished",
                run_id=invocation.run_id,
                node_id=binding.node_id,
                request_id=invocation.request_id,
                binding_digest=binding.binding_digest,
                is_error=sanitized.is_error,
                artifact_count=len(artifacts),
                redaction_count=redactions,
            )
            return RivetBridgeResult(sanitized, binding, artifacts, redactions)
        finally:
            self._active.pop(active_key, None)

    def cancel_authority(self, authority_id: str, *, reason: str) -> int:
        cancelled = 0
        for key, (session_id, request_id) in tuple(self._active.items()):
            if key[0] != authority_id:
                continue
            if self._gateway.cancel(session_id, request_id, reason):
                cancelled += 1
        return cancelled


__all__ = [
    "RivetBoundInvocation",
    "RivetBridgeResult",
    "RivetGatewayBridge",
    "RivetNodeInvocation",
]
