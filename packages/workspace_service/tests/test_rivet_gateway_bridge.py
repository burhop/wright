import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from core.rivet_mcp import ApprovalState, CapabilityBinding
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.rivet_authority import (
    AuthorityClaims,
    RivetRunAuthorityService,
)
from workspace_service.rivet_approvals import RivetApprovalService

from workspace_service.rivet_gateway_bridge import (
    RivetBoundInvocation,
    RivetGatewayBridge,
    RivetGatewayBridgeError,
    RivetNodeInvocation,
)


class Gateway:
    async def call_tool(
        self,
        session_id,
        request_id,
        name,
        arguments,
        *,
        workspace_approvals=None,
        client_approval_hint=False,
    ):
        return {
            "session": session_id,
            "name": name,
            "approvals": workspace_approvals,
            "hint": client_approval_hint,
        }


@pytest.mark.asyncio
async def test_bridge_binds_run_scope_and_never_sets_client_approval():
    bridge = RivetGatewayBridge(Gateway(), run_scope={"run": ("workspace", "session")})
    result = await bridge.invoke(
        RivetNodeInvocation(
            "run", "node", "workspace", "session", "tool", {}, "request"
        ),
        workspace_approvals={"approve"},
    )
    assert result["hint"] is False
    with pytest.raises(PermissionError):
        await bridge.invoke(
            RivetNodeInvocation(
                "run", "node", "other", "session", "tool", {}, "request"
            )
        )
    with pytest.raises(PermissionError):
        await bridge.invoke(
            RivetNodeInvocation(
                "run", "node", "workspace", "other-session", "tool", {}, "request"
            )
        )


class BoundGateway:
    def __init__(self) -> None:
        self.calls = []
        self.cancelled = []

    async def call_tool(
        self,
        session_id,
        request_id,
        name,
        arguments,
        *,
        workspace_approvals=None,
        client_approval_hint=False,
        progress_callback=None,
    ):
        self.calls.append(
            (session_id, request_id, name, arguments, client_approval_hint)
        )
        if progress_callback:
            await progress_callback({"status": "running", "progress": 0.5})
        return GatewayToolResult(
            content=({"type": "text", "text": "ok"},),
            structured_content={"result": 2},
        )

    def cancel(self, session_id, request_id, reason=None):
        self.cancelled.append((session_id, request_id, reason))
        return True


class CancelledGateway(BoundGateway):
    async def call_tool(self, *args, **kwargs):
        raise asyncio.CancelledError("remote transport request was cancelled")


class ChildCallRepository:
    def __init__(self) -> None:
        self.records = []

    def append_child_call(self, record) -> None:
        self.records.append(record)


def _binding():
    return CapabilityBinding.build(
        binding_id="binding-1",
        workspace_id="workspace",
        workflow_id="workflow",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="Main",
        node_id="node",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        server_revision="1",
        capability_digest="b" * 64,
        validation_evidence_id="evidence",
        workspace_grant_digest="c" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={
            "data_classes": [],
            "effect_classes": [],
            "required_approvals": [],
            "idempotency": "idempotent",
            "annotations_untrusted": True,
        },
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )


def _approval_binding():
    binding = _binding()
    return CapabilityBinding.build(
        binding_id=binding.binding_id,
        workspace_id=binding.workspace_id,
        workflow_id=binding.workflow_id,
        workflow_revision=binding.workflow_revision,
        workflow_digest=binding.workflow_digest,
        graph_id=binding.graph_id,
        node_id=binding.node_id,
        node_handle=binding.node_handle,
        requirement_id=binding.requirement_id,
        qualified_tool_name=binding.qualified_tool_name,
        server_id=binding.server_id,
        server_revision=binding.server_revision,
        capability_digest=binding.capability_digest,
        validation_evidence_id=binding.validation_evidence_id,
        workspace_grant_digest=binding.workspace_grant_digest,
        input_schema=binding.input_schema,
        output_schema=binding.output_schema,
        risk={**binding.risk, "required_approvals": ["engineering.write"]},
        units_policy=binding.units_policy,
        material_defaults=binding.material_defaults,
        argument_constraints=binding.argument_constraints,
        created_at=binding.created_at,
    )


@pytest.mark.asyncio
async def test_bound_bridge_resolves_tool_from_authority_and_projects_progress():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    authority_service = RivetRunAuthorityService(
        clock=lambda: now, id_factory=lambda: "authority"
    )
    binding = _binding()
    grant = authority_service.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="Main",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    gateway = BoundGateway()
    progress = []
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authority_service,
        resolve_binding=lambda digest: (
            binding if digest == binding.binding_digest else None
        ),
    )
    result = await bridge.invoke_bound(
        grant.token,
        grant.claims.audience,
        RivetBoundInvocation(
            "run",
            1,
            "authority",
            binding.node_handle,
            binding.binding_digest,
            "request",
            {"value": 2},
        ),
        progress_callback=lambda event: progress.append(event),
    )
    assert gateway.calls == [
        ("session", "request", "alpha__inspect", {"value": 2}, False)
    ]
    assert progress[0]["nodeId"] == "node"
    assert result.result.structured_content == {"result": 2}


