# Contract: Wright process interactions v1

**Version:** `wright.process-interaction/1`. Proposed implementation contract.
Breaking changes require another major version; additive optional fields remain
compatible. Python/Pydantic and TypeScript contracts must share schema fixtures.
Schemas are generated from owning contracts during implementation, not hand-drifted.

## Snapshot

### Retained producer attempts (9 October local implementation)

The recorder's complete read now projects byte-pinned workspace files retained
before a `design_revision` event, independently of the current output map. This
also works when the next producer attempt fails before returning any results.
Existing run records are read without migration or rewriting. No earlier output
is reintroduced into execution responses, current ports or approval subjects.

The owning process projection uses the existing `outputs[]` shape with role
`previous_attempt`, `producer_attempt`, and a stable history occurrence ID.
Original run/step/port identity and file path/hash remain recorded; assessment
matching uses the original result identity and exact bytes. The common view
groups these under **Previous attempts** and labels them as superseded evidence.
Saved generated interfaces can consume these existing fields; compatibility and
their treatment of this role must still be checked before claiming a particular
tailored view presents history correctly. The common view remains available.

History navigation and file access reuse the existing process scope, artifact
owner and readers. Reads require exact run, source, occurrence ID, path and hash;
changed files report stale. A history ID grants no execution/review authority.
Only byte-pinned workspace representations qualify: a live CAD document or
step-response locator may now refer to a later attempt and is not exposed as an
immutable historical representation. Complete current and prior inventories
share the recorder's item/byte bounds and fail explicitly if exceeded.

| Field | Contract |
|---|---|
| context | ProcessRef, optional run_id, input_snapshot_id/digest, contract_version, snapshot cursor and generated_at |
| inputs[] | Stable input/block/port ID, title, bounded value schema, unit/frame, required/default, provenance, dependencies, current value reference, configured option source and freshness |
| readiness | ready/blocked/unsupported, assessment identity/expiry, classifications and actionable reasons; check again at start |
| outputs[] | Existing EngineeringResult and representation references, roles/formats, exact producer revision/hash, assessments/currentness, supported view/download capabilities |
| interactions[] | Declared pending checkpoint ID/type/step, subject digest, frozen response schema or decisions, evidence references, state, instructions |
| actions[] | Stable action ID, operation, exact subject, enabled, reasons[], prerequisite references, idempotency requirements; backend authority |
| observations[] | Provider/operation identity, lifecycle/activity, nullable %/time/layer or generic metrics, observed_at, stale_after, provenance, limitations |
| diagnostics[] | Optional bounded recorded-run Reasons with owning step, correction and exact log/navigation references; no checkpoint or action authority |
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
| POST /process-interfaces/interactions/{checkpoint_id}/decision | Exact approval/artifact decision using current review owners; server-derived run and actor |
| POST /process-interfaces/actions/{action_id} | Exact permitted action; current services are composed, not reimplemented |
| POST /process-interfaces/runs/{run_id}/cancel | Explicit cancel request/outcome |
| POST /process-interfaces/inputs/upload | Bounded declared-file input publication; no preparation or execution |
| POST /process-interfaces/representations/read | Exact prepared-input or recorded-result membership and hash-checked bytes |
| POST /process-interfaces/navigation | Resolve exact presentation target through source/run/result/082 owners |

Existing result/validation/review read/export routes remain canonical. The client
maps to them through owning services. Legacy source-start stream can adapt to
start+follow for compatibility, but disconnect must no longer cancel execution.
Do not duplicate existing reviewer authorization or result repositories.

Approval decision readiness concerns the exact persisted subject, accepted source,
frozen inputs, criteria, reviewed files and actor authority. It does not require
the producer's live capabilities. A pending decision can therefore be enabled
while execution would be unavailable. Continuation independently requalifies
current tools, options, readers and frozen model routing before consuming or
dispatching the action. Clients must use each action's own permitted state;
neither decision availability nor a recorded approval implies that continuation
is available. This does not change the transport or UI compatibility version.

