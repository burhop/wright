from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from data_vault import RivetMcpRepository, upgrade_database
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service import (
    AuthorityClaims,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)
from workspace_service.rivet_runtime_host import RivetRuntimeHost
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import RivetMcpRuntimeGrant, RunnerSettings
from workspace_service.workflows import WorkspaceWorkflowStore


ROOT = Path(__file__).resolve().parents[2]
STDIO_SERVER = ROOT / "tests" / "fixtures" / "rivet_mcp_stdio_server.py"
PROJECT = """version: 4
data:
  attachedData: {}
  graphs:
    graph-mcp:
      metadata:
        id: graph-mcp
        name: Main
        description: ""
      nodes:
        '[node-cad]:mcpToolCall "CAD Inspect"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: cad__test_tool
            toolArguments: '{"val":"bracket"}'
            toolCallId: call-cad
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: false
            useToolCallIdInput: false
          outgoingConnections:
            - response->"CAD" output-cad/value
          visualData: 0/0/280/null//
        '[node-fea]:mcpToolCall "FEA Inspect"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: fea__test_tool
            toolArguments: '{"val":"stress"}'
            toolCallId: call-fea
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: false
            useToolCallIdInput: false
          outgoingConnections:
            - response->"FEA" output-fea/value
          visualData: 0/300/280/null//
        '[output-cad]:graphOutput "CAD"':
          data:
            id: cad
            dataType: object[]
          visualData: 400/0/280/null//
        '[output-fea]:graphOutput "FEA"':
          data:
            id: fea
            dataType: object[]
          visualData: 400/300/280/null//
  metadata:
    id: project-real-stdio-pair
    title: Real stdio pair
    description: ""
    mainGraphId: graph-mcp
  plugins: []
"""


class Workspaces:
    def __init__(self, workspace: str) -> None:
        self.workspace = workspace

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert principal_id == "wright-rivet"
        assert workspace_id == "workspace-1"
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.workspace,
        }

    def enabled_server_ids(self, _session):
        return {"cad", "fea"}


