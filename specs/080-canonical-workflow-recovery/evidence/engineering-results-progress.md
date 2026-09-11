# Engineering task/result integration — September 7

Latest local delivery audit: `engineering-results-audit.md`. Manual testing:
`../../../docs/contributing/engineering-workflow-test-handoff.md` (repository
path `docs/contributing/engineering-workflow-test-handoff.md`). Historical entries
below retain their original scope and failures; the final entry supersedes their
pending-work status.

User goal: attachment `3ec746a4-03db-4a48-9455-93dd099ced4f/pasted-text.txt`.
Implementation continues in the existing 080 checkout, web 5227/API 8018.
Prior uncommitted authoring/runtime work is preserved. No release claim.

## Work sequence

1. Shared result contract and actual prompt/CAD execution publication; identity,
   revisions, explicit collections, typed representation selection.
2. Compatible CAD output projection/migration: one model, grouped named exports,
   preserved old port IDs/edges and workspace source/layout.
3. Adapter execution lifecycle, asynchronous operations, cancellation/partial
   evidence and conflict handling, with honest unsupported-provider reporting.
4. Inventory actual authored workflows against the existing 100-process plan;
   bounded campaign runner, output oracles and existing-dashboard coverage.
5. Focused regressions, workspace-entry browser checks, representative real runs,
   manual examples and precise remaining integration gaps.

## Discovery

The existing `docs/programs/engineering-process-platform/benchmark-coverage.json`
sets a target of 100 and proposed domain quotas. It is not itself a collection of
100 executable workflow files. Development campaign evidence must remain distinct
from frozen qualification/holdout evidence and must not change historical counts.

## Implemented and checked in this continuation

- Shared result publication from actual prompt and CAD executor; model/native
  representations grouped with named exports, provenance and input revisions.
- Same-provider CAD consumers use the shared representation check. Upstream
  revision changes fail before edits where the provider exposes a revision.
- Headless API preserves results and accepts resource-only/large CAD results.
- Existing canvas retains saved port addresses and hides unused native aliases;
  result links use the existing workspace viewer. TypeScript build passes.
- Run records checkpoint before execution and after each event.
- Optional provider-declared asynchronous operation monitor submits once,
  polls pinned job IDs and separates cancel requests from confirmed cancellation.
  This is a Wright adapter contract, tested with simulated services, not a live
  Onshape/FEA integration or general MCP Tasks implementation.
- Inventory/explicit-ID campaign runner and read-only existing-dashboard section.
  Inventory found 25 files, 10 rehearsal copies, 13 compiling workflows. The
  target remains 100; no qualification counts changed.

Focused checks passed: shared results/CAD/source (40), task/log and API response
(25), canvas/results compatibility (18 after fixing one text matcher), campaign
(3), asynchronous/MCP/CAD (28), and preserved existing operations with async/CAD
(25). These sets overlap; they are not an additive total. Last narrowed async/
result/campaign recheck passed 19 tests. TypeScript build and diff whitespace
check passed. Initial async module/test filename collision was repaired by
restoring both unchanged existing files and using workflow_async_operations;
the preserved service tests passed afterward.

## Fresh live evidence

API and web were authoritatively stopped (no listeners); restored on 8018/5227
with the preserved workspace database. Existing dashboard resumed on 8765.

Campaign attempt `0d1b3502220e4fc3b096928e3f9b7126` ran Prompt to HTML through the
normal workspace API. It produced report-001.html (3,764 bytes), verified actual
HTML structure and SHA-256, and returned one common engineering result.

Browser evidence root:
`artifacts/ui-walkthrough/cad-deliverables/2026-09-07T14-42-20-769Z`.
Entered the plain workspace via Workflows; opened CAD working copy test and
verified one CAD model plus named grouped export with saved source unchanged.
Ran Prompt to HTML through the UI, producing report-002.html (5,402 bytes).
The result panel's Open action rendered it in the existing HTML viewer with no
recorded browser errors. No new viewer code was introduced.

Dashboard `/api/workflow-campaign` returned 200 with the actual inventory and
retained attempt history. User acceptance remains pending for all new work.

## Next work / incomplete requirements

### September 7 continuation, through live CAD handoff

- Added provider-declared application resource selection, expected-revision edits,
  copy/new-revision and exports through the same AI task loop. Persistent cloud
  resources can complete without a local file. This is a Wright metadata adapter;
  no configured Onshape/cloud-analysis integration was live-verified.
- Added resource controls to the existing inspector, no new editor. Component
  tests cover source round-trip and revision selection; browser capability check
  used a simulated provider. The extended browser export check was interrupted
  by an automation timeout and is not claimed complete.
- Cross-process OS leases now serialize application edits. Contract tests cover
  competing processes and cancellation. Export naming policy is explicit.