`PendingInteraction.decision` optionally exposes the retained decision, actor,
bounded redacted reason, request identity and integration-test attribution. It
cannot appear on input interactions. Native review bodies contain only the
source/session reference, subject digest, declared decision, reason and request
ID; actor, run, destination, automatic-review and integration flags are rejected.
The client verifies the exact returned subject/request/decision. Identical retries
read the existing decision and can repair an interrupted recorder projection;
they do not dispatch or rerun work. Approval consumption remains a separate action.

The native input-response route additionally accepts a strict optional `auto`
boolean, defaulting to false, for explicitly authorized isolated tests. The
ordinary scoped client and generated interfaces do not expose this switch.
When true, the existing integration-policy owner checks enabled, current,
non-revoked enrollment against the checkpoint's workspace, accepted source,
input subject and frozen campaign/dataset identities. It derives the test actor;
the caller cannot supply an actor, `integration_test` flag, run or grant.
Enrollment alone never changes a manual response into a test answer. The input
owner still validates the answer schema and current source, model configuration
and upstream artifacts before its existing one-shot continuation. Test attribution
grants no review, validation override or external-action authority. Identical
requests return the same retained answer; uncertain claimed work is not replayed.

Native navigation returns shared `NavigationResolution(process, target,
representation?)`. The resolved target preserves every supplied identity and can
add its recorded producer/result identity. Run-backed result/assessment/evidence
navigation requires an explicit run; caller paths grant no read authority. A
checked result and its validator's recorded assessment file can have different
result IDs. Missing or ambiguous assessment files and omitted bounded-read
results remain unavailable rather than guessed. The workspace host retains open
editor drafts and observers while selecting the exact existing tab. This is a
presentation read, never a process mutation or action authority.

Generated apps access the same bounded operation envelopes under the reserved
preview route `/__wright/process`; this server resolves process/UI/run scope
from the presentation. Parent bearer tokens and printer credentials never appear
in app JavaScript. SSE reconnect uses cursor replay; a lost/expired cursor obtains
a full snapshot. Backend events are retained authority, browser state is cache.

For managed navigation only, the bridge supplies its authorized presentation run
when the target omits `run_id`. Explicit run selectors must match that binding;
they are never replaced. A preparation presentation supplies no run. The native
navigation owner still requires an explicit run for recorded output evidence and
verifies exact source/result/assessment membership before resolving it.

Representation reads accept optional `preview: "toolpaths"` and a confined
`archive_entry` only in that mode. They retain the same process/results grant,
exact run or preparation membership and original artifact SHA-256. The passive
derived MIME is `application/vnd.wright.toolpaths+json`, with view format
`wright.gcode.toolpaths.v1`; the SHA-256 response header identifies the original
recorded artifact rather than claiming the JSON bytes are the artifact.
Parser provenance separately identifies the actual G-code entry bytes and
records true layers, comment-based feature categories, nominal arc approximation
and excluded unlayered extrusion. Unknown labels stay unclassified. Multi-plate
ambiguity, unsupported motion, bounds or deadline return inspection/download
fallback; they never change process acceptance or dispatch any operation.

## Currentness, limits and errors

An optional `preview: "validation-report"` on the existing representation read
returns passive `text/markdown`, with `X-Wright-View-Format:
wright.validation.report.v1`. The artifact hash header still identifies the
original assessment JSON. The owner first enforces exact process/run/result/file
membership and unchanged bytes, then matches those bytes to a report returned by
the existing validator for that workspace/run. An embedded assessment ID alone
grants no access. This mode requires a recorded result (not a prepared input),
accepts no page/archive selector, and is bounded to16MiB source and2MiB report
under the existing worker deadline. It carries original checks and currentness;
it cannot create a review, change a verdict, or start work. Native and managed
transports use the same owner and process.results grant. Missing capability or
unsupported reports retain exact download fallback. Existing UI bundles need an
explicit rebuild to adopt new reader code; no stored bundle is silently changed.

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
