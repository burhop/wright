from __future__ import annotations

import pytest

from data_vault import WorkflowReviewRepository
from workspace_service.workflow_operations import (
    WorkflowOperationsError,
    WorkflowOperationsSettings,
    WorkspaceWorkflowOperations,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from workspace_service.workflows import WorkspaceWorkflowStore

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

from data_vault import WorkflowRunEventRecord, WorkflowRunRecord
from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessStopResult,
    RuntimeSnapshot,
)


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
        updated = replace(
            snapshot,
            status="stopped",
            stop_result=ProcessStopResult(0, True, False, (), ()),
        )
        self.snapshots[runtime_id] = updated
        return updated


def _operations(tmp_path) -> WorkspaceWorkflowOperations:
    fixture = tmp_path / "fixture.mjs"
    fixture.write_text("// fixture", encoding="utf-8")
    runner = WorkspaceWorkflowRunner(
        supervisor=_Supervisor(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True),
        node_path="node",
        fixture_path=fixture,
        id_factory=lambda: "run-1",
    )
    return WorkspaceWorkflowOperations(
        WorkflowReviewRepository(str(tmp_path / "state.db")),
        runner,
        settings=WorkflowOperationsSettings(enabled=True),
    )


@pytest.mark.asyncio
async def test_operations_run_saved_revision_without_review_and_preserve_scope(
    tmp_path,
):
    WorkspaceWorkflowStore(str(tmp_path)).create("sample", '{"nodes": []}')
    operations = _operations(tmp_path)

    run = await operations.start(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="sample",
    )
    assert run.workflow_id
    with pytest.raises(WorkflowOperationsError, match="not found"):
        await operations.history(
            workspace_id="workspace-b", session_id="session-a", run_id=run.run_id
        )


@pytest.mark.asyncio
async def test_saved_workflow_does_not_require_a_new_review(tmp_path):
    store = WorkspaceWorkflowStore(str(tmp_path))
    store.create("sample", '{"nodes": []}')
    operations = _operations(tmp_path)
    store.save("sample", 1, '{"nodes": ["changed"]}')

    run = await operations.start(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="sample",
    )
    assert run.revision == 2


class _InspectionRunner:
    def __init__(self) -> None:
        self.record = WorkflowRunRecord(
            run_id="run-inspection",
            workspace_id="workspace-a",
            session_id="session-a",
            workflow_id="workflow-a",
            revision=4,
            digest="a" * 64,
            graph="Main",
            state="succeeded",
            generation=2,
            started_at=100,
            completed_at=103,
            reason_code=None,
            output_summary={"outputs": {"answer": {"ok": True}}},
            output_truncated=False,
            trace_id="trace-inspection",
        )
        self.persisted_events = (
            WorkflowRunEventRecord("run-inspection", 1, 100, "started", {}),
            WorkflowRunEventRecord("run-inspection", 2, 103, "succeeded", {}),
        )

    def get(self, run_id: str):
        assert run_id == self.record.run_id
        return SimpleNamespace(
            workspace_id=self.record.workspace_id,
            session_id=self.record.session_id,
        )

    def result(self, run_id: str) -> WorkflowRunRecord:
        assert run_id == self.record.run_id
        return self.record

    def events(self, run_id: str, *, after_sequence: int = 0):
        assert run_id == self.record.run_id
        return tuple(
            event for event in self.persisted_events if event.sequence > after_sequence
        )

    def manifest(self, run_id: str):
        assert run_id == self.record.run_id
        return None

    def recent_records(self, **kwargs):
        assert kwargs == {
            "workspace_id": "workspace-a",
            "session_id": "session-a",
            "workflow_id": "workflow-a",
            "limit": 7,
        }
        return (self.record,)

    def latest_sequence(self, run_id: str) -> int:
        assert run_id == self.record.run_id
        return 2


@pytest.mark.asyncio
async def test_operations_are_default_disabled(tmp_path):
    operations = WorkspaceWorkflowOperations(
        WorkflowReviewRepository(str(tmp_path / "state.db")),
        runner=None,  # type: ignore[arg-type]
    )
    with pytest.raises(WorkflowOperationsError, match="disabled"):
        await operations.detail(
            workspace_id="workspace", workspace_dir=str(tmp_path), slug="sample"
        )


def test_inspection_and_recent_runs_preserve_scope_and_event_cursor(tmp_path):
    runner = _InspectionRunner()
    operations = WorkspaceWorkflowOperations(
        WorkflowReviewRepository(str(tmp_path / "state.db")),
        runner,  # type: ignore[arg-type]
        settings=WorkflowOperationsSettings(enabled=True),
    )

    inspection = operations.inspection(
        workspace_id="workspace-a",
        session_id="session-a",
        run_id="run-inspection",
        after_sequence=1,
    )
    assert inspection["run"]["run_id"] == "run-inspection"
    assert [event["sequence"] for event in inspection["events"]] == [2]
    assert inspection["final_outputs"][0]["name"] == "answer"

    recent = operations.recent_runs(
        workspace_id="workspace-a",
        session_id="session-a",
        workflow_id="workflow-a",
        limit=7,
    )
    assert recent[0]["revision"] == 4
    assert recent[0]["latest_sequence"] == 2

    with pytest.raises(WorkflowOperationsError, match="not found"):
        operations.inspection(
            workspace_id="workspace-b",
            session_id="session-a",
            run_id="run-inspection",
        )
