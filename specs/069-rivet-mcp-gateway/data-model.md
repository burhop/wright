# Data Model: Rivet Workspace MCP Gateway Execution

## Identity and canonicalization

All digest-bearing values use canonical UTF-8 JSON with lexicographically sorted object keys, no insignificant whitespace, explicit null handling, and SHA-256. Raw authority tokens, credentials, authorization headers, child environments, and unrestricted host paths are excluded from every durable entity.

## CapabilityBinding

Immutable resolution of one Rivet MCP node to one current workspace capability. The JSON contract is `contracts/capability-binding.schema.json`.

| Field | Type | Rules |
|-------|------|-------|
| `binding_id` | UUID/string | Stable immutable identity |
| `workspace_id` | string | Exact workspace scope |
| `workflow_id` | string | Exact workflow identity |
| `workflow_revision` | integer | Positive revision |
| `workflow_digest` | hex | Exact project bytes |
| `graph_id` | string | Selected graph |
| `node_id` | string | Unique executable MCP node |
| `node_handle` | string | Random/non-semantic reserved handle exposed to runner; unique in binding set |
| `requirement_id` | string/null | Portable capability requirement, when authored |
| `qualified_tool_name` | string | Gateway namespace-qualified identity |
| `server_id` / `server_revision` | strings | Exact child registration and implementation revision |
| `capability_digest` | hex | Catalog/local capability record identity |
| `validation_evidence_id` | string | Current local validation evidence |
| `workspace_grant_digest` | hex | Enablement/member projection at review |
| `input_schema` | JSON object | Bounded canonical schema |
| `output_schema` | JSON object/null | Bounded canonical schema |
| `schema_digest` | hex | Canonical schemas together |
| `risk` | JSON object | Data/effect/approval/idempotency facts; annotations remain untrusted hints |
| `units_policy` / `material_defaults` | JSON | Material engineering assumptions bound into review |
| `argument_constraints` | JSON Schema/object | Limits on dynamic arguments; tool identity is never dynamic |
| `binding_digest` | hex | Canonical digest of all material fields |
| `created_at` | timestamp | UTC |

Uniqueness: `(workspace_id, workflow_id, workflow_revision, workflow_digest, graph_id, node_id)` and `binding_digest`.

## WorkflowBindingSet

One immutable set used by a review and later authority.

- `binding_set_id`
- workspace/workflow/revision/digest/graph identity
- sorted `binding_ids[]` and `binding_digests[]`
- `discovery_snapshot_digest`
- `policy_snapshot_digest`
- `binding_set_digest`
- `created_at`

Every executable MCP tool-call node appears exactly once. Extra bindings are rejected. A graph with no MCP nodes has an explicit empty binding set.

## WorkflowReview v2

Extends the existing review without storing workflow content.

- existing workspace/workflow/revision/state/reviewer/updated fields
- `workflow_digest`
- `graph_id`
- `binding_set_id` and `binding_set_digest`
- `policy_snapshot_digest`
- `review_digest`: canonical identity of reviewable facts plus reviewer/state/time
- `stale_reason_code`: computed projection, not authority

Only `approved` and current exact identities allow a run. Legacy reviews without v2 identity remain valid for non-MCP graphs only.

## RivetRunAuthority (memory only)

- `authority_id`
- `token_digest` (raw 256-bit token held only by caller and service memory)
- run/generation/workspace/session/workflow/revision/digest/graph identities
- review and binding-set digests
- `node_bindings`: node handle -> binding digest
- `issued_at`, `expires_at`, `revoked_at`, `terminal_at`
- `state`: `issued`, `active`, `revoked`, `expired`, `terminal`
- active request IDs and consumed one-shot approval IDs

State transitions:

```text
issued -> active -> terminal
   |         |
   |         `-> revoked -> terminal
   `-> expired -> terminal
```

Validation uses constant-time token comparison. Restart discards all records, making old tokens unusable.

## PendingRivetCallApproval

Durable exact approval request created only after gateway policy reports required gates.

- `approval_id`
- run, authority, node, binding, session, server, tool, and request identities
- `argument_digest`
- sorted `required_gates[]`
- `state`: `pending`, `approved`, `denied`, `expired`, `consumed`, `cancelled`
- requesting actor, deciding actor, reason, created/expiry/decided/consumed times
- `approval_digest`