- Live working-copy UI run: run 56404dbf879a43f3b6ddc5e2a88fdbf8, native
  cad-test/bracket-modified-003.psm (278528 bytes), STEP
  cad-test/bracket-modified-001.step (13707 bytes), original SHA-256 unchanged,
  MaterialThickness read back as 2.5 mm. Both output hashes verified.
- Added workspace file workflows/cad-result-handoff.workflow.wflow, displayed
  name CAD result handoff. Initial example authoring errors were repaired and
  retained in the report. The real second CAD task received the exact first-task
  document identity. A false temporary warning exposed lost native representation;
  fixed and rerun. Corrected outputs: cad-test/handoff-001.psm (278528 bytes),
  cad-test/handoff-001.step (13651 bytes), both digest checked. Native representation
  carries forward only while document/file remain unchanged.
- Live reports: cad-deliverables/2026-09-07T15-19-24-445Z and
  cad-deliverables/2026-09-07T15-30-02-145Z under artifacts/ui-walkthrough.
- Campaign now inventories 26 saved workflows (14 compile), plus four actual
  legacy scenario specifications as planned migrations. Their engineering
  assertions are retained, without reintroducing Rivet as the workspace editor.
  Named subsets and bounded hashed fixture bundles were added. The real smoke
  bundle restored four files into an isolated directory.
- Focused backend run passed 72 tests before final validation additions;
  narrowed result/application/campaign run passed 24; CAD durability run passed
  17; authoring preflight/source run passed 19; fixture bundle run passed 3.
  These overlap and are not an additive total. UI service/inspector tests passed
  28; result/presentation/inspector run passed 4. TypeScript build passed.

Goal remains active. Fresh local creation and unsaved-session examples, broader
representation-consuming adapters/export offers, live async/cloud integration
where available, partial-result recovery/UI and additional engineering oracles
remain to be completed. No user acceptance or production delivery is claimed.

Continue the full list in `docs/contributing/engineering-task-results.md`:
cloud resource selection/result adapters and durable remote outputs, broader
capability-aware connections/export offers, safe revision/copy/concurrency
semantics, portable fixture setup and engineering-specific oracles, real CAD
and cloud/analysis representative runs, broader browser regression and final
requirement-by-requirement audit. The goal remains active; this slice is not
completion of the requested end state.
# Partial failures, run history, and numerical oracles — September 7 continuation

Application results now emit immediately after adapter verification. Durable run
logs retain those partial results through later failure/cancellation. Run details
keeps output links and the saved-log control; prompt file writes retain the
existing all-responses-valid-before-write behavior.

Host-local run ownership uses OS leases. Read-only recent history marks a released
known-host owner as interrupted; legacy/foreign-host records remain unknown. It
never retries mutations and explicitly notes that remote work may still run.
The API and UI reuse the workspace file authority and existing viewers.

Evidence: 53 focused application/task/source tests; 27 history/task tests;
28 editor tests; one focused history component test; TypeScript build passed.
These counts overlap and are not additive. Simulated partial-failure browser
report `artifacts/ui-walkthrough/cad-deliverables/2026-09-07T16-06-09-603Z`
passed its structural validator with no browser errors. The live read-only
history report is `2026-09-07T16-15-44-483Z`; actual earlier native and grouped
STEP links remain visible after reopening.

The campaign runner accepts source-hash-bound CAD variable and resource revision
assertions. Thirteen oracle/campaign tests passed, including rejection of wrong
units, wrong model identity, later geometry mutation, and narration-only evidence.
Attempt `recheck-b1709fa526c34140bc47616f72905a63` rechecks preserved live CAD
evidence: both task readbacks are 2.5 mm, native/STEP hashes match, and the
original file is unchanged. It is labeled `live-record-recheck`; no CAD or model
call was made by this recheck. Whole-design review and user acceptance remain open.

## Import offers, narrow entry and fresh creation — September 7 continuation

Provider-declared import formats and input kinds now drive compatible application
export offers and canvas connection validation. Imports pin the receiving
resource and verify workspace file hashes; unsupported transfers fail preflight.
The simulated-provider browser run found unnecessary CAD capability probing on
application tasks. That was repaired; the corrected report
`cad-deliverables/2026-09-07T16-40-01-969Z` has no browser errors and passed its
validator. The original `2026-09-07T16-37-27-087Z` failure remains. No live cloud
transfer is claimed. Focused application/source tests and 19 UI tests passed.

At a 748-pixel width, the plain workspace hid its Workflows entry through the
legacy chat-only branch. It now preserves navigation when workflow authoring is
enabled, before a workflow is requested. The corrected plain-workspace entry
and live new CAD creation are recorded in `2026-09-07T16-51-07-946Z` (validator
passed, no browser errors, TypeScript build passed). Original startup and
narrow-entry stopping reports remain unchanged.

