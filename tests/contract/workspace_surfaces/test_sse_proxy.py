from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest

from api.surface_sse_proxy import (
    SseProxyError,
    SseProxyRequest,
    SurfaceSseProxy,
)
from workspace_service.config import SurfacePolicySettings
from workspace_service.surfaces.limits import SurfaceLimitPolicy
from workspace_service.surfaces.target_policy import ResolvedTargetPin


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


@asynccontextmanager
async def _upstream():
    observations = []

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            block = await reader.readuntil(b"\r\n\r\n")
            lines = block.decode("latin-1").split("\r\n")
            _method, target, _version = lines[0].split(" ", 2)
            headers = [tuple(line.split(":", 1)) for line in lines[1:] if ":" in line]
            observations.append((target, headers))
            path = target.split("?", 1)[0]
            if path == "/base/end":
                writer.write(b"HTTP/1.1 204 No Content\r\n\r\n")
            else:
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n"
                    b"Cache-Control: no-cache\r\nTransfer-Encoding: chunked\r\n\r\n"
                )
                await writer.drain()
                if path == "/base/silent":
                    await asyncio.sleep(2)
                elif path == "/base/idle":
                    part = b": first heartbeat\n\n"
                    writer.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
                    await writer.drain()
                    await asyncio.sleep(2)
                elif path == "/base/revoked":
                    for _ in range(100):
                        part = b": heartbeat\n\n"
                        writer.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
                        await writer.drain()
                        await asyncio.sleep(0.02)
                else:
                    for part in (
                        b": heartbeat\n\n",
                        b"id: 42\nretry: 1000\ndata: hello\n\n",
                    ):
                        writer.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
                        await writer.drain()
                        await asyncio.sleep(0.01)
                    writer.write(b"0\r\n\r\n")
            await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError, BrokenPipeError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1], observations
    finally:
        server.close()
        await server.wait_closed()


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


def _request(path="/events", headers=()) -> SseProxyRequest:
    return SseProxyRequest(
        raw_path=path,
        raw_query="channel=one",
        headers=tuple(headers),
        presentation_id="presentation-1",
        sse_declared=True,
    )


def _limits(**administrator):
    return SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator=administrator
    )


async def _read(stream) -> bytes:
    return b"".join([chunk async for chunk in stream.body])


async def test_preserves_comments_heartbeat_retry_id_and_last_event_id_without_buffering() -> None:
    async with _upstream() as (port, observations):
        proxy = SurfaceSseProxy()
        stream = await proxy.open(
            _request(headers=(("Last-Event-ID", "41"),)),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        body = await _read(stream)
        await proxy.aclose()

    assert body == b": heartbeat\n\nid: 42\nretry: 1000\ndata: hello\n\n"
    assert ("Cache-Control", "no-cache") in stream.headers
    target, headers = observations[0]
    assert target == "/base/events?channel=one"
    assert next(value.strip() for name, value in headers if name.lower() == "last-event-id") == "41"


async def test_204_terminates_without_event_stream_body() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceSseProxy()
        stream = await proxy.open(
            _request("/end"),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        assert stream.status == 204
        assert await _read(stream) == b""
        await proxy.aclose()


async def test_heartbeat_idle_deadline_and_revocation_fail_closed() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceSseProxy(revalidation_seconds=0.01)
        with pytest.raises(SseProxyError) as idle:
            await proxy.open(
                _request("/silent"),
                pin=_pin(port),
                limits=_limits(first_byte_timeout_seconds=1),
                authority_valid=lambda: True,
                target_valid=lambda: True,
            )
        assert idle.value.code == "SURFACE_LIMIT_FIRST_BYTE"

        heartbeat = await proxy.open(
            _request("/idle"),
            pin=_pin(port),
            limits=_limits(stream_heartbeat_idle_seconds=1),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        heartbeat_iterator = heartbeat.body.__aiter__()
        assert await heartbeat_iterator.__anext__() == b": first heartbeat\n\n"
        with pytest.raises(SseProxyError) as heartbeat_idle:
            await heartbeat_iterator.__anext__()
        assert heartbeat_idle.value.code == "SURFACE_LIMIT_IDLE"

        deadline = await proxy.open(
            _request("/revoked"),
            pin=_pin(port),
            limits=_limits(live_connection_lifetime_seconds=1),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        with pytest.raises(SseProxyError) as lifetime:
            async for _chunk in deadline.body:
                pass
        assert lifetime.value.code == "SURFACE_LIMIT_LIFETIME"

        allowed = [True]
        stream = await proxy.open(
            _request("/revoked"),
            pin=_pin(port),
            limits=_limits(stream_heartbeat_idle_seconds=1),
            authority_valid=lambda: allowed[0],
            target_valid=lambda: True,
        )
        iterator = stream.body.__aiter__()
        await iterator.__anext__()
        allowed[0] = False
        with pytest.raises(SseProxyError) as revoked:
            await iterator.__anext__()
        assert revoked.value.code == "SURFACE_PRESENTATION_REVOKED"
        await stream.aclose()
        await proxy.aclose()


async def test_disconnect_closes_upstream_and_undeclared_sse_is_denied() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceSseProxy()
        with pytest.raises(SseProxyError) as undeclared:
            await proxy.open(
                SseProxyRequest("/events", "", (), "p-1", False),
                pin=_pin(port),
                limits=_limits(),
                authority_valid=lambda: True,
                target_valid=lambda: True,
            )
        assert undeclared.value.code == "SURFACE_PROTOCOL_TRANSPORT_UNDECLARED"

        stream = await proxy.open(
            _request("/revoked"),
            pin=_pin(port),
            limits=_limits(),
            authority_valid=lambda: True,
            target_valid=lambda: True,
        )
        await stream.body.__aiter__().__anext__()
        await stream.aclose()
        await proxy.aclose()
