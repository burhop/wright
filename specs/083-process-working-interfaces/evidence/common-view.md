# Common process view evidence

## T019 native component — 2026-09-30

Branch: `codex/083-process-working-interfaces`. This entry proves the native
component and recovery controller. Workspace hosting and actual served-browser
proof are T020–T021 and remain pending.

### Implemented

`CommonProcessView.tsx` composes the public client and kit for declared schema
inputs, units/options, uploaded-image thumbnails, explicit preparation/readiness,
backend-permitted start/cancel, recorded progress, exact results/assessments,
representation preview/download, declared-checkpoint inspection and navigation.
Optional missing ports and read-only views remain visible and disabled. Input
edits invalidate readiness; uploads must finish before preparation. Ready
assessments expire visibly while idle and cannot enable a start after expiry.

The controller reads on mount and follows a saved run; it never prepares, starts,
reviews or cancels on subscription. It uses the existing public `setInputs`,
`checkReadiness`, `start`, `follow`, `cancel`, representation and navigation ports.
There is no graph executor, provider protocol, tool invocation or independent
engineering/job-status authority. Unsupported checkpoint response controls remain
disabled pending T024–T027; this milestone does not claim those capabilities.

`process-view-recovery.ts` stores only compact backend input identities and
request/receipt locators, without input values, file bytes or credentials.
Recovery records are bounded and scoped to session/workspace/path/source revision.
The immutable preparation derives one stable start request ID; cancellation
derives one stable ID from its run. The journal is written and verified before
start submission. A lost acknowledgement preserves that same identity for an
explicit reconciliation; no mutation is retried automatically. Reopening reads
the existing run. Unreadable recovery blocks new preparation rather than
overwriting an uncertain request. A different explicit run does not adopt a
cached receipt. Existing backend scope, fresh readiness and durable receipt
authority continue to control every operation.

Scoped remounts and read generations discard late replies. Closing aborts only
the event observer. An already submitted start can still save its accepted receipt
after close. A cancellation acknowledgement is a request, not confirmation of
stopping. Another view's pending start is checked before draft clearing, before
and after asynchronous preparation, and before writing a start. These guards and
stable immutable-preparation IDs complement backend deduplication; the browser
cache is not a distributed locking or execution authority.

Result pages retain exact identities and reject merging changed snapshot cursors.
Representations use the owning host callback, bound digest and safe public viewer;
the native download uses a Blob URL released on close/replacement. Rendering and
empty findings cannot approve an engineering result. New-run preparation remains
a separate host action after a recorded terminal outcome.

