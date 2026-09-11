# Engineering task results and development campaign

Current handoff: [engineering-workflow-test-handoff.md](engineering-workflow-test-handoff.md).
The requirement audit is in
`specs/080-canonical-workflow-recovery/evidence/engineering-results-audit.md`.
Later dated entries supersede the historical remaining-work notes below.

Local implementation continues in the existing workspace graphical editor.
Source remains a visible workspace `.workflow.wflow` file. UI and campaign runs
both use `/api/workspace/workflow-sources/run`.

## Result contract

`workflow_results.py` defines version 1 results: kind, stable result ID, name,
representations, producing run/task/output identity and input revisions. A
representation identifies a value, workspace file, open document or cloud
resource. Provider/resource identity is required for application resources;
revisions may be unavailable and are never invented. Durability is persistent,
session or run. Collections are explicit and never silently unwrapped.

CAD execution publishes one model with its live document and verified native
file representations. Named export results are grouped under that model.
Prompt responses retain their value and saved file representations. File digests
are verified or computed from the actual saved content. Activity is in run logs.
CAD-to-CAD consumption checks the common contract's provider compatibility and
rejects changed upstream revisions when the provider supplies revisions.

### Compatibility

Existing source, instructions, layout, ports, connections and export policies
are retained. `cad-output-presentation.ts` applies a read-time projection:
unused legacy native-file sockets are hidden; connected legacy file sockets
retain their exact address and are labeled Saved model file. Export addresses
are unchanged, grouped under Exports and labeled by filename. Newly created CAD
blocks do not add a duplicate native-file socket. Saving a native file still
attaches it to the model result. No bulk rewrite or destructive migration occurs.

## Asynchronous application adapter

`workflow_async_operations.py` supports the optional **Wright adapter contract**
`wright/operation` in a tool's upstream metadata. This is not universal MCP Tasks
support. An integration must explicitly map its job APIs:

```json
{"version":1,"id_field":"operation_id","id_argument":"operation_id",
 "status_tool":"get_job","result_tool":"get_result","cancel_tool":"cancel_job",
 "status_field":"status","poll_seconds":1,
 "states":{"running":"working","done":"completed","error":"failed"}}
```

Status/result tools must be read-only and on the selected server. Capabilities
are checked before submission. The returned job ID is pinned, submission occurs
once, completion is polled and results collected within the step deadline.
Cancellation is recorded as requested/unconfirmed, never as proven stopped.
Each event is checkpointed to the existing workspace run log. A nonterminal log
after interruption requires inspecting the identified job; it is not automatic
permission to repeat a mutation. No live cloud/FEA integration is verified yet.

## Development campaign

### Application resource adapter (September 7 continuation)

`workflow_application_task.py` adds an opt-in Wright adapter declared by MCP
tools in `upstream_meta['wright/application']`. This is a Wright extension, not
an assertion that every MCP server or Onshape server already implements it.
The shared AI task loop can create, inspect, modify, copy and export an identified
resource, including a persistent cloud deliverable with no local file.

The version-1 profile declares `provider_id`, `name`, `kind`, read-only `list_tool`
and `inspect_tool`, optional `create_tools`, `copy_tool`, `export_tool`, `formats`,
`export_policies` (indexed/overwrite), `id_argument` (default resource_id), and
optional `revision_argument`. Listed/inspected resources have resource_id, name,
revision when available, durability, optional HTTP(S) url and format. Mutating
operations return the updated resource, directly or under `resource`.
Export receives resource ID, expected revision when supported, format, name and
policy; it returns the actual exported resource. Providers must enforce revision
preconditions and naming policy. Wright rejects undeclared export policies.

`GET /api/workspace/workflow-sources/application` exposes capability discovery.
Explicit `resources=true` lists available resources through the read-only tool.
The existing inspector exposes selection by name/revision, new versus existing
resource, upstream resource, working copy and named exports. Existing Solid Edge
continues using its CAD adapter. Application-resource controls appear only for
declared capabilities. Saved source retains the configuration and connection IDs.

Contract tests cover cloud create/copy/modify/export, stale or mismatched resources,
upstream handoff, naming policies and completion without a local file. Browser
capability/selection inspection uses an explicitly simulated provider; no live
Onshape or cloud analysis integration is claimed. General imported representations
and automatic export offers remain outstanding.

Both CAD and application adapters now use an OS file lease across API processes
on the same host. Provider revision preconditions protect remote edits where
available; this does not invent revision support for current Solid Edge.

