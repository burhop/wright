from data_vault import (
    WorkflowRunEventRecord,
    WorkflowRunRecord,
    WorkflowTraceRepository,
)
from workspace_service.workflow_trace.capture import WorkflowTraceCapture


DIGEST = "a" * 64


def test_incremental_capture_survives_restart_and_duplicate_delivery(tmp_path) -> None:
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    capture = WorkflowTraceCapture(repository)
    run = WorkflowRunRecord(
        run_id="run-1",
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        revision=1,
        digest=DIGEST,
        graph="main",
        state="running",
        generation=1,
        started_at=1,
        completed_at=None,
        reason_code=None,
        output_summary=None,
        output_truncated=False,
    )
    capture.register_rivet_run(run)
    event = WorkflowRunEventRecord(
        run_id="run-1",
        sequence=1,
        occurred_at=2,
        kind="progress",
        payload={"phase": "node-start", "nodeId": "block-1"},
    )
    capture.append_rivet_event(event)
    WorkflowTraceCapture(
        WorkflowTraceRepository(tmp_path / "state.db")
    ).append_rivet_event(event)
    assert repository.get_run("run-1") is not None


def test_capture_failure_does_not_escape_execution_boundary(tmp_path) -> None:
    capture = WorkflowTraceCapture(WorkflowTraceRepository(tmp_path / "state.db"))
    capture.append_rivet_event(
        WorkflowRunEventRecord(
            run_id="missing", sequence=1, occurred_at=2, kind="progress", payload={}
        )
    )
