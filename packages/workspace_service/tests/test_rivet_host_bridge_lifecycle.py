from __future__ import annotations

import asyncio

import pytest
from workspace_service import RivetGatewayBridgeError


class HostBridgeLifecycle:
    def __init__(self, *, fail_start: bool = False, wait: bool = False) -> None:
        self.fail_start = fail_start
        self.wait = wait
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()
        self.receipts: list[tuple] = []

    def lifecycle_projection(self, _server_id):
        return {
            "kind": "host_bridge",
            "visible_application": True,
            "cancellation_supported": True,
            "recovery_action": "inspect_host_application",
            "private_host_configuration": "must-not-cross-boundary",
        }

    async def ensure_started(self, server_id, *, workspace_path, approval_context):
        self.receipts.append(
            ("start", server_id, workspace_path, dict(approval_context))
        )
        if self.fail_start:
            raise RuntimeError("private host diagnostic")

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        self.receipts.append(
            (
                "call",
                server_id,
                tool_name,
                dict(arguments),
                dict(approval_context),
            )
        )
        self.started.set()
        if progress_callback is not None:
            await progress_callback(
                {
                    "phase": "child-progress",
                    "progress": 0.5,
                    "message": "Host fixture is inspecting the model.",
                }
            )
        if self.wait:
            try:
                await asyncio.Event().wait()
            finally:
                self.cancelled.set()
        return {
            "content": [{"type": "text", "text": "Host model inspected"}],
            "structuredContent": {"value": arguments["value"]},
        }

    async def shutdown(self):
        return None


@pytest.mark.asyncio
async def test_bound_host_bridge_matches_provider_neutral_result_and_progress(
    governed_lifecycle_harness,
) -> None:
    lifecycle = HostBridgeLifecycle()
    harness = governed_lifecycle_harness(lifecycle, server_id="solid-edge")
    progress: list[dict] = []

    result = await harness.invoke(
        request_id="host-request",
        progress_callback=lambda update: progress.append(dict(update)),
    )

    assert result.result.structured_content == {"value": 2}
    assert [item["phase"] for item in progress] == [
        "lifecycle-starting",
        "lifecycle-ready",
        "child-progress",
    ]
    assert all(item["lifecycle"]["kind"] == "host_bridge" for item in progress)
    assert all(
        "private_host_configuration" not in item["lifecycle"] for item in progress
    )
    assert lifecycle.receipts[1][3] == {"value": 2}
    assert set(lifecycle.receipts[1][4]) == {"workspace_id", "session_id"}
    assert harness.audit.events[-1]["metadata"]["lifecycle_kind"] == "host_bridge"
    await harness.gateway.shutdown()


@pytest.mark.asyncio
async def test_bound_host_bridge_failure_has_stable_safe_recovery(
    governed_lifecycle_harness,
) -> None:
    lifecycle = HostBridgeLifecycle(fail_start=True)
    harness = governed_lifecycle_harness(lifecycle, server_id="solid-edge")

    with pytest.raises(RivetGatewayBridgeError) as caught:
        await harness.invoke(request_id="host-failure")

    assert caught.value.code == "RIVET_MCP_HOST_BRIDGE_UNAVAILABLE"
    assert caught.value.recovery_action == "inspect_host_application"
    assert "private host diagnostic" not in str(caught.value)
    await harness.gateway.shutdown()


@pytest.mark.asyncio
async def test_bound_host_bridge_cancellation_reaches_owned_call(
    governed_lifecycle_harness,
) -> None:
    lifecycle = HostBridgeLifecycle(wait=True)
    harness = governed_lifecycle_harness(lifecycle, server_id="solid-edge")
    task = asyncio.create_task(harness.invoke(request_id="host-cancel"))
    await lifecycle.started.wait()

    assert harness.gateway.cancel("gateway-session", "host-cancel", "run_cancelled")
    with pytest.raises(asyncio.CancelledError):
        await task
    assert lifecycle.cancelled.is_set()
    await harness.gateway.shutdown()
