# Desktop workflow transfer

Local follow-on at `codex/desktop-workflow-transfer`, based on the separate
upload branch at 5d6c58df. Not installed, pushed or integrated. PR156's current
correction and all frozen services remain separate.

Journey: select a saved workflow, export its definition/dependencies, or inspect
and explicitly import a transfer file into a fresh destination. Reuse the shared
WorkflowBundleDialog and authenticated workflow-bundles owners. Keep the neutral
editor, draft guards, workspace identity and common-view fallback. V1–V7 apply.
Export is not a run, engineering review, provider grant or confirmed host save.

## Lost acknowledgement qualification

The actual MCP/browser harness now deliberately withholds one successful private
import reply. A second click is blocked by the native client without another MCP
import call; explicit **Open saved destination** reads and opens the exact saved
copy. Eight browser checks pass, including the original navigation/draft checks:
`/tmp/wright-desktop-workflow-transfer-state-20261015-06/browser-home-1792061268549/report.json`.
No engineering run starts. This tests reply loss after successful publication,
not process termination during partial publication; the latter has separate
owner-level reservation tests, and full host close/restart UI acceptance remains.

The first lost-reply test stopped because its assertion expected different error
wording. Its actual saved copy and failure evidence were retained; the completed
proof used a distinct, explicitly named test destination. Neither import was
replayed. Logs: `/tmp/wright-transfer-lost-reply-20261015.log` and `-02.log`.
The installed plugin is unchanged.

## Served transfer journey — 15 October

The existing native-home browser harness now exercises workflow transfer through
real MCP/HTTP owners. Fresh state06 verifies seven checks: home discovery,
narrow transfer dialog, real Chromium file download, inspection and exactly one
fresh import with return to its exact saved source, workspace/Files refresh,
Back and retained draft guards. Original accepted source remains unchanged;
no process runs or engineering approvals occur. Windows file delivery is still
unverified. Full shared-editor/Hermes gates and installed candidate checks remain.

Browser evidence:
`/tmp/wright-desktop-workflow-transfer-state-20261015-06/browser-home-1792061115573/report.json`.
Final service: API8193, session99416, editor-only profile. State04 and state05
services stopped before resource rebuilds; their evidence is preserved.

The first state04 browser attempt failed during connection because the harness
requested a working-view profile absent from this service. The second exposed a
real shared UI defect: reference discovery offered undeclared workspace files,
which the export owner correctly rejected. The picker now intersects existing
files with the exact source's owner-provided dependency manifest; a failed
manifest read does not offer arbitrary files. Export enforcement is unchanged.
The final test verifies exclusion of the unrelated fixture and a source transfer;
selected-asset and saved-interface round trips remain separate pending proofs.

Visual inspection moved the transfer control into the existing styled workflow
header instead of adding a raw button above the canvas. The final screenshot
shows the preserved canvas and run-details control. 38 focused tests, TypeScript,
focused ESLint and diff checks pass. A presentation-test stub initially lacked
the new header callback; it was updated without removing the draft/stale-source
assertions. Earlier failure logs and screenshots remain alongside final evidence.
No installed plugin, engineering provider, push or release changed in this slice.

## Current checkpoint — merged baseline and packaged candidate

The feature branch merged dev `3b994c56d43b311e290cf943376e0b83881500f5`
without conflicts at local merge `f553c17e6066faa81bc7f2fac9328a3405bdb438`.
PR156 is merged; its development image publication is still pending in the last
observed run `38720558428`. The named installed plugin remains 0.11.0.
Older state/version observations below are historical, not the current runtime.

The native bundle now includes the transfer controls (2,261,707 bytes, zero
external assets). The initial build failed because the dependency guard mistook
`client.import(...)` for dynamic JavaScript import. Syntax inspection using the
already pinned TypeScript dependency preserves the guard and distinguishes real
imports from property calls, method declarations and strings. Five syntax cases
passed, including nested dynamic-import rejection. Logs:
`/tmp/wright-transfer-native-build-20261015.log` (initial failure),
`/tmp/wright-transfer-native-build-20261015-02.log` (successful package).

