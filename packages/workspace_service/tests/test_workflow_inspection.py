from __future__ import annotations

from data_vault import WorkflowRunEventRecord, WorkflowRunRecord
from workspace_service.workflow_inspection import build_workflow_inspection


def persisted_run(**overrides) -> WorkflowRunRecord:
    values = {
        "run_id": "run-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "workflow_id": "workflow-1",
        "revision": 2,
        "digest": "a" * 64,
        "graph": "Main",
        "state": "failed",
        "generation": 3,
        "started_at": 100,
        "completed_at": 109,
        "reason_code": "RIVET_MCP_TRANSPORT_CANCELLED",
        "output_summary": {"outputs": {"upstream": {"ok": True}}, "durationMs": 9000},
        "output_truncated": False,
        "trace_id": "trace-run-1",
    }
    values.update(overrides)
    return WorkflowRunRecord(**values)


def run_event(sequence: int, kind: str, **payload) -> WorkflowRunEventRecord:
    return WorkflowRunEventRecord("run-1", sequence, 100 + sequence, kind, payload)


def child_call(**overrides) -> dict:
    values = {
        "call_id": "call-1",
        "request_id": "request-1",
        "run_id": "run-1",
        "node_id": "node-search",
        "qualified_tool_name": "onshape.search",
        "trace_id": "trace-child-1",
        "state": "failed",
        "child_received": True,
        "started_at": "1970-01-01T00:01:41Z",
        "completed_at": "1970-01-01T00:01:42Z",
        "reason_code": "RIVET_MCP_TRANSPORT_CANCELLED",
        "result": None,
        "result_complete": True,
        "artifacts": [],
        "redaction_count": 0,
    }
    values.update(overrides)
    return values


def test_failed_child_is_correlated_with_plain_recovery_and_upstream_output() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(),
        events=(
            run_event(1, "started", phase="running"),
            run_event(2, "failed", code="RIVET_MCP_TRANSPORT_CANCELLED"),
        ),
        incremental_events=(
            run_event(2, "failed", code="RIVET_MCP_TRANSPORT_CANCELLED"),
        ),
        child_calls=(child_call(),),
        manifest={"residue_possible": False},
    )

    assert inspection["run"]["latest_sequence"] == 2
    assert inspection["steps"][0]["node_id"] == "node-search"
    assert inspection["diagnostic"]["code"] == "RIVET_MCP_TRANSPORT_CANCELLED"
    assert inspection["diagnostic"]["failed_step_id"] == "call-1"
    assert inspection["diagnostic"]["full_rerun_available"] is True
    assert inspection["diagnostic"]["partial_retry_available"] is False
    assert inspection["final_outputs"][0]["name"] == "upstream"


def test_old_success_record_is_projected_without_child_evidence() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded",
            reason_code=None,
            output_summary={"outputs": {"answer": 42}, "durationMs": 5},
        ),
        events=(run_event(1, "completed", duration_ms=5),),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )

    assert inspection["diagnostic"] is None
    assert inspection["final_outputs"][0]["value"] == 42
    assert inspection["completeness"]["outputs_complete"] is True
    assert inspection["events"] == []