@pytest.mark.asyncio
async def test_bound_bridge_projects_orphan_transport_cancellation() -> None:
    now = datetime(2026, 8, 13, tzinfo=UTC)
    authority_service = RivetRunAuthorityService(
        clock=lambda: now, id_factory=lambda: "authority"
    )
    binding = _binding()
    grant = authority_service.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="Main",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    repository = ChildCallRepository()
    bridge = RivetGatewayBridge(
        CancelledGateway(),
        authorities=authority_service,
        resolve_binding=lambda _: binding,
        repository=repository,
    )

    with pytest.raises(RivetGatewayBridgeError) as captured:
        await bridge.invoke_bound(
            grant.token,
            grant.claims.audience,
            RivetBoundInvocation(
                "run",
                1,
                "authority",
                binding.node_handle,
                binding.binding_digest,
                "request",
                {},
            ),
        )

    assert captured.value.code == "RIVET_MCP_CALL_CANCELLED"
    assert repository.records[0].reason_code == "RIVET_MCP_CALL_CANCELLED"
    assert repository.records[0].child_received is True


@pytest.mark.asyncio
async def test_bound_bridge_rejects_stale_binding_before_child():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    authority_service = RivetRunAuthorityService(
        clock=lambda: now, id_factory=lambda: "authority"
    )
    binding = _binding()
    grant = authority_service.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="Main",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    gateway = BoundGateway()
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authority_service,
        resolve_binding=lambda _: binding,
        validate_current=lambda _binding, _session, _workspace: (
            "tool_schema_changed",
        ),
    )
    with pytest.raises(PermissionError, match="stale"):
        await bridge.invoke_bound(
            grant.token,
            grant.claims.audience,
            RivetBoundInvocation(
                "run",
                1,
                "authority",
                binding.node_handle,
                binding.binding_digest,
                "request",
                {},
            ),
        )
    assert gateway.calls == []


@pytest.mark.asyncio
async def test_bound_bridge_waits_for_exact_one_shot_wright_approval():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    authority_service = RivetRunAuthorityService(
        clock=lambda: now, id_factory=lambda: "authority"
    )
    binding = _approval_binding()
    grant = authority_service.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="Main",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    approvals = RivetApprovalService(clock=lambda: now, id_factory=lambda: "approval")
    gateway = BoundGateway()
    progress = []
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authority_service,
        resolve_binding=lambda _: binding,
        approvals=approvals,
    )
    import asyncio

    pending_call = asyncio.create_task(
        bridge.invoke_bound(
            grant.token,
            grant.claims.audience,
            RivetBoundInvocation(
                "run",
                1,
                "authority",
                binding.node_handle,
                binding.binding_digest,
                "request",
                {"value": 2},
            ),
            progress_callback=lambda event: progress.append(event),
        )
    )
    await asyncio.sleep(0)
    pending = approvals.get("approval")
    assert gateway.calls == []
    approvals.decide(
        pending.approval_id,
        expected_digest=pending.approval_digest,
        actor="engineer",
        approved=True,
    )
    await pending_call
    assert progress[0]["type"] == "approval_required"
    assert gateway.calls[0][4] is False


@pytest.mark.asyncio
async def test_bound_bridge_uses_user_run_as_exact_one_shot_approval():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    authority_service = RivetRunAuthorityService(
        clock=lambda: now, id_factory=lambda: "authority"
    )
    binding = _approval_binding()
    grant = authority_service.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="Main",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        )
    )
    approvals = RivetApprovalService(clock=lambda: now, id_factory=lambda: "approval")
    gateway = BoundGateway()
    progress = []
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authority_service,
        resolve_binding=lambda _: binding,
        approvals=approvals,
        automatic_call_approvals=True,
    )

    await bridge.invoke_bound(
        grant.token,
        grant.claims.audience,
        RivetBoundInvocation(
            "run",
            1,
            "authority",
            binding.node_handle,
            binding.binding_digest,
            "request",
            {"value": 2},
        ),
        progress_callback=lambda event: progress.append(event),
    )

    approval = approvals.get("approval")
    assert approval.state is ApprovalState.CONSUMED
    assert approval.decided_by == "wright-workflow-run"
    assert progress[0]["type"] == "progress"
    assert progress[0]["phase"] == "approval-satisfied"
    assert gateway.calls[0][4] is False
