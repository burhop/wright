from __future__ import annotations

import asyncio
import os
import shutil
import sqlite3
import time
from datetime import UTC, datetime, timedelta

import pytest
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from core.workflow_runs import RunnerAvailability, WorkflowRunState
from data_vault import (
    RivetMcpRepository,
    WorkflowRunRepository,
    upgrade_database,
)
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service import (
    AuthorityClaims,
    RivetApprovalService,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)
from workspace_service.rivet_runtime_host import RivetRuntimeHost, RivetRuntimeResult
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import (
    RivetMcpRuntimeGrant,
    RunnerSettings,
    WorkspaceWorkflowRunner,
)
from workspace_service.workflows import WorkspaceWorkflowStore


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
        '[node-alpha]:mcpToolCall "Alpha Inspect"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: alpha__inspect
            toolArguments: '{"value":2}'
            toolCallId: call-alpha
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: false
            useToolCallIdInput: false
          outgoingConnections:
            - response->"Alpha" output-alpha/value
          visualData: 0/0/280/null//
        '[node-beta]:mcpToolCall "Beta Inspect"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: beta__inspect
            toolArguments: '{"value":3}'
            toolCallId: call-beta
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: false
            useToolCallIdInput: false
          outgoingConnections:
            - response->"Beta" output-beta/value
          visualData: 0/300/280/null//
        '[output-alpha]:graphOutput "Alpha"':
          data:
            id: alpha
            dataType: object[]
          visualData: 400/0/280/null//
        '[output-beta]:graphOutput "Beta"':
          data:
            id: beta
            dataType: object[]
          visualData: 400/300/280/null//
  metadata:
    id: project-mcp-pair
    title: Bound MCP Pair
    description: ""
    mainGraphId: graph-mcp
  plugins: []
