from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect

from test_surface_webmcp import (
    ORIGIN_A,
    _client,
    _registration,
    _route,
)
from tool_registry.webmcp_router import WebMcpRouter


def test_wrong_origin_is_denied_before_registration() -> None:
    webmcp = WebMcpRouter()
    client = _client(_route("surface-one", ORIGIN_A), webmcp)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/__wright/webmcp",
            headers={
                "Host": "s-one.preview.example.test",
                "Origin": "https://evil.example.test",
            },
            cookies={"wright_surface": "cookie"},
        ):
            pass
    assert (
        webmcp.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        )
        == ()
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update({"jsonrpc": "1.0"}),
        lambda payload: payload["payload"]["tool"].update(
            {"inputSchema": {"type": "array"}}
        ),
        lambda payload: payload["payload"]["tool"].update({"description": "x" * 3000}),
    ],
)
def test_malformed_schema_and_oversized_registration_close_fail_closed(
    mutation,
) -> None:
    webmcp = WebMcpRouter(maximum_message_bytes=4096)
    client = _client(_route("surface-one", ORIGIN_A), webmcp)
    payload = _registration()
    mutation(payload)
    with client.websocket_connect(
        "/__wright/webmcp",
        headers={"Host": "s-one.preview.example.test", "Origin": ORIGIN_A},
        cookies={"wright_surface": "cookie"},
    ) as socket:
        assert socket.receive_json()["operation"] == "webmcp.connected"
        socket.send_json(payload)
        with pytest.raises(WebSocketDisconnect):
            socket.receive_json()
    assert (
        webmcp.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        )
        == ()
    )


def test_disconnect_removes_registration_immediately() -> None:
    webmcp = WebMcpRouter()
    client = _client(_route("surface-one", ORIGIN_A), webmcp)
    with client.websocket_connect(
        "/__wright/webmcp",
        headers={"Host": "s-one.preview.example.test", "Origin": ORIGIN_A},
        cookies={"wright_surface": "cookie"},
    ) as socket:
        assert socket.receive_json()["operation"] == "webmcp.connected"
        socket.send_json(_registration())
        socket.receive_json()
        assert (
            len(
                webmcp.matching(
                    workspace_id="workspace-1",
                    server_id="web-app",
                    tool_name="select_part",
                )
            )
            == 1
        )
    assert (
        webmcp.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        )
        == ()
    )
