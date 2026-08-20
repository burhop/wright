"""Narrow governed bridge from a Rivet run to Wright's gateway."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import uuid
from typing import Any, Awaitable, Callable, Mapping, Protocol

import structlog
from core.rivet_mcp import (
    ApprovalState,
    CapabilityBinding,
    RivetChildCallRecord,
    canonical_digest,
)
from core.tracing import traced
from tool_registry.gateway_models import GatewayToolResult

from .rivet_authority import RivetRunAuthorityService
from .rivet_approvals import RivetApprovalError, RivetApprovalService
from .rivet_evidence import (
    project_result_value,
    redact_value,
    sanitize_gateway_result,
)


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
    call: RivetChildCallRecord | None = None


class RivetGatewayBridgeError(RuntimeError):
    """Stable, safe error projected from Wright-owned application lifecycle."""

    def __init__(self, code: str, recovery_action: str | None = None) -> None:
        super().__init__("The required engineering application is unavailable")
        self.code = code
        self.recovery_action = recovery_action


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


class ChildCallRepository(Protocol):
    def append_child_call(self, record: RivetChildCallRecord) -> None: ...


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
        repository: ChildCallRepository | None = None,
        approval_ttl_seconds: float = 300.0,
        automatic_call_approvals: bool = False,
    ) -> None:
        self._gateway = gateway
        self._run_scope = run_scope or {}
        self._authorities = authorities
        self._resolve_binding = resolve_binding
        self._validate_current = validate_current or (
            lambda binding, session_id, workspace_id: ()
        )
        self._approvals = approvals
        self._repository = repository
        self._approval_ttl_seconds = max(1.0, approval_ttl_seconds)
        self._automatic_call_approvals = automatic_call_approvals
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

        progress_redactions = 0

        async def project_progress(update: Mapping[str, Any]) -> None:
            nonlocal progress_redactions
            if progress_callback is None:
                return
            event = {
                "type": str(update.get("type") or "progress"),
                "phase": str(update.get("phase") or "child-progress"),
                **dict(update),
                "runId": invocation.run_id,
                "nodeId": binding.node_id,
                "requestId": invocation.request_id,
                "bindingDigest": binding.binding_digest,
            }
            safe_event, redactions = redact_value(event)
            progress_redactions += redactions
            callback_result = progress_callback(dict(safe_event))
            if callback_result is not None:
                await callback_result

        active_key = (invocation.authority_id, invocation.request_id)
        call_id = str(uuid.uuid4())
        trace_id = uuid.uuid4().hex
        started_at = datetime.now(UTC)
        child_received = False
        call_record: RivetChildCallRecord | None = None
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
                if self._automatic_call_approvals:
                    decision = self._approvals.decide(
                        approval.approval_id,
                        expected_digest=approval.approval_digest,
                        actor="wright-workflow-run",
                        approved=True,
                        reason="User launched this reviewed workspace workflow run.",
                    )
                    await project_progress(
                        {
                            "type": "progress",
                            "phase": "approval-satisfied",
                            "approvalId": approval.approval_id,
                            "approvalDigest": approval.approval_digest,
                        }
                    )
                else:
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
            child_received = True
            result = await self._gateway.call_tool(
                authority.claims.session_id,
                invocation.request_id,
                binding.qualified_tool_name,
                invocation.arguments,
                workspace_approvals=workspace_approvals,
                client_approval_hint=False,
                progress_callback=project_progress,
            )
            # A child that ignores cancellation cannot turn a revoked run into
            # a late success. Revalidate the exact authority before accepting
            # or persisting its terminal result.
            self._authorities.validate(
                token,
                audience=audience,
                run_id=invocation.run_id,
                generation=invocation.generation,
                node_handle=invocation.node_handle,
                binding_digest=invocation.binding_digest,
            )
            sanitized, artifacts, redactions = sanitize_gateway_result(
                result, workspace_id=authority.claims.workspace_id
            )
            retained_result = project_result_value(
                {
                    "content": list(sanitized.content),
                    "structured_content": sanitized.structured_content,
                    "meta": sanitized.meta,
                    "is_error": sanitized.is_error,
                    "error_code": sanitized.error_code,
                },
                name=binding.qualified_tool_name,
                origin="step_output",
            )
            redactions += progress_redactions
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
            call_record = RivetChildCallRecord(
                call_id=call_id,
                request_id=invocation.request_id,
                run_id=invocation.run_id,
                authority_id=invocation.authority_id,
                node_id=binding.node_id,
                binding_digest=binding.binding_digest,
                qualified_tool_name=binding.qualified_tool_name,
                server_revision=binding.server_revision,
                schema_digest=binding.schema_digest,
                validation_evidence_id=binding.validation_evidence_id,
                argument_digest=canonical_digest(invocation.arguments),
                trace_id=trace_id,
                state="failed" if sanitized.is_error else "succeeded",
                child_received=True,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                reason_code=(
                    str(sanitized.error_code) if sanitized.error_code else None
                ),
                artifacts=tuple(artifacts),
                redaction_count=redactions,
                result=retained_result,
                result_complete=bool(retained_result["complete"]),
            )
            if self._repository is not None:
                self._repository.append_child_call(call_record)
            return RivetBridgeResult(
                sanitized, binding, artifacts, redactions, call_record
            )
        # Gateway cancellation is a normal terminal control-flow state.  Do
        # not reclassify it as an unavailable engineering application: the
        # runner needs the cancellation to persist the run as cancelled.
        except asyncio.CancelledError:
            raise
        except Exception as error:
            original_error = error
            projected_error: Exception = error
            lifecycle_kind = str(getattr(error, "lifecycle_kind", ""))
            if lifecycle_kind == "panel":
                projected_error = RivetGatewayBridgeError(
                    "RIVET_MCP_PANEL_UNAVAILABLE",
                    str(
                        getattr(error, "recovery_action", None)
                        or "reopen_panel_and_inspect"
                    ),
                )
            elif lifecycle_kind == "host_bridge":
                projected_error = RivetGatewayBridgeError(
                    "RIVET_MCP_HOST_BRIDGE_UNAVAILABLE",
                    str(
                        getattr(error, "recovery_action", None)
                        or "inspect_host_application"
                    ),
                )
            if self._repository is not None and call_record is None:
                reason_code = str(
                    getattr(projected_error, "code", "RIVET_MCP_CALL_FAILED")
                )
                self._repository.append_child_call(
                    RivetChildCallRecord(
                        call_id=call_id,
                        request_id=invocation.request_id,
                        run_id=invocation.run_id,
                        authority_id=invocation.authority_id,
                        node_id=binding.node_id,
                        binding_digest=binding.binding_digest,
                        qualified_tool_name=binding.qualified_tool_name,
                        server_revision=binding.server_revision,
                        schema_digest=binding.schema_digest,
                        validation_evidence_id=binding.validation_evidence_id,
                        argument_digest=canonical_digest(invocation.arguments),
                        trace_id=trace_id,
                        state="failed",
                        child_received=child_received,
                        started_at=started_at,
                        completed_at=datetime.now(UTC),
                        reason_code=reason_code[:128],
                    )
                )
            if projected_error is not original_error:
                raise projected_error from original_error
            raise
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

    def active_count(self, authority_id: str) -> int:
        return sum(1 for key in self._active if key[0] == authority_id)


__all__ = [
    "RivetBoundInvocation",
    "RivetBridgeResult",
    "RivetGatewayBridgeError",
    "RivetGatewayBridge",
    "RivetNodeInvocation",
]
