# Desktop workflow transfer

Local follow-on at `codex/desktop-workflow-transfer`, based on the separate
upload branch at 5d6c58df. Not installed, pushed or integrated. PR156's current
correction and all frozen services remain separate.

Journey: select a saved workflow, export its definition/dependencies, or inspect
and explicitly import a transfer file into a fresh destination. Reuse the shared
WorkflowBundleDialog and authenticated workflow-bundles owners. Keep the neutral
editor, draft guards, workspace identity and common-view fallback. V1–V7 apply.
Export is not a run, engineering review, provider grant or confirmed host save.

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

- Connect the shared dialog and qualified discovery ports to native panel controls
  and exact imported-document navigation. Preserve standard Wright/Hermes defaults.
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