### Verification

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/components/process-interfaces/CommonProcessView.spec.tsx src/components/common/ProcessUIKit.spec.tsx tests/ThreeDViewer.spec.tsx src/services/process-client.spec.ts vite.config.spec.ts
node ../../node_modules/eslint/bin/eslint.js src/components/process-interfaces/CommonProcessView.tsx src/components/process-interfaces/CommonProcessView.spec.tsx src/services/process-view-recovery.ts
```

**124 checks pass**, five files, 4.53 seconds: 30 common-controller/recovery,
30 public kit, four mocked geometry/lifecycle, 45 scoped client and 15 native
configuration/proxy/license checks. ESLint passes with no warnings/errors.
These are component/client/config checks with mocked backend/provider/WebGL
boundaries, not an actual served workspace, live model/MCP or engineering proof.

From the repository:

```text
node apps/web/node_modules/typescript/bin/tsc -p apps/web/tsconfig.app.json --noEmit
node apps/web/node_modules/typescript/bin/tsc -p packages/ui_kit/tsconfig.json
node apps/web/node_modules/typescript/bin/tsc -p packages/process_client/tsconfig.json
.venv/Scripts/python.exe packages/process_client/scripts/generate_contracts.py --check
git diff --check
```

Whole-app and both public-package type checks pass. The owning contract schemas
remain unchanged. Ten original prototype hashes, three protected campaign hashes,
approved feature context and two original startup/router deltas remain preserved.

### Observed corrections and pending scope

- Initial component selectors omitted the schema widget's required suffix;
  corrected selectors and strengthened the blocked downstream-input assertion.
- React 19 refs require explicit initial values; corrected strict type errors.
- An intermediate upload-status insertion matched the wrong JSX button;
  corrected it before the final passing compile/checks.
- Ref callback updates moved into an effect, and observer cleanup uses an explicit
  invalidation callback; the final focused ESLint run is clean.
- A preservation comparison initially used Windows locale decoding; reran it
  with explicit UTF-8 and verified the actual hashes/deltas. No baseline files
  were rewritten to make that check pass.

T020 must wire typed workspace tabs, restoration, exact native host ports and
deep links while preserving the reviewed editor. T021 must prove mocked and
actual served workspace journeys, reconnect and navigation. Authoring through
Wright, scoped hosting, actual digital engineering tools, migration and installed
distribution proofs remain required. No service restart, live model/provider
invocation, physical effect, campaign execution or remote publication occurred
during T019.

## 2026-10-01 — Workspace tab hosting (T020 partial)

Branch: `codex/083-process-working-interfaces`. This extends the existing viewer
store, workspace layout persistence and document strip. `Use saved process` opens
the common working view from the accepted source document; it does not save a
draft or start a run. The retained authoring panel remains mounted. Returning to
an open workflow selects it without triggering a reload or replacing its drafts,
layout or undo state. Passive definition navigation/restoration reads an existing
source; a missing file produces a reason instead of creating a replacement.

Versioned process-tab metadata contains only view/process/run locators. Host
workspace scope is checked on restore, and ordinary providers do not resolve the
reserved virtual paths. Links preserve other workspace/editor parameters while
identifying the accepted source hash and recorded run. A late accepted receipt
can update an existing view without changing focus, replacing its subject, or
reopening a closed tab. URL observation does not act as a tab-lifecycle authority.

The native host memoizes the scoped client across equivalent restored metadata
and run attachment. Closing unmounts the existing common controller's observer;
no implicit start, review or cancellation operation is introduced. The SDK exports
the existing shape/relative-locator checks as `assertProcessReference` for native
restoration. Normal backend authorization remains required.

### Checks and limits

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/services/process-workspace-tabs.spec.ts src/store/viewer-process-tabs.spec.tsx src/components/process-interfaces/ProcessWorkspaceTab.spec.tsx tests/WorkspacePanelSessions.spec.tsx tests/EditorTabs.spec.tsx src/components/pages/WorkflowRecoveryPage.spec.tsx src/services/process-client.spec.ts src/components/process-interfaces/CommonProcessView.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t020-workspace-tabs-vitest.json
```

**176 checks pass in eight files**: 32 locator, 11 store, six host, 34 mocked
workspace, two document-strip, 16 source-page, 45 scoped-client and 30 common-view
checks. These exercise component/client/store and mocked workspace boundaries;
they do not prove an actual served-browser, live provider, GPU or engineering
journey. An initial failing traversal case exposed a shape-only locator check;
the native host now reuses the SDK's confined-reference check. Two failing
navigation cases exposed the old-URL tab-reopening/focus race, corrected before
the final passing run. Returning to an existing editor was also changed from
explicit reload to selection so authoring state remains intact.

Whole-app and public-client type checks, owning-schema freshness, and whitespace
checks pass. Focused ESLint across the changed native components/tests has no
errors; its one pre-existing stream-activity dependency warning uses an expression
identical to HEAD. The final production build passes (926 modules, 1.90 seconds)
at `.local-run/process-interfaces-083/t020-workspace-tabs-final`; its existing
license artifact is 236,029 bytes. The existing large-chunk and external-output
directory notices remain. No preview/API service was launched or browser served.

Ten original prototype hashes, three protected campaign hashes, approved
feature/agent context and the original startup/router deltas remain preserved.

**T020 stays unchecked:** exact block/result/assessment/evidence navigation and
authorized representation/input-upload host ports still require their owning
service integration. This host currently reports those common-view capabilities
as unavailable; it does not supply a broad generic file-read or vendor shortcut.
T021 still requires actual served-workspace/editor/reconnect verification. The
full remaining M0–M5 scope is unchanged.

## 2026-10-01 — Native input uploads and exact representation reads

