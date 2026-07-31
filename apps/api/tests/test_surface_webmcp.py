from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_preview import router as preview_router
from api.surface_route_authority import AuthorizedSurfaceRoute
from tool_registry.webmcp_router import WebMcpRouter


ORIGIN_A = "https://s-one.preview.example.test"
ORIGIN_B = "https://s-two.preview.example.test"


class _Authority:
    def __init__(self, route: AuthorizedSurfaceRoute) -> None:
        self.route = route

    def authorize(self, *, host: str, cookie: str) -> AuthorizedSurfaceRoute:
        assert cookie == "cookie"
        return self.route


def _route(surface_id: str, origin: str) -> AuthorizedSurfaceRoute:
    return AuthorizedSurfaceRoute(
        presentation_id=f"presentation-{surface_id}",
        presentation_origin=origin,
        principal_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        surface_id=surface_id,
        source_id="web-app",
        instance_id=f"instance-{surface_id}",
        generation=3,
        pin=object(),
        http_declared=True,
        websocket_declared=True,
        sse_declared=False,
        limits=object(),
        authority_valid=lambda: True,
        target_valid=lambda: True,
        activity=lambda: None,
    )


def _client(route: AuthorizedSurfaceRoute, webmcp: WebMcpRouter) -> TestClient:
    app = FastAPI()
    app.state.surface_route_authority = _Authority(route)
    app.state.surface_webmcp_router = webmcp
    app.include_router(preview_router)
    return TestClient(app)


def _registration(
    call_id: str | None = None,
    *,
    surface_id: str = "surface-one",
    origin: str = ORIGIN_A,
    operation: str = "webmcp.register",
) -> dict:
    now = datetime.now(UTC)
    return {
        "protocolVersion": "1.0",
        "kind": "request",
        "messageId": call_id or str(uuid.uuid4()),
        "correlationId": str(uuid.uuid4()),
        "binding": {
            "workspaceId": "workspace-1",
            "sessionId": "session-1",
            "surfaceId": surface_id,
            "instanceId": f"instance-{surface_id}",
            "generation": 3,
            "documentOrigin": origin,
            "serverId": "web-app",
        },
        "operation": operation,
        "toolName": "select_part",
        "sequence": 0,
        "createdAt": now.isoformat(),
        "deadlineAt": (now + timedelta(seconds=30)).isoformat(),
        "payload": {
            "tool": {
                "name": "select_part",
                "description": "Select a visible part",
                "inputSchema": {
                    "type": "object",
                    "properties": {"partId": {"type": "string"}},
                    "required": ["partId"],
                },
            }
        },
    }


def test_two_same_name_pages_register_under_distinct_surface_identity() -> None:
    webmcp = WebMcpRouter()
    first = _client(_route("surface-one", ORIGIN_A), webmcp)
    second = _client(_route("surface-two", ORIGIN_B), webmcp)
    headers_a = {"Host": "s-one.preview.example.test", "Origin": ORIGIN_A}
    headers_b = {"Host": "s-two.preview.example.test", "Origin": ORIGIN_B}

    with first.websocket_connect(
        "/__wright/webmcp", headers=headers_a, cookies={"wright_surface": "cookie"}
    ) as socket_a, second.websocket_connect(
        "/__wright/webmcp", headers=headers_b, cookies={"wright_surface": "cookie"}
    ) as socket_b:
        socket_a.send_json(
            _registration("11111111-1111-4111-8111-111111111111")
        )
        socket_b.send_json(
            _registration("22222222-2222-4222-8222-222222222222", surface_id="surface-two", origin=ORIGIN_B)
        )
        assert socket_a.receive_json()["operation"] == "webmcp.connected"
        assert socket_b.receive_json()["operation"] == "webmcp.connected"
        ack_a = socket_a.receive_json()
        ack_b = socket_b.receive_json()
        assert ack_a["payload"] == {"registered": True}
        assert ack_b["payload"] == {"registered": True}
        assert ack_a["binding"]["surfaceId"] == "surface-one"
        assert ack_b["binding"]["surfaceId"] == "surface-two"
        matches = webmcp.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        )
        assert {item.surface_id for item in matches} == {
            "surface-one",
            "surface-two",
        }

    assert webmcp.matching(
        workspace_id="workspace-1",
        server_id="web-app",
        tool_name="select_part",
    ) == ()


def test_unregister_uses_exact_generation_origin_server_and_tool_binding() -> None:
    webmcp = WebMcpRouter()
    route = _route("surface-one", ORIGIN_A)
    client = _client(route, webmcp)
    headers = {"Host": "s-one.preview.example.test", "Origin": ORIGIN_A}
    with client.websocket_connect(
        "/__wright/webmcp", headers=headers, cookies={"wright_surface": "cookie"}
    ) as socket:
        assert socket.receive_json()["operation"] == "webmcp.connected"
        socket.send_json(_registration())
        socket.receive_json()
        unregister = _registration(operation="webmcp.unregister")
        socket.send_json(unregister)
        assert socket.receive_json()["payload"] == {"unregistered": True}
        assert webmcp.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        ) == ()
