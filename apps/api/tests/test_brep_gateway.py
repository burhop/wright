from __future__ import annotations

import json

import httpx
import pytest

from api.brep_gateway import BrepPanelGatewayLifecycle


class _Delegate:
    def __init__(self) -> None:
        self.started = []
        self.called = []
        self.closed = False

    async def ensure_started(self, server_id, *, workspace_path, approval_context):
        self.started.append((server_id, workspace_path, approval_context))

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        self.called.append((server_id, tool_name, arguments, approval_context))
        return {"delegate": True}

    async def shutdown(self):
        self.closed = True


@pytest.mark.asyncio
async def test_brep_gateway_routes_panel_server_through_wright_api() -> None:
    requests: list[tuple[str, dict]] = []
    progress: list[dict] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append((request.url.path, payload))
        if request.url.path.endswith("/panel"):
            return httpx.Response(200, json={"connected": True})
        return httpx.Response(200, json={"structuredContent": {"connected": True}})

    delegate = _Delegate()
    lifecycle = BrepPanelGatewayLifecycle(
        delegate,
        "brep-server",
        transport=httpx.MockTransport(handler),
    )
    context = {"session_id": "session-1", "workspace_id": "workspace-1"}

    await lifecycle.ensure_started(
        "brep-server",
        workspace_path="D:\\workspace",
        approval_context=context,
    )
    result = await lifecycle.call_tool(
        "brep-server",
        "brep.app.status",
        {},
        approval_context=context,
        progress_callback=lambda update: progress.append(dict(update)),
    )

    assert delegate.started == []
    assert delegate.called == []
    assert requests == [
        ("/api/workspace/brep/panel", {"session_id": "session-1"}),
        (
            "/api/workspace/brep/tool",
            {
                "session_id": "session-1",
                "tool_name": "brep.app.status",
                "arguments": {},
            },
        ),
    ]
    assert result == {"structuredContent": {"connected": True}}
    assert [item["status"] for item in progress] == ["running", "completed"]
    assert progress[0]["title"] == "Opening BREP in Wright"
    assert progress[1]["title"] == "BREP panel ready"


@pytest.mark.asyncio
async def test_brep_gateway_delegates_other_servers() -> None:
    delegate = _Delegate()
    lifecycle = BrepPanelGatewayLifecycle(delegate, "brep-server")
    context = {"session_id": "session-1"}

    await lifecycle.ensure_started(
        "other-server",
        workspace_path="D:\\workspace",
        approval_context=context,
    )
    result = await lifecycle.call_tool(
        "other-server",
        "status",
        {},
        approval_context=context,
    )
    await lifecycle.shutdown()

    assert delegate.started
    assert delegate.called
    assert delegate.closed is True
    assert result == {"delegate": True}