The native working tab now supplies the common view's upload and representation
ports through the public scoped client. `uploadInput` checks the host source and
declared file input before publication through the existing workspace file owner.
Publication returns a unique immutable workspace reference; it neither prepares
inputs nor edits accepted source nor starts execution. Preparation and file access
share the existing consumer/reference validation. The owning file service gained a
bounded byte reader; the legacy reference reader retains its 4 MiB limit while
process inputs support the approved 32 MiB upload bound.

`getRepresentation` requires exactly one recorded run or frozen input snapshot.
The service verifies exact membership in its canonical result/preparation, then
checks the on-disk SHA-256 before returning any bytes. Paths alone grant no read
authority. Result reads are bounded to 100 MiB, input reads to the upload limit;
smaller administrative limits remain effective. Omitted results in a truncated
canonical view produce an unavailable-reader reason instead of a false unrelated
subject claim. The route returns an inert attachment with no-store, nosniff, exact
length and owning hash headers. HTML/SVG never become executable previews.
The client bounds actual streamed bytes and checks those headers/length; the
canonical server owns the hash check. Closing or replacing a preview aborts only
its read, never the process.

The API checks exposed a real streaming defect in the existing request-body
middleware: after replaying the bounded request it invented `http.disconnect`.
It now delegates to the actual receive channel after body completion. The real
multipart/read routes and a direct connection-lifetime check prove this correction.
Another initial failure identified an import from the wrong module; result
restoration now uses the existing continuation owner, as the projection does.

Verification on Windows / Python 3.13.5 / Node 25.2.0:

```text
.venv/Scripts/python.exe -m pytest apps/api/tests/test_process_interface_artifacts.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_sources_api.py packages/workspace_service/tests/test_process_artifact_access.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py -q -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t020-artifact-batch
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_files.py packages/workspace_service/tests/test_process_run_supervisor.py apps/api/tests/test_process_interface_run_lifecycle.py -q -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t020-artifact-regressions
```

