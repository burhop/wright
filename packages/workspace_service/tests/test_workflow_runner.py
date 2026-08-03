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
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
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
