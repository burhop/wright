# Contract: Rivet Run Inspector API

All routes remain under `/api/workspace`, require the existing local workspace session identity, return `Cache-Control: no-store`, and use thin FastAPI handlers over `workspace_service` projections.

## List recent runs

`GET /workflows/{slug}/runs?session_id={session_id}&limit={1..50}`

Response:

```json
{
  "workflow_id": "workflow-123",
  "current_revision": 7,
  "runs": [
    {
      "run_id": "run-123",
      "workflow_id": "workflow-123",
      "revision": 7,
      "digest": "<sha256>",
      "graph": "Main",
      "generation": 4,
      "state": "running",
      "started_at": "2026-08-20T14:00:00Z",
      "completed_at": null,
      "duration_ms": 1350,
      "reason_code": null,
      "trace_id": "<non-secret-correlation-id>",
      "latest_sequence": 9,
      "has_outputs": false,
      "has_diagnostic": false,
      "output_truncated": false
    }
  ]
}
```

Rules:

- Scope must match workspace, session, and resolved workflow identity.
- The endpoint never creates, resumes, cancels, or mutates a run.
- A missing workflow returns 404. An invalid limit returns 422.
- The UI selects the newest active run on workspace load; otherwise it selects the newest terminal run without rerunning it.

## Get one inspection snapshot

`GET /workflows/runs/{run_id}/inspection?session_id={session_id}&after_sequence={n}`

Response:

```json
{
  "schema_version": 1,
  "run": {
    "run_id": "run-123",
    "workspace_id": "workspace-123",
    "session_id": "session-123",
    "workflow_id": "workflow-123",
    "revision": 7,
    "digest": "<sha256>",
    "graph": "Main",
    "generation": 4,
    "state": "failed",
    "started_at": "2026-08-20T14:00:00Z",
    "completed_at": "2026-08-20T14:00:09Z",
    "duration_ms": 9351,
    "reason_code": "RIVET_MCP_BRIDGE_DENIED",
    "trace_id": "trace-123",
    "latest_sequence": 14,
    "output_truncated": false,
    "output_redaction_count": 0
  },
  "progress": {
    "phase": "child-call",
    "current_step_id": "call-2",
    "completed_steps": 1,
    "total_steps": 3,
    "last_sequence": 14,
    "updated_at": "2026-08-20T14:00:09Z"
  },
  "events": [
    {
      "sequence": 14,
      "kind": "failed",
      "occurred_at": "2026-08-20T14:00:09Z",
      "payload": { "code": "RIVET_MCP_BRIDGE_DENIED" }
    }
  ],
  "steps": [
    {
      "step_id": "call-2",
      "sequence": 2,
      "node_id": "node-search",
      "label": "Search FeatureScript documentation",
      "kind": "mcp_call",
      "qualified_tool_name": "onshape-labs-featurescript-mcp.search",
      "request_id": "request-2",
      "trace_id": "child-trace-2",
      "state": "failed",
      "started_at": "2026-08-20T14:00:08Z",
      "completed_at": "2026-08-20T14:00:09Z",
      "duration_ms": 1000,
      "reason_code": "RIVET_MCP_BRIDGE_DENIED",
      "result": null,
      "artifacts": [],
      "redaction_count": 0
    }
  ],
  "final_outputs": [],
  "diagnostic": {
    "code": "RIVET_MCP_BRIDGE_DENIED",
    "summary": "Wright stopped this MCP call before it reached the selected server.",
    "recovery_action": "Refresh the workflow's tool connections and run the saved revision again.",
    "failed_step_id": "call-2",
    "failed_node_id": "node-search",
    "qualified_tool_name": "onshape-labs-featurescript-mcp.search",
    "trace_id": "child-trace-2",
    "full_rerun_available": true,
    "partial_retry_available": false,
    "residue_possible": false
  },
  "completeness": {
    "outputs_complete": true,
    "steps_complete": true,
    "events_complete": true,
    "evidence_available": true,
    "reasons": []
  }
}
```

Rules:

- `events` contains only events with sequence greater than `after_sequence`; `steps`, `run`, `progress`, outputs, and diagnostic remain complete snapshots so refresh and dropped polls recover safely.
- While a run is active, polling at 500 ms is allowed. The client stops polling at terminal state and uses exponential backoff only for transient transport errors.
- Result values are already redacted and bounded. Clients must not reconstruct omitted values from logs or metadata.
- `complete=false` and `completeness.reasons` must be shown whenever backend limits, expiry, or missing historical evidence affect the projection.
- Failure responses use existing 404 scope behavior and stable 409/422 validation behavior; they never reveal whether another workspace owns a run.

## Result item

```json
{
  "result_id": "final:mesh",
  "name": "mesh",
  "origin": "final_output",
  "kind": "artifact",
  "value": null,
  "preview": "Bracket.stl",
  "complete": true,
  "truncation_reason": null,
  "original_bytes": 128,
  "retained_bytes": 128,
  "digest": "<sha256>",
  "redaction_count": 0,
  "artifact": {
    "artifact_id": "Bracket.stl",
    "label": "Bracket.stl",
    "media_type": "model/stl",
    "sha256": "<sha256>",
    "bytes": 4096
  }
}
```

Copy and JSON export use exactly this safe retained projection. Artifact open/download continues through the existing authorized artifact route.

## Existing routes retained

- `POST /workflows/{slug}/runs` remains the only start operation.
- `POST /workflows/runs/{run_id}/cancel` retains generation checks.
- `GET /workflows/runs/{run_id}/history` remains available to existing clients and honors `after_sequence`.
- `GET /workflows/runs/{run_id}/evidence` and `/evidence/export` remain the technical evidence contract.
- No partial-retry endpoint is added in schema version 1.