State03 was stopped before rebuilding. Fresh state04 runs on API8193, session67842,
with explicit source paths for this worktree's workspace-service, core and API;
it reuses only the isolated upload environment's installed dependencies.
`/tmp/wright-desktop-workflow-transfer-state-20261015-04/workflow-export-proof.json`
records passing actual MCP definition round trips for the two existing examples,
with exact accepted bytes, stale-revision denial, occupied-destination denial,
zero runs and no host download claim. This exercises the updated shared import
owner. It does not establish saved-interface transfer or full engineering use.

37 focused frontend tests and TypeScript pass after the merge and bundle rebuild.
Test log: `/tmp/wright-transfer-ui-postmerge-20261015.log`.
Served browser interactions, full repository gates and actual Windows panel/file
acceptance remain pending. No candidate installation, push or release occurred.

## Implemented boundary

The UI-only `wright_workflow_export` operation delegates to the existing export
owner after exact workspace/session verification. It carries the saved source
digest, mode and explicit reference/UI selections. The shared bundle schema and
canonical digest validate the reply; source digest and mode must match the
request. No generic HTTP proxy or retry is added. Existing frozen native-source
module hashing covers this addition. The preview admits only the three exact
export/inspect/import POST routes when its native editor is enabled.

UI-only inspection validates the bundle digest and the existing `can_run: false`
contract. Import pins the inspected digest and verifies the exact returned source,
destination and workspace. Errors after submission remain OUTCOME_UNKNOWN: the
owner can publish assets or its manifest before source publication fails. No
automatic retry or rollback is added. UI reconciliation is still pending.

The backend retains instruction, dependency, credential exclusion and saved-UI
compatibility rules. Transferred interface source never grants a trusted build
or enables generated UI authoring. Missing dependencies stay explicit; export
does not establish readiness. User-selected references are not automatically
expanded to unrelated workspace files.

## Qualification so far

- 52 transfer/source/bridge tests pass, including scope denial, invalid/mismatched
  reply, stale response identity, extra authority, timeout, no retry and UI-only
  tool metadata. These do not prove actual Windows hosting.
- Actual MCP/HTTP source export/inspect/import round trips pass for fresh manufacturing-preparation and
  SteveCAD native definition copies. Both retain exact owner-accepted source,
  dependency inventories and original-source hashes; stale digests are denied.
  Normal source creation materializes its existing defaults; accepted bytes,
  rather than pre-save draft bytes, are the export identity. Imported bytes are
  identical; inspection rejects the already occupied destination without another
  import attempt. Neither inspection nor import grants execution readiness.
- The earlier export-only preview rejected import/inspect with 503; that historical
  boundary was explicitly expanded for the three qualified transfer routes. No
  process run starts. This is definition transfer, not engineering execution.
- Current receipt: `/tmp/wright-desktop-workflow-transfer-state-20261015-02/workflow-export-proof.json`.
  Prior export and route evidence remain in state01; its service stopped cleanly
  before transport changes. Current state02 uses API8193, session13314 and
  native-editor only; no engineering execution qualification flags.
  Test interpreter reuses the upload environment's unchanged owning packages;
  the new prototype modules are loaded from this worktree. Installed-package
  qualification remains required.

## Remaining tasks

Native-control checkpoint: the panel now opens the shared transfer dialog from
**Export / import workflow** after rereading the exact accepted source. Drafts
and pending working-view changes block entry; an open dialog blocks workspace
navigation and run preparation. Reference/interface discovery uses the qualified
native ports. Successful imports use the existing generation/dirty-guarded
workflow opener in the same workspace. **Open saved destination** after an
uncertain reply is read-only navigation to the attempted destination, never a
second import or a completion claim. Unavailable destinations retain an explicit
notice. 24 focused UI tests, TypeScript and lint pass before this final notice
consolidation; browser/package/Windows checks are still pending. The generated
native resource has not yet been rebuilt and installed.

