# Contract: Wright process interactions v1

**Version:** `wright.process-interaction/1`. Proposed implementation contract.
Breaking changes require another major version; additive optional fields remain
compatible. Python/Pydantic and TypeScript contracts must share schema fixtures.
Schemas are generated from owning contracts during implementation, not hand-drifted.

## Snapshot

| Field | Contract |
|---|---|
| context | ProcessRef, optional run_id, input_snapshot_id/digest, contract_version, snapshot cursor and generated_at |
| inputs[] | Stable input/block/port ID, title, bounded value schema, unit/frame, required/default, provenance, dependencies, current value reference, configured option source and freshness |
| readiness | ready/blocked/unsupported, assessment identity/expiry, classifications and actionable reasons; check again at start |
| outputs[] | Existing EngineeringResult and representation references, roles/formats, exact producer revision/hash, assessments/currentness, supported view/download capabilities |
| interactions[] | Declared pending checkpoint ID/type/step, subject digest, frozen response schema or decisions, evidence references, state, instructions |
| actions[] | Stable action ID, operation, exact subject, enabled, reasons[], prerequisite references, idempotency requirements; backend authority |
| observations[] | Provider/operation identity, lifecycle/activity, nullable %/time/layer or generic metrics, observed_at, stale_after, provenance, limitations |
| navigation[] | Validated process/block/run/result/assessment/evidence targets, no arbitrary executable URL |

Reason shape: code, readable_message, correction, affected_binding/step,
optional navigation and technical_details_ref. Default UI shows the message and
next action. Codes/digests/raw tool failures remain available in details.

Readiness classifications: supplied, explicit_default, upstream_produced,
declared_human_response, unresolved. Optional absent inputs are explicitly omitted.
Required unknown schemas/options/evidence do not pass. Provider option identity
contains configured binding+schema/resource revision+value; a friendly label is
not authority. A device-specific option shape stays provider data.

`waiting_human`, `waiting_external`, `reconciliation_required`, `failed` and
`cancellation_requested` have distinct visible meanings. A submitted action
receipt, observed operation start and observed completion are separate facts.

## Scoped client

Public package `@wright/process-client` exports the same interface over two
transports: authenticated native Wright control plane and presentation-bound
preview origin. Host supplies scope; app arguments cannot select a principal or
another workspace. Public operation categories are:

| Method | Owner / behavior |
|---|---|
| getSnapshot() / follow(cursor) | Rebuild facts and attach events; no execution on subscription |
| setInputs(values,files,expectedSource) | Create/update preparation, validate schema and return snapshot identity; no accepted-source write |
| checkReadiness(inputSnapshot) | Compile supported dependencies and qualify current prerequisites |
| start(inputSnapshot,requestId) | Fresh readiness + durable start receipt + existing backend executor |
| attach(runId) | Server validates that run belongs to this allowed process/workspace |
| respond(checkpoint,subject,values,requestId) | Declared input response, frozen schema/currentness, one-shot continuation |
| decide(checkpoint,subject,decision,reason,requestId) | Existing exact-subject review authority; actor derived from auth |
| requestAction(actionId,subject,requestId) | Backend-permitted action only; fresh checks, consume/reconcile rules |
| cancel(runId,requestId) | Explicit supported cancellation; actual outcome, no success assumption |
| getRepresentation(ref) | Authorized bounded read/download; references resolved server-side |
| navigate(target) | Exact host navigation intent, not a process mutation |

No public `invokeTool`, `executeGraph`, arbitrary shell, destination override or
automatic approval operation is exposed to generated apps. A supported workflow
can still invoke its configured tools through the existing runtime.

## Transport/API mapping

Under the existing authenticated workspace router mount, add a thin
`process-interfaces` API. Route suffixes below are relative to that mount; preserve
existing deployment prefix rather than introducing a competing API root.

| Route suffix | Operation |
|---|---|
| GET /process-interfaces/interaction | Snapshot for explicit accepted source reference and optional authorized run |
| POST /process-interfaces/inputs | Immutable prepared input snapshot |
| POST /process-interfaces/readiness | Fresh readiness assessment |
| POST /process-interfaces/runs | Backend-owned start; return 202 + run/receipt identity |
| GET /process-interfaces/runs/{run_id} | Snapshot/outcome reconciliation |
| GET /process-interfaces/runs/{run_id}/events | SSE following existing recorded events, with durable cursor |
| POST /process-interfaces/interactions/{checkpoint_id}/response | Input response; decision routes delegate to current review service |
| POST /process-interfaces/actions/{action_id} | Exact permitted action; current services are composed, not reimplemented |
| POST /process-interfaces/runs/{run_id}/cancel | Explicit cancel request/outcome |

Existing result/validation/review read/export routes remain canonical. The client
maps to them through owning services. Legacy source-start stream can adapt to
start+follow for compatibility, but disconnect must no longer cancel execution.
Do not duplicate existing reviewer authorization or result repositories.

Generated apps access the same bounded operation envelopes under the reserved
preview route `/__wright/process`; this server resolves process/UI/run scope
from the presentation. Parent bearer tokens and printer credentials never appear
in app JavaScript. SSE reconnect uses cursor replay; a lost/expired cursor obtains
a full snapshot. Backend events are retained authority, browser state is cache.

## Currentness, limits and errors

Each mutation includes request_id, expected_source_digest and exact subject/input
identity as appropriate. Reuse with different payload returns conflict; duplicates
return recorded outcome. Cursor is for reconciliation, not permission to act.
Backend rereads current dependencies before mutation. A layout/theme-only update
does not alter engineering subject identity.

Initial bounds: 256 projected bindings/interactions per snapshot page, 64 KiB
inline value/diagnostic payload, 32 MiB image/file upload per item and 64 MiB per
input request; larger supported artifact representations use streamed vault
references and reader-specific bounds. JSON schemas allow bounded objects/arrays,
primitive enums/ranges/local definitions; no remote references/executable validators.
Required unsupported schema features return unsupported, not weakened validation.

Error categories: INPUT_REQUIRED, READINESS_UNSUPPORTED, SOURCE_CHANGED,
SUBJECT_STALE, OPTION_STALE, INTERACTION_NOT_DECLARED, RESPONSE_INVALID,
REQUEST_CONFLICT, CAPABILITY_UNAVAILABLE, ACTION_NOT_PERMITTED, OUTCOME_UNKNOWN,
UI_INCOMPATIBLE, SCOPE_DENIED, PRESENTATION_EXPIRED. These are platform error
semantics; adapters map existing detailed codes without losing diagnostics.

Required negative fixtures cover stale source/result/option, absent required
evidence, revoked presentation, cross-workspace/run/UI scope, duplicate/lost
responses, and unauthorized mutations. Common and generated views receive the
same reasons. Unknown external outcomes block repeat submission.