**86 + 38 = 124 backend checks pass.** These cover real bounded local file
publication/read, preparation, canonical records with a controlled generator,
stale/foreign/forged references, bounds, unknown/duplicate form fields,
authentication/origin/RBAC, inert download headers and affected source/run/file
regressions. They do not constitute live model or engineering MCP evidence.
The two existing TestClient/httpx/anyio dependency deprecation warnings remain.
Raw logs: `.local-run/process-interfaces-083/t020-artifact-batch.log` and
`t020-artifact-regressions.log`.

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/services/process-workspace-tabs.spec.ts src/store/viewer-process-tabs.spec.tsx src/components/process-interfaces/ProcessWorkspaceTab.spec.tsx tests/WorkspacePanelSessions.spec.tsx tests/EditorTabs.spec.tsx src/components/pages/WorkflowRecoveryPage.spec.tsx src/services/process-client.spec.ts src/components/process-interfaces/CommonProcessView.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t020-artifact-ports-qualified-vitest.json
```

**192 checks pass in eight actual files:** 32 locator, 11 store, seven host,
34 mocked workspace, two document-strip, 16 source-page, 59 client and 31
common-view checks. A prior filter run matched only five files; its 145 passing
checks were not used to claim workspace/store regression coverage. The final
eight-file report proves that scope. Tests include exact form fields, wrong-source
receipts, download bounds/headers/length, inert MIME, abort and preserved run
identity. Full app/client types, schema freshness, focused Ruff/ESLint and
whitespace checks pass. A fresh production build passes (926 modules, 1.90 s) at
`.local-run/process-interfaces-083/t020-artifact-ports-build`. Existing large-chunk
and external-output-directory notices remain. No browser/API/model/provider
service was launched; no served-build, engineering or user acceptance claim is made.

Ten prototype hashes, three campaign hashes and the approved context remain
unchanged. The original startup/workspace-router deltas were independently
compared to their saved baselines; only the request-streaming hunk of `main.py`
belongs to this milestone. **T020 stays unchecked for exact navigation; T021
still requires the served workspace/editor journey.** Declared interactions,
actual Wright default-model UI authoring/hosting, both digital engineering
chains, migration and distribution proof remain required.

## 2026-10-01 — Exact navigation through the native workspace

Native `navigate` resolves a shared `NavigationResolution` through a scoped thin
API and the existing accepted source, canonical recorded run, result projection
and 082 report owners. Caller paths/IDs alone never grant file access. The reply
preserves supplied identities and can add an exact producer/result reference.
Source-only navigation does not prepare inputs, create a database or start work.
Run-backed result/assessment/evidence navigation requires an explicit run.
Foreign source/run/result/producer/file identities are rejected; changed sources
retain the existing conflict semantics. An omitted output in a truncated read is
explicitly unavailable. Assessment-file resolution requires one exact recorded
SHA-256 match; an absent or ambiguous recorded file remains unavailable.

The native host selects an existing matching run tab or opens another run
separately, without retargeting its original observer. Source links select the
retained workflow tab without issuing its explicit reload action. The editor
maps source keys through its existing authoring identity rules and preserves an
unsaved source draft. A revision mismatch or deleted draft step explains why it
cannot focus the requested step. Result and assessment focus use their exact
IDs; assessment evidence retains its own validator-produced result ID, separate
from the checked engineering result. Representation reads reuse the scoped
owner and abort handling. Focus notices do not erase execution/reconciliation
notices. These are presentation intents, not process mutations or permissions.

The latest callback is supplied through a stable native dispatcher so changing
workspace callbacks does not replace the process client or reattach its run.
Initially the React ref capture failed the hook lint rule; using that dispatcher
resolved it. Test failures identified incorrect assumptions about the editor's
compact control, source-view value, textarea ID and inspector title. The final
test uses the actual Source control and verifies the selected step's exact
purpose alongside unchanged draft text. A missing-revision message initially
remained hidden when no block was selected; the inspector now displays it.

Verification on Windows / Python 3.13.5 / Node 25.2.0:

```text
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_process_navigation.py packages/workspace_service/tests/test_process_interaction_projection.py packages/core/tests/test_process_interface_contracts.py apps/api/tests/test_process_interface_artifacts.py packages/workspace_service/tests/test_process_artifact_access.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_run_supervisor.py apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_process_interfaces_api.py -q -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t020-navigation-qualified
```

**172 backend checks pass**, including actual local file/source/canonical-run
owners with a controlled generator, exact producer/evidence references, scoped
API rejection and affected contract/readiness/supervisor regressions. The
assessment navigation test composes an actual local 082 report with injected
canonical-read facts; it is not a live MCP or complete validator-run proof.
Raw log: `.local-run/process-interfaces-083/t020-navigation-qualified.log`.

From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/services/process-workspace-tabs.spec.ts src/store/viewer-process-tabs.spec.tsx src/components/process-interfaces/ProcessWorkspaceTab.spec.tsx tests/WorkspacePanelSessions.spec.tsx tests/EditorTabs.spec.tsx src/components/pages/WorkflowRecoveryPage.spec.tsx src/services/process-client.spec.ts src/components/process-interfaces/CommonProcessView.spec.tsx src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t020-navigation-qualified-vitest.json
```

**247 checks pass in nine actual files:** 32 locator, 11 store, eight native
host, 37 mocked workspace, two document-strip, 16 source-page, 60 client, 33
common-view and 48 refined editor checks. They cover native tab reuse, a separate
run observer, retained drafts, exact focus/read identity and wrong-scope reply
rejection. The full report is at the command's stated path; earlier failed focus
reports remain in that private evidence directory.

App/client type checks and owning-schema freshness pass. Focused Ruff passes;
ESLint with the explicit existing web config passes with its two pre-existing
hook dependency warnings. An initial combined lint invocation did not find a
config for the shared kit; reran it with `--config apps/web/eslint.config.js`.
The two TestClient/httpx/anyio deprecation warnings also remain. A fresh production
build passes at `.local-run/process-interfaces-083/t020-navigation-build`
(927 modules, 2.04 s), retaining the existing chunk-size/out-of-tree notices.

Preservation report: `.local-run/process-interfaces-083/t020-navigation-preservation.json`.
Ten prototype and three campaign hashes match; approved AGENTS/083 feature context
equals HEAD, and both original mixed startup/router deltas match saved baselines.
The earlier 082 feature pointer intentionally differs after the already-approved
083 activation; it is checked against approved HEAD separately.

