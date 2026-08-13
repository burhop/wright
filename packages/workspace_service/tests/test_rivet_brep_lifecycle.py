from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from api.brep_gateway import BrepPanelGatewayLifecycle
from workspace_service import RivetGatewayBridgeError


class _UnusedDelegate:
    def __init__(self) -> None:
        self.receipts: list[tuple] = []

    def lifecycle_projection(self, _server_id):
        return {"kind": "ordinary"}

    async def ensure_started(self, *args, **kwargs):
        self.receipts.append(("start", args, kwargs))

    async def call_tool(self, *args, **kwargs):
        self.receipts.append(("call", args, kwargs))
        return {"structuredContent": {"delegate": True}}

    async def shutdown(self):
        return None


@pytest.mark.asyncio
async def test_bound_rivet_brep_call_preserves_visible_panel_contract(
    governed_lifecycle_harness,
) -> None:
    requests: list[tuple[str, dict]] = []
    progress: list[dict] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append((request.url.path, payload))
        if request.url.path.endswith("/panel"):
            return httpx.Response(200, json={"connected": True})
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "BREP inspected"}],
                "structuredContent": {"value": payload["arguments"]["value"]},
            },
        )

    delegate = _UnusedDelegate()
    lifecycle = BrepPanelGatewayLifecycle(
        delegate,
        "brep",
        transport=httpx.MockTransport(handler),
    )
    harness = governed_lifecycle_harness(lifecycle, server_id="brep")

    result = await harness.invoke(
        request_id="brep-request",
        progress_callback=lambda update: progress.append(dict(update)),
    )

    assert delegate.receipts == []
    assert requests == [
        ("/api/workspace/brep/panel", {"session_id": "gateway-session"}),
        (
            "/api/workspace/brep/tool",
            {
                "session_id": "gateway-session",
                "tool_name": "inspect",
                "arguments": {"value": 2},
            },
        ),
    ]
    assert result.result.structured_content == {"value": 2}
    assert [item["phase"] for item in progress[:2]] == [
        "lifecycle-starting",
        "lifecycle-ready",
    ]
    assert all(item["lifecycle"]["kind"] == "panel" for item in progress)
    assert progress[0]["lifecycle"]["visible_application"] is True
    assert harness.audit.events[-1]["metadata"]["lifecycle_kind"] == "panel"
    await harness.gateway.shutdown()


@pytest.mark.asyncio
async def test_bound_rivet_brep_failure_has_stable_recovery(
    governed_lifecycle_harness,
) -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "fixture unavailable"})

    lifecycle = BrepPanelGatewayLifecycle(
        _UnusedDelegate(),
        "brep",
        transport=httpx.MockTransport(handler),
    )
    harness = governed_lifecycle_harness(lifecycle, server_id="brep")

    with pytest.raises(RivetGatewayBridgeError) as caught:
        await harness.invoke(request_id="brep-failure")

    assert caught.value.code == "RIVET_MCP_PANEL_UNAVAILABLE"
    assert caught.value.recovery_action == "reopen_panel_and_inspect"
    await harness.gateway.shutdown()


@pytest.mark.asyncio
async def test_bound_rivet_brep_call_cancels_the_panel_request(
    governed_lifecycle_harness,
) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/panel"):
            return httpx.Response(200, json={"connected": True})
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    lifecycle = BrepPanelGatewayLifecycle(
        _UnusedDelegate(),
        "brep",
        transport=httpx.MockTransport(handler),
    )
    harness = governed_lifecycle_harness(lifecycle, server_id="brep")
    task = asyncio.create_task(harness.invoke(request_id="brep-cancel"))
    await started.wait()

    assert harness.gateway.cancel("gateway-session", "brep-cancel", "run_cancelled")
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set()
    await harness.gateway.shutdown()
