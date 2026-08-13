from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from core.workflow_runs import RunnerAvailability, WorkflowRunState
from data_vault import WorkflowRunRepository, upgrade_database
from workspace_service import (
    AuthorityClaims,
    RivetApprovalService,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from workspace_service.workflows import WorkspaceWorkflowStore


@dataclass
class ManifestRepository:
    binding_set: WorkflowBindingSet

    def __post_init__(self):
        self.draft = None
        self.manifest = None
        self.state = None

    def get_binding_set_by_digest(self, digest):
        return (
            self.binding_set if digest == self.binding_set.binding_set_digest else None
        )

    def create_manifest_draft(self, _manifest_id, draft):
        self.draft = draft

    def set_manifest_state(self, _manifest_id, state):
        self.state = state

    def set_manifest_cancellation(self, _manifest_id, draft):
        self.state = "cancelling"
        self.draft = draft

    def finalize_manifest(self, _manifest_id, manifest):
        assert self.manifest is None
        self.manifest = manifest

    def get_manifest_document(self, _run_id):
        return self.manifest.digest_material() if self.manifest else None

    def run_evidence_documents(self, _run_id):
        return (), ()

    def finalize_orphaned_manifests(self, *, reason_code="runner_restarted"):
        return 0


class Assets:
    def status(self):
        return (
            RunnerAvailability.AVAILABLE,
            SimpleNamespace(
                protocol_version=2,
                rivet_version="2.8.9",
                package_version="2.1.9",
                sha256="1" * 64,
                source_revision="fixture-revision",
            ),
            None,
        )


class SlowHost:
    def __init__(self) -> None:
        self.started = asyncio.Event()

    async def run(self, **_kwargs):
        self.started.set()
        await asyncio.Event().wait()


class CancellationBridge:
    def __init__(self, authorities, *, acknowledged: bool) -> None:
        self.authorities = authorities
        self.acknowledged = acknowledged
        self.calls = []

    async def ensure_started(self):
        return "http://127.0.0.1:43123/internal/rivet-mcp/v1"

    async def cancel_authority(self, authority_id, *, reason, timeout_seconds):
        snapshot = self.authorities.snapshot(authority_id)
        self.calls.append((snapshot.state, reason, timeout_seconds))
        return 1, self.acknowledged

    async def close(self):
        return None


def _binding(document):
    return CapabilityBinding.build(
        binding_id="binding-1",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-mcp",
        node_id="node-alpha",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        server_revision="fixture-v1",
        capability_digest="a" * 64,
        validation_evidence_id="evidence-1",
        workspace_grant_digest="b" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
    )


async def _cancelled_run(tmp_path, *, acknowledged: bool):
    fixture = (
        Path(__file__).resolve().parents[3]
        / "integrations"
        / "rivet"
        / "runner"
        / "tests"
        / "fixtures"
        / "valid-bound-mcp.rivet-project"
    ).read_text(encoding="utf-8")
    document = WorkspaceWorkflowStore(str(tmp_path)).create("cancel", fixture)
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
    binding_set = WorkflowBindingSet.build(
        binding_set_id="set-1",
        workspace_id="workspace-1",
        workflow_id=document.workflow_id,
        workflow_revision=1,
        workflow_digest=document.digest,
        graph_id="graph-mcp",
        bindings=(_binding(document),),
        discovery_snapshot_digest="c" * 64,
        policy_snapshot_digest="d" * 64,
        created_at=datetime.now(UTC),
    )
    repository = ManifestRepository(binding_set)
    authorities = RivetRunAuthorityService()
    bridge = CancellationBridge(authorities, acknowledged=acknowledged)
    host = SlowHost()
    runner = WorkspaceWorkflowRunner(
        supervisor=object(),  # type: ignore[arg-type]
        settings=RunnerSettings(
            enabled=True,
            real_execution_enabled=True,
            run_timeout_seconds=20,
            cancellation_seconds=0.05,
        ),
        node_path="node",
        artifact_catalog=Assets(),  # type: ignore[arg-type]
        runtime_host=host,  # type: ignore[arg-type]
        run_repository=WorkflowRunRepository(str(database)),
        id_factory=lambda: "cancel-run",
    )
    runner.configure_mcp(
        repository=repository,  # type: ignore[arg-type]
        authorities=authorities,
        approvals=RivetApprovalService(),
        bridge=bridge,
        session_resolver=lambda _session, _workspace: "gateway-session",
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    run = await runner.start(
        workspace_id="workspace-1",
        session_id="session-1",
        workspace_dir=str(tmp_path),
        slug="cancel",
        expected_revision=1,
        expected_digest=document.digest,
        expected_review_digest="e" * 64,
        binding_set_digest=binding_set.binding_set_digest,
        graph="Main",
    )
    await host.started.wait()
    cancelled = await runner.cancel(run.run_id, generation=1)
    return cancelled, repository, bridge, authorities


@pytest.mark.asyncio
@pytest.mark.parametrize("acknowledged", [True, False])
async def test_authority_is_revoked_before_child_cancel_and_manifest_reports_residue(
    tmp_path, acknowledged
):
    run, repository, bridge, authorities = await _cancelled_run(
        tmp_path, acknowledged=acknowledged
    )
    assert run.state is WorkflowRunState.CANCELLED
    assert str(bridge.calls[0][0]) == "revoked"
    assert repository.manifest.cancellation_acknowledged is acknowledged
    assert repository.manifest.residue_possible is (not acknowledged)
    assert repository.manifest.recovery_code == (
        "RIVET_MCP_CANCELLED_CLEAN" if acknowledged else "RIVET_MCP_RESIDUE_POSSIBLE"
    )
    assert authorities.snapshot(repository.draft.authority_id).state == "terminal"
    second = run
    assert second.state is WorkflowRunState.CANCELLED


class SlowGateway:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.cancelled = []

    async def call_tool(self, *_args, **_kwargs):
        self.started.set()
        await self.release.wait()
        from tool_registry.gateway_models import GatewayToolResult

        return GatewayToolResult(content=(), structured_content={"late": True})

    def cancel(self, session_id, request_id, reason=None):
        self.cancelled.append((session_id, request_id, reason))
        return True


@pytest.mark.asyncio
async def test_revoked_authority_rejects_late_child_success_and_cleans_active_request():
    now = datetime.now(UTC)
    authorities = RivetRunAuthorityService()
    binding = CapabilityBinding.build(
        binding_id="binding",
        workspace_id="workspace",
        workflow_id="workflow",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="graph",
        node_id="node",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__slow",
        server_id="alpha",
        server_revision="1",
        capability_digest="b" * 64,
        validation_evidence_id="evidence",
        workspace_grant_digest="c" * 64,
        input_schema={"type": "object"},
        output_schema=None,
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={},
        created_at=now,
    )
    issued = authorities.mint(
        AuthorityClaims(
            run_id="run",
            generation=1,
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="graph",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    gateway = SlowGateway()
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=lambda _digest: binding,
    )
    from workspace_service.rivet_gateway_bridge import RivetBoundInvocation

    call = asyncio.create_task(
        bridge.invoke_bound(
            issued.token,
            issued.claims.audience,
            RivetBoundInvocation(
                "run",
                1,
                issued.authority_id,
                binding.node_handle,
                binding.binding_digest,
                "request",
                {},
            ),
        )
    )
    await gateway.started.wait()
    authorities.revoke(issued.authority_id, reason="cancelled")
    assert bridge.cancel_authority(issued.authority_id, reason="cancelled") == 1
    gateway.release.set()
    with pytest.raises(PermissionError, match="revoked"):
        await call
    assert bridge.active_count(issued.authority_id) == 0