The workspace now contains 26 saved files: 10 authoring rehearsal copies
and 16 other development examples (including the new CAD result handoff). 14
compile for the supported executor. These are not 26 qualified distinct
engineering cases. The older process-100 plan has
a target and quotas, not an authored 100-workflow collection; historical
qualification and holdout counts remain unchanged.

Four packaged engineering scenarios were also located in
`engineering_scenario_catalog`: structural bracket, enclosure cooling, parametric
manufacturing and chatter review. Their actual inputs, capabilities and engineering
assertions are retained in `planned_cases`. Their legacy Rivet fixtures are not
counted as authored/runnable workspace workflows. Current-attempt history is sorted
by time, and missing setup files produce recorded failures rather than aborting
the entire batch.

Inventory:

```powershell
.venv/Scripts/python.exe scripts/workflow-campaign.py --workspace <workspace-folder> --manifest artifacts/workflow-campaign/manifest.json
```

Run explicitly selected IDs through the existing API:

```powershell
.venv/Scripts/python.exe scripts/workflow-campaign.py --manifest artifacts/workflow-campaign/manifest.json --run WF-33dbea68c9ab --session <workspace-session> --max-runs 1 --max-model-calls 2 --timeout 180
```

Defaults limit runs to 3, model decisions to 40, per-case time to 600 seconds and
concurrency to 1. Cases sharing a server serialize. Model decisions are a cost
bound proxy, not a dollar billing guarantee. Every attempt has its own immutable
JSON evidence file. Source changes require refreshing/reviewing inventory.
Oracles check actual files, recorded sizes/digests, HTML/JSON/STEP/native file
structure, and unchanged original files for working-copy tasks. Unsupported
formats fail the oracle. `--oracles artifacts/workflow-campaign/oracles.json`
adds reviewed assertions tied to exact source hashes. Supported assertions check
CAD variable readbacks (model identity, unit, value, tolerance, and no later
geometry mutation) and application resource revisions. `engineering_verified`
means those explicit assertions passed, not that an entire design is accepted.
Analysis quantities use revision-bound provider inspections, exact units and
explicit numerical tolerances; each scenario still needs reviewed expected values.

Run details retains verified application results if a later task fails. Each
`result_ready` event checkpoints its result in the visible workspace run log;
failed and cancelled runs keep their diagnostic link. **Previous runs** reads
saved history and result links after reopening. Host-local OS leases distinguish
running from interrupted execution owners; older or foreign-host nonterminal
records show **Status needs checking**. An interrupted execution host does not
prove a remote job stopped. History is read-only and never resubmits operations.

`--subset prompt-smoke|cad-copy|cad-handoff|workspace-smoke` loads explicit IDs
from `artifacts/workflow-campaign/subsets.json`, subject to the same run budgets.
Use `--bundle <IDs> --bundle-dir <new-directory>` to capture source and referenced
workspace inputs, or `--restore <bundle-directory> --workspace <workspace-folder>`
to restore missing files. Different existing files are never overwritten. Bundles
verify hashes before writing, are bounded to 128 files/100 MiB, and retain the
application setup limitations. Re-inventory the restored workspace before running.
`fixtures/smoke-20260907` contains the three current smoke definitions and original
CAD input; this is fixture setup, not an additional live verification claim.

The existing port-8765 dashboard includes a campaign section and
`/api/workflow-campaign`, separating compilation, structural live evidence,
contract tests, UI integration and pending user acceptance. Earlier failures
remain in the attempt history and stale-source attempts do not establish current
coverage.

## Historical remaining-work notes before the final integration checks

- Live provider mapping for cloud/application resource discovery and execution
  beyond the new tested opt-in adapter; no configured cloud integration was verified.
- Capability-aware representation selection for all consumers and an actionable
  UI export offer. Provider-declared application import formats, matching producer
  export offers, and direct-canvas validation now have focused and browser
  contract evidence; remaining local CAD and scalar/file consumers need audit.
- Cross-host/external edit protection requires provider revision support; revisions
  are not available from the current local CAD adapter.
- End-to-end asynchronous/cloud examples against configured real integrations
  where available. Interruption classification and partial-output failure cases
  are contract-tested; actual saved history has a live browser walkthrough.
- Additional scenario-specific engineering oracles. Analysis quantity assertions
  now use the final provider inspection, exact provider/resource/revision,
  reviewed field path, explicit units and numerical tolerance. The inspection
  is retained in the run record and must match an actual successful tool call.
  A shared async-analysis execution test verifies this chain; malformed, stale,
  wrong-unit and narration-only evidence fail. This is contract evidence, not a
  live solver qualification. Portable
  fixtures and named regression subsets are implemented. The full approximately
  100-case corpus still needs actual case design.
