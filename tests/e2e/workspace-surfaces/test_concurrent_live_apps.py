from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

import pytest

from api.surface_http_proxy import HttpProxyError, ProxyHttpRequest, SurfaceHttpProxy
from workspace_service.config import SurfacePolicySettings
from workspace_service.surfaces.limits import SurfaceLimitPolicy
from workspace_service.surfaces.target_policy import ResolvedTargetPin


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.anyio]


async def _empty_body():
    if False:
        yield b""


@dataclass
class _IsolatedRuntime:
    instance_id: str
    generation: int
    port: int
    active: bool = True
    healthy: bool = True
    logs: list[str] = field(default_factory=list)

    def pin(self) -> ResolvedTargetPin:
        return ResolvedTargetPin(
            scheme="http",
            numeric_address="127.0.0.1",
            port=self.port,
            source_hostname="127.0.0.1",
            host_header=f"127.0.0.1:{self.port}",
            server_name=None,
            base_path="/",
            resolved_answers=("127.0.0.1",),
            ownership="launched",
            ownership_proof="process-listener-proof",
            instance_id=self.instance_id,
            generation=self.generation,
        )


async def _server(instance_id: str):
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request = await reader.readuntil(b"\r\n\r\n")
        lines = request.decode("latin-1").split("\r\n")
        method, target, _version = lines[0].split(" ", 2)
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                name, value = line.split(":", 1)
                headers[name.lower()] = value.strip()
        body = json.dumps(
            {
                "instance": instance_id,
                "method": method,
                "target": target,
                "cookie": headers.get("cookie", ""),
            },
            separators=(",", ":"),
        ).encode()
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = int(server.sockets[0].getsockname()[1])
    return server, port


async def _read(response) -> dict:
    try:
        payload = b"".join([chunk async for chunk in response.body])
        return json.loads(payload)
    finally:
        await response.aclose()


async def test_two_apps_and_same_app_isolated_instances_never_cross_routes_or_state() -> None:
    server_a, port_a = await _server("app-a-shared")
    server_b, port_b = await _server("app-b-shared")
    server_isolated, port_isolated = await _server("app-a-isolated")
    runtimes = {
        "presentation-a": _IsolatedRuntime("app-a-shared", 1, port_a),
        "presentation-b": _IsolatedRuntime("app-b-shared", 1, port_b),
        "presentation-isolated": _IsolatedRuntime(
            "app-a-isolated", 1, port_isolated
        ),
    }
    limits = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "requests_per_presentation_per_minute": 1000,
            "request_burst": 1000,
            "connections_per_app": 100,
            "stream_bytes_per_second": 10 * 1024 * 1024,
            "stream_burst_bytes": 10 * 1024 * 1024,
        }
    )
    proxy = SurfaceHttpProxy()

    async def interact(index: int) -> tuple[str, dict]:
        presentation_id = tuple(runtimes)[index % len(runtimes)]
        runtime = runtimes[presentation_id]
        response = await proxy.forward(
            ProxyHttpRequest(
                method="GET",
                raw_path=f"/nested/chart/{index}",
                raw_query=f"series={presentation_id}&point={index}",
                headers=(
                    ("Host", f"s-{presentation_id}.preview.test"),
                    (
                        "Cookie",
                        f"wright_surface=private-{presentation_id}; "
                        f"app_session=session-{runtime.instance_id}",
                    ),
                ),
                body=_empty_body(),
                presentation_id=presentation_id,
            ),
            pin=runtime.pin(),
            limits=limits,
            authority_valid=lambda: runtime.active,
            target_valid=lambda: runtime.active,
            activity=lambda: runtime.logs.append(f"{presentation_id}:request:{index}"),
        )
        return presentation_id, await _read(response)

    try:
        results = await asyncio.gather(*(interact(index) for index in range(100)))
        for presentation_id, payload in results:
            runtime = runtimes[presentation_id]
            assert payload["instance"] == runtime.instance_id
            assert f"series={presentation_id}" in payload["target"]
            assert payload["cookie"] == f"app_session=session-{runtime.instance_id}"
            assert "wright_surface" not in payload["cookie"]
        assert sum(len(runtime.logs) for runtime in runtimes.values()) == 200
        for presentation_id, runtime in runtimes.items():
            assert all(item.startswith(f"{presentation_id}:") for item in runtime.logs)
        assert all(runtime.healthy for runtime in runtimes.values())

        stopped = runtimes["presentation-isolated"]
        stopped.active = False
        stopped.healthy = False
        with pytest.raises(HttpProxyError) as denied:
            await interact(101)
        assert denied.value.code == "SURFACE_PRESENTATION_REVOKED"

        presentation_id, payload = await interact(102)
        assert presentation_id == "presentation-a"
        assert payload["instance"] == "app-a-shared"
        assert runtimes["presentation-b"].active
        assert runtimes["presentation-b"].healthy
        assert all(
            item.startswith("presentation-a:")
            for item in runtimes["presentation-a"].logs
        )
    finally:
        await proxy.aclose()
        for server in (server_a, server_b, server_isolated):
            server.close()
            await server.wait_closed()
