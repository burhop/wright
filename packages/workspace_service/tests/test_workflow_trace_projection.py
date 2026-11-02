import pytest

from core.workflow_trace import TraceRunRecord
from data_vault import WorkflowTraceRepository
from workspace_service.workflow_trace.projection import WorkflowTraceProjection


def test_projection_is_workspace_scoped_and_read_only(tmp_path) -> None:
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(
        TraceRunRecord(
            workspace_id="workspace-1",
            run_id="run-1",
            source_kind="legacy",
            source_record_ref="run:1",
            source_record_digest="a" * 64,
            workflow_id="workflow-1",
            original_status="failed",
            outcome="failed",
            capture_state="legacy",
        )
    )
    projection = WorkflowTraceProjection(repository)
    summary = projection.summary(workspace_id="workspace-1", run_id="run-1")
    assert summary["run"]["outcome"] == "failed"
    assert summary["mutations_allowed"] is False
    with pytest.raises(KeyError):
        projection.summary(workspace_id="workspace-2", run_id="run-1")
