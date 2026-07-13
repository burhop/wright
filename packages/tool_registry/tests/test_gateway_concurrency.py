from __future__ import annotations

import anyio
import pytest
from mcp import ClientSession

from tool_registry.mcp_stdio import StdioGatewayBinding, run_mcp_streams
from test_gateway_service import service


@pytest.mark.asyncio
async def test_one_hundred_responses_remain_decodable_amid_notifications() -> None:
    gateway, _, _ = service()
    binding = StdioGatewayBinding("mixed-stress", "stdio:789", "w1")
    gateway.workspaces.bindings["mixed-stress"] = (
        "stdio:789",
        "w1",
        "/workspace/one",
    )
    client_write, server_read = anyio.create_memory_object_stream(300)
    server_write, client_read = anyio.create_memory_object_stream(300)
    notifications = 0

    async def handle(message) -> None:
        nonlocal notifications
        if type(getattr(message, "root", None)).__name__.endswith(
            "ListChangedNotification"
        ):
            notifications += 1

    async with anyio.create_task_group() as group:
        group.start_soon(run_mcp_streams, gateway, binding, server_read, server_write)
        async with ClientSession(
            client_read, client_write, message_handler=handle
        ) as client:
            await client.initialize()
            await client.list_tools()
            with anyio.fail_after(1):
                while gateway.notifier.subscriber_count("w1") != 1:
                    await anyio.sleep(0)

            results = []

            async def call(index: int) -> None:
                results.append(await client.call_tool("cad__run", {"message": index}))

            async with anyio.create_task_group() as calls:
                for index in range(100):
                    calls.start_soon(call, index)
                    gateway.notifier.publish(
                        workspace_id="w1", event="tools/list_changed"
                    )

            assert len(results) == 100
            assert all(item.structuredContent["workspace"] == "w1" for item in results)
            with anyio.fail_after(1):
                while notifications < 100:
                    await anyio.sleep(0)
        group.cancel_scope.cancel()
