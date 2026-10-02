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
The fresh default-model heat update succeeded through normal Wright controls:
13 browser steps prove generation, fixed build, preview, save and opening revision
`revision-7de5f2d40aef4d26b44a172b85c631f9`. Its 97-line source imports the shared
controls and retains the comparison and exact evidence callbacks. Actual prepared
and waiting-state control qualification remains pending. Three fresh reuse checks
stopped at loading; a timing trace records the requested run snapshot returning
HTTP 200 after 32.849 seconds, beyond their 30-second limit. A read-only snapshot
confirms the second run is waiting and undecided. These failed checks are retained;
the delay remains usability debt. The earlier timed-out authoring update is also
retained. The successful update/build scope is published separately in
`artifacts/process-interfaces/083/20261002-live-heat-shared-controls/`.

The longer-read walkthrough reached the waiting review, then exposed a genuine
preparation defect: the presentation API shell lacked the main API's gateway,
so required MCP-tool qualification reported unavailable. Startup now binds the
same existing gateway and proxy/authority owners to that shell; it constructs no
second gateway. The actual saved build also contained no stylesheet. The fixed
host entry now explicitly imports the installed kit stylesheet so named-export
tree shaking cannot discard it. The 82-check gateway-boundary/build/static suite,
changed-file Ruff and web TypeScript pass. A fresh revision and served check are
still required; historical saved bundles and failed screenshots are unchanged.
Shared controls now display activity while checking inputs or confirming a
recorded request; their focused component checks pass.

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