Approval can be consumed once by the same run/node/tool/argument digest. Repeated non-idempotent calls need distinct approval records unless existing gateway policy explicitly proves equivalence.

## RunManifest

Immutable run identity plus terminal summary. JSON contract is `contracts/run-manifest.schema.json`.

- schema/protocol/runner versions and source digest
- run/generation/workspace/session/workflow/revision/digest/graph
- review/binding-set/policy snapshot digests
- authority ID/digest, issue/expiry/revocation times (never token)
- ordered binding summaries and schema/server/validation identities
- child-call summary counts and ordered record IDs
- approval summary IDs/digests
- artifact references: vault ID, media type, digest, size, label
- start/completion times, terminal state, reason code
- cancellation acknowledgement and residue summary
- event/output truncation and redaction counters
- trace ID and manifest digest

## RivetChildCallRecord

Append-only evidence for one attempted node invocation.

| Field group | Contents |
|-------------|----------|
| identity | call ID, request ID, run, authority, node, binding, trace/correlation IDs |
| target | qualified tool, server/revision, schema and validation digests |
| input | argument digest, byte count, redaction count; bounded safe preview only |
| policy | decision/reason, required gates, approval ID/digest |
| lifecycle | preparation/start/health/cleanup states and stable reason codes |
| timing | queued, started, progress, completed, cancelled timestamps |
| result | success/error/cancelled/timeout, structured-result digest, content byte count |
| artifacts | bounded vault references |
| residue | cancellation acknowledgement, externally-running/unknown flag, recovery text |

Calls denied before child invocation have `child_received=false`. This field is asserted by negative tests.

## RivetRunEvent

Uses the existing ordered workflow-run event table with a typed payload:

- `phase`: `authority-issued`, `node-start`, `binding-validated`, `approval-required`, `approval-resolved`, `child-starting`, `child-progress`, `child-result`, `artifact`, `cancelling`, `child-cancelled`, `residue`, `node-finish`, `terminal`
- run/node/call/binding/trace identities
- stable status/reason code
- bounded title/message/progress numbers
- no secret material or raw child log

The repository enforces contiguous sequence and 64 KiB maximum event JSON.

## DiscoveryProjection

Read-only, non-authoritative view returned during authoring/review:

- discovery snapshot digest and observed time
- workspace and gateway session identity
- stable qualified name and display title
- server identity/revision, capability/validation identity
- bounded input/output schemas and schema digest
- compatibility, health, locality, data/effect/risk/approval facts
- binding eligibility and stable blocking reasons

Tool annotations are labeled hints. Credentials/configuration are reduced to safe status booleans.

## Database migration 14

Migration 14 is additive:

- extend `workspace_workflow_reviews` with v2 digest/graph/binding/policy/review columns, nullable for legacy non-MCP rows;
- add `workspace_workflow_binding_sets`;
- add `workspace_workflow_capability_bindings`;
- add `workspace_workflow_run_manifests`;
- add `workspace_workflow_child_calls`;
- add `workspace_workflow_call_approvals`;
- add run-manifest identity columns to `workspace_workflow_runs` where indexed projection is required.

Foreign keys use restrictive deletion for review/run evidence. Workflow deletion retains run history according to current product retention. Migration and runtime `_ensure` paths are idempotent and preserve schema-13 data.

## Invariants

1. A binding maps one exact graph node to one namespace-qualified tool.
2. A binding-set digest changes when any material binding, graph, workflow, workspace grant, server/schema/validation, or policy fact changes.
3. An MCP run starts only from a current approved v2 review and exact binding set.
4. A raw run token appears in no database row, log, event, UI response, artifact, or workflow file.
5. Authority cannot list/call outside its workspace, run, node handles, binding set, or expiry.
6. Every call revalidates current enablement and binding identity before lifecycle start.
7. Review never satisfies a required tool approval.
8. Terminal or revoked authority rejects every later call, and late results cannot change terminal state.
9. Denied pre-child calls record `child_received=false`.
10. Existing non-MCP workflows retain behavior during migration and rollback.