class Catalog:
    def __init__(self) -> None:
        now = int(time.time())
        self._servers = tuple(
            McpServer(
                server_id=server_id,
                name=f"{server_id.upper()} real stdio fixture",
                type="stdio",
                command=[sys.executable, str(STDIO_SERVER)],
                is_active=True,
                is_installed=True,
                status="active",
                created_at=now,
                updated_at=now,
            )
            for server_id in ("cad", "fea")
        )

    def servers(self):
        return self._servers

    def tools(self, server_id):
        return (
            GatewayTool(
                name=f"{server_id}__test_tool",
                server_id=server_id,
                tool_name="test_tool",
                title=f"{server_id.upper()} test tool",
                description="Real MCP stdio subprocess fixture",
                input_schema={
                    "type": "object",
                    "properties": {"val": {"type": "string"}},
                    "required": ["val"],
                    "additionalProperties": False,
                },
                output_schema=None,
                provenance={"server_revision": "stdio-fixture-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class RealStdioLifecycle:
    def __init__(self) -> None:
        self.receipts: list[tuple[str, str, dict]] = []

    async def ensure_started(self, _server_id, **_kwargs):
        return None

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        del approval_context, progress_callback
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(STDIO_SERVER)],
        )
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "wright-rivet-stdio-fixture"
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == {"test_tool"}
                result = await session.call_tool(tool_name, dict(arguments))
        self.receipts.append((server_id, tool_name, dict(arguments)))
        return result.model_dump(mode="json", by_alias=True)

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


def _binding(document, node_id: str, server_id: str, handle: str):
    return CapabilityBinding.build(
        binding_id=f"binding-{server_id}",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-mcp",
        node_id=node_id,
        node_handle=handle,
        requirement_id=None,
        qualified_tool_name=f"{server_id}__test_tool",
        server_id=server_id,
        server_revision="stdio-fixture-v1",
        capability_digest=("a" if server_id == "cad" else "b") * 64,
        validation_evidence_id=f"stdio-validation-{server_id}",
        workspace_grant_digest=("c" if server_id == "cad" else "d") * 64,
        input_schema={"type": "object"},
        output_schema=None,
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
    )


def _supervisor():
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_local_fastapi_pinned_node_and_two_real_stdio_mcps(
    tmp_path, offline_api_client
):
    health = offline_api_client.get("/api/health")
    assert health.status_code == 200

    document = WorkspaceWorkflowStore(str(tmp_path)).create("real-pair", PROJECT)
    database = tmp_path / "rivet-real-stdio.db"
    upgrade_database(database)
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
            VALUES ('real-stdio-run', 'workspace-1', 'session-1', ?, 1, ?,
                    'Main', 'running', 1, 1, 0)""",
            (document.workflow_id, document.digest),
        )
    repository = RivetMcpRepository(str(database))
    bindings = (
        _binding(document, "node-cad", "cad", "wright:abcdefghijklmnop"),
        _binding(document, "node-fea", "fea", "wright:qrstuvwxyzabcdef"),
    )
    binding_set = WorkflowBindingSet.build(
        binding_set_id="real-stdio-set",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-mcp",
        bindings=bindings,
        discovery_snapshot_digest="e" * 64,
        policy_snapshot_digest="f" * 64,
        created_at=datetime.now(UTC),
    )
    repository.save_binding_set(binding_set)
    lifecycle = RealStdioLifecycle()
    audit = Audit()
    gateway = GatewayService(
        workspaces=Workspaces(str(tmp_path)),
        catalog=Catalog(),
        lifecycle=lifecycle,
        audit=audit,
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
    )
    gateway.open_session(
        session_id="gateway-session",
        principal_id="wright-rivet",
        workspace_id="workspace-1",
        transport="legacy",
        binding_session_id="session-1",
    )
    gateway.initialize_session(
        "gateway-session",
        protocol_version="2025-11-25",
        client_name="wright-rivet",
        client_version="2",
        client_capabilities={},
    )
    authorities = RivetRunAuthorityService()
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=repository.get_binding_by_digest,
        repository=repository,
    )
    application = RivetRunnerBridgeApplication(
        bridge=bridge,
        authorities=authorities,
        repository=repository,
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    audience = await application.ensure_started()
    now = datetime.now(UTC)
    issued = authorities.mint(
        AuthorityClaims(
            run_id="real-stdio-run",
            generation=1,
            workspace_id="workspace-1",
            session_id="gateway-session",
            workflow_id=document.workflow_id,
            workflow_revision=1,
            workflow_digest=document.digest,
            graph_id="graph-mcp",
            review_digest="9" * 64,
            binding_set_digest=binding_set.binding_set_digest,
            audience=audience,
            node_bindings={item.node_handle: item.binding_digest for item in bindings},
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    grant = RivetMcpRuntimeGrant(
        issued.authority_id,
        audience,
        issued.token,
        issued.claims.expires_at,
        binding_set.binding_set_digest,
        "wright-workspace",
        tuple(
            {
                "nodeId": item.node_id,
                "handle": item.node_handle,
                "qualifiedToolName": item.qualified_tool_name,
                "bindingDigest": item.binding_digest,
            }
            for item in bindings
        ),
    )
    host = RivetRuntimeHost(
        supervisor=_supervisor(),
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=30,
            cancellation_seconds=2,
        ),
    )
    try:
        result = await host.run(
            run_id="real-stdio-run",
            workspace_id="workspace-1",
            session_id="session-1",
            workspace_dir=str(tmp_path),
            document=document,
            graph="Main",
            requirements=("mcp",),
            mcp_grant=grant,
        )
        assert result.state == "succeeded"
        assert {receipt[0] for receipt in lifecycle.receipts} == {"cad", "fea"}
        assert len(lifecycle.receipts) == 2
        assert all(event["principal_id"] == "wright-rivet" for event in audit.events)
        assert issued.token not in json_safe(result.outputs)
    finally:
        await application.close()
        await gateway.shutdown()


def json_safe(value) -> str:
    import json

    return json.dumps(value, sort_keys=True, default=str)
