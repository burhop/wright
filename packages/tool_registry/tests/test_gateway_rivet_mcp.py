from __future__ import annotations

import time

import anyio
import pytest
from mcp import ClientSession
from data_vault import upgrade_database

from tool_registry.catalog_reconcile import reconcile_wright_managed_servers
from tool_registry.db import insert_server, insert_tools
from tool_registry.gateway_adapters import DatabaseGatewayCatalog
from tool_registry.gateway_management import (
    GatewayManagementTools,
    GatewayManagementToolSpec,
)
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.mcp_server import create_mcp_server, initialization_options
from tool_registry.models import McpServer, McpTool
from tool_registry.wright_managed_servers import RIVET_WORKFLOW_MUTATION_APPROVAL


class _Workspaces:
    def __init__(self, path: str) -> None:
        self.path = path
        self.enabled = {"rivet-workflows", "other"}

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert (session_id, principal_id, workspace_id) == ("session-1", "p1", "w1")
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.path,
        }

    def enabled_server_ids(self, _session):
        return set(self.enabled)


class _Lifecycle:
    def __init__(self) -> None:
        self.starts: list[tuple[str, str, dict]] = []
        self.calls: list[tuple[str, str, dict]] = []

    async def ensure_started(self, server_id, *, workspace_path, approval_context):
        self.starts.append((server_id, workspace_path, dict(approval_context)))

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        del approval_context
        self.calls.append((server_id, tool_name, dict(arguments)))
        if progress_callback is not None:
            await progress_callback(
                {"progress": 1, "total": None, "message": "Rivet graph starting"}
            )
        return {
            "content": [{"type": "text", "text": "ok"}],
            "structuredContent": {"ok": True},
            "isError": False,
        }

    async def shutdown(self):
        return None


class _Audit:
    def record(self, _event):
        return None


def _other_server() -> tuple[McpServer, McpTool]:
    now = int(time.time())
    return (
        McpServer(
            server_id="other",
            name="Other MCP",
            type="stdio",
            command=["other"],
            is_active=True,
            is_installed=True,
            status="active",
            created_at=now,
            updated_at=now,
        ),
        McpTool(
            tool_id="other:ping",
            server_id="other",
            name="ping",
            description="Ping another MCP",
            input_schema={"type": "object"},
            is_enabled=True,
            created_at=now,
        ),
    )


def _service(tmp_path):
    database = str(tmp_path / "state.db")
    upgrade_database(database)
    reconcile_wright_managed_servers(database)
    server, tool = _other_server()
    insert_server(database, server)
    insert_tools(database, [tool])
    workspaces = _Workspaces(str(tmp_path))
    lifecycle = _Lifecycle()
    service = GatewayService(
        workspaces=workspaces,
        catalog=DatabaseGatewayCatalog(database),
        lifecycle=lifecycle,
        audit=_Audit(),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
    )
    service.open_session(
        session_id="session-1",
        principal_id="p1",
        workspace_id="w1",
        transport="stdio",
    )
    service.initialize_session(
        "session-1",
        protocol_version="2025-11-25",
        client_name="Hermes",
        client_version="1",
        client_capabilities={},
    )
    return service, lifecycle, workspaces


