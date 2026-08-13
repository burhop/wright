from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from core.workflow_runs import (
    RunnerAvailability,
    WorkflowRunnerError,
    WorkflowRunnerUnavailable,
    WorkflowRunState,
)
from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessStopResult,
    RuntimeSnapshot,
)
from workspace_service.workflow_runner import (
    RunnerAssetCatalog,
    RunnerSettings,
    WorkspaceWorkflowRunner,
)
from workspace_service.workflows import WorkspaceWorkflowStore


class _Supervisor:
    def __init__(self) -> None:
        self.snapshots: dict[str, RuntimeSnapshot] = {}

    async def start(self, **kwargs) -> RuntimeSnapshot:
        runtime_id = f"runtime-{len(self.snapshots) + 1}"
        snapshot = RuntimeSnapshot(
            runtime_id=runtime_id,
            workspace_id=kwargs["workspace_id"],
            instance_id=kwargs["instance_id"],
            generation=kwargs["generation"],
            status="running",
            identity=PlatformProcessIdentity("test", 1, 1.0, "test", "test"),
            started_at=datetime.now(UTC),
        )
        self.snapshots[runtime_id] = snapshot
        return snapshot

    def snapshot(self, runtime_id: str) -> RuntimeSnapshot:
        return self.snapshots[runtime_id]

    async def stop(
        self, *, runtime_id: str, generation: int, deadline: datetime
    ) -> RuntimeSnapshot:
        snapshot = self.snapshots[runtime_id]
        assert snapshot.generation == generation
        updated = replace(
            snapshot,
            status="stopped",
            stop_result=ProcessStopResult(0, True, False, (), ()),
        )
        self.snapshots[runtime_id] = updated
        return updated


def _runner(
    tmp_path, *, enabled: bool = True, limit: int = 2
) -> WorkspaceWorkflowRunner:
    fixture = tmp_path / "fixture.mjs"
    fixture.write_text("// fixture", encoding="utf-8")
    return WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=enabled, maximum_concurrent_runs=limit),
        node_path="node",
        fixture_path=fixture,
        id_factory=lambda: "run-1",
    )


@pytest.mark.asyncio
async def test_runner_is_default_disabled_and_never_starts_child(tmp_path):
    runner = _runner(tmp_path, enabled=False)
    assert runner.status().availability is RunnerAvailability.DISABLED
    with pytest.raises(WorkflowRunnerUnavailable):
        await runner.start(
            workspace_id="workspace",
            session_id="session",
            workspace_dir=str(tmp_path),
            slug="missing",
        )


@pytest.mark.asyncio
async def test_runner_reports_missing_node_without_launching_child(
    tmp_path, monkeypatch
):
    import workspace_service.workflow_runner as runner_module

    monkeypatch.setattr(runner_module.shutil, "which", lambda _: None)
    runner = WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True),
        fixture_path=tmp_path / "missing.mjs",
    )
    assert runner.status().availability is RunnerAvailability.INCOMPATIBLE
    fixture = tmp_path / "fixture.mjs"
    fixture.write_text("// fixture", encoding="utf-8")
    runner = WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True),
        fixture_path=fixture,
    )
    assert runner.status().availability is RunnerAvailability.MISSING
    with pytest.raises(WorkflowRunnerUnavailable):
        await runner.start(
            workspace_id="workspace",
            session_id="session",
            workspace_dir=str(tmp_path),
            slug="missing",
        )


@pytest.mark.asyncio
async def test_runner_snapshots_persisted_revision_and_cancels_with_generation(
    tmp_path,
):
    WorkspaceWorkflowStore(str(tmp_path)).create("fixture", '{"nodes": []}')
    runner = _runner(tmp_path)
    run = await runner.start(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    assert run.state is WorkflowRunState.RUNNING
    assert run.revision == 1
    with pytest.raises(WorkflowRunnerError, match="stale"):
        await runner.cancel(run.run_id, generation=2)
    cancelled = await runner.cancel(run.run_id, generation=1)
    assert cancelled.state is WorkflowRunState.CANCELLED
    assert [event.kind for event in runner.events(run.run_id)] == [
        "queued",
        "started",
        "cancelling",
        "cancelled",
    ]


@pytest.mark.asyncio
async def test_runner_enforces_concurrency_and_reconciliation_invalidates_generation(
    tmp_path,
):
    WorkspaceWorkflowStore(str(tmp_path)).create("fixture", '{"nodes": []}')
    runner = _runner(tmp_path, limit=1)
    await runner.start(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    with pytest.raises(WorkflowRunnerError, match="concurrency"):
        await runner.start(
            workspace_id="workspace",
            session_id="session",
            workspace_dir=str(tmp_path),
            slug="fixture",
        )
    reconciled = await runner.reconcile()
    assert reconciled[0].reason == "runner_restarted"
    assert runner.status().generation == 2


def test_real_runner_catalog_verifies_pinned_inventory(tmp_path):
    import hashlib
    import json

    source = tmp_path / "src" / "wright-runner.ts"
    source.parent.mkdir()
    source.write_text("source", encoding="utf-8")
    artifact = tmp_path / "dist" / "wright-runner.mjs"
    artifact.parent.mkdir()
    artifact.write_text("bundle", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "runner": "wright-rivet2-node",
        "protocol_version": 1,
        "rivet_version": "2.8.9",
        "source": {
            "repository": "https://github.com/valerypopoff/rivet2.0.git",
            "revision": "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053",
            "package": "@valerypopoff/rivet2-node",
            "package_version": "2.1.9",
        },
        "entrypoint": "dist/wright-runner.mjs",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "bytes": len(artifact.read_bytes()),
        "build_input": {
            "path": "src/wright-runner.ts",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        "runtime_network_policy": "wright-bridge-only",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    catalog = RunnerAssetCatalog(manifest_path)
    assert catalog.status()[0] is RunnerAvailability.AVAILABLE

    artifact.write_text("changed", encoding="utf-8")
    assert catalog.status()[0] is RunnerAvailability.INCOMPATIBLE


def test_real_runner_status_fails_closed_for_missing_or_wrong_version(tmp_path):
    runner = WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True, real_execution_enabled=True),
        node_path="node",
        fixture_path=tmp_path / "fixture.mjs",
        artifact_catalog=RunnerAssetCatalog(tmp_path / "missing.json"),
    )
    assert runner.status().availability is RunnerAvailability.MISSING

    (tmp_path / "manifest.json").write_text(
        '{"schema_version":1,"runner":"wright-rivet2-node","protocol_version":2}',
        encoding="utf-8",
    )
    runner = WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True, real_execution_enabled=True),
        node_path="node",
        fixture_path=tmp_path / "fixture.mjs",
        artifact_catalog=RunnerAssetCatalog(tmp_path / "manifest.json"),
    )
    assert runner.status().availability is RunnerAvailability.INCOMPATIBLE
