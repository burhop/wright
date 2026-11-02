from data_vault import WorkflowRunRecord
from workspace_service.workflow_trace.sources import adapt_rivet_run, adapt_source_run


DIGEST = "a" * 64


def rivet(state: str, completed_at=None) -> WorkflowRunRecord:
    return WorkflowRunRecord(
        run_id="run-1",
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        revision=1,
        digest=DIGEST,
        graph="main",
        state=state,
        generation=1,
        started_at=1,
        completed_at=completed_at,
        reason_code=None,
        output_summary=None,
        output_truncated=False,
    )


def test_adapts_completed_failed_cancelled_and_interrupted_rivet_runs() -> None:
    assert adapt_rivet_run(rivet("succeeded", 2)).outcome == "completed"
    assert adapt_rivet_run(rivet("failed", 2)).outcome == "failed"
    assert adapt_rivet_run(rivet("cancelled", 2)).outcome == "cancelled"
    interrupted = adapt_rivet_run(rivet("running"))
    assert interrupted.outcome == "interrupted"
    assert interrupted.ended_at is None


def test_source_adapter_preserves_blocked_status_and_legacy_gaps() -> None:
    record = adapt_source_run(
        {"run_id": "run-2", "workflow_id": "workflow-2", "status": "blocked"},
        workspace_id="workspace-1",
        source_ref="runs/run-2.json",
    )
    assert record.outcome == "blocked"
    assert record.capture_state == "legacy"
    assert record.definition_digest is None


def test_source_adapter_keeps_revision_digest_without_current_definition() -> None:
    record = adapt_source_run(
        {
            "run_id": "run-3",
            "workflow_id": "workflow-2",
            "status": "completed",
            "workflow_digest": DIGEST,
            "definition_ref": "vault:def-3",
            "layout_ref": "vault:layout-3",
            "capture_complete": True,
        },
        workspace_id="workspace-1",
        source_ref="runs/run-3.json",
    )
    assert record.definition_digest == DIGEST
    assert record.definition_ref == "vault:def-3"
    assert record.capture_state == "complete"
