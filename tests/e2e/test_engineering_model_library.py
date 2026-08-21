from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from api.routers.engineering_models import router as engineering_models_router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from data_vault import ModelArtifactStore, ModelRepository, RivetMcpRepository
from fastapi import FastAPI
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
            toolArguments: '{"x":4.0}'
            toolCallId: call-model-library
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
    id: project-engineering-model-library
    title: Engineering model library
    description: ""
    mainGraphId: graph-model
  plugins: []
"""


class Workspaces:
    def __init__(self, path: str) -> None:
        self.path = path

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert workspace_id == "workspace-model-library"
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
        raise AssertionError("A model call bypassed its capability provider")

    async def call_tool(self, *_args, **_kwargs):
        raise AssertionError("A model call bypassed its capability provider")

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def record(self, event):
        self.events.append(dict(event))


def _process_supervisor() -> ProcessSupervisor:
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


def _api(application: EngineeringModelService) -> FastAPI:
    app = FastAPI()
    app.state.security_settings = SecuritySettings(
        mode="compat",
        api_token=None,
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )
    app.state.engineering_model_application = application
    app.add_middleware(ControlPlaneSecurityMiddleware)
    app.include_router(engineering_models_router, prefix="/api/v1/engineering-models")
    return app


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_local_api_adapter_gateway_and_real_rivet_worker_share_one_lifecycle(
    tmp_path,
) -> None:
    database = tmp_path / "wright-model-library.db"
    from data_vault import upgrade_database

    upgrade_database(database)
    document = WorkspaceWorkflowStore(str(tmp_path)).create(
        "model-library-flow", PROJECT
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-model-library', 'session-model-library', ?, 1, 1)""",
            (str(tmp_path),),
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, started_at, output_truncated)
            VALUES ('run-model-library', 'workspace-model-library',
                    'session-model-library', ?, 1, ?, 'Main', 'running', 1, 1, 0)""",
            (document.workflow_id, document.digest),
        )

    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "model-data")
    models = EngineeringModelService(repository=repository, artifact_store=store)
    transport = httpx.ASGITransport(app=_api(models))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://wright.local"
    ) as client:
        catalog = await client.get("/api/v1/engineering-models/catalog?limit=100")
        assert catalog.status_code == 200
        assert catalog.json()["snapshot"]["offline"] is True
        plan = await client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "install",
                "model_id": "wright-affine-test",
                "variant_id": "json-cpu-f64",
            },
        )
        assert plan.status_code == 200
        installed = await client.post(
            f"/api/v1/engineering-models/plans/{plan.json()['plan_id']}/confirm",
            json={"plan_digest": plan.json()["plan_digest"]},
        )
        assert installed.status_code == 200
        installation_id = installed.json()["result"]["installation_id"]
        tested = await client.post(
            f"/api/v1/engineering-models/installations/{installation_id}/standard-test"
        )
        assert tested.status_code == 200
        assert tested.json()["evidence"][0]["state"] == "passed"
        bound = await client.post(
            "/api/v1/engineering-models/workspaces/workspace-model-library/bindings",
            headers={"X-Wright-Workspace-ID": "workspace-model-library"},
            json={"installation_id": installation_id, "task_id": "predict"},
        )
        assert bound.status_code == 200
        assert bound.json()["state"] == "enabled"

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
        session_id="gateway-model-library",
        principal_id="wright-rivet",
        workspace_id="workspace-model-library",
        transport="legacy",
        binding_session_id="session-model-library",
    )
    gateway.initialize_session(
        "gateway-model-library",
        protocol_version="2025-11-25",
        client_name="wright-rivet",
        client_version="2",
        client_capabilities={},
    )
    capabilities = RivetCapabilityService(
        gateway,
        session_resolver=lambda _session, _workspace: "gateway-model-library",
    )
    snapshot = capabilities.discover(
        session_id="session-model-library", workspace_id="workspace-model-library"
    )
    projected = next(
        item
        for item in snapshot.tools
        if item.qualified_tool_name == "wright_model__wright_affine_test__predict"
    )
    model_binding = CapabilityBinding.build(
        binding_id="binding-model-library",
        workspace_id="workspace-model-library",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-model",
        node_id="node-model",
        node_handle="wright:qrstuvwxyzabcdef",
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
        binding_set_id="binding-set-model-library",
        workspace_id="workspace-model-library",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-model",
        bindings=(model_binding,),
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
    bridge_application = RivetRunnerBridgeApplication(
        bridge=bridge,
        authorities=authorities,
        repository=rivet_repository,
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    audience = await bridge_application.ensure_started()
    now = datetime.now(UTC)
    issued = authorities.mint(
        AuthorityClaims(
            run_id="run-model-library",
            generation=1,
            workspace_id="workspace-model-library",
            session_id="gateway-model-library",
            workflow_id=document.workflow_id,
            workflow_revision=1,
            workflow_digest=document.digest,
            graph_id="graph-model",
            review_digest="9" * 64,
            binding_set_digest=binding_set.binding_set_digest,
            audience=audience,
            node_bindings={model_binding.node_handle: model_binding.binding_digest},
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
                "nodeId": model_binding.node_id,
                "handle": model_binding.node_handle,
                "qualifiedToolName": model_binding.qualified_tool_name,
                "bindingDigest": model_binding.binding_digest,
            },
        ),
    )
    host = RivetRuntimeHost(
        supervisor=_process_supervisor(),
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=30,
            cancellation_seconds=2,
        ),
    )
    try:
        result = await host.run(
            run_id="run-model-library",
            workspace_id="workspace-model-library",
            session_id="session-model-library",
            workspace_dir=str(tmp_path),
            document=document,
            graph="Main",
            requirements=("mcp",),
            mcp_grant=grant,
        )
        assert result.state == "succeeded"
        assert any(event.get("outcome") == "succeeded" for event in audit.events)
        assert not tuple((store.root / "runtime-scratch").glob("runtime-*"))
        assert issued.token not in str(result.outputs)
    finally:
        await bridge_application.close()
        await gateway.shutdown()
