# Shared controls and prepared-file handoffs

Resume checkpoint, 2 October 2026. Implementation evidence; not complete live
interface, engineering or user acceptance.

## Shared controls

`@wright/ui-kit` exports `WorkingControls`, a composition over the existing
scoped client and host-supplied interaction snapshot. It provides preparation,
declared review/response/action and backend-permitted cancellation controls.
There is no graph executor, model call, provider implementation or independent
process-status authority in this composition.

Preparation freezes explicit drafts, checks that input snapshot, and reads the
backend projection for its ID. Start requires a current ready assessment and an
enabled Start action for the exact frozen input digest. Editing inputs clears
preparation; another source/run projection cannot grant Start. Preview remains
read-only. Pending reads/uploads abort when scope changes without cancelling a
run.

Mutation intent is retained in session storage before sending. Persistence
failure prevents submission; a second click cannot submit again. Restoration
does not replay. Explicit reconciliation clears an uncertain review/action only
for its exact request/checkpoint/subject receipt in the same process and run.
If a start, response or cancellation receipt is absent from the public projection,
the controls keep the request held and direct recovery to the canonical common
view. This limitation is explicit; no receipt is inferred.

The focused serialized component run passes **100 checks**, including the new
controls, existing kit and common view. Web TypeScript compilation passes.
Private reports: `t046-working-controls-004.json`; previous reports remain
retained. The preceding parallel run had one existing layer-slider assertion
failure; it is not reported as passing. No geometry renderer change was made.
The authoring/build/toolchain suite also passes **58 checks**, including the
fixed local builder. Private report: `t046-working-controls-authoring-001.xml`.
The generated heat interface still needs a fresh default-model update and served
browser qualification using this composition. The earlier timed-out update is
retained and the previous saved comparison remains authoritative.

## Prepared file consumption

The completed wheel construction and repair exposed a distinct handoff defect:
the slicer accepted a produced STL reference but the dependency verifier rejected
its prepared input profile files because those inputs were not engineering
results. Supplied/defaulted `WorkflowReference` inputs now use the same confined
path, SHA-256 and recorded byte-count check immediately before consumption.
They do not acquire fabricated engineering producer provenance. Missing, changed,
mismatched or unpinned files stop before either exact-tool or scoped-AI execution.

**57 focused runtime checks pass**, including actual compiled consumers of
unchanged/changed supplied files, deterministic output handoffs, MCP execution,
approval and the original example preparation. Ruff passes for both changed
Python files. Private report: `t045-supplied-file-dependency-003.xml`.

The passing component/runtime reports and their checked scope are retained in
`artifacts/process-interfaces/083/20261002-shared-working-controls/`.

The failed wheel run remains failed; it has not been replayed or reclassified.
Loading this fix and qualifying a fresh digital chain remains pending. No slicer
completion, full wheel assessment, physical dispatch or engineering acceptance
is claimed by these tests.
