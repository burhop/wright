from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta

import pytest
from core.rivet_mcp import CapabilityBinding
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
)
from workspace_service.rivet_authority import (
    AuthorityClaims,
    RivetRunAuthorityService,
)
from workspace_service.rivet_gateway_bridge import (
    RivetBoundInvocation,
    RivetGatewayBridge,
)


NOW = datetime(2026, 8, 13, tzinfo=UTC)


def _binding() -> CapabilityBinding:
    return CapabilityBinding.build(
        binding_id="binding-recovery",
        workspace_id="workspace",
        workflow_id="workflow",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="Main",
        node_id="node-recovery",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="fixture__long_operation",
        server_id="fixture",
        server_revision="1",
        capability_digest="b" * 64,
        validation_evidence_id="evidence",
        workspace_grant_digest="c" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=NOW,
    )


def _governed_bridge(gateway):
    binding = _binding()
    authorities = RivetRunAuthorityService(
        clock=lambda: NOW,
        id_factory=lambda: "authority-recovery",
    )
    grant = authorities.mint(
        AuthorityClaims(
            run_id="run-recovery",
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
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
        )
    )
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=lambda digest: (
            binding if digest == binding.binding_digest else None
        ),
    )
    invocation = RivetBoundInvocation(
        "run-recovery",
        1,
        grant.authority_id,
        binding.node_handle,
        binding.binding_digest,
        "request-recovery",
        {},
    )
    return binding, authorities, grant, bridge, invocation


def test_every_tier_one_cleanup_deadline_is_explicit_and_bounded() -> None:
    catalog = EngineeringScenarioCatalog()
    deadlines = {
        entry.scenario_id: catalog.get(entry.scenario_id).document["cleanup"][
            "timeout_seconds"
        ]
        for entry in catalog.list(tier="tier1")
    }

    assert deadlines
    assert all(0 < seconds <= 5 for seconds in deadlines.values())


@pytest.mark.asyncio
async def test_progress_without_a_total_stays_honestly_indeterminate() -> None:
    class IndeterminateGateway:
        async def call_tool(self, *_args, progress_callback=None, **_kwargs):
            assert progress_callback is not None
            await progress_callback({"status": "running", "message": "Working"})
            return GatewayToolResult(
                content=(),
                structured_content={"state": "complete"},
            )

        def cancel(self, *_args, **_kwargs):
            return True

    binding, _, grant, bridge, invocation = _governed_bridge(IndeterminateGateway())
    progress: list[dict] = []

    await bridge.invoke_bound(
        grant.token,
        grant.claims.audience,
        invocation,
        progress_callback=lambda event: progress.append(event),
    )

    assert len(progress) == 1
    assert progress[0]["phase"] == "child-progress"
    assert progress[0]["nodeId"] == binding.node_id
    assert progress[0]["status"] == "running"
    assert not {"percentage", "progress", "total"}.intersection(progress[0])


@pytest.mark.asyncio
async def test_cancellation_is_prompt_and_late_success_cannot_win() -> None:
    class LateGateway:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.release = asyncio.Event()
            self.cancelled: list[tuple[str, str, str | None]] = []

        async def call_tool(self, *_args, **_kwargs):
            self.started.set()
            await self.release.wait()
            return GatewayToolResult(
                content=(),
                structured_content={"late": True},
            )

        def cancel(self, session_id, request_id, reason=None):
            self.cancelled.append((session_id, request_id, reason))
            return True

    gateway = LateGateway()
    _, authorities, grant, bridge, invocation = _governed_bridge(gateway)
    pending = asyncio.create_task(
        bridge.invoke_bound(grant.token, grant.claims.audience, invocation)
    )
    await asyncio.wait_for(gateway.started.wait(), timeout=0.25)

    authorities.revoke(grant.authority_id, reason="cancelled")
    started = time.perf_counter()
    assert bridge.cancel_authority(grant.authority_id, reason="cancelled") == 1
    assert time.perf_counter() - started < 1.0
    assert gateway.cancelled == [
        ("session", "request-recovery", "cancelled"),
    ]

    gateway.release.set()
    with pytest.raises(PermissionError, match="revoked"):
        await pending
    assert bridge.active_count(grant.authority_id) == 0
