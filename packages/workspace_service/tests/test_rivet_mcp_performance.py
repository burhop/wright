from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from statistics import quantiles
from time import perf_counter

import pytest
from tool_registry.gateway_models import GatewayTool
from workspace_service import (
    AuthorityClaims,
    RivetCapabilityService,
    RivetRunAuthorityService,
)


class DiscoveryGateway:
    def __init__(self, count: int = 500) -> None:
        self.tools = tuple(
            GatewayTool(
                name=f"server-{index:03d}__inspect",
                server_id=f"server-{index:03d}",
                tool_name="inspect",
                title=f"Inspect {index}",
                description="Deterministic engineering capability",
                input_schema={
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                },
                output_schema={"type": "object"},
                provenance={"server_revision": "fixture-v1"},
            )
            for index in range(count)
        )

    def list_tools(self, session_id: str):
        assert session_id == "session-1"
        return self.tools


class ImmediateLifecycle:
    async def ensure_started(self, _server_id, **_kwargs):
        return None

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        del approval_context
        if progress_callback is not None:
            await progress_callback({"phase": "fixture", "progress": 0.5})
        return {
            "content": [{"type": "text", "text": "ok"}],
            "structuredContent": {
                "server": server_id,
                "tool": tool_name,
                "value": arguments["value"],
            },
        }

    async def shutdown(self):
        return None


def _claims(now: datetime) -> AuthorityClaims:
    return AuthorityClaims(
        run_id="performance-run",
        generation=1,
        workspace_id="workspace-1",
        session_id="gateway-session",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="graph-1",
        review_digest="b" * 64,
        binding_set_digest="c" * 64,
        audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
        node_bindings={"wright:abcdefghijklmnop": "d" * 64},
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )


def test_500_tool_discovery_and_authority_issuance_meet_interaction_budgets():
    service = RivetCapabilityService(DiscoveryGateway())
    started = perf_counter()
    snapshot = service.discover(session_id="session-1", workspace_id="workspace-1")
    discovery_ms = (perf_counter() - started) * 1000
    assert len(snapshot.tools) == 500
    assert discovery_ms < 500, f"500-tool discovery took {discovery_ms:.1f} ms"

    authority = RivetRunAuthorityService()
    started = perf_counter()
    issued = authority.mint(_claims(datetime.now(UTC)))
    issuance_ms = (perf_counter() - started) * 1000
    assert issued.token
    assert issuance_ms < 100, f"authority issuance took {issuance_ms:.1f} ms"


@pytest.mark.asyncio
async def test_bridge_overhead_and_progress_projection_meet_runtime_budgets(
    governed_lifecycle_harness,
):
    harness = governed_lifecycle_harness(ImmediateLifecycle(), server_id="performance")
    samples: list[float] = []
    progress_latencies: list[float] = []
    for index in range(30):
        started = perf_counter()

        async def progress(_event, *, call_started=started):
            progress_latencies.append((perf_counter() - call_started) * 1000)

        await harness.invoke(
            request_id=f"performance-{index}", progress_callback=progress
        )
        samples.append((perf_counter() - started) * 1000)

    p95_ms = quantiles(samples, n=20)[18]
    assert p95_ms < 100, f"governed bridge p95 was {p95_ms:.1f} ms"
    assert progress_latencies
    assert max(progress_latencies) < 250


@pytest.mark.asyncio
async def test_gateway_cancellation_delivery_meets_one_second_budget(
    governed_lifecycle_harness,
):
    class BlockingLifecycle(ImmediateLifecycle):
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.cancelled = asyncio.Event()

        async def call_tool(self, *_args, **_kwargs):
            self.started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled.set()
                raise

    lifecycle = BlockingLifecycle()
    harness = governed_lifecycle_harness(lifecycle, server_id="cancellation")
    call = asyncio.create_task(harness.invoke(request_id="cancel-performance"))
    await asyncio.wait_for(lifecycle.started.wait(), timeout=0.25)
    started = perf_counter()
    assert harness.gateway.cancel(
        "gateway-session", "cancel-performance", "performance measurement"
    )
    await asyncio.wait_for(lifecycle.cancelled.wait(), timeout=1.0)
    cancellation_ms = (perf_counter() - started) * 1000
    assert cancellation_ms < 1000
    with pytest.raises(asyncio.CancelledError):
        await call