"""


class Workspaces:
    def __init__(self, path: str) -> None:
        self.path = path

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert session_id == "session-1"
        assert workspace_id == "workspace-1"
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.path,
        }

    def enabled_server_ids(self, _session):
        return {"alpha", "beta"}


class Catalog:
    def __init__(self) -> None:
        now = int(time.time())
        self._servers = tuple(
            McpServer(
                server_id=name,
                name=name.title(),
                type="stdio",
                command=[name],
                is_active=True,
                is_installed=True,
                status="active",
                created_at=now,
                updated_at=now,
            )
            for name in ("alpha", "beta")
        )

    def servers(self):
        return self._servers

    def tools(self, server_id):
        return (
            GatewayTool(
                name=f"{server_id}__inspect",
                server_id=server_id,
                tool_name="inspect",
                title=f"{server_id.title()} inspect",
                description="Deterministic engineering fixture",
                input_schema={
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                    "required": ["value"],
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
                required_approvals=(
                    frozenset({"engineering.write"})
                    if server_id == "beta"
                    else frozenset()
                ),
                provenance={"server_revision": "fixture-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class Lifecycle:
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
        self.receipts.append((server_id, tool_name, dict(arguments)))
        if progress_callback:
            await progress_callback(
                {"status": "running", "progress": 0.5, "title": "Inspecting"}
            )
        return {
            "content": [{"type": "text", "text": f"{server_id}: inspected"}],
            "structuredContent": {"server": server_id, "value": arguments["value"]},
        }

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


def _binding(document, node_id: str, server_id: str, *, approval: bool):
    return CapabilityBinding.build(
        binding_id=f"binding-{server_id}",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=document.revision,
        workflow_digest=document.digest,
        graph_id="graph-mcp",
        node_id=node_id,
        node_handle=(
            "wright:abcdefghijklmnop"
            if server_id == "alpha"
            else "wright:qrstuvwxyzabcdef"
        ),
        requirement_id=None,
        qualified_tool_name=f"{server_id}__inspect",
        server_id=server_id,
        server_revision="fixture-v1",
        capability_digest=("a" if server_id == "alpha" else "b") * 64,
        validation_evidence_id=f"evidence-{server_id}",
        workspace_grant_digest=("c" if server_id == "alpha" else "d") * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={
            "required_approvals": ["engineering.write"] if approval else [],
            "effect_classes": ["application_mutation"] if approval else [],
        },
        units_policy={"value": "mm"},
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
async def test_real_runner_calls_two_fake_children_only_through_gateway_with_approval(
    tmp_path,
):
    document = WorkspaceWorkflowStore(str(tmp_path)).create("mcp-pair", PROJECT)
    database = tmp_path / "state.db"
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
            VALUES ('run-pair', 'workspace-1', 'session-1', ?, 1, ?,
                    'Main', 'running', 1, 1, 0)""",
            (document.workflow_id, document.digest),
        )
    repository = RivetMcpRepository(str(database))
    bindings = (
        _binding(document, "node-alpha", "alpha", approval=False),
        _binding(document, "node-beta", "beta", approval=True),
    )
    binding_set = WorkflowBindingSet.build(
        binding_set_id="binding-set-pair",
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

    lifecycle = Lifecycle()
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
    approvals = RivetApprovalService(repository=repository)
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=repository.get_binding_by_digest,
        approvals=approvals,
        repository=repository,
    )
    bridge_application = RivetRunnerBridgeApplication(
        bridge=bridge,
        authorities=authorities,
        repository=repository,
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    audience = await bridge_application.ensure_started()
    now = datetime.now(UTC)
    issued = authorities.mint(
        AuthorityClaims(
            run_id="run-pair",
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
            run_timeout_seconds=20,
            cancellation_seconds=2,
        ),
    )
    run_task = asyncio.create_task(
        host.run(
            run_id="run-pair",
            workspace_id="workspace-1",
            session_id="session-1",
            workspace_dir=str(tmp_path),
            document=document,
            graph="Main",
            requirements=("mcp",),
            mcp_grant=grant,
        )
    )
    try:
        for _ in range(500):
            pending = approvals.list_for_run("run-pair")
            if pending:
                break
            await asyncio.sleep(0.01)
        assert len(pending) == 1
        approvals.decide(
            pending[0].approval_id,
            expected_digest=pending[0].approval_digest,
            actor="engineer",
            approved=True,
        )
        result = await run_task
        assert result.state == "succeeded"
        assert {receipt[0] for receipt in lifecycle.receipts} == {"alpha", "beta"}
        assert len(lifecycle.receipts) == 2
        assert approvals.list_for_run("run-pair")[0].state == "consumed"
        child_documents, approval_documents = repository.run_evidence_documents(
            "run-pair"
        )
        assert len(child_documents) == 2
        assert all(item["child_received"] for item in child_documents)
        assert len(approval_documents) == 1
        assert any(event["outcome"] == "succeeded" for event in audit.events)
        assert issued.token not in str(result.outputs)
    finally:
        if not run_task.done():
            run_task.cancel()
            await asyncio.gather(run_task, return_exceptions=True)
        await bridge_application.close()
        await gateway.shutdown()


@pytest.mark.asyncio
async def test_workspace_runner_mints_memory_only_grant_and_finalizes_manifest(
    tmp_path,
):
    document = WorkspaceWorkflowStore(str(tmp_path)).create("mcp-pair", PROJECT)
    database = tmp_path / "runner-state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
    repository = RivetMcpRepository(str(database))
    bindings = (
        _binding(document, "node-alpha", "alpha", approval=False),
        _binding(document, "node-beta", "beta", approval=False),
    )
    binding_set = WorkflowBindingSet.build(
        binding_set_id="runner-set",
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

    class Assets:
        def status(self):
            return RunnerAvailability.AVAILABLE, object(), None

    class Host:
        grant = None

        async def run(self, **kwargs):
            self.grant = kwargs["mcp_grant"]
            return RivetRuntimeResult(
                kwargs["run_id"],
                "succeeded",
                {"ok": True},
                None,
                (),
                "runtime-1",
                5,
            )

    class PrivateBridge:
        cancelled = []

        async def ensure_started(self):
            return "http://127.0.0.1:43123/internal/rivet-mcp/v1"

        async def close(self):
            return None

        def cancel_authority(self, authority_id, *, reason):
            self.cancelled.append((authority_id, reason))
            return 0

    host = Host()
    private_bridge = PrivateBridge()
    authorities = RivetRunAuthorityService()
    runner = WorkspaceWorkflowRunner(
        supervisor=object(),  # type: ignore[arg-type]
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=20,
        ),
        node_path="node",
        artifact_catalog=Assets(),  # type: ignore[arg-type]
        runtime_host=host,  # type: ignore[arg-type]
        run_repository=WorkflowRunRepository(str(database)),
        id_factory=lambda: "manifest-run",
    )
    runner.configure_mcp(
        repository=repository,
        authorities=authorities,
        approvals=RivetApprovalService(repository=repository),
        bridge=private_bridge,
        session_resolver=lambda _session, _workspace: "gateway-session",
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    started = await runner.start(
        workspace_id="workspace-1",
        session_id="session-1",
        workspace_dir=str(tmp_path),
        slug="mcp-pair",
        expected_revision=1,
        expected_digest=document.digest,
        expected_review_digest="9" * 64,
        binding_set_digest=binding_set.binding_set_digest,
        graph="Main",
    )
    for _ in range(100):
        completed = runner.get(started.run_id)
        if completed.state is WorkflowRunState.SUCCEEDED:
            break
        await asyncio.sleep(0.01)
    assert completed.state is WorkflowRunState.SUCCEEDED
    assert host.grant is not None
    manifest = runner.manifest(started.run_id)
    assert manifest is not None
    assert manifest["terminal_state"] == "succeeded"
    assert manifest["binding_set_digest"] == binding_set.binding_set_digest
    assert host.grant.token not in str(manifest)
    assert authorities.snapshot(host.grant.authority_id).state == "terminal"