**T020 implementation is complete; T021 served-workspace acceptance is pending.**
No browser/API/model/provider service was launched, no real tool chain or physical
operation ran, and no user acceptance is claimed. Historical changed-source
compatibility, declared interactions, actual model-authored interfaces, the two
digital engineering proofs, migration and installed-distribution checks retain
their later task scope. The full goal remains active.

## 2026-10-01 — Served workspace common view and open regression findings

Product navigation baseline: `ce6c1b3d` on
`codex/083-process-working-interfaces`, `D:/repos/wright`. The tested working
changes are the new browser fixture/journeys and the snapshot-receipt clock fix.
The common view is entered from `/workspace/ws-recovery` by clicking Workflows
and then Use saved process. It uses the actual frontend/native client/kit/tab and
refined editor components, with explicitly controlled HTTP contract responses.
**This is served frontend evidence, not a live API/model/MCP/tool-chain proof.**

Focused final run: **three passed in 15.2 s**, no skipped/flaky/unexpected tests.
Installed Chrome **154.0.8037.58**, 1280×720; Vite **8.2.0** at
`http://127.0.0.1:5236`. Flags `VITE_WRIGHT_WORKFLOW_RECOVERY`,
`VITE_WRIGHT_PROCESS_DEFINITION_VIEW` and `VITE_WRIGHT_WORKFLOW_COMPOSER` were `1`.
The actual browser version, URLs, source digest, flags, screenshot hashes and
claim boundaries are in
[checked-scope.json](../../../artifacts/process-interfaces/083/20261001-t021-common-final/checked-scope.json).
The URL identifies the tested service; it is now stopped and is not an operator
URL for a live process. API requests were intercepted browser contracts.

Verified behaviours: initial start disabled; missing input blocks start; entered
input preparation is visibly busy; only an explicit start sends the request;
event connection failure reconciles snapshots; output/assessment identities
remain distinct; the actual producing step opens in the retained editor without
losing its unapplied source draft; closing the working document does not request
cancellation; reopening its exact run link does not start again. A separate test
loses start acknowledgement, reloads, prohibits another new start, and reconciles
the original request identity. The fixture records one accepted receipt across
the two requests; actual durable dispatch authority is tested separately by the
backend checks above. No engineering result was generated or accepted here.

The screenshots were visually inspected. The assessment screenshot includes its
actual controlled JSON representation; the source screenshot includes the
unapplied draft and exact producer inspector. The completion screenshot displays
100% last reported after receipt-clock correction. Initially fresh observations
could be compared with the previous timer tick and appear momentarily stale.
Publishing the snapshot now refreshes presentation time; a dedicated component
test verifies fresh progress without waiting for the next tick. Existing future/
expired observation handling is retained. **34 common-view tests pass** in
`.local-run/process-interfaces-083/t021-clock-vitest.json`.

Commands (root directory, private installed-browser config):

```powershell
$env:VITE_WRIGHT_WORKFLOW_RECOVERY = '1'
$env:VITE_WRIGHT_PROCESS_DEFINITION_VIEW = '1'
$env:VITE_WRIGHT_WORKFLOW_COMPOSER = '1'
node node_modules/vite/bin/vite.js apps/web --config apps/web/vite.config.ts --host 127.0.0.1 --port 5236 --strictPort
```