Live creation record: `runs/cad-model-exports-test/20260907T165221Z-ba111081c541.json`.
The task corrected an invalid recipe argument before successful native tab/flange
creation. Native `cad-test/bracket-002.psm` is 290816 bytes, SHA256
`f3d18cd016ea3cc6aa382a8474e569a202762b40c0ef474521a39737dfdd43f7`;
STEP `cad-test/bracket-001.step` is 13609 bytes, SHA256
`bf0c661a6c161818eed3e21bc50c02270dfc75a802434b29f774e58932fe3893`.
Both hashes and native/STEP headers were checked, the existing STEP viewer opened,
and canvas run state cleared. Provider evidence reports same-session rebuild;
fresh-session rebuild and whole-design acceptance are not established.

Analysis quantity oracles now inspect a final provider readback against the
result's provider/resource/revision, a reviewed field path, explicit units and
tolerance. The shared async application execution records that readback. Thirty-five
focused oracle/application tests pass, including stale resources, wrong units,
missing quantities and narration-only claims. This is simulated solver evidence.

The explicitly selected unsaved-session example is now saved as
`workflows/cad-unsaved-session-test.workflow.wflow` and live verified. Report
`2026-09-07T16-59-39-809Z` passed the walkthrough validator. The copy read back
2.25 mm from the unsaved source, then 2.75 mm after modification. A separate
read-only MCP call confirmed the original still held 2.25 mm, and its saved
native file hash remained unchanged. Distinct original/copy IDs are recorded.
Native `cad-test/unsaved-copy.psm` and grouped `cad-test/unsaved-copy.step` passed
size/format/hash checks. The report's `playwright/verify-results.py` reproduces
these checks without model/CAD calls; attempt
`recheck-6c82fb41486e46ea86bfe7f8673d7291` records that scope. Setup used only the
newly created owned test document. The inspector loading delay recovered;
the setup automation connection timed out and was reattached, leaving its
pre-run trace incomplete. Workflow execution and completion have a fresh trace,
screenshots and durable provider evidence.

The manifest now has 27 saved files / 15 compiling and four planned legacy
scenarios. Consolidated regressions pass 93 backend tests and 48 editor tests
across five files. These are local checks, not merge/release or user acceptance.
Broader consuming-adapter audit, representative cloud/async UI coverage,
scenario-specific cases and the final goal audit remain open.

### Input handoff and remote-result continuation

File/Image inputs now become hashed, typed results for explicit application
imports; provider kind and extension capabilities are checked before import.
Opaque files cannot be silently consumed as prompt text. Invalid authoring actors
are rejected before tool preparation. Focused tests cover file and image import,
unsupported formats and actor rejection.

The cloud browser fixture now verifies correct workspace/path scope, persistent
analysis completion, grouped CSV links, partial-output preservation on Cancel,
one submission only and cleared running animation. The corrected report
`2026-09-07T17-28-24-274Z` passed the artifact validator. Invalid actor/scope
fixtures `17-22-26-728Z` and `17-24-44-115Z` remain historical failures. There was
no real cloud provider call. Cancellation wording now tells users to check the
submitted application job before another run; it does not claim remote rollback.

Image references now travel through the shared AI-MCP task and model bridge as
actual multimodal attachments, including action-format repair. The live browser
attempt first exposed a compiler restriction and hidden preflight error; report
`2026-09-07T17-43-45-531Z` preserves that 422. The next attempt made a real product
discovery read, then stopped on a changed catalog (`17-47-53-374Z`). AI tasks now
refresh the catalog before each decision with stable aliases, while still
rejecting changes occurring after the decision. No completed operations are
silently retried. The corrected live run is being verified separately.

Consolidated workflow/bridge/API checks passed 171 tests before the catalog fix;
68 affected task/MCP/CAD/application tests pass after that fix. UI checks pass
29 editor tests and 33 service/connection/application tests. TypeScript passes.
The actual inventory now contains 28 saved files, 16 compiling, and four planned
legacy scenarios. The new image example and its uploaded input are visible in
the existing workspace. No production or user-acceptance claim is made.

The corrected live image task completed in report `2026-09-07T17-51-58-564Z`.
It transcribed Autodesk Fusion / Sheet metal bend relief from the image, called
product discovery and help search, and saved `reports/image-to-mcp-test.md`.
The task prompt contains no topic string. Both report URLs occur in the actual
search result. Input SHA256 is
`258e2db41eea57dd2945e0ce905658286d1b0927cfea734403c3d1036a0ee05b`;
the 544-byte output SHA256 is
`ecd7c7aad2cd2375650027c8b5db8a847374b943c393e8984e71ffb1c5fce965`.
The existing Markdown viewer renders the report without browser errors.
Durable log: `runs/image-to-mcp-test/20260907T175159Z-a2f8c746f59c.json`.
The report validator passes. Its `playwright/verify-results.py` rechecks the
preserved evidence without new model/tool calls; immutable attempt
`recheck-ab6c085128cc4484a8485035d3074665` records this limited verification.
Current API pid 23984 loaded the compiler, image bridge and catalog-refresh
changes. Restart checks found no active workflow locks and preserved open CAD
documents. The evidence dashboard's coverage JSON now includes this live case.

