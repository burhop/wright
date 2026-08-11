# Data Model: Rivet Hermes AI and MCP Execution

## Existing entities retained

### WorkflowDocument

File-authoritative entity rooted at `workflows/<slug>/`.

| Field | Type | Rules |
|---|---|---|
| workflow_id | UUID string | Stable across rename/save |
| slug | safe slug | 1-63 lowercase letters, digits, hyphens |
| revision | positive integer | Incremented on every save/rename |
| digest | SHA-256 | Digest of exact project bytes |
| project | UTF-8 Rivet project | Existing 4 MiB limit |
| datasets | map of safe slug to JSON text | Existing per-dataset limit |

### WorkflowReview

Durable SQLite approval bound to `(workspace_id, workflow_id, revision)`. A later revision is not approved by an earlier review.

### WorkflowTemplate

Reviewed package resource identified by catalog ID, title, kind, requirements, source repository/revision/path, and exact project bytes.

## New/extended entities

### RivetAiBridgeSession

In-memory only.

| Field | Type | Rules |
|---|---|---|
| token_digest | secret digest | Raw token returned only to the trusted same-origin client |
| audience | enum | `editor` or `runner` |
| model_alias | string | Fixed `wright-hermes` |
| created_at | timestamp | Monotonic/runtime-owned |
| expires_at | timestamp | Short bounded lifetime |
| maximum_request_bytes | integer | Positive configured cap |
| active_requests | integer | Bounded concurrency |

State: `issued -> active -> expired/revoked`. Host shutdown revokes immediately.

### RivetCompatibilityRequest

Validated transient projection of an OpenAI Chat Completions request.

| Field | Type | Rules |
|---|---|---|
| request_id | UUID | Correlation only |
| messages | bounded list | Supported roles/content only |
| tools | bounded list | Function tools only, unique safe names |
| tool_choice | supported choice | `auto`, `required`, `none`, or one named function |
| stream | boolean | Both modes supported |
| model | string | Replaced/normalized to the configured Hermes alias |

Parallel tool calls are rejected for the Graph Builder compatibility path.

### WorkflowValidationResult

Bounded, serializable result for one immutable workflow revision.

| Field | Type | Rules |
|---|---|---|
| workflow_id | UUID | Matches document |
| revision | integer | Matches document |
| digest | SHA-256 | Matches exact project |
| valid | boolean | False if any error exists |
| main_graph | graph summary/null | Selected default if valid |
| graphs | bounded graph summary list | ID/name/input/output declarations |
| requirements | bounded enum list | AI, dataset, native file, code, network, MCP, interactive input |
| errors | bounded issue list | Stable code, graph/node location, message |
| warnings | bounded issue list | Stable code, graph/node location, message |

### WorkflowRunRequest

| Field | Type | Rules |
|---|---|---|
| run_id | UUID | Wright-generated |
| workspace_id | string | Trusted binding only |
| session_id | string | Trusted binding only |
| workflow_id | UUID | Re-read from store |
| slug | safe slug | Tool/UI supplied |
| revision | integer | Must match current and approved revision |
| digest | SHA-256 | Must match current bytes |
| graph | string/null | Must resolve inside project |
| inputs | bounded JSON object | Converted to Rivet loose data values |
| context | bounded JSON object | Converted to Rivet loose data values |
| approved_capabilities | enum set | Server-derived, never graph-derived |

### WorkflowRunRecord

Durable bounded SQLite projection; project content and full model transcript are excluded.

| Field | Type | Rules |
|---|---|---|
| run_id | UUID | Primary identity |
| workspace_id/session_id | string | Access boundary |
| workflow_id/revision/digest | immutable identity | Exact executed document |
| graph | string | Resolved graph |
| state | enum | queued, running, cancelling, cancelled, succeeded, failed |
| generation | integer | Reject stale process control |
| started_at/completed_at | timestamp/null | Lifecycle timing |
| reason_code | string/null | Stable terminal failure code |
| output_summary | bounded JSON/null | Successful outputs within cap |
| output_truncated | boolean | True when full output exceeds cap |

Transitions:

```text
queued -> running -> succeeded
                  -> failed
                  -> cancelling -> cancelled
queued -> cancelled
queued/running/cancelling -> failed (reconcile or cleanup failure)
```

### WorkflowRunEvent

Append-only bounded event projection keyed by `(run_id, sequence)` with timestamp, kind, and bounded redacted payload. Events include queued, started, node progress, AI wait/progress, output-ready, cancelling, cancelled, completed, and failed.

### WrightManagedMcpServer

Registry definition compiled into Wright, not the public catalog.

| Field | Value/rule |
|---|---|
| server_id | `rivet-workflows` |
| transport | stdio |
| command | installed `wright-rivet-mcp` entry point |
| installed | true |
| default enabled | true on first seed; preserve later user choice |
| risk | medium |
| workspace binding | canonical cwd plus trusted IDs/database path |
| credentials | none exposed to MCP |

## Relationships

```text
WorkflowTemplate --creates--> WorkflowDocument --has--> WorkflowReview
                                            |--validates--> WorkflowValidationResult
                                            `--executes--> WorkflowRunRecord --has--> WorkflowRunEvent

Rivet editor ----+
                 +--> shared workflow services --> authoritative workspace file
Rivet MCP -------+

RivetAiBridgeSession --> Hermes adapter --> existing Hermes/Codex subscription
```