Durable import reservation checkpoint: the existing bundle owner now publishes
its write-once manifest before assets, then publishes the source last. No receipt
format, instruction bytes, successful response shape or new database is added.
The manifest is intent, never completion. A controlled first-asset failure retains
that reservation; a newly constructed owner rejects another attempt at the same
destination without writes. Existing-source and saved-interface checks remain.
34 owner/API/imported-interface tests pass. The initial sandbox invocation timed
out during export before reaching the injected failure; the unchanged host test
reproduced the missing receipt in 0.17 seconds. Logs are retained separately at
`/tmp/wright-transfer-reservation-red.log`, `-red-host.log`, and `-green-host.log`.
This fixes durable replay protection, not the remaining UI reconciliation journey.

The existing state03 service was created before this shared owner change and
must not be presented as its qualification. Future probes must load this
worktree's workspace-service package explicitly or use a newly installed runtime.

Asset-discovery checkpoint: `wright_workflow_transfer_assets` is a UI-only,
read-only operation with two closed kinds: references and interfaces. It verifies
the saved source before calling the existing input-file or interface-list owner;
stale/foreign scopes fail. Shared dialog discovery can use injected functions
without changing the web defaults or partial-failure behavior. The native client
validates both result scopes. 56 Python boundary tests and 29 frontend tests pass;
TypeScript, focused lint and diff checks pass.

Fresh state03 actual-MCP proof discovers an explicitly private test text file,
confirms the empty saved-interface list, and repeats both definition round trips
without runs. Receipt:
`/tmp/wright-desktop-workflow-transfer-state-20261015-03/workflow-export-proof.json`.
State02 stopped before its frozen transport changed. Current API8193 uses state03,
session55491. These file-list fixtures are not engineering inputs/results, and
empty-interface discovery does not qualify transfer of a real saved interface.

Frontend transport checkpoint: the existing bundle service now accepts a closed
three-operation transport, preserving its web default and shared response
validation. The shared dialog accepts that client; the native client binds exact
workspace/session and import/source identities. Lost, malformed or mismatched
import replies latch further submissions in that client instance while allowing
read-only inspection. Only an explicitly known pre-submission rejection clears
that latch. This is not durable reconciliation across panel closure.

27 focused shared-service/dialog/native-client tests pass, as does TypeScript.
Tests use isolated Node 26.0.0 under `/tmp/wright-transfer-node26`; the system
Node 22.22.0 produced an engine warning during the initial locked dependency
installation and was not used for these frontend checks. No system runtime or
live plugin changed. The dialog injection is verified; the native panel menu,
reference/interface discovery and exact imported-document navigation are not yet
connected, and actual Windows delivery remains unverified.

- Qualify the connected native panel controls and exact imported-document
  navigation in the served browser/package and Windows host. Preserve web/Hermes defaults.
- Finish the UI inspection/import journey and uncertain acknowledgement
  reconciliation. Never automatically repeat an import or overwrite a conflicting
  destination. Backend ports alone do not establish a complete user journey.
- Qualify selected asset/UI bundle round trips and exclusion of credentials,
  live runs, input answers, reviews and trusted builds. Do not turn these source
  export probes into a claim of complete portable transfer.
- Qualify file delivery in the actual Windows panel. A Blob anchor click is not
  a confirmed download; unsupported host behavior must stay explicit. Add no
  public file server or arbitrary URL downloader to conceal a missing capability.
- Verify served Workflows entry, return to exact imported source, draft/focus
  behavior, narrow panel and Hermes regression. Run repository gates and package
  qualification before the authorized named-plugin update.

The full engineering goal still requires actual SteveCAD four/six-hole and
heat-spreader runs, genuine reviews, Robot/manufacturing regressions and native
Windows acceptance. This slice does not reduce those requirements.
