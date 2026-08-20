from __future__ import annotations

import asyncio
import shutil
import sqlite3
import time

import anyio
import mcp.types as types
import pytest
import workspace_service.rivet_mcp as rivet_mcp_module
from data_vault import WorkflowReview, upgrade_database
from mcp import ClientSession

from workspace_service.rivet_mcp import (
    RivetMcpBinding,
    RivetWorkflowMcpService,
    create_bound_rivet_service,
    create_rivet_mcp_server,
    initialization_options,
)


async def _session(service: RivetWorkflowMcpService):
    server = create_rivet_mcp_server(service)
    client_write, server_read = anyio.create_memory_object_stream(20)
    server_write, client_read = anyio.create_memory_object_stream(20)
    return server, client_write, server_read, server_write, client_read


@pytest.mark.asyncio
async def test_official_sdk_initialize_lists_six_bounded_tools(tmp_path) -> None:
    binding = RivetMcpBinding(str(tmp_path), str(tmp_path / "state.db"), "w1", "s1")
    service = RivetWorkflowMcpService(binding)
    server, client_write, server_read, server_write, client_read = await _session(
        service
    )
    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(client_read, client_write) as client:
            initialized = await client.initialize()
            assert initialized.serverInfo.name == "rivet-workflows"
            assert (
                initialized.instructions
                and "bound Wright workspace" in initialized.instructions
            )
            tools = (await client.list_tools()).tools
            assert [tool.name for tool in tools] == [
                "list_templates",
                "list_workflows",
                "inspect_workflow",
                "create_workflow",
                "validate_workflow",
                "run_workflow",
            ]
            annotations = {tool.name: tool.annotations for tool in tools}
            assert annotations["list_templates"].readOnlyHint is True
            assert annotations["create_workflow"].destructiveHint is True
            assert annotations["run_workflow"].openWorldHint is False
            for tool in tools:
                encoded = str(tool.inputSchema)
                assert "workspace" not in encoded.lower()
                assert "session" not in encoded.lower()
                assert "path" not in encoded.lower()
        group.cancel_scope.cancel()


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_approved_real_run_returns_outputs_and_official_sdk_progress(
    tmp_path, monkeypatch
) -> None:
    captured: list[tuple[str, dict[str, object]]] = []

    class CaptureLogger:
        def info(self, event: str, **values: object) -> None:
            captured.append((event, values))

    monkeypatch.setattr(rivet_mcp_module, "logger", CaptureLogger())
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('w1', 's1', ?, 1, 1)""",
            (str(tmp_path),),
        )
    service = create_bound_rivet_service(
        RivetMcpBinding(str(tmp_path), str(database), "w1", "s1")
    )
    server, client_write, server_read, server_write, client_read = await _session(
        service
    )
    progress: list[tuple[float, float | None, str | None]] = []

    async def capture(value: float, total: float | None, message: str | None) -> None:
        progress.append((value, total, message))

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run, server_read, server_write, initialization_options(server)
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            created = await client.call_tool(
                "create_workflow", {"slug": "run-me", "templateId": "basic-flow"}
            )
            identity = created.structuredContent["workflow"]
            service.reviews.set(
                WorkflowReview(
                    "w1",
                    identity["workflowId"],
                    identity["revision"],
                    "approved",
                    "test-reviewer",
                    int(time.time()),
                )
            )
            result = await client.call_tool(
                "run_workflow",
                {
                    "slug": "run-me",
                    "expectedRevision": identity["revision"],
                    "expectedDigest": identity["digest"],
                    "graph": "Passthrough",
                    "inputs": {"input": "hello through MCP"},
                },
                progress_callback=capture,
            )

            assert not result.isError
            assert result.structuredContent["state"] == "succeeded"
            assert (
                result.structuredContent["outputs"]["output"]["value"]
                == "hello through MCP"
            )
            assert progress
            assert [item[0] for item in progress] == sorted(
                item[0] for item in progress
            )
            assert all(item[1] is None for item in progress)
        group.cancel_scope.cancel()
    assert [event for event, _values in captured] == ["rivet_mcp_run_completed"]
    values = captured[0][1]
    assert values["run_id"] == result.structuredContent["runId"]
    assert values["duration_ms"] == result.structuredContent["durationMs"]
    encoded = str(captured)
    assert "hello through MCP" not in encoded
    assert str(tmp_path) not in encoded


@pytest.mark.asyncio
async def test_official_sdk_cancellation_cancels_the_owned_run_handler(
    tmp_path,
) -> None:
    binding = RivetMcpBinding(str(tmp_path), str(tmp_path / "state.db"), "w1", "s1")
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def run_handler(_arguments, _document, _validation, _progress):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    service = RivetWorkflowMcpService(binding, run_handler=run_handler)
    document = service.store.create(
        "cancel-me", service.catalog.instantiate("basic-flow")
    )
    service.reviews.set(
        WorkflowReview(
            "w1",
            document.workflow_id,
            document.revision,
            "approved",
            "test-reviewer",
            int(time.time()),
        )
    )
    server, client_write, server_read, server_write, client_read = await _session(
        service
    )
    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run, server_read, server_write, initialization_options(server)
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            call = asyncio.create_task(
                client.call_tool(
                    "run_workflow",
                    {
                        "slug": "cancel-me",
                        "expectedRevision": document.revision,
                        "expectedDigest": document.digest,
                        "graph": "Passthrough",
                    },
                )
            )
            await asyncio.wait_for(started.wait(), timeout=2)
            await client.send_notification(
                types.ClientNotification(
                    types.CancelledNotification(
                        params=types.CancelledNotificationParams(
                            requestId=1, reason="test cancellation"
                        )
                    )
                )
            )
            await asyncio.wait_for(cancelled.wait(), timeout=2)
            call.cancel()
            await asyncio.gather(call, return_exceptions=True)
        group.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_templates_create_inspect_validate_and_list_round_trip(tmp_path) -> None:
    service = RivetWorkflowMcpService(
        RivetMcpBinding(str(tmp_path), str(tmp_path / "state.db"), "w1", "s1")
    )
    server, client_write, server_read, server_write, client_read = await _session(
        service
    )
    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run, server_read, server_write, initialization_options(server)
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            templates = await client.call_tool("list_templates", {})
            assert not templates.isError
            assert templates.structuredContent["templates"]
            created = await client.call_tool(
                "create_workflow", {"slug": "hello-flow", "templateId": "basic-flow"}
            )
            assert not created.isError
            identity = created.structuredContent["workflow"]
            assert identity["slug"] == "hello-flow"
            assert identity["revision"] == 1
            assert len(identity["digest"]) == 64
            assert created.structuredContent["validation"]["valid"] is True

            inspected = await client.call_tool(
                "inspect_workflow", {"slug": "hello-flow"}
            )
            assert inspected.structuredContent["workflow"] == identity
            assert "project" not in inspected.structuredContent
            validated = await client.call_tool(
                "validate_workflow",
                {
                    "slug": "hello-flow",
                    "expectedRevision": 1,
                    "expectedDigest": identity["digest"],
                },
            )
            assert validated.structuredContent["valid"] is True
            workflows = await client.call_tool("list_workflows", {"limit": 10})
            assert workflows.structuredContent["workflows"][0]["slug"] == "hello-flow"
        group.cancel_scope.cancel()


@pytest.mark.asyncio
async def test_run_tool_requires_exact_identity_but_not_workflow_review(tmp_path) -> None:
    service = RivetWorkflowMcpService(
        RivetMcpBinding(str(tmp_path), str(tmp_path / "state.db"), "w1", "s1")
    )

    async def run_handler(arguments, document, validation, progress_callback):
        return {
            "runId": "run-1",
            "revision": document.revision,
            "graph": validation.main_graph.name,
        }

    service.run_handler = run_handler
    server, client_write, server_read, server_write, client_read = await _session(
        service
    )
    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run, server_read, server_write, initialization_options(server)
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            created = await client.call_tool(
                "create_workflow", {"slug": "review-me", "templateId": "basic-flow"}
            )
            identity = created.structuredContent["workflow"]
            result = await client.call_tool(
                "run_workflow",
                {
                    "slug": "review-me",
                    "expectedRevision": identity["revision"],
                    "expectedDigest": identity["digest"],
                    "graph": "Passthrough",
                    "inputs": {"input": "hello"},
                },
            )
            assert not result.isError
            assert result.structuredContent["runId"] == "run-1"
        group.cancel_scope.cancel()
