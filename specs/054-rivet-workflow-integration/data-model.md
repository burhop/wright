# Data Model: Incremental Rivet Workflow Integration

**Branch**: `054-rivet-workflow-integration`

**Status**: Umbrella conceptual model; each owning slice defines physical schemas and migrations.

## Ownership Rules

- User-authored workflow definitions, datasets, and attachments are workspace files.
- Relational identity, revision indexes, review state, runs, events, policies, and publications use existing embedded SQLite ownership patterns.
- Large or immutable recordings, logs, and generated outputs use the existing file vault/artifact model.
- Credentials and reusable secrets use the Wright secret provider and are referenced by opaque configuration identity only.
- Process IDs, ports, WebSocket endpoints, presentation credentials, approval grants, and runtime handles are ephemeral and are never treated as durable state after restart.

## Workflow Definition

Represents one workspace-owned Rivet project.

| Field | Meaning | Invariant |
|---|---|---|
| `workflow_id` | Stable Wright opaque identifier | Never derived solely from a user-editable path |
| `workspace_id` | Owning workspace | Mandatory and immutable |
| `slug` | Human-readable directory name | Unique under the workspace workflow collection |
| `title` | Display name | Bounded and sanitized for presentation |
| `project_path` | Canonical relative `.rivet-project` location | Confined under `workflows/<slug>/` |
| `format_version` | Rivet/Wright schema compatibility marker | Future unsupported versions fail closed |
| `content_revision` | ETag/content digest or monotonic revision | Required for save and run |
| `content_digest` | Digest of exact authored bytes | Links reviews and runs to immutable content |
| `plugin_requirements` | Declared plugin IDs/versions | Must be allowlisted and available |
| `policy_classification` | Requested/effective capability class | Requested capability never grants authority |
| `review_state` | `draft`, `reviewed`, `changes_requested`, `retired` | A content change invalidates prior review |
| `created_at`, `updated_at` | Audit timestamps | Server generated |

Relationships: owns zero or more datasets and attachments; has many revisions/reviews/runs; may have zero or more publications.

## Workflow Dataset

| Field | Meaning | Invariant |
|---|---|---|
| `dataset_id` | Rivet-visible stable dataset ID | Unique within one workflow project |
| `workflow_id` | Owning workflow | Mandatory |
| `relative_path` | Workspace-relative sidecar location | Confined below the workflow directory |
| `schema_version` | Dataset representation version | Validated before use |
| `revision` / `digest` | Conflict and provenance identity | Atomic update required |
| `size_bytes`, `row_count` | Bounded metadata | Enforced before editor/runner transfer |
| `updated_at` | Last durable write | Server generated |

Datasets cannot reference another workspace or a project by an unvalidated absolute path.

## Workflow Revision

An immutable execution/review source.

| Field | Meaning |
|---|---|
| `workflow_id` | Parent workflow |
| `revision_id` | Stable revision identity |
| `project_digest` | Exact project content digest |
| `dataset_manifest_digest` | Exact set of referenced dataset digests |
| `plugin_manifest_digest` | Exact approved plugin set |
| `created_by`, `created_at` | Authorship audit |
| `review_id` | Optional review approving this exact revision |

A run snapshots the revision before it enters `starting`; later saves never mutate it.

## Workflow Editor Surface Binding

| Field | Meaning | Durability |
|---|---|---|
| `surface_id` | Existing `LiveAppSurface` identity | Durable intent |
| `workspace_id` | Bound workspace | Durable intent |
| `selected_workflow_id` | Current project, if any | Recoverable preference |
| `editor_build_id` | Pinned bundle/adapter compatibility ID | Durable diagnostics |
| `runtime_generation` | Current process/bootstrap generation | Ephemeral |
| `dirty_state` | `clean`, `dirty`, `autosaving`, `conflicted`, `recoverable` | Recoverable, never sole source of authored truth |
| `last_heartbeat_at` | Liveness | Ephemeral |
| `recovery_blob_ref` | Optional bounded unsaved recovery payload | Durable only under workspace metadata policy |

One active editor binding per workspace is the default; existing Workspace Surface retention limits remain authoritative.

## Runtime Generation

Identifies one supervised runner/editor process lifetime so stale clients cannot reconnect to a replacement.

| Field | Meaning |
|---|---|
| `generation_id` | Opaque random identity |
| `workspace_id` | Bound workspace |
| `kind` | `editor` or `runner` |
| `compatible_build_id` | Editor/runner pin |
| `started_at`, `expires_at` | Lifecycle bounds |
| `status` | `starting`, `ready`, `draining`, `stopped`, `failed` |

PID, port, socket, and credentials are held only in live supervisor state and reconciled on restart.

## Workflow Run

