from __future__ import annotations

import asyncio
import os
import shutil
import sqlite3
import time
from datetime import UTC, datetime, timedelta

import pytest

from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet, canonical_digest
from data_vault import (
    ModelArtifactStore,
    ModelRepository,
    RivetMcpRepository,
    upgrade_database,
)
from model_registry.gateway_provider import EngineeringModelGatewayProvider
from model_registry.generated import generated_chatter_package
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
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


def _chatter_arguments() -> dict:
    arguments = generated_chatter_package().variants[0].test_vectors[0].input
    source = arguments["candidates"][0]
    candidates = []
    for candidate_id, first_value in (
        ("candidate-a", 0.0),
        ("candidate-b", 4.9),
        ("candidate-c", 10.0),
    ):
        values = [
            int(value) if isinstance(value, float) and value.is_integer() else value
            for value in source["values"]
        ]
        values[0] = first_value
        candidates.append({**source, "candidate_id": candidate_id, "values": values})
    return {**arguments, "candidates": candidates}


CHATTER_ARGUMENTS = _chatter_arguments()
CHATTER_TOOL = "wright_model__wright_chatter_generated_test__screen_chatter_candidates"
CHATTER_PROJECT = f"""version: 4
data:
  attachedData: {{}}
  graphs:
    graph-model:
      metadata: {{id: graph-model, name: Main, description: ""}}
      nodes:
        '[node-cad]:mcpToolCall "CAD context"':
          data: {{name: wright-rivet, version: 2.0.0, transportType: http, toolName: fixture_cad__inspect_setup, toolArguments: '{{"fixture":"chatter"}}', toolCallId: call-cad, useNameInput: false, useVersionInput: false, useServerUrlInput: false, useServerIdInput: false, useToolNameInput: false, useToolArgumentsInput: false, useToolCallIdInput: false}}
          outgoingConnections:
            - response->"CAD" output-cad/value
          visualData: 0/300/280/null//
        '[node-cam]:mcpToolCall "CAM candidates"':
          data: {{name: wright-rivet, version: 2.0.0, transportType: http, toolName: fixture_cam__generate_candidates, toolArguments: '{{"fixture":"chatter"}}', toolCallId: call-cam, useNameInput: false, useVersionInput: false, useServerUrlInput: false, useServerIdInput: false, useToolNameInput: false, useToolArgumentsInput: false, useToolCallIdInput: false}}
          outgoingConnections:
            - response->"CAM response" node-cam-response/array
            - response->"CAM" output-cam/value
          visualData: 0/600/280/null//
        '[node-cam-response]:pop "CAM response"':
          data: {{fromFront: false}}
          outgoingConnections:
            - lastItem->"CAM payload" node-cam-payload/object
          visualData: 320/600/220/null//
        '[node-cam-payload]:destructure "CAM payload"':
          data: {{paths: [$.value]}}
          outgoingConnections:
            - match_0->"Chatter screening" node-model/toolArguments
          visualData: 580/600/240/null//
        '[node-model]:mcpToolCall "Chatter screening"':
          data:
            name: wright-rivet
            version: 2.0.0
            transportType: http
            toolName: {CHATTER_TOOL}
            toolArguments: '{{}}'
            toolCallId: call-model
            useNameInput: false
            useVersionInput: false
            useServerUrlInput: false
            useServerIdInput: false
            useToolNameInput: false
            useToolArgumentsInput: true
            useToolCallIdInput: false
          outgoingConnections:
            - response->"Screening" output-model/value
          visualData: 0/0/280/null//
        '[output-model]:graphOutput "Screening"':
          data: {{id: screening, dataType: "object[]"}}
          visualData: 400/0/280/null//
        '[output-cad]:graphOutput "CAD"':
          data: {{id: cad, dataType: "object[]"}}
          visualData: 400/300/280/null//
        '[output-cam]:graphOutput "CAM"':
          data: {{id: cam, dataType: "object[]"}}
          visualData: 400/600/280/null//
  metadata: {{id: project-chatter-model, title: Chatter screening, description: "", mainGraphId: graph-model}}
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
        return {"fixture-cad", "fixture-cam"}


class EmptyCatalog:
    def __init__(self) -> None:
        now = int(time.time())
        self._servers = tuple(
            McpServer(
                server_id=server_id,
                name=f"{server_id} deterministic fixture",
                type="stdio",
                command="fixture",
                is_active=True,
                is_installed=True,
                status="active",
                created_at=now,
                updated_at=now,
            )
            for server_id in ("fixture-cad", "fixture-cam")
        )

    def servers(self):
        return self._servers

    def tools(self, server_id):
        tool_name = (
            "inspect_setup" if server_id == "fixture-cad" else "generate_candidates"
        )
        return (
            GatewayTool(
                name=f"{server_id.replace('-', '_')}__{tool_name}",
                server_id=server_id,
                tool_name=tool_name,
                description="Deterministic proprietary-free engineering fixture.",
                input_schema={
                    "type": "object",
                    "properties": {"fixture": {"type": "string"}},
                    "required": ["fixture"],
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
                provenance={"server_revision": f"{server_id}-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class EmptyLifecycle:
    def __init__(self) -> None:
        self.receipts = []

    async def ensure_started(self, *_args, **_kwargs):
        return None

    async def call_tool(self, server_id, tool_name, arguments, **_kwargs):
        self.receipts.append((server_id, tool_name, dict(arguments)))
        if server_id == "fixture-cam":
            return {"structuredContent": CHATTER_ARGUMENTS}
        return {
            "structuredContent": {
                "provider": server_id,
                "tool": tool_name,
                "simulation_only": True,
            }
        }

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
@pytest.mark.parametrize(
    ("project", "model_id", "variant_id", "task_id", "fixture_mcps"),
    [
        (PROJECT, "wright-affine-test", "json-cpu-f64", "predict", False),
        (
            CHATTER_PROJECT,
            "wright-chatter-generated-test",
            "generated-forest-cpu-f64",
            "screen_chatter_candidates",
            True,
        ),
    ],
)
async def test_real_rivet_worker_calls_tested_models_only_through_gateway_service(
    tmp_path, monkeypatch, project, model_id, variant_id, task_id, fixture_mcps
) -> None:
    document = WorkspaceWorkflowStore(str(tmp_path)).create("model-flow", project)
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
    captured_model_arguments = []
    invoke_model_capability = models.invoke_model_capability

    async def capture_model_arguments(**values):
        captured_model_arguments.append(dict(values["arguments"]))
        return await invoke_model_capability(**values)

    monkeypatch.setattr(models, "invoke_model_capability", capture_model_arguments)
    plan = models.create_plan(
        operation_kind="install",
        model_id=model_id,
        variant_id=variant_id,
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
        task_id=task_id,
        workspace_id="workspace-one",
        principal_id="engineer-one",
    )
    audit = Audit()
    lifecycle = EmptyLifecycle()
    gateway = GatewayService(
        workspaces=Workspaces(str(tmp_path)),
        catalog=EmptyCatalog(),
        lifecycle=lifecycle,
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

    def make_binding(item, *, node_id, handle):
        return CapabilityBinding.build(
            binding_id=f"binding-{node_id}",
            workspace_id="workspace-one",
            workflow_id=document.workflow_id,
            workflow_revision=1,
            workflow_digest=document.digest,
            graph_id="graph-model",
            node_id=node_id,
            node_handle=handle,
            requirement_id=None,
            qualified_tool_name=item.qualified_tool_name,
            server_id=item.server_id,
            server_revision=item.server_revision,
            capability_digest=item.capability_digest,
            validation_evidence_id=item.validation_evidence_id,
            workspace_grant_digest=item.workspace_grant_digest,
            input_schema=item.input_schema,
            output_schema=item.output_schema,
            risk={"required_approvals": [], "idempotency": "idempotent"},
            units_policy={},
            material_defaults={},
            argument_constraints=item.input_schema,
            created_at=datetime.now(UTC),
            provider=item.provider,
        )

    binding = make_binding(
        projected, node_id="node-model", handle="wright:abcdefghijklmnop"
    )
    bindings = [binding]
    if fixture_mcps:
        for name, node_id, handle in (
            ("fixture_cad__inspect_setup", "node-cad", "wright:cadcadcadcadcadc"),
            (
                "fixture_cam__generate_candidates",
                "node-cam",
                "wright:camcamcamcamcamc",
            ),
        ):
            capability = next(
                item for item in snapshot.tools if item.qualified_tool_name == name
            )
            assert capability.binding_eligible is True
            bindings.append(make_binding(capability, node_id=node_id, handle=handle))
    binding_set = WorkflowBindingSet.build(
        binding_set_id="rivet-model-set",
        workspace_id="workspace-one",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-model",
        bindings=tuple(bindings),
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
        assert result.state == "succeeded", result.error
        assert tested["evidence"][0]["state"] == "passed"
        assert model_binding["binding_digest"] == projected.capability_digest
        succeeded = [event for event in audit.events if event["outcome"] == "succeeded"]
        assert any(
            event["server_id"] == "wright-models" and event["target_name"] == task_id
            for event in succeeded
        )
        assert projected.provider.provider_kind == "engineering_model"
        assert len(lifecycle.receipts) == (2 if fixture_mcps else 0)
        if fixture_mcps:
            child_calls, _approvals = rivet_repository.run_evidence_documents(
                "model-run"
            )
            model_call = next(
                call for call in child_calls if call["node_id"] == "node-model"
            )
            assert len(CHATTER_ARGUMENTS["candidates"]) == 3
            assert captured_model_arguments == [CHATTER_ARGUMENTS]
            assert model_call["argument_digest"] == canonical_digest(
                captured_model_arguments[0]
            )
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
                    "package_revision": 1,
                    "manifest_digest": "e" * 64,
                    "variant_id": "slow-cpu",
                    "artifact_set_digest": "f" * 64,
                    "binding_id": "binding-slow",
                    "binding_digest": "a" * 64,
                    "binding_state": "enabled",
                    "installation_id": "installation-slow",
                    "installation_digest": "b" * 64,
                    "installation_state": "ready",
                    "adapter_id": "slow-adapter",
                    "adapter_version": "1.0.0",
                    "runtime_version": "runtime-1",
                    "evidence_id": "evidence-slow",
                    "evidence_state": "passed",
                    "material_digest": "c" * 64,
                    "test_material_digest": "1" * 64,
                    "input_schema_digest": "2" * 64,
                    "output_schema_digest": "3" * 64,
                    "resource_digest": "4" * 64,
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