- Broader editor regression evidence and final completion audit.
  Working-copy execution now has fresh UI evidence: 2.5 mm MaterialThickness,
  unchanged original hash, native/STEP output digest checks and existing viewer.
  A real two-task CAD handoff also passed after fixing downstream retention of
  the unchanged native representation. Dirty models and changed files do not
  inherit a stale native representation. Original failed evidence is retained.
  Fresh CAD creation is now live verified through the normal workspace entry:
  `cad-model-exports-test.workflow.wflow`, run log
  `runs/cad-model-exports-test/20260907T165221Z-ba111081c541.json`.
  Native `cad-test/bracket-002.psm` and grouped `cad-test/bracket-001.step`
  match their recorded hashes and recognizable file headers. Provider evidence
  reports native tab/flange creation and same-session rebuild; no fresh-session
  or whole-design acceptance is implied. The STEP opens in the existing viewer.
  The explicitly selected unsaved-model test also passed: its working copy
  contains the original's unsaved 2.25 mm thickness, then changes to 2.75 mm.
  The original remains 2.25 mm in session and its saved file hash is unchanged.
  Native/STEP outputs are verified. See report `2026-09-07T16-59-39-809Z` and its
  reproducible `playwright/verify-results.py`. The original remains open and
  dirty intentionally; only the owned test model was used. The saved example is
  `workflows/cad-unsaved-session-test.workflow.wflow`; after restarting CAD,
  select the intended open test model again before running this session example.

At narrow widths the legacy chat-only shell hid the Workflows entry before a
workflow was open. Workspace navigation now stays available when workflow
authoring is enabled, regardless of whether the URL already requests a workflow.
The corrected 748-pixel plain-workspace entry and live creation walkthrough are
in `artifacts/ui-walkthrough/cad-deliverables/2026-09-07T16-51-07-946Z`.
The original startup and narrow-entry stopping reports remain preserved.

This document records current scope honestly; these remaining items keep the
active goal open. No production delivery or user acceptance is claimed.

## September 7 input and asynchronous browser verification

Workspace File and Image blocks can feed a provider-declared application import.
The selected server must advertise both the input kind and file extension. The
runtime preserves the workspace file's hash, size and input provenance, then
verifies the file before importing a new application resource. Opaque CAD bytes
are accepted for that import; connecting the same bytes as prompt/reference text
still fails rather than treating a filename or binary data as document contents.

AI tasks with MCP tools now accept image reference connections directly. The
shared model bridge sends image pixels as multimodal attachments on every
decision and protocol repair, not JSON text subject to transcript truncation.
Instructions remain text. Exact MCP calls still require their declared argument
types. The workflow decision bridge bounds the complete request, including image
data, to 16 MiB; its workflow text translation budget is 200,000 bytes, including
the translation instructions and any protocol-repair reserve. This is a
conservative Wright policy, not a claim about the configured provider's context
window. The generic compatibility bridge retains its 60,000-byte default.
Hermes text parts remain bounded at 65,536 characters; whole observations,
instructions and advertised tool schemas must fit without truncation. Requests
whose mandatory evidence exceeds these limits fail before a model call. A
provider can impose a smaller effective context or output reservation, so live
validation with the configured model remains necessary. Actual image
understanding depends on the configured model's vision capability.

AI tasks refresh the selected server's catalog before each model decision,
preserving stable tool aliases and prior tool evidence. They still reject a
contract changed between that decision and invocation. This handles lazy server
discovery without silently executing against a schema the model did not receive.
Exact MCP blocks retain their saved-schema review requirement.

The simulated browser report `2026-09-07T17-28-24-274Z` verifies a persistent
cloud analysis result and grouped CSV link, then cancellation after submission.
Cancellation closes the client request without resubmission, clears running
animation, and retains verified partial results. The UI explicitly states that
the submitted application job may still run; backend contracts separately cover
provider cancellation. No live cloud solver is claimed. Earlier invalid fixture
actor/scope reports remain preserved and are not counted as passing runs.

