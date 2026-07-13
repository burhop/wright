from __future__ import annotations

import asyncio
import anyio
import pytest
import mcp.types as types
from mcp import ClientSession

from tool_registry.mcp_server import create_mcp_server, initialization_options
from test_gateway_service import service


@pytest.mark.asyncio
async def test_official_sdk_initialize_list_call_and_resources() -> None:
    gateway, lifecycle, audit = service()
    server = create_mcp_server(gateway, "s1")
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(client_read, client_write) as client:
            initialized = await client.initialize()
            assert initialized.serverInfo.name == "wright-gateway"
            assert (
                initialized.instructions and "authoritative" in initialized.instructions
            )

            tools = await client.list_tools()
            assert [tool.name for tool in tools.tools] == ["cad__run"]
            assert tools.tools[0].outputSchema == {"type": "object"}
            assert tools.tools[0].meta["wright/safetyReviewed"] is True

            result = await client.call_tool("cad__run", {"shape": "cube"})
            assert not result.isError
            assert result.structuredContent == {"server": "cad", "workspace": "w1"}

            resources = await client.list_resources()
            assert any(
                str(item.uri) == "wright://workspace/w1" for item in resources.resources
            )
            workspace = await client.read_resource("wright://workspace/w1")
            assert '"workspace_id": "w1"' in workspace.contents[0].text

        group.cancel_scope.cancel()

    assert lifecycle.calls[0][0] == "cad"
    assert any(event["outcome"] == "succeeded" for event in audit.events)


@pytest.mark.asyncio
async def test_official_sdk_returns_stable_error_for_foreign_tool() -> None:
    gateway, _, _ = service()
    server = create_mcp_server(gateway, "s1")
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            result = await client.call_tool("fea__run", {})
            assert result.isError
            assert result.structuredContent == {"error": "not_found"}
        group.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_official_sdk_delivers_workspace_scoped_list_changes() -> None:
    gateway, _, _ = service()
    server = create_mcp_server(gateway, "s1")
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)
    received: list[type] = []
    changed = anyio.Event()

    async def handle(message) -> None:
        if isinstance(message, types.ServerNotification):
            received.append(type(message.root))
            if len(received) == 2:
                changed.set()

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(
            client_read, client_write, message_handler=handle
        ) as client:
            initialized = await client.initialize()
            assert str(initialized.protocolVersion) == "2025-11-25"
            await client.list_tools()
            with anyio.fail_after(1):
                while gateway.notifier.subscriber_count("w1") != 1:
                    await anyio.sleep(0)
            gateway.notifier.publish(workspace_id="foreign", event="tools/list_changed")
            gateway.notifier.publish(workspace_id="w1", event="tools/list_changed")
            gateway.notifier.publish(workspace_id="w1", event="resources/list_changed")
            with anyio.fail_after(1):
                await changed.wait()
            assert received == [
                types.ToolListChangedNotification,
                types.ResourceListChangedNotification,
            ]
        group.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_official_sdk_cancellation_cancels_only_owned_request() -> None:
    gateway, lifecycle, audit = service()
    lifecycle.gate = asyncio.Event()
    server = create_mcp_server(gateway, "s1")
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            call = asyncio.create_task(client.call_tool("cad__run", {}))
            with anyio.fail_after(1):
                while not gateway._requests:
                    await anyio.sleep(0)
            request_id = next(iter(gateway._requests))[1]
            await client.send_notification(
                types.CancelledNotification(
                    params=types.CancelledNotificationParams(
                        requestId=int(request_id), reason="operator"
                    )
                )
            )
            with anyio.fail_after(1):
                while not any(
                    event["outcome"] == "cancelled" for event in audit.events
                ):
                    await anyio.sleep(0)
            assert gateway._requests == {}
            call.cancel()
            with pytest.raises(asyncio.CancelledError):
                await call
        group.cancel_scope.cancel()
