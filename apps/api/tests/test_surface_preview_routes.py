from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_preview import router
from api.surface_route_authority import AuthorizedSurfaceRoute, SurfaceRouteAuthority
from api.surface_websocket_proxy import WebSocketMessage
from workspace_service.surfaces.live_app_manager import LiveAppRoute, LiveAppRoutingPolicy
from workspace_service.surfaces.target_policy import ResolvedTargetPin


pytestmark = pytest.mark.workspace_surfaces
HOST = "s-presentation-1.preview.example.test"
ORIGIN = f"https://{HOST}"


def _pin(*, port: int = 8123) -> ResolvedTargetPin:
    return ResolvedTargetPin(
        scheme="http",
        numeric_address="127.0.0.1",
        port=port,
        source_hostname="127.0.0.1",
        host_header=f"127.0.0.1:{port}",
        server_name=None,
        base_path="/",
        resolved_answers=("127.0.0.1",),
        ownership="launched",
        ownership_proof="process-listener-proof",
        instance_id="instance-1",
        generation=3,
    )


class _Authority:
    def __init__(self, route: AuthorizedSurfaceRoute) -> None:
        self.route = route
        self.calls: list[tuple[str, str]] = []

    def authorize(self, *, host: str, cookie: str) -> AuthorizedSurfaceRoute:
        self.calls.append((host, cookie))
        return self.route


class _Body:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


class _HttpProxy:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any], bytes]] = []
        self.body = _Body([b"proxied"])

    async def forward(self, request, **kwargs):
        payload = b"".join([chunk async for chunk in request.body])
        self.calls.append((request, kwargs, payload))
        return SimpleNamespace(
            status=201,
            headers=(("Content-Type", "text/plain"), ("X-App", "nested")),
            body=self.body,
            aclose=self.body.aclose,
        )


class _SseProxy:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any]]] = []
        self.body = _Body([b": heartbeat\n\nid: 7\ndata: ready\n\n"])

    async def open(self, request, **kwargs):
        self.calls.append((request, kwargs))
        return SimpleNamespace(
            status=200,
            headers=(("Content-Type", "text/event-stream"),),
            body=self.body,
            aclose=self.body.aclose,
        )


class _WebSocketProxy:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    async def bridge(self, downstream, *, request, **kwargs):
        self.calls.append((request, kwargs))
        await downstream.accept(subprotocol=request.subprotocols[0])
        message = await downstream.receive()
        assert message == WebSocketMessage.text("ping")
        await downstream.send(WebSocketMessage.text("pong"))
        await downstream.close(code=1000, reason="complete")


@dataclass
class _ConfiguredPreview:
    client: TestClient
    authority: _Authority
    http: _HttpProxy
    sse: _SseProxy
    websocket: _WebSocketProxy
    activities: list[str]


def _configured_preview() -> _ConfiguredPreview:
    activities: list[str] = []
    route = AuthorizedSurfaceRoute(
        presentation_id="presentation-1",
        presentation_origin=ORIGIN,
        instance_id="instance-1",
        generation=3,
        pin=_pin(),
        http_declared=True,
        websocket_declared=True,
        sse_declared=True,
        limits=object(),
        authority_valid=lambda: True,
        target_valid=lambda: True,
        activity=lambda: activities.append("traffic"),
    )
    app = FastAPI()
    authority = _Authority(route)
    http = _HttpProxy()
    sse = _SseProxy()
    websocket = _WebSocketProxy()
    app.state.surface_route_authority = authority
    app.state.surface_http_proxy = http
    app.state.surface_sse_proxy = sse
    app.state.surface_websocket_proxy = websocket
    app.include_router(router)
    return _ConfiguredPreview(
        TestClient(app), authority, http, sse, websocket, activities
    )


def _headers(**extra: str) -> dict[str, str]:
    return {"Host": HOST, "Cookie": "wright_surface=C" * 1, **extra}


