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
async def test_operations_require_current_approved_review_and_preserve_scope(tmp_path):
    WorkspaceWorkflowStore(str(tmp_path)).create("sample", '{"nodes": []}')
    operations = _operations(tmp_path)

    with pytest.raises(WorkflowOperationsError, match="not been approved"):
        await operations.start(
            workspace_id="workspace-a",
            session_id="session-a",
            workspace_dir=str(tmp_path),
            slug="sample",
        )
    detail = await operations.review(
        workspace_id="workspace-a",
        workspace_dir=str(tmp_path),
        slug="sample",
        state="approved",
        reviewer="owner",
    )
    assert detail.review and detail.review.revision == 1
    run = await operations.start(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="sample",
    )
    assert run.workflow_id == detail.workflow_id
    with pytest.raises(WorkflowOperationsError, match="not found"):
        await operations.history(
            workspace_id="workspace-b", session_id="session-a", run_id=run.run_id
        )


@pytest.mark.asyncio
async def test_saved_workflow_invalidates_previous_review(tmp_path):
    store = WorkspaceWorkflowStore(str(tmp_path))
    store.create("sample", '{"nodes": []}')
    operations = _operations(tmp_path)
    await operations.review(
        workspace_id="workspace-a",
        workspace_dir=str(tmp_path),
        slug="sample",
        state="approved",
        reviewer="owner",
    )
    store.save("sample", 1, '{"nodes": ["changed"]}')

    with pytest.raises(WorkflowOperationsError, match="not been approved"):
        await operations.start(
            workspace_id="workspace-a",
            session_id="session-a",
            workspace_dir=str(tmp_path),
            slug="sample",
        )


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