The live image example is `workflows/image-to-mcp-test.workflow.wflow` in
**Wright workflow evidence**, using `engineering-help-image-test.png`. Its first
preflight failure exposed the remaining compiler restriction and an API-envelope
parsing bug; both are fixed. The later catalog change failure remains in run
history. The corrected live run passed: report `2026-09-07T17-51-58-564Z`, log
`runs/image-to-mcp-test/20260907T175159Z-a2f8c746f59c.json`. It read the image topic,
made real product-discovery and help-search calls, and saved
`reports/image-to-mcp-test.md`. Both output links match actual tool results;
input/output digests and the existing Markdown viewer were verified. The report
contains a repeatable evidence verifier. This qualifies the image-to-task/document
handoff, not CAD geometry or general image-recognition accuracy.

Repeat this case with `--subset image-mcp`; its source and image are bundled in
`artifacts/workflow-campaign/fixtures/image-mcp-20260907`. Restoration into the
separate `fixture-restore-image-mcp-20260907` test directory verified both files.
Use the real workspace when running; restoration alone does not register a new
workspace or enable its model/server.

Run details now keeps its collapse header visible while output contents scroll.
The clipped-header finding at the 1184 by 791 review viewport is preserved in
`2026-09-07T17-59-11-453Z`; the corrected scroll/collapse/reopen browser check is
`2026-09-07T18-00-43-928Z`. This extends the existing drawer rather than adding a
new output viewer.

## Named exported files as downstream inputs

Prompt and reference connections read one explicitly named workspace export as
verified contents. SHA256 and recorded size must still match. Supported UTF-8
documents become text; PNG/JPEG/GIF/WebP exports become image attachments.
Cloud-only links, ambiguous file representations and binary CAD files receive
corrective errors instead of being rendered as prompt text. Native CAD paths
used by advanced exact tool calls retain their existing path behavior.

The live example is `workflows/cad-export-review.workflow.wflow`, titled
**CAD export to AI review**, in **Wright workflow evidence**. It inspects the
explicitly selected owned `unsaved-copy.psm`, exports
`cad-test/model-preview.jpg`, then writes `reports/cad-preview-review.md` from
the actual image. Both files open in the existing viewers. Report
`2026-09-07T18-18-31-721Z` contains the completed run, hashes and a repeatable
`playwright/verify-results.py`; the initial invalid source fixture is retained
in `2026-09-07T18-17-22-982Z`. This is image-content handoff evidence, not
geometry or manufacturability qualification.

The final preservation check found a provider side effect: the same document
was marked dirty after screenshot export, although its saved native file was
unchanged and the logged task made only reads plus the export. The provider
activates the folded model and updates the view. Do not clear that dirty flag
or silently save the document. The CAD adapter now re-reads state after exports
and reports a clean-to-dirty transition. This correction passes focused tests;
its subsequent served/live verification is recorded below. The original browser report remains marked
with this finding, not an unqualified pass. Selected session document IDs may
change when the MCP process reconnects; reselect the intended test document.

## Final September 7 integration checks

The live working-copy/export-state report `2026-09-07T18-41-04-407Z` verifies the
fresh post-export document state and user notice, native/JPEG file digests, and
preserved original file/session snapshot. The older dirty-state finding remains
in its original report. Exact MCP text/JSON argument consumers now resolve named
result contents with digest checks; legacy native CAD path parameters remain paths.

Generic application adapters can declare `export_path_argument` as a distinct
string argument of their export tool. Wright supplies an owned staging path on
the shared filesystem, verifies actual file bytes and format, then uses the
existing atomic indexed/overwrite workspace writer. The API's
`exports_to_workspace` capability changes the label to File name or path. Providers
without that capability retain application/cloud export names and locations.
Later export failure or cancellation preserves earlier verified outputs and
incomplete staging evidence; it does not imply provider rollback. Eight focused
export cases cover these paths. No generic non-CAD local provider was live-tested.

The final consolidated results are 313 backend tests passed, 7 Windows-specific
skips, 164 editor tests passed, and TypeScript passed. The first concurrent backend
run timed out starting one test child process; its report is preserved along with
the isolated pass and complete serial rerun. The final browser handoff report
`2026-09-07T19-05-14-539Z` passed artifact validation and records its initial trace
loss on an automation timeout; screenshots and a returned-graph continuation
trace remain. No product failure or workflow rerun occurred in that walkthrough.

The existing dashboard now separates prior source-revision verification from
current run readiness. Its collector remains current. Inventory is 30 saved files,
18 compiling, and four actual planned legacy migrations. The handoff names the
next batch and precise unavailable-provider prerequisites. This prepares the
larger campaign without claiming 100 authored/qualified workflows, user acceptance,
CI integration or production delivery.
