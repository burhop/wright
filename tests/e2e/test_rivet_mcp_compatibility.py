from __future__ import annotations

import sqlite3
import time
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from core.workflow_runs import WorkflowRunState
from data_vault import database_status, upgrade_database
from data_vault.migrations import MIGRATIONS
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service.brep_panel import panel_environment, parse_brep_status_result
from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessStopResult,
    RuntimeSnapshot,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from workspace_service.workflows import WorkspaceWorkflowStore


class Supervisor:
    def __init__(self) -> None:
        self.snapshots: dict[str, RuntimeSnapshot] = {}

    async def start(self, **kwargs):
        snapshot = RuntimeSnapshot(
            runtime_id="runtime-non-mcp",
            workspace_id=kwargs["workspace_id"],
            instance_id=kwargs["instance_id"],
            generation=kwargs["generation"],
            status="running",
            identity=PlatformProcessIdentity("fixture", 1, 1.0, "fixture", "fixture"),
            started_at=datetime.now(UTC),
        )
        self.snapshots[snapshot.runtime_id] = snapshot
        return snapshot

    def snapshot(self, runtime_id):
        return self.snapshots[runtime_id]

    async def stop(self, *, runtime_id, generation, deadline):
        del deadline
        current = self.snapshots[runtime_id]
        assert current.generation == generation
        stopped = replace(
            current,
            status="stopped",
            stop_result=ProcessStopResult(0, True, False, (), ()),
        )
        self.snapshots[runtime_id] = stopped
        return stopped


@pytest.mark.asyncio
async def test_non_mcp_workflow_runs_without_gateway_authority(tmp_path):
    WorkspaceWorkflowStore(str(tmp_path)).create("ordinary", '{"nodes": []}')
    fixture = tmp_path / "ordinary-runner.mjs"
    fixture.write_text("// deterministic fixture", encoding="utf-8")
    runner = WorkspaceWorkflowRunner(
        supervisor=Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True),
        node_path="node",
        fixture_path=fixture,
        id_factory=lambda: "ordinary-run",
    )
    started = await runner.start(
        workspace_id="workspace-1",
        session_id="session-1",
        workspace_dir=str(tmp_path),
        slug="ordinary",
    )
    assert started.state is WorkflowRunState.RUNNING
    cancelled = await runner.cancel(started.run_id, generation=1)
    assert cancelled.state is WorkflowRunState.CANCELLED
    assert runner.manifest(started.run_id) is None


class Workspaces:
    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": "D:/workspace",
        }

    def enabled_server_ids(self, _session):
        return {"shared"}


class Catalog:
    def __init__(self) -> None:
        now = int(time.time())
        self.server = McpServer(
            server_id="shared",
            name="Shared MCP",
            type="stdio",
            command=["fixture"],
            is_active=True,
            is_installed=True,
            status="active",
            created_at=now,
            updated_at=now,
        )

    def servers(self):
        return (self.server,)

    def tools(self, server_id):
        assert server_id == "shared"
        return (
            GatewayTool(
                name="shared__inspect",
                server_id="shared",
                tool_name="inspect",
                title="Inspect",
                description="Shared provider-neutral tool",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                provenance={"server_revision": "fixture-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class Lifecycle:
    async def ensure_started(self, _server_id, **_kwargs):
        return None

    async def call_tool(self, server_id, tool_name, arguments, **_kwargs):
        return {
            "content": [{"type": "text", "text": "ok"}],
            "structuredContent": {
                "server": server_id,
                "tool": tool_name,
                "value": arguments["value"],
            },
        }

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


@pytest.mark.asyncio
async def test_agent_manager_and_chat_gateway_clients_remain_isolated_and_work():
    audit = Audit()
    gateway = GatewayService(
        workspaces=Workspaces(),
        catalog=Catalog(),
        lifecycle=Lifecycle(),
        audit=audit,
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
    )
    for session_id, principal in (
        ("agent-session", "wright-agent-manager"),
        ("chat-session", "wright-chat"),
    ):
        gateway.open_session(
            session_id=session_id,
            principal_id=principal,
            workspace_id="workspace-1",
            transport="legacy",
        )
        gateway.initialize_session(
            session_id,
            protocol_version="2025-11-25",
            client_name=principal,
            client_version="1",
            client_capabilities={},
        )
    agent = await gateway.call_tool(
        "agent-session", "agent-call", "shared__inspect", {"value": 1}
    )
    chat = await gateway.call_tool(
        "chat-session", "chat-call", "shared__inspect", {"value": 2}
    )
    assert agent.structured_content["value"] == 1
    assert chat.structured_content["value"] == 2
    assert {event["session_id"] for event in audit.events} == {
        "agent-session",
        "chat-session",
    }
    await gateway.shutdown()


def test_brep_panel_remains_wright_owned_loopback_application():
    environment = panel_environment({})
    status = parse_brep_status_result(
        {
            "structuredContent": {
                "connected": False,
                "controlUrl": "http://127.0.0.1:61234/?token=ci-test-panel-token-012345",
                "moduleUrl": environment["BREP_CAD_MODULE_URL"],
            }
        }
    )
    assert environment["BREP_MCP_APP_PORT"] == "0"
    assert environment["BREP_MCP_AUTO_OPEN"] == "0"
    assert status.control_url.startswith("http://127.0.0.1:")
    assert status.module_url == environment["BREP_CAD_MODULE_URL"]


def test_schema_13_database_upgrades_in_place_to_rivet_gateway_schema(tmp_path):
    database = tmp_path / "schema-13.db"
    upgrade_database(database, migrations=MIGRATIONS[:13])
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, started_at, output_truncated)
            VALUES ('legacy-run', 'workspace-1', 'session-1', 'workflow-1', 1, ?,
                    'Main', 'succeeded', 1, 1, 0)""",
            ("a" * 64,),
        )
    result = upgrade_database(database)
    assert result.starting_version == 13
    assert result.ending_version == 14
    assert database_status(database).current_version == 14
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT state FROM workspace_workflow_runs WHERE run_id='legacy-run'"
        ).fetchone() == ("succeeded",)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {
        "workspace_workflow_binding_sets",
        "workspace_workflow_run_manifests",
        "workspace_workflow_child_calls",
        "workspace_workflow_call_approvals",
    } <= tables