| Field | Meaning | Invariant |
|---|---|---|
| `run_id` | Opaque run identity | Globally unique |
| `workflow_id`, `revision_id` | Exact execution source | Immutable after creation |
| `workspace_id`, `principal_id`, `session_id` | Wright authority context | Revalidated at every privileged boundary |
| `runtime_generation` | Runner lifetime | Stale generation cannot append/act |
| `graph_id` | Selected Rivet graph | Must exist in pinned revision |
| `input_digest` / protected input reference | Exact bounded inputs | Secret-safe and access controlled |
| `effective_policy_id` | Server-selected policy snapshot | Immutable for audit; revocation can further restrict |
| `trace_id` | Cross-service correlation | Required |
| `status` | Run state | Transitions below |
| `queued_at`, `started_at`, `finished_at` | Lifecycle timestamps | Server generated |
| `terminal_reason` | Bounded structured outcome | Required for terminal states |

### Run State Machine

```text
queued -> starting -> running -> succeeded
                   |       |-> waiting_approval -> running
                   |       |                    -> failed
                   |       |                    -> cancelling
                   |       |-> pausing -> paused -> running
                   |       |                    -> cancelling
                   |       |-> cancelling -> cancelled
                   |       `-> failed
                   `-> failed

Any non-terminal live state discovered after Wright restart -> orphaned -> failed or cancelled after reconciliation.
```

Terminal states are `succeeded`, `failed`, and `cancelled`. `orphaned` is a reconciliation state, not a successful restoration of the old process. State transitions are idempotent by event sequence and runtime generation.

## Workflow Node Event

| Field | Meaning |
|---|---|
| `run_id`, `runtime_generation` | Parent and live generation |
| `sequence` | Monotonic per run for ordering/idempotency |
| `node_id`, `graph_id` | Rivet location when applicable |
| `kind` | `started`, `progress`, `partial_output`, `tool_request`, `approval_wait`, `artifact`, `warning`, `failed`, `completed` |
| `payload_ref` | Inline bounded redacted value or vault reference |
| `trace_id`, `timestamp` | Correlation and time |

Oversized or binary payloads are stored as access-controlled artifacts; event streams carry references and summaries.

## Workflow Artifact

Extends Wright's existing artifact record with:

- `run_id`, `workflow_id`, `revision_id`, `node_id`
- producing tool/external-function identity
- input/effective-constraint digests
- approval identities/outcomes where applicable
- MIME type, size, content digest, vault reference
- protected prompt/direct-execution provenance consistent with Workspace Surfaces

Artifacts never inherit public visibility from a Rivet node or plugin.

## Workflow Policy Profile

| Capability | Example values |
|---|---|
| `code` | disabled / reviewed-only |
| `network` | disabled / Wright allowlist |
| `direct_mcp` | disabled (default) / explicitly approved |
| `plugins` | Wright baseline only / named allowlist |
| `filesystem` | disabled / mediated workspace reads / mediated writes |
| `project_references` | disabled / same-workflow allowlist |
| `graph_upload` | disabled / authorized authors |
| `agent_publication` | disabled / authorized publishers |
| resource limits | duration, memory, concurrency, event/output/log sizes |

The effective profile is the intersection of deployment policy, workspace policy, user role, workflow review, and requested capabilities. Client/project declarations can only narrow it.

## Workflow Publication

| Field | Meaning |
|---|---|
| `publication_id` | Stable projection identity |
| `workflow_id`, `revision_id`, `review_id` | Exact approved source |
| `workspace_id` | Discovery and execution boundary |
| `kind` | `catalog` or optional `agent_tool` |
| `name`, `description` | User/agent-facing metadata |
| `input_schema`, `output_schema` | Bounded typed contract |
| `policy_profile_id` | Execution policy |
| `status` | `active`, `suspended`, `retired` |

A revision change, expired/revoked review, missing plugin, incompatible runtime, or policy tightening suspends publication until explicitly revalidated.

## Delivery Slice Record

This is a planning record in umbrella documentation, not a production database entity.

| Field | Meaning |
|---|---|
| `short_name` | Stable branch suffix from the roadmap |
| `spec_number` | Assigned only when Spec Kit starts the slice |
| `base_commit` | Latest umbrella commit used to branch |
| `prerequisites` | Merged slices/contracts required |
| `status` | planned / specifying / planning / approved / implementing / validating / merged / deferred |
| `plan_approval` | Human decision and date |
| `evidence` | Tests, artifacts, and limitations |
| `rollback` | Proven disable/downgrade path |

## Validation Rules Owned by Slices

- Persistence owns path, slug, revision, atomicity, dataset, format, and migration validation.
- Runner owns state transitions, generation, event ordering, limits, cancel, and reconciliation.
- Editor adapters own bootstrap, selected-workflow, conflict, dirty/recovery, and bundle compatibility.
- Wright nodes own tool/approval/artifact/policy validation.
- Operations owns review and interactive publication validation.
- Agent publication owns typed projection and invalidation.
- Hardening proves the aggregate invariants across supported platforms and packages.
