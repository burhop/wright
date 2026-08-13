from __future__ import annotations

import asyncio
import os
import shutil
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from data_vault import (
    ModelArtifactStore,
    ModelRepository,
    RivetMcpRepository,
    upgrade_database,
)
from model_registry.gateway_provider import EngineeringModelGatewayProvider
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from workspace_service import (
    AuthorityClaims,
    EngineeringModelService,
    RivetCapabilityService,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)
from workspace_service.rivet_runtime_host import RivetRuntimeHost
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import RivetMcpRuntimeGrant, RunnerSettings
from workspace_service.workflows import WorkspaceWorkflowStore


PROJECT = """version: 4
data:
  attachedData: {}
  graphs:
    graph-model:
      metadata:
        id: graph-model
        name: Main
        description: ""
      nodes:
        '[node-model]:mcpToolCall "Affine prediction"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: wright_model__wright_affine_test__predict
            toolArguments: '{"x":3.0}'
            toolCallId: call-model
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: false
            useToolCallIdInput: false
          outgoingConnections:
            - response->"Prediction" output-model/value
          visualData: 0/0/280/null//
        '[output-model]:graphOutput "Prediction"':
          data:
            id: prediction
            dataType: object[]
          visualData: 400/0/280/null//
  metadata:
    id: project-engineering-model
    title: Engineering model
    description: ""
    mainGraphId: graph-model
  plugins: []
"""


class Workspaces:
    def __init__(self, path: str) -> None:
        self.path = path

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert workspace_id == "workspace-one"
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.path,
        }

    def enabled_server_ids(self, _session):
        return set()


class EmptyCatalog:
    def servers(self):
        return ()

    def tools(self, _server_id):
        return ()

    def resources(self, _session):
        return ()


class EmptyLifecycle:
    async def ensure_started(self, *_args, **_kwargs):
        raise AssertionError("Model capability bypassed its dynamic provider")

    async def call_tool(self, *_args, **_kwargs):
        raise AssertionError("Model capability bypassed its dynamic provider")

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


