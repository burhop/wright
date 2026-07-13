from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

import anyio
import pytest
from mcp import ClientSession

from tool_registry.gateway_models import SessionState
from tool_registry.mcp_stdio import StdioGatewayBinding, run_mcp_streams
from test_gateway_service import service
from data_vault import upgrade_database
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository


@pytest.mark.asyncio
async def test_explicit_stdio_binding_and_eof_cleanup() -> None:
    gateway, _, _ = service()
    binding = StdioGatewayBinding("stdio-session", "stdio:123", "w1")
    gateway.workspaces.bindings["stdio-session"] = ("stdio:123", "w1", "/workspace/one")
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)

    async with anyio.create_task_group() as group:
        group.start_soon(
            run_mcp_streams,
            gateway,
            binding,
            server_read,
            server_write,
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            assert [tool.name for tool in (await client.list_tools()).tools] == [
                "cad__run"
            ]
        await client_write.aclose()

    assert gateway._sessions["stdio-session"].state is SessionState.CLOSED


@pytest.mark.asyncio
async def test_stdio_rejects_missing_explicit_workspace_binding() -> None:
    gateway, _, _ = service()
    client_write, server_read = anyio.create_memory_object_stream(1)
    server_write, _ = anyio.create_memory_object_stream(1)
    with pytest.raises(RuntimeError, match="binding denied"):
        await run_mcp_streams(
            gateway,
            StdioGatewayBinding("missing", "stdio:123", ""),
            server_read,
            server_write,
        )
    await client_write.aclose()


@pytest.mark.asyncio
async def test_stdio_serializes_one_hundred_concurrent_results() -> None:
    gateway, _, _ = service()
    binding = StdioGatewayBinding("stress", "stdio:456", "w1")
    gateway.workspaces.bindings["stress"] = ("stdio:456", "w1", "/workspace/one")
    client_write, server_read = anyio.create_memory_object_stream(200)
    server_write, client_read = anyio.create_memory_object_stream(200)

    async with anyio.create_task_group() as group:
        group.start_soon(run_mcp_streams, gateway, binding, server_read, server_write)
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            results = []

            async def call(index: int) -> None:
                result = await client.call_tool("cad__run", {"index": index})
                results.append(result)

            async with anyio.create_task_group() as calls:
                for index in range(100):
                    calls.start_soon(call, index)

            assert len(results) == 100
            assert all(not result.isError for result in results)
            assert all(
                result.structuredContent["workspace"] == "w1" for result in results
            )
        group.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_real_stdio_accepts_partial_frame_and_closes_on_eof(tmp_path) -> None:
    database = tmp_path / "state.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(str(database))
    WorkspaceRepository(
        str(database), secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create("w1", "s1", str(workspace), workspace_name="STDIO")
    environment = {
        **os.environ,
        "DATABASE_PATH": str(database),
        "WRIGHT_TESTING": "1",
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "api.gateway_stdio",
            "--session-id",
            "s1",
            "--workspace-id",
            "w1",
            "--principal-id",
            "stdio:test",
        ],
        cwd=str(tmp_path),
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert process.stdin is not None and process.stdout is not None
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "partial", "version": "1"},
            },
        }
    )
    midpoint = len(request) // 2
    process.stdin.write(request[:midpoint])
    process.stdin.flush()
    await asyncio.sleep(0.05)
    assert process.poll() is None
    process.stdin.write(request[midpoint:] + "\n")
    process.stdin.flush()
    response = await asyncio.wait_for(
        asyncio.to_thread(process.stdout.readline), timeout=10
    )
    assert json.loads(response)["result"]["protocolVersion"] == "2025-11-25"
    process.stdin.close()
    await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=10)
    assert process.returncode == 0