Then, with that owned service:

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5236'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR = 'D:/repos/wright/artifacts/process-interfaces/083/20261001-t021-common-final'
$env:PLAYWRIGHT_JSON_OUTPUT_NAME = 'D:/repos/wright/.local-run/process-interfaces-083/t021-common-final-playwright.json'
node node_modules/@playwright/test/cli.js test tests/ui-integration/process-common-view.spec.ts tests/ui-integration/workflow-composer.spec.ts --config .local-run/process-interfaces-083/playwright-system-chrome.config.ts --project=chromium --workers=1 --reporter=line,json --global-timeout=120000
```

Use a **fresh output directory** when reproducing. The private config imports the
repository config, sets absolute root test/server paths and selects installed
`C:/Program Files/Google/Chrome/Application/chrome.exe`; with explicit base URL it
does not own a web server. Default repository/CI browser configuration is unchanged.
The expected Playwright browser cache was unavailable. Initial attempts also
identified incomplete test ports and a reused typed port key; corrected the
fixture to complete, uniquely named source ports. Windows managed-web-server
cleanup timed out on an earlier attempt. The saved Vite PID 54608 was checked
for its exact Vite/5235 command before stopping; the final 5236 owned tool session
was separately stopped. No unrelated service was terminated.

App/browser-test type checks and focused lint pass. The production build at
`.local-run/process-interfaces-083/t021-common-build` passes (927 modules, 2.10 s)
with the existing chunk-size/out-of-tree notices. Browser tests used the served
development build; the separately built production files were not served in this
check. Existing React Flow attribution warnings and one unrelated surfaces-event
proxy refusal were observed in the broader run's Vite log.

### Broader editor/082 batch remains unresolved

The same browser/served workspace also ran `workflow-recovery.spec.ts` and
`process-validation.spec.ts` alongside the three common/composer checks, with a
180 s bound. **11 passed, seven failed, none skipped** in 151.3 s. Report:
`.local-run/process-interfaces-083/t021-common-qualified-playwright.json`.
Failure contexts remain under
`artifacts/process-interfaces/083/20261001-t021-common-qualified/`.

| Existing test location | Observed failure / pending investigation |
|---|---|
| `process-validation.spec.ts:279` | Expected “Requirements review”; panel displays “Review results against the requirements.” Later review assertions remain unverified by this run. |
| `workflow-recovery.spec.ts:173` | Expected Run disabled after partial input configuration; displayed Save & run enabled. Remaining reopen assertions not reached. |
| `workflow-recovery.spec.ts:386` | Expected Run disabled after invalid draft containment; displayed Save & run enabled. |
| `workflow-recovery.spec.ts:536` | Layout save expected definition revision 2, received 3; exact semantic/source preservation requires inspection. |
| `workflow-recovery.spec.ts:695` | Expected unsupported production Run disabled; displayed Run enabled. |
| `workflow-recovery.spec.ts:759` | Feedback latency checks reached their Run assertion, which expected disabled but received enabled. |
| `workflow-recovery.spec.ts:798` | Initial accessibility checks reached their Run assertion, which expected disabled but received enabled; later mobile assertions not reached. |

Do not infer that these are all stale tests or all new regressions. Diagnose the
accepted source, current editor baseline and owning execution/readiness semantics
before changing behaviour or assertions. Preserve engineering gates and the refined
editor. **T021 stays partial** while affected served preservation checks remain
open; T027/T052/T053 also retain the integration/regression obligations. The
complete Feature 083 goal, live authoring/tool chains and installed checks remain
active and unfinished. User/engineering/physical acceptance is not claimed.

### 2026-10-01 — Three regressions resolved; four expectations remain open

Fixed layout-only saves to retain the exact last accepted source bytes instead
of invoking the semantic formatter. The served typed-handle/layout check now
passes with definition revision 2 and unchanged source. Semantic edits still
format and save through the existing owner; real changes are not disguised as
layout edits. Native Run is disabled while a source draft is unapplied/invalid
or conflicted; a new component check and the full existing served authoring
journey verify containment and subsequent editing controls.

The 082 review check expected obsolete heading/campaign-specific wording. Updated
only those assertions to the actual engineering-judgment wording, preserving
the exact requirements, IDs, source locators, subject digest and approval-label
checks. The served check passes. Expanded the existing details drawer before its
retained screenshot so the requirements are visible in the viewport.

The later reviewed editor baseline already uses a clickable native Run/preflight
affordance rather than the older disabled-button expectations. Four cases from
the earlier seven failures remain open: partial input configuration (`:173`),
unsupported production (`:695`), feedback latency (`:759`) and accessibility
(`:798`). Do not report all editor acceptance complete or replace the backend
readiness authority with another frontend executor. Integrate/recheck those
expectations with T027's shared input/runtime work; T021/T052/T053 remain pending.

Current targeted evidence is in [interactions.md](interactions.md): 185 backend
checks pass (two Windows symlink skips), 126 component checks pass, four distinct
served browser checks pass, plus a repeated expanded review check. These counts
do not supersede the earlier broader failure report or prove live MCP/model use.