@pytest.mark.asyncio
async def test_gateway_discovers_bound_rivet_tools_lazily_with_policy_and_progress(
    tmp_path,
) -> None:
    service, lifecycle, workspaces = _service(tmp_path)
    tools = {tool.name: tool for tool in service.list_tools("session-1")}

    assert len([name for name in tools if name.startswith("rivet-workflows__")]) == 6
    assert "other__ping" in tools
    assert lifecycle.starts == []
    assert tools["rivet-workflows__list_templates"].required_approvals == frozenset()
    assert tools["rivet-workflows__create_workflow"].required_approvals == frozenset(
        {RIVET_WORKFLOW_MUTATION_APPROVAL}
    )
    assert tools["rivet-workflows__run_workflow"].required_approvals == frozenset(
        {RIVET_WORKFLOW_MUTATION_APPROVAL}
    )

    updates: list[dict] = []
    listed = await service.call_tool(
        "session-1",
        "request-list",
        "rivet-workflows__list_templates",
        {},
        progress_callback=lambda update: updates.append(dict(update)),
    )
    assert not listed.is_error
    assert lifecycle.starts[0] == (
        "rivet-workflows",
        str(tmp_path),
        {"workspace_id": "w1", "session_id": "session-1"},
    )
    assert updates[0]["server"] == "rivet-workflows"
    assert updates[0]["correlationId"]

    denied = await service.call_tool(
        "session-1",
        "request-create-denied",
        "rivet-workflows__create_workflow",
        {"slug": "new-flow", "templateId": "basic-flow"},
    )
    assert denied.is_error
    assert denied.structured_content == {"error": "approval_required"}

    trusted_approvals = service.workspace_approvals_for_model_call(
        "session-1", "rivet-workflows__create_workflow"
    )
    assert trusted_approvals == {RIVET_WORKFLOW_MUTATION_APPROVAL}
    allowed = await service.call_tool(
        "session-1",
        "request-create-approved",
        "rivet-workflows__create_workflow",
        {"slug": "new-flow", "templateId": "basic-flow"},
        workspace_approvals=trusted_approvals,
    )
    assert not allowed.is_error

    workspaces.enabled = {"other"}
    assert (
        service.workspace_approvals_for_model_call(
            "session-1", "rivet-workflows__create_workflow"
        )
        == set()
    )
    assert [tool.name for tool in service.list_tools("session-1")] == ["other__ping"]


@pytest.mark.asyncio
async def test_enabled_rivet_server_grants_official_mcp_client_scoped_mutation(
    tmp_path,
) -> None:
    service, lifecycle, _workspaces = _service(tmp_path)
    server = create_mcp_server(service, "session-1")
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
            result = await client.call_tool(
                "rivet-workflows__create_workflow",
                {"slug": "chat-flow", "templateId": "basic-flow"},
            )
            assert not result.isError
            assert result.structuredContent == {"ok": True}
        group.cancel_scope.cancel()

    assert lifecycle.calls[-1] == (
        "rivet-workflows",
        "create_workflow",
        {"slug": "chat-flow", "templateId": "basic-flow"},
    )


@pytest.mark.asyncio
async def test_enabled_rivet_server_grants_builtin_graph_mutation_from_mcp_client(
    tmp_path,
) -> None:
    service, _lifecycle, _workspaces = _service(tmp_path)
    captured: list[dict] = []

    async def add_node(_session, arguments):
        captured.append(dict(arguments))
        return {"revision": 2}

    service.management = GatewayManagementTools(
        server_status=lambda _session: {},
        catalog_status=lambda _session: {},
        workspace_status=lambda _session: {},
        extra_tools=[
            (
                GatewayManagementToolSpec(
                    "wright__rivet_add_node",
                    "Add a node to a Wright-owned Rivet workflow.",
                    {
                        "type": "object",
                        "properties": {
                            "slug": {"type": "string"},
                            "expected_revision": {"type": "integer"},
                        },
                        "required": ["slug", "expected_revision"],
                        "additionalProperties": False,
                    },
                    {"type": "object"},
                    read_only=False,
                    idempotent=False,
                    required_approvals=frozenset({RIVET_WORKFLOW_MUTATION_APPROVAL}),
                ),
                add_node,
            )
        ],
    )
    server = create_mcp_server(service, "session-1")
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
            result = await client.call_tool(
                "wright__rivet_add_node",
                {"slug": "rivet", "expected_revision": 1},
            )
            assert not result.isError
            assert result.structuredContent == {"revision": 2}
        group.cancel_scope.cancel()

    assert captured == [{"slug": "rivet", "expected_revision": 1}]