### Named export contents and live CAD image handoff

`reference_from_result` now reads a single named workspace file and verifies
its digest/size before delivering text or image contents to the next AI task.
Cloud links, ambiguous representations, unsupported binaries and changed files
fail explicitly. The complete compiled CAD export pipeline has regression tests,
including image pixels reaching the generator and STEP rejection before it runs.
The redundant "contents are not inlined" message is omitted for consumed files.

100 affected tests passed before local API restart (parent 14456, port 8018).
Live `cad-export-review.workflow.wflow` completed in
`runs/cad-export-review/20260907T181926Z-42994d9a4cb3.json`.
JPEG `cad-test/model-preview.jpg`: 44,535 bytes, SHA256
`fddb11a2a36ee7bb16cce55dd2946bca230bf84f97137f29a63334d095daacde`.
Markdown `reports/cad-preview-review.md`: 755 bytes, SHA256
`3f3a2a51beaa2078a8a262f09a2a3959150686bdb2ba5058452a6825c330373b`.
Consumer input digest matches the JPEG. Both existing viewers were verified.
Report `2026-09-07T18-18-31-721Z` and its verifier passed artifact validation.
The initial source fixture omitted required purpose fields; stopped report
`2026-09-07T18-17-22-982Z` is retained. A missing save-request flag was corrected
before the successful source save; no CAD operation occurred during that repair.

The final live check found that screenshot export marked the selected
`unsaved-copy.psm` document dirty; its native-file hash stayed unchanged.
The report remains flagged. Read-only provider inspection confirmed the same
document identity. Local provider code activates the folded model/view during
JPEG export. No provider code was changed and no dirty model was saved/reset.
Wright now refreshes post-export document state and emits a clean-to-dirty
notice. After correcting the test's state snapshot placement, 101 affected
tests pass. This last CAD state correction is not yet loaded in the API.
Generic application workspace export delivery and exact MCP argument consumers
remain open; the broader goal is active.

### Final local verification and campaign handoff

Generic application workspace exports now use a declared shared-filesystem path,
verified staging bytes and the existing atomic file writer; earlier verified
exports survive later failure/cancellation. Exact MCP text/JSON arguments now read
verified named output contents. Legacy CAD file arguments remain paths. The
application API advertises whether export names are workspace paths. These
generic boundaries are contract-tested, not misrepresented as a live cloud solve.

Live `cad-export-state-test.workflow.wflow` completed in
`runs/cad-export-state-test/20260907T184132Z-4ac901899bf3.json` and report
`2026-09-07T18-41-04-407Z`. It verifies a distinct working copy, accurate dirty
state after JPEG export, the user notice, native/JPEG hashes and original
preservation. The original export-induced modified-state finding remains in the
earlier report. Both saved export-example verifiers passed again; immutable
rechecks `recheck-ee6e3a88294d4418b094d4d9f9eb6794` and
`recheck-18d630792b034624b173345b942fc871` explicitly do not claim new executions.

Final regression artifacts in `artifacts/workflow-campaign/checks`: 313 backend
passed, 7 skipped; 164 editor passed; TypeScript passed. Skips identify six
Windows symlink-privilege cases and one POSIX rename race. The earlier concurrent
backend test-process startup timeout is preserved, followed by its isolated pass
and a passing complete serial rerun. No test or product timeout was weakened.

The existing dashboard was reloaded using its current launcher and collector,
preserving process ownership. It now displays conservative current readiness
separately from historical source-revision evidence. Provider availability records
identify missing Onshape credentials/installation and a licensed Fluent/gateway
requirement without exposing secrets. Inventory: 30 saved files / 18 compiling /
four planned legacy scenarios. Explicit CAD export subsets were added, and image
signature/digest checks allow their real outputs in the campaign runner.

Final workspace handoff report `2026-09-07T19-05-14-539Z` passed validation:
normal Workflows entry, saved CAD graph, direct task controls, actual history/file
links and dashboard readiness. Initial browser trace was lost on a tool timeout;
screenshots/actions and a returned-graph continuation trace remain. The STEP
opens in the existing text viewer, not a newly verified 3D preview. Saved source
digest is unchanged. The CAD handoff graph is returned to the attached browser;
opening it in this Codex task's panel is queued by the app.

The full requirement audit and manual handoff distinguish local delivery from
the future larger campaign, unavailable live cloud/FEA integrations, human
acceptance and consolidated CI/release work. No historical qualification count
was changed and no duplicate workflows were invented to fill the target.
