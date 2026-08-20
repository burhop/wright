# Data Model: Rivet Run Inspector

## Workflow Run Summary

The durable identity and lifecycle projection for one execution.

| Field | Type | Rules |
|---|---|---|
| `run_id` | string | Immutable and unique. |
| `workspace_id` | string | Must match the requesting workspace. |
| `session_id` | string | Must match the requesting session. |
| `workflow_id` | string | Immutable workflow identity. |
| `revision` | integer | At least 1; identifies the exact saved workflow revision. |
| `digest` | SHA-256 string | Digest of the exact saved workflow bytes. |
| `graph` | string | Selected graph name, bounded by the existing runner contract. |
| `generation` | integer | At least 1; prevents stale cancellation and status updates. |
| `state` | enum | `queued`, `running`, `cancelling`, `cancelled`, `succeeded`, or `failed`. |
| `started_at` | UTC timestamp or null | Set on the first transition to running. |
| `completed_at` | UTC timestamp or null | Set exactly once for a terminal state. |
| `duration_ms` | integer or null | Runner duration when available; otherwise derived from timestamps. |
| `reason_code` | string or null | Stable technical terminal reason. |
| `trace_id` | string or null | Correlation identity when available; never a reusable token. |
| `latest_sequence` | integer | Highest persisted run-event sequence. |
| `output_truncated` | boolean | True when retained output is incomplete. |
| `output_redaction_count` | integer | Number of redactions applied to the retained projection. |

### State transitions

```text
queued -> running -> succeeded
                 -> failed
                 -> cancelling -> cancelled
                              -> failed
queued -> cancelled
queued -> failed
```

Terminal states are immutable. Refresh reattaches to an existing active state; it never creates a new run.

## Run Progress

A current projection derived from persisted events.

| Field | Type | Rules |
|---|---|---|
| `phase` | string or null | Latest safe phase label. |
| `current_step_id` | string or null | Correlated execution step, when known. |
| `completed_steps` | integer | Count of terminal successful/failed/cancelled steps. |
| `total_steps` | integer or null | Known graph execution-step count when available. |
| `last_sequence` | integer | Event cursor used for incremental polling. |
| `updated_at` | UTC timestamp or null | Time of the latest included event. |

## Execution Step

A stable user-facing reduction of progress and child-call evidence.

| Field | Type | Rules |
|---|---|---|
| `step_id` | string | Stable within the run; prefers child call ID, otherwise node/request correlation. |
| `sequence` | integer | Deterministic display order. |
| `node_id` | string or null | Rivet node identity when known. |
| `label` | string | Readable node, tool, or phase label. |
| `kind` | enum | `node`, `mcp_call`, `approval`, or `runner`. |
| `qualified_tool_name` | string or null | Namespaced MCP tool identity when applicable. |
| `request_id` | string or null | Correlation identifier, not authority. |
| `trace_id` | string or null | Child trace identity when available. |
| `state` | enum | `queued`, `running`, `succeeded`, `failed`, `cancelled`, `not_run`, or `unknown`. |
| `started_at` | UTC timestamp or null | From child evidence or first correlated event. |
| `completed_at` | UTC timestamp or null | From child evidence or terminal event. |
| `duration_ms` | integer or null | Derived only when both times or an explicit duration exist. |
| `reason_code` | string or null | Stable technical reason. |
| `result` | Run Result or null | Safe retained intermediate result. |
| `artifacts` | list of artifact references | Only workspace-authorized artifacts. |
| `redaction_count` | integer | Redactions applied before persistence. |

Child-call terminal evidence wins over transient progress if their states conflict. Missing evidence is shown as unknown; it is not guessed from graph topology.

## Run Result

A safe representation of one final output or intermediate step result.

| Field | Type | Rules |
|---|---|---|
| `result_id` | string | Stable within the run and result origin. |
| `name` | string | Named output, content block label, or fallback label. |
| `origin` | enum | `final_output` or `step_result`. |
| `kind` | enum | `text`, `structured`, `list`, `link`, `artifact`, `media`, `null`, or `unknown`. |
| `value` | JSON value or null | Complete retained redacted value when `complete` is true. |
| `preview` | string or null | Bounded readable preview. |
| `complete` | boolean | False when backend limits, expiry, or missing evidence prevent full display. |
| `truncation_reason` | string or null | Stable reason when incomplete. |
| `original_bytes` | integer or null | Serialized size before bounded projection, after redaction. |
| `retained_bytes` | integer | Serialized retained size. |
| `digest` | SHA-256 string or null | Digest of the complete redacted value when available. |
| `redaction_count` | integer | Number of removed secret-bearing fields or URL values. |
| `artifact` | artifact reference or null | Authorized open/download target when applicable. |

Final outputs use the existing 1 MiB run-output boundary. Each intermediate child result uses the existing 64 KiB event/evidence scale. An oversized value produces an incomplete result descriptor instead of failing an otherwise successful workflow.

## Run Diagnostic

Deterministic user guidance derived from terminal reason and step evidence.

| Field | Type | Rules |
|---|---|---|
| `code` | string | Stable reason code. |
| `summary` | string | Plain-language explanation without secrets. |
| `recovery_action` | string | Concrete safe next action. |
| `failed_step_id` | string or null | Correlated failed step. |
| `failed_node_id` | string or null | Correlated canvas node. |
| `qualified_tool_name` | string or null | Failed MCP tool when applicable. |
| `trace_id` | string or null | Available run or child trace identity. |
| `full_rerun_available` | boolean | True only when current saved revision remains eligible. |
| `partial_retry_available` | boolean | Always false in this feature version. |
| `residue_possible` | boolean | Requires child application inspection before rerun. |

## Run Inspection

The single API projection consumed by the bottom inspector.

| Field | Type | Rules |
|---|---|---|
| `schema_version` | literal `1` | Enables additive evolution. |
| `run` | Workflow Run Summary | Authoritative current or terminal state. |
| `progress` | Run Progress | Current event reduction. |
| `steps` | list of Execution Step | Bounded and ordered. |
| `final_outputs` | list of Run Result | Complete named terminal outputs when retained. |
| `diagnostic` | Run Diagnostic or null | Present for failed/cancelled runs when a reason exists. |
| `completeness` | object | Declares output, timeline, child-call, and evidence truncation or unavailability. |

## Workflow Run History

A bounded list of run summaries scoped to one workspace, session, and workflow.

- Default limit: 20.
- Maximum limit: 50.
- Sort: newest effective start time first, then run identity for deterministic ties.
- Active runs are included.
- Historical revisions remain immutable and visibly distinct from the current document revision.
- Old records lacking newer optional evidence fields remain readable with explicit unavailable values.

