from __future__ import annotations

import asyncio
import gzip
from contextlib import asynccontextmanager

import pytest

from api.surface_http_proxy import (
    HttpProxyError,
    ProxyHttpRequest,
    SurfaceHttpProxy,
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
            header_block = await reader.readuntil(b"\r\n\r\n")
            lines = header_block.decode("latin-1").split("\r\n")
            method, target, _version = lines[0].split(" ", 2)
            headers = [tuple(line.split(":", 1)) for line in lines[1:] if ":" in line]
            length = next(
                (
                    int(value.strip())
                    for name, value in headers
                    if name.lower() == "content-length"
                ),
                0,
            )
            body = await reader.readexactly(length) if length else b""
            observations.append((method, target, headers, body))
            path = target.split("?", 1)[0]
            if path == "/base/gzip":
                payload = gzip.compress(b"compressed-response")
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Length: "
                    + str(len(payload)).encode()
                    + b"\r\n\r\n"
                    + payload
                )
            elif path == "/base/chunk":
                writer.write(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n")
                for part in (b"first-", b"second"):
                    writer.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
                    await writer.drain()
                    await asyncio.sleep(0.01)
                writer.write(b"0\r\n\r\n")
            elif path == "/base/status204":
                writer.write(b"HTTP/1.1 204 No Content\r\nContent-Length: 4\r\n\r\noops")
            elif path == "/base/status304":
                writer.write(b"HTTP/1.1 304 Not Modified\r\nContent-Length: 4\r\n\r\noops")
            elif path == "/base/redirect":
                writer.write(
                    b"HTTP/1.1 302 Found\r\nLocation: /base/next?tab=1\r\nContent-Length: 0\r\n\r\n"
                )
            elif path == "/base/evil-redirect":
                writer.write(
                    b"HTTP/1.1 302 Found\r\nLocation: https://evil.example/\r\nContent-Length: 0\r\n\r\n"
                )
            elif path == "/base/informational":
                writer.write(
                    b"HTTP/1.1 103 Early Hints\r\nLink: </style.css>; rel=preload\r\n\r\n"
                    b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nfinal"
                )
            elif path == "/base/slow":
                writer.write(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n")
                for _ in range(100):
                    writer.write(b"4\r\ndata\r\n")
                    await writer.drain()
                    await asyncio.sleep(0.05)
            else:
                payload = method.encode() + b"|" + target.encode() + b"|" + body
                writer.write(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Set-Cookie: one=1; Domain=.example.test; Path=/\r\n"
                    b"Set-Cookie: two=2; Path=/\r\n"
                    b"Content-Length: " + str(len(payload)).encode() + b"\r\n\r\n" + payload
                )
            await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError, BrokenPipeError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        yield port, observations
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


def _limits():
    return SurfaceLimitPolicy(SurfacePolicySettings()).compose()


async def _body(value: bytes):
    yield value


async def _read(response) -> bytes:
    return b"".join([chunk async for chunk in response.body])


async def test_preserves_method_path_query_body_duplicates_and_target_cookies() -> None:
    async with _upstream() as (port, observations):
        proxy = SurfaceHttpProxy()
        response = await proxy.forward(
            ProxyHttpRequest(
                method="PATCH",
                raw_path="/items/42",
                raw_query="a=1&a=2",
                headers=(
                    ("X-Duplicate", "one"),
                    ("X-Duplicate", "two"),
                    ("Cookie", "wright_surface=secret; app=ok"),
                    ("Content-Length", "7"),
                ),
                body=_body(b"payload"),
                presentation_id="presentation-1",
            ),
            pin=_pin(port),
            limits=_limits(),
        )
        body = await _read(response)
        await proxy.aclose()

    assert body == b"PATCH|/base/items/42?a=1&a=2|payload"
    _method, _target, headers, _body_value = observations[0]
    duplicates = [value.strip() for name, value in headers if name.lower() == "x-duplicate"]
    assert duplicates == ["one", "two"]
    cookie = next(value.strip() for name, value in headers if name.lower() == "cookie")
    assert cookie == "app=ok"
    assert response.headers.count(("Set-Cookie", "one=1; Path=/")) == 1
    assert response.headers.count(("Set-Cookie", "two=2; Path=/")) == 1


async def test_streams_compressed_and_chunked_responses_without_semantic_rewrite() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceHttpProxy()
        compressed = await proxy.forward(
            ProxyHttpRequest.get("/gzip", presentation_id="p-1"),
            pin=_pin(port),
            limits=_limits(),
        )
        encoded = await _read(compressed)
        assert gzip.decompress(encoded) == b"compressed-response"

        chunked = await proxy.forward(
            ProxyHttpRequest.get("/chunk", presentation_id="p-1"),
            pin=_pin(port),
            limits=_limits(),
        )
        assert await _read(chunked) == b"first-second"
        await proxy.aclose()


async def test_no_body_status_redirect_and_informational_limitations_are_exact() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceHttpProxy()
        for path, status in (("/status204", 204), ("/status304", 304)):
            response = await proxy.forward(
                ProxyHttpRequest.get(path, presentation_id="p-1"),
                pin=_pin(port),
                limits=_limits(),
            )
            assert response.status == status
            assert await _read(response) == b""

        redirect = await proxy.forward(
            ProxyHttpRequest.get("/redirect", presentation_id="p-1"),
            pin=_pin(port),
            limits=_limits(),
        )
        assert ("Location", "/base/next?tab=1") in redirect.headers
        with pytest.raises(HttpProxyError) as raised:
            await proxy.forward(
                ProxyHttpRequest.get("/evil-redirect", presentation_id="p-1"),
                pin=_pin(port),
                limits=_limits(),
            )
        assert raised.value.code == "SURFACE_TARGET_REDIRECT_REJECTED"

        informational = await proxy.forward(
            ProxyHttpRequest.get("/informational", presentation_id="p-1"),
            pin=_pin(port),
            limits=_limits(),
        )
        assert informational.status == 200
        assert await _read(informational) == b"final"
        assert proxy.informational_response_support == "upstream-adapter-not-exposed"
        await proxy.aclose()


async def test_trace_is_denied_and_cancellation_closes_upstream_stream() -> None:
    async with _upstream() as (port, _observations):
        proxy = SurfaceHttpProxy()
        with pytest.raises(HttpProxyError) as raised:
            await proxy.forward(
                ProxyHttpRequest(
                    "TRACE", "/", "", (), _body(b""), "p-1"
                ),
                pin=_pin(port),
                limits=_limits(),
            )
        assert raised.value.code == "SURFACE_PROTOCOL_METHOD_DENIED"

        response = await proxy.forward(
            ProxyHttpRequest.get("/slow", presentation_id="p-1"),
            pin=_pin(port),
            limits=_limits(),
        )
        iterator = response.body.__aiter__()
        await iterator.__anext__()
        await response.aclose()
        await proxy.aclose()