def test_all_http_methods_preserve_nested_target_query_headers_and_body() -> None:
    preview = _configured_preview()
    response = preview.client.patch(
        "/dash/assets/update?series=a%2Fb&point=7",
        headers=_headers(**{"X-App-Header": "chart"}),
        content=b'{"value":42}',
    )
    assert response.status_code == 201
    assert response.content == b"proxied"
    assert response.headers["x-app"] == "nested"
    request, options, payload = preview.http.calls[0]
    assert request.method == "PATCH"
    assert request.raw_path == "/dash/assets/update"
    assert request.raw_query == "series=a%2Fb&point=7"
    assert ("x-app-header", "chart") in tuple(
        (name.lower(), value) for name, value in request.headers
    )
    assert payload == b'{"value":42}'
    assert options["pin"] == _pin()
    assert options["authority_valid"]()
    assert options["target_valid"]()
    assert preview.http.body.closed
    assert preview.authority.calls == [(HOST, "C")]


def test_sse_accept_routes_only_through_declared_unbuffered_transport() -> None:
    preview = _configured_preview()
    response = preview.client.get(
        "/events?channel=graph",
        headers=_headers(Accept="text/event-stream", **{"Last-Event-ID": "6"}),
    )
    assert response.status_code == 200
    assert response.content == b": heartbeat\n\nid: 7\ndata: ready\n\n"
    request, options = preview.sse.calls[0]
    assert request.raw_path == "/events"
    assert request.raw_query == "channel=graph"
    assert request.sse_declared is True
    assert ("last-event-id", "6") in tuple(
        (name.lower(), value) for name, value in request.headers
    )
    assert options["pin"] == _pin()
    assert not preview.http.calls
    assert preview.sse.body.closed


def test_websocket_preserves_origin_subprotocol_path_query_and_frames() -> None:
    preview = _configured_preview()
    with preview.client.websocket_connect(
        "/socket/deep?room=alpha",
        headers=_headers(Origin=ORIGIN),
        subprotocols=["graph.v1"],
    ) as socket:
        socket.send_text("ping")
        assert socket.receive_text() == "pong"
    request, options = preview.websocket.calls[0]
    assert request.raw_path == "/socket/deep"
    assert request.raw_query == "room=alpha"
    assert request.origin == ORIGIN
    assert request.presentation_origin == ORIGIN
    assert request.subprotocols == ("graph.v1",)
    assert request.websocket_declared is True
    assert options["pin"] == _pin()


def test_reserved_control_paths_never_fall_through_or_require_runtime_state() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    for path in ("/api/secret", "/mcp", "/__wright/internal"):
        assert client.get(path, headers={"Host": HOST}).status_code == 404


class _Tokens:
    def __init__(self) -> None:
        self.active = True
        self.record = SimpleNamespace(
            presentation_id="presentation-1",
            workspace_id="workspace-1",
            instance_id="instance-1",
            generation=3,
            effective_origin=ORIGIN,
        )

    def authorize(self, *, host: str, cookie: str):
        assert (host, cookie) == (HOST, "C")
        if not self.active:
            from workspace_service.surfaces.presentation_tokens import (
                PresentationTokenError,
            )

            raise PresentationTokenError("revoked", "revoked", status_code=410)
        return self.record


class _Manager:
    def __init__(self) -> None:
        self.pin = _pin()
        self.activities = 0

    def resolve_route(self, instance_id: str, *, generation: int) -> LiveAppRoute:
        assert (instance_id, generation) == ("instance-1", 3)
        return LiveAppRoute(
            LiveAppRoutingPolicy(instance_id, generation, True, True, True, object()),
            self.pin,
        )

    def record_route_activity(self, instance_id: str) -> None:
        assert instance_id == "instance-1"
        self.activities += 1


def test_route_authority_revalidates_cookie_generation_and_immutable_pin() -> None:
    tokens = _Tokens()
    manager = _Manager()
    authority = SurfaceRouteAuthority(
        tokens=tokens, manager_for_workspace=lambda workspace_id: manager
    )
    route = authority.authorize(host=HOST, cookie="C")
    assert route.authority_valid()
    assert route.target_valid()
    route.activity()
    assert manager.activities == 1

    tokens.active = False
    assert not route.authority_valid()
    manager.pin = _pin(port=8124)
    assert not route.target_valid()
