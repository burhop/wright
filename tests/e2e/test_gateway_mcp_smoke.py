from __future__ import annotations

import anyio
import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class _TestClientTransport(httpx.AsyncBaseTransport):
    def __init__(self, client) -> None:
        self.client = client

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(405, request=request)
        body = await request.aread()

        def send():
            return self.client.request(
                request.method,
                str(request.url),
                headers=dict(request.headers),
                content=body,
            )

        response = await anyio.to_thread.run_sync(send)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )


@pytest.mark.asyncio
@pytest.mark.mcp_protocol
async def test_official_sdk_streamable_http_list_call_and_resource(
    offline_api_client, gateway_smoke_seed
) -> None:
    headers = {
        **gateway_smoke_seed["headers"],
        "Host": "localhost",
    }
    async with httpx.AsyncClient(
        transport=_TestClientTransport(offline_api_client),
        headers=headers,
    ) as http_client:
        async with streamable_http_client(
            "http://localhost/mcp", http_client=http_client
        ) as (read_stream, write_stream, session_id):
            async with ClientSession(read_stream, write_stream) as client:
                initialized = await client.initialize()
                assert str(initialized.protocolVersion) == "2025-11-25"
                assert session_id()
                tools = await client.list_tools()
                assert gateway_smoke_seed["tool_name"] in {
                    item.name for item in tools.tools
                }
                result = await client.call_tool(
                    gateway_smoke_seed["tool_name"], {"ping": True}
                )
                assert not result.isError
                resources = await client.list_resources()
                assert "wright://workspace/smoke-workspace" in {
                    str(item.uri) for item in resources.resources
                }
                missing = await client.call_tool("foreign__tool", {})
                assert missing.isError
                assert missing.structuredContent == {"error": "not_found"}
