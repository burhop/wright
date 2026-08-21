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
from workspace_service.engineering_scenario_artifacts import normalize_artifact
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    workflow_text,
)
from workspace_service.engineering_scenario_service import _extract_artifact_claims
from workspace_service.rivet_runtime_host import RivetRuntimeHost
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import RivetMcpRuntimeGrant, RunnerSettings
from workspace_service.workflows import WorkspaceWorkflowStore


FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "engineering_scenario_mcp.py"
)


class Workspaces:
    def __init__(self, path: str, server_ids: set[str]) -> None:
        self.path = path
        self.server_ids = server_ids

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert principal_id == "wright-rivet"
        assert workspace_id == "workspace-1"
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.path,
        }

    def enabled_server_ids(self, _session):
        return self.server_ids


class Catalog:
    def __init__(self, tools: dict[str, str], scenario_id: str, run_id: str) -> None:
        now = int(time.time())
        self.scenario_id = scenario_id
        self.run_id = run_id
        self._servers = tuple(
            McpServer(
                server_id=server_id,
                name=f"{server_id} deterministic engineering fixture",
                type="stdio",
                command=[
                    sys.executable,
                    str(FIXTURE),
                    "--scenario",
                    scenario_id,
                    "--server",
                    server_id,
                    "--tool",
                    tool_name,
                    "--run-id",
                    run_id,
                ],
                is_active=True,
                is_installed=True,
                status="active",
                created_at=now,
                updated_at=now,
            )
            for server_id, tool_name in tools.items()
        )
        self._tools = tools

    def servers(self):
        return self._servers

    def tools(self, server_id):
        tool_name = self._tools[server_id]
        return (
            GatewayTool(
                name=f"{server_id}__{tool_name}",
                server_id=server_id,
                tool_name=tool_name,
                title=f"{server_id} scenario fixture",
                description="Wright-generated deterministic engineering artifact",
                input_schema={
                    "type": "object",
                    "properties": {"fixture": {"type": "string"}},
                    "required": ["fixture"],
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
                provenance={"server_revision": "engineering-fixture-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class RealLifecycle:
    def __init__(self, scenario_id: str, run_id: str, tools: dict[str, str]) -> None:
        self.scenario_id = scenario_id
        self.run_id = run_id
        self.tools = tools
        self.receipts: list[tuple[str, str]] = []

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
            args=[
                str(FIXTURE),
                "--scenario",
                self.scenario_id,
                "--server",
                server_id,
                "--tool",
                tool_name,
                "--run-id",
                self.run_id,
            ],
        )
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == f"wright-engineering-{server_id}"
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == {tool_name}
                result = await session.call_tool(tool_name, dict(arguments))
        self.receipts.append((server_id, tool_name))
        return result.model_dump(mode="json", by_alias=True)

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


def _supervisor():
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


def _binding(document, graph_id, capability, index):
    server_id, tool_name = capability["tool_name"].split("__", 1)
    return CapabilityBinding.build(
        binding_id=f"binding-{server_id}",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id=graph_id,
        node_id=capability["node_id"],
        node_handle=f"wright:{index:016d}",
        requirement_id=capability["requirement_id"],
        qualified_tool_name=capability["tool_name"],
        server_id=server_id,
        server_revision="engineering-fixture-v1",
        capability_digest=f"{index:x}" * 64,
        validation_evidence_id=f"fixture-validation-{server_id}",
        workspace_grant_digest=f"{index + 8:x}" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": []},
        units_policy={"scenario": "deterministic"},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
@pytest.mark.parametrize(
    "scenario_id",
    [
        "structural-bracket",
        "electronics-enclosure-cooling",
        "parametric-manufacturing",
    ],
)
async def test_tier1_scenario_calls_multiple_real_stdio_mcps_and_passes_assertions(
    tmp_path, scenario_id
):
    manifest = EngineeringScenarioCatalog().get(scenario_id)
    graph_id = manifest.document["workflow"]["graph_id"]
    run_id = f"scenario-e2e-{scenario_id}"
    document = WorkspaceWorkflowStore(str(tmp_path)).create(
        scenario_id, workflow_text(manifest)
    )
    capabilities = tuple(manifest.document["capabilities"])
    tools = {
        value["tool_name"].split("__", 1)[0]: value["tool_name"].split("__", 1)[1]
        for value in capabilities
    }
    assert len(tools) >= 2
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
            VALUES (?, 'workspace-1', 'session-1', ?, 1, ?, ?, 'running', 1, 1, 0)""",
            (run_id, document.workflow_id, document.digest, graph_id),
        )
        connection.commit()
    repository = RivetMcpRepository(str(database))
    bindings = tuple(
        _binding(document, graph_id, capability, index)
        for index, capability in enumerate(capabilities, 1)
    )
    binding_set = WorkflowBindingSet.build(
        binding_set_id=f"binding-set-{scenario_id}",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id=graph_id,
        bindings=bindings,
        discovery_snapshot_digest="e" * 64,
        policy_snapshot_digest="f" * 64,
        created_at=datetime.now(UTC),
    )
    repository.save_binding_set(binding_set)
    lifecycle = RealLifecycle(scenario_id, run_id, tools)
    audit = Audit()
    gateway = GatewayService(
        workspaces=Workspaces(str(tmp_path), set(tools)),
        catalog=Catalog(tools, scenario_id, run_id),
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
            run_id=run_id,
            generation=1,
            workspace_id="workspace-1",
            session_id="gateway-session",
            workflow_id=document.workflow_id,
            workflow_revision=1,
            workflow_digest=document.digest,
            graph_id=graph_id,
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
            run_id=run_id,
            workspace_id="workspace-1",
            session_id="session-1",
            workspace_dir=str(tmp_path),
            document=document,
            graph=graph_id,
            requirements=("mcp",),
            mcp_grant=grant,
        )
        assert result.state == "succeeded"
        assert {server for server, _tool in lifecycle.receipts} == set(tools)
        assert len(lifecycle.receipts) == len(tools)
        claims = _extract_artifact_claims(result.outputs)
        artifacts = {
            artifact.artifact_id: artifact
            for artifact in (normalize_artifact(value) for value in claims)
        }
        assertions = EngineeringAssertionRegistry().evaluate_manifest(
            manifest.document["assertions"], artifacts
        )
        assert set(artifacts) == {
            value["artifact_id"] for value in manifest.document["artifacts"]
        }
        assert assertions and all(str(value.state) == "pass" for value in assertions)
        assert all(event["principal_id"] == "wright-rivet" for event in audit.events)
        assert issued.token not in str(result.outputs)
    finally:
        await application.close()
        await gateway.shutdown()
