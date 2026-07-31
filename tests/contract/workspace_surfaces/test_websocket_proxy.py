from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from api.surface_websocket_proxy import (
    SurfaceWebSocketProxy,
    WebSocketMessage,
    WebSocketProxyError,
    WebSocketProxyRequest,
)
from workspace_service.config import SurfacePolicySettings
from workspace_service.surfaces.limits import SurfaceLimitPolicy
from workspace_service.surfaces.target_policy import ResolvedTargetPin


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


@asynccontextmanager
async def _upstream():
    connections = []

    async def echo(websocket):
        connections.append(websocket.subprotocol)
        try:
            async for message in websocket:
                if message == "close-upstream":
                    await websocket.close(code=4001, reason="upstream done")
                    return
                await websocket.send(message)
        except ConnectionClosed:
            return

    async with serve(echo, "127.0.0.1", 0, subprotocols=["graph.v1"]) as server:
        yield server.sockets[0].getsockname()[1], connections


class Downstream:
    def __init__(self, messages=()) -> None:
        self.incoming = asyncio.Queue()
        for message in messages:
            self.incoming.put_nowait(message)
        self.accepted = None
        self.sent = []
        self.closed = None
        self.active_sends = 0
        self.maximum_active_sends = 0

    async def accept(self, *, subprotocol=None):
        self.accepted = subprotocol

    async def receive(self):
        message = await self.incoming.get()
        if message.kind == "close":
            await asyncio.sleep(0.03)
        return message

    async def send(self, message):
        self.active_sends += 1
        self.maximum_active_sends = max(self.maximum_active_sends, self.active_sends)
        await asyncio.sleep(0)
        self.sent.append(message)
        self.active_sends -= 1

    async def close(self, *, code, reason=""):
        self.closed = (code, reason)


def _pin(port: int) -> ResolvedTargetPin:
    return ResolvedTargetPin(
        scheme="http",
        numeric_address="127.0.0.1",
        port=port,
        source_hostname="app.example.test",
        host_header=f"app.example.test:{port}",
        server_name=None,
        base_path="/base/",
        resolved_answers=("127.0.0.1",),
        ownership="launched",
        ownership_proof="process-listener-identity",
        instance_id="instance-1",
        generation=1,
    )


def _request(**changes) -> WebSocketProxyRequest:
    values = {
        "raw_path": "/socket",
        "raw_query": "room=one",
        "origin": "http://preview.localhost:8000",
        "presentation_origin": "http://preview.localhost:8000",
        "subprotocols": ("graph.v1",),
        "headers": (),
        "presentation_id": "presentation-1",
        "websocket_declared": True,
    }
    values.update(changes)
    return WebSocketProxyRequest(**values)


def _limits(**administrator):
    return SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator=administrator
    )


async def test_real_text_binary_subprotocol_ordering_and_close() -> None:
    async with _upstream() as (port, connections):
        downstream = Downstream(
            (
                WebSocketMessage.text("hello"),
                WebSocketMessage.binary(b"\x00\x01"),
                WebSocketMessage.close(1000, "done"),
            )
        )
        result = await SurfaceWebSocketProxy().bridge(
            downstream,
            request=_request(),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )

    assert downstream.accepted == "graph.v1"
    assert downstream.sent == [
        WebSocketMessage.text("hello"),
        WebSocketMessage.binary(b"\x00\x01"),
    ]
    assert downstream.maximum_active_sends == 1
    assert result.close_code == 1000
    assert connections == ["graph.v1"]


async def test_origin_declaration_size_and_rate_limits_fail_closed() -> None:
    proxy = SurfaceWebSocketProxy()
    with pytest.raises(WebSocketProxyError) as origin:
        await proxy.bridge(
            Downstream(),
            request=_request(origin="https://evil.example"),
            pin=_pin(1),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
    assert origin.value.code == "SURFACE_PROTOCOL_ORIGIN_MISMATCH"

    with pytest.raises(WebSocketProxyError) as declaration:
        await proxy.bridge(
            Downstream(),
            request=_request(websocket_declared=False),
            pin=_pin(1),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
    assert declaration.value.code == "SURFACE_PROTOCOL_TRANSPORT_UNDECLARED"

    async with _upstream() as (port, _connections):
        too_large = Downstream(
            (WebSocketMessage.binary(b"12345"), WebSocketMessage.close(1000))
        )
        result = await proxy.bridge(
            too_large,
            request=_request(),
            pin=_pin(port),
            limits=_limits(websocket_message_bytes=4),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        assert result.close_code == 1009

    async with _upstream() as (port, _connections):
        too_fast = Downstream(
            (
                WebSocketMessage.text("one"),
                WebSocketMessage.text("two"),
                WebSocketMessage.close(1000),
            )
        )
        result = await proxy.bridge(
            too_fast,
            request=_request(),
            pin=_pin(port),
            limits=_limits(
                websocket_messages_per_second=1,
                websocket_message_burst=1,
            ),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        assert result.outcome == "limit"
        assert result.close_code == 1008


async def test_reconnect_reauthorizes_and_revocation_tears_down_both_halves() -> None:
    async with _upstream() as (port, connections):
        checks = 0

        def authority():
            nonlocal checks
            checks += 1
            return True

        proxy = SurfaceWebSocketProxy(revalidation_seconds=0.01)
        for _ in range(2):
            await proxy.bridge(
                Downstream((WebSocketMessage.close(1000),)),
                request=_request(),
                pin=_pin(port),
                limits=_limits(),
                authority_valid=authority,
                target_valid=lambda: True,
            )
        assert len(connections) == 2
        assert checks >= 2

        allowed = [True]
        downstream = Downstream()

        async def revoke():
            await asyncio.sleep(0.03)
            allowed[0] = False

        task = asyncio.create_task(revoke())
        result = await proxy.bridge(
            downstream,
            request=_request(),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: allowed[0],
            target_valid=lambda: True,
        )
        await task
        assert result.outcome == "revoked"
        assert result.close_code == 1008


async def test_upstream_close_code_and_reason_are_preserved() -> None:
    async with _upstream() as (port, _connections):
        downstream = Downstream((WebSocketMessage.text("close-upstream"),))
        result = await SurfaceWebSocketProxy().bridge(
            downstream,
            request=_request(),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        assert result.close_code == 4001
        assert result.close_reason == "upstream done"
        assert downstream.closed == (4001, "upstream done")