def supervisor():
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_real_rivet_worker_calls_a_tested_model_only_through_gateway_service(
    tmp_path,
) -> None:
    document = WorkspaceWorkflowStore(str(tmp_path)).create("model-flow", PROJECT)
    database = tmp_path / "rivet-model.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-one', 'session-one', ?, 1, 1)""",
            (str(tmp_path),),
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, started_at, output_truncated)
            VALUES ('model-run', 'workspace-one', 'session-one', ?, 1, ?,
                    'Main', 'running', 1, 1, 0)""",
            (document.workflow_id, document.digest),
        )
    model_repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "model-data")
    models = EngineeringModelService(
        repository=model_repository,
        artifact_store=store,
    )
    plan = models.create_plan(
        operation_kind="install",
        model_id="wright-affine-test",
        variant_id="json-cpu-f64",
        principal_id="engineer-one",
    )
    operation = models.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-one",
        plan_digest=plan["plan_digest"],
        trace_id="trace-install",
    )
    installation_id = operation["result"]["installation_id"]
    tested = await models.run_standard_test(
        installation_id,
        principal_id="engineer-one",
        trace_id="trace-test",
    )
    model_binding = models.create_workspace_binding(
        installation_id,
        task_id="predict",
        workspace_id="workspace-one",
        principal_id="engineer-one",
    )
    audit = Audit()
    gateway = GatewayService(
        workspaces=Workspaces(str(tmp_path)),
        catalog=EmptyCatalog(),
        lifecycle=EmptyLifecycle(),
        audit=audit,
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        capability_providers=(EngineeringModelGatewayProvider(models),),
    )
    gateway.open_session(
        session_id="gateway-session",
        principal_id="wright-rivet",
        workspace_id="workspace-one",
        transport="legacy",
        binding_session_id="session-one",
    )
    gateway.initialize_session(
        "gateway-session",
        protocol_version="2025-11-25",
        client_name="wright-rivet",
        client_version="2",
        client_capabilities={},
    )
    capabilities = RivetCapabilityService(
        gateway, session_resolver=lambda _session, _workspace: "gateway-session"
    )
    snapshot = capabilities.discover(
        session_id="session-one", workspace_id="workspace-one"
    )
    projected = next(
        item
        for item in snapshot.tools
        if item.qualified_tool_name == model_binding["tool_name"]
    )
    assert projected.binding_eligible is True
    binding = CapabilityBinding.build(
        binding_id="binding-rivet-model",
        workspace_id="workspace-one",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-model",
        node_id="node-model",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name=projected.qualified_tool_name,
        server_id=projected.server_id,
        server_revision=projected.server_revision,
        capability_digest=projected.capability_digest,
        validation_evidence_id=projected.validation_evidence_id,
        workspace_grant_digest=projected.workspace_grant_digest,
        input_schema=projected.input_schema,
        output_schema=projected.output_schema,
        risk={"required_approvals": [], "idempotency": "idempotent"},
        units_policy={},
        material_defaults={},
        argument_constraints=projected.input_schema,
        created_at=datetime.now(UTC),
    )
    binding_set = WorkflowBindingSet.build(
        binding_set_id="rivet-model-set",
        workspace_id="workspace-one",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-model",
        bindings=(binding,),
        discovery_snapshot_digest=snapshot.snapshot_digest,
        policy_snapshot_digest="f" * 64,
        created_at=datetime.now(UTC),
    )
    rivet_repository = RivetMcpRepository(str(database))
    rivet_repository.save_binding_set(binding_set)
    authorities = RivetRunAuthorityService()
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=rivet_repository.get_binding_by_digest,
        repository=rivet_repository,
    )
    application = RivetRunnerBridgeApplication(
        bridge=bridge,
        authorities=authorities,
        repository=rivet_repository,
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    audience = await application.ensure_started()
    now = datetime.now(UTC)
    issued = authorities.mint(
        AuthorityClaims(
            run_id="model-run",
            generation=1,
            workspace_id="workspace-one",
            session_id="gateway-session",
            workflow_id=document.workflow_id,
            workflow_revision=1,
            workflow_digest=document.digest,
            graph_id="graph-model",
            review_digest="9" * 64,
            binding_set_digest=binding_set.binding_set_digest,
            audience=audience,
            node_bindings={binding.node_handle: binding.binding_digest},
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
        (
            {
                "nodeId": binding.node_id,
                "handle": binding.node_handle,
                "qualifiedToolName": binding.qualified_tool_name,
                "bindingDigest": binding.binding_digest,
            },
        ),
    )
    host = RivetRuntimeHost(
        supervisor=supervisor(),
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=30,
            cancellation_seconds=2,
        ),
    )
    try:
        result = await host.run(
            run_id="model-run",
            workspace_id="workspace-one",
            session_id="session-one",
            workspace_dir=str(tmp_path),
            document=document,
            graph="Main",
            requirements=("mcp",),
            mcp_grant=grant,
        )
        assert result.state == "succeeded"
        assert tested["evidence"][0]["state"] == "passed"
        assert model_binding["binding_digest"] == projected.capability_digest
        succeeded = [event for event in audit.events if event["outcome"] == "succeeded"]
        assert succeeded[-1]["server_id"] == "wright-models"
        assert succeeded[-1]["target_name"] == "predict"
        assert not tuple((store.root / "runtime-scratch").glob("runtime-*"))
    finally:
        await application.close()
        await gateway.shutdown()


@pytest.mark.asyncio
async def test_gateway_cancellation_reaches_the_model_provider_and_wins() -> None:
    gate = asyncio.Event()

    class SlowApplication:
        cancelled = []

        def declared_model_tool_names(self):
            return frozenset({"wright_model__slow_model__predict"})

        def discover_model_capabilities(self, **_values):
            return (
                {
                    "model_id": "slow-model",
                    "task_id": "predict",
                    "description": "Bounded cancellation fixture.",
                    "input_schema": {"type": "object", "additionalProperties": False},
                    "output_schema": {"type": "object"},
                    "workspace_id": "workspace-one",
                    "binding_id": "binding-slow",
                    "binding_digest": "a" * 64,
                    "binding_state": "enabled",
                    "installation_id": "installation-slow",
                    "installation_digest": "b" * 64,
                    "installation_state": "ready",
                    "adapter_id": "slow-adapter",
                    "adapter_version": "1.0.0",
                    "evidence_id": "evidence-slow",
                    "evidence_state": "passed",
                    "material_digest": "c" * 64,
                    "policy_snapshot_digest": "d" * 64,
                    "policy_current": True,
                },
            )

        async def invoke_model_capability(self, **_values):
            await gate.wait()
            return {"structuredContent": {"y": 1}}

        async def cancel_model_request(self, *, session_id, request_id):
            self.cancelled.append((session_id, request_id))

        async def close_model_session(self, **_values):
            return None

        async def shutdown_model_runtime(self):
            return None

    application = SlowApplication()
    gateway = GatewayService(
        workspaces=Workspaces("/workspace"),
        catalog=EmptyCatalog(),
        lifecycle=EmptyLifecycle(),
        audit=Audit(),
        notifier=GatewayNotificationHub(),
        capability_providers=(EngineeringModelGatewayProvider(application),),
    )
    gateway.open_session(
        session_id="gateway-session",
        principal_id="wright-rivet",
        workspace_id="workspace-one",
        transport="legacy",
    )
    gateway.initialize_session(
        "gateway-session",
        protocol_version="2025-11-25",
        client_name="wright-rivet",
        client_version="2",
        client_capabilities={},
    )
    call = asyncio.create_task(
        gateway.call_tool(
            "gateway-session",
            "cancel-model",
            "wright_model__slow_model__predict",
            {},
        )
    )
    await asyncio.sleep(0)
    assert gateway.cancel("gateway-session", "cancel-model", "run-cancelled")
    with pytest.raises(asyncio.CancelledError):
        await call
    await asyncio.sleep(0)
    assert application.cancelled == [("gateway-session", "cancel-model")]
    await gateway.shutdown()
