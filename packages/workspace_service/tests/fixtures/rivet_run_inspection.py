from __future__ import annotations

from data_vault import WorkflowRunEventRecord, WorkflowRunRecord


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
