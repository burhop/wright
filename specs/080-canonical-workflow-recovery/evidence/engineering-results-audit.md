# Engineering task/result goal audit — September 7, 2026

Authority: the complete user goal in attachment
`3ec746a4-03db-4a48-9455-93dd099ced4f/pasted-text.txt`, including its eight
representative cases and campaign preparation requirements. This audit does not
replace that goal with the subset that happened to pass first.

Subject: local `codex/080-canonical-workflow-recovery` working tree at
`D:/repos/wright/.local-run/epp-f02b-writer/wright`; existing UI 5227, API 8018,
workspace **Wright workflow evidence**, dashboard 8765. The API was reloaded
with parent PID 20848; `/api/health` reports connected and the saved-source API
returns the expected workspace source. `/health` is a frontend fallback and is
not used as API-health evidence. No commit, CI integration, release or new user
acceptance is inferred from these local checks.

## Product and result requirements

| Explicit requirement                                                                                                                                | Current implementation and inspected evidence                                                                                                                                                                                                                                                                         | Conclusion / boundary                                                                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Preserve the reviewed graphical editor and normal workspace entry                                                                                   | Root `docs/contributing/workflow-ui-integration.md`, 080 plan/north-star and `image-redesign-delivery.json` read; existing `WorkspacePanel`, `WorkflowRecoveryConcept`, React Flow canvas and command system retained. Normal workspace entry and saved handoff graph rechecked in report `2026-09-07T19-05-14-539Z`. | Integrated in the existing editor; no replacement route/authority.                                                                                                    |
| Workflows are visible workspace files, available to UI and agents                                                                                   | Saved source API, Open workflow picker, source digest comparison in the final report, `workflow_sources.py` and source/layout tests.                                                                                                                                                                                  | Same saved file remains authoritative; final read-only handoff preserved its exact digest.                                                                            |
| Independently useful application task: instructions, selected inputs/application, expected results, multiple calls, internal correction and exports | `workflow_ai_task.py`, `workflow_cad.py`, `workflow_application_task.py`; standalone prompt, image/MCP, CAD creation and copy runs. Direct inspector controls verified after capability discovery.                                                                                                                    | One-server task owns its internal calls. Advanced exact MCP remains optional; ordinary task users do not map raw parameters.                                          |
| Prominent prompt, simple input/model selectors and relevant settings; technical mechanics optional                                                  | Existing direct editors, `CadTaskOptions`, `ApplicationTaskOptions`; 164 current editor tests, final inspector walkthrough and earlier input/import walkthroughs.                                                                                                                                                     | Existing authoring behavior preserved. Reusable grouped blocks deferred.                                                                                              |
| Text, image, file, structured, CAD and analysis results; local/session/cloud representations                                                        | `workflow_results.py` defines all six kinds, four representation kinds, explicit `ResultCollection`, provenance and durability. `test_workflow_results.py`, application and result-content tests.                                                                                                                     | Versioned common contract; persistent cloud resources need no local file. Session-only resources remain identified as temporary.                                      |
| Stable provider/resource identity, location, revision when available, durability, provenance and associated files                                   | Required provider/resource fields; pinned CAD document ID and application resource/revision; run/task/output lineage and input revisions. CAD and application stale/reference tests.                                                                                                                                  | Revisions are not invented. Current local CAD provider has no revision token; external manual/cross-host edits cannot all be detected.                                |
| One CAD model result, native/session/cloud as representations; named grouped Exports                                                                | `cad-output-presentation.ts`, `EngineeringResults.tsx`, CAD publication, saved handoff graph, actual native/STEP history links.                                                                                                                                                                                       | No competing new native-model output. Each producing task has its own provenance; the same model may appear in multiple tasks' history.                               |
| Keep activity separate from deliverables; retain final prompt file behavior                                                                         | Shared executor publishes engineering results separately from events/tool calls; terminal prompt saves and indexed/overwrite regressions.                                                                                                                                                                             | Run details uses existing viewers and separate technical logs.                                                                                                        |
| Typed individual/collection and capability-aware connections; actionable export offer                                                               | `engineering-connections.ts`, `ApplicationTaskOptions.tsx`, common representation selector, application import validation; `test_workflow_application_task.py`, `test_workflow_result_contents.py`, exact MCP argument cases and simulated import-controls report `2026-09-07T16-40-01-969Z`.                         | Unsupported/binary/ambiguous inputs fail with correction. Provider-declared conversion is configured on the producer; no silent conversion or universal import claim. |
| Named export can be consumed as actual document/image/JSON contents                                                                                 | Digest-checked `reference_from_result`, shared executor's input resolution; live CAD JPEG→AI review plus exact-tool and generic-export contract tests.                                                                                                                                                                | Cloud-only links cannot masquerade as file contents. Advanced legacy CAD file parameters retain their explicit path behavior.                                         |

## Execution, migration and rerun requirements

| Explicit requirement                                                                             | Current evidence                                                                                                                                                                                                                                                             | Conclusion / boundary                                                                                                                                            |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UI and headless share one execution path                                                         | Both use `/api/workspace/workflow-sources/run`; live API prompt campaign, browser runs and compiled executor tests.                                                                                                                                                          | No separate runtime authority introduced.                                                                                                                        |
| Resource selection/revision pinning, modification/copy/new revision, indexed/overwrite           | CAD target guards, `ApplicationResourceTask`, source-bound oracles; live working-copy and unsaved-copy evidence; application copy/revision contracts.                                                                                                                        | Local and cloud differences are adapter capabilities, not an assumed local filename.                                                                             |
| Concurrent conflicting edit protection                                                           | `workflow_resource_lease.py` OS leases; competing-process and cancelled-waiter tests; application revision arguments forwarded and stale revision rejected.                                                                                                                  | Protects cooperating local processes and provider-supported revision preconditions. External edits without provider revision support remain a stated limitation. |
| Async local/cloud submission, monitoring, timeout, cancellation, failure and verified completion | `workflow_async_operations.py`; submission once, pinned job, status/result read-only checks, unknown-state rejection and cancellation contracts; shared analysis task test and simulated browser report `2026-09-07T17-28-24-274Z`.                                          | Submission is not completion. Explicit opt-in adapter, not a claim that every MCP implements this protocol.                                                      |
| Interrupted work reported without mutation replay; actual partial outputs retained               | `workflow_run_record.py`, run-history UI, partial-result events; exact logs and failed attempts retained. Generic staged export failure/cancel tests preserve earlier files and incomplete staging evidence.                                                                 | Unknown remote completion requires inspection before retry. No automatic mutation replay or cancellation-as-rollback claim.                                      |
| Real-state animation, understandable progress and outputs, deeper logs                           | Current editor tests for active/cancelled/completed runs; live CAD runs, simulated cancellation, final history walkthrough.                                                                                                                                                  | Active badges clear after completion; records and outputs remain inspectable.                                                                                    |
| Compatible CAD migration preserves instructions/connections/positions/policies/files             | Read-time compatibility projection retains old addresses and connected legacy sockets; new blocks avoid duplicate sockets. `cad-output-presentation.spec.ts`, `CadTaskOptions.spec.ts`, authoring/source/layout and command roundtrips. Saved handoff source hash unchanged. | Explicit compatibility rather than bulk rewriting workspace files.                                                                                               |

## Numbered representative verification

All browser report paths below are under
`artifacts/ui-walkthrough/cad-deliverables/`. They are evidence for their recorded
source/build, not permission to relabel failed attempts or claim a new run.

| Goal case                                                           | Authoritative evidence                                                                                                                                                                                       | Classification                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| 1. Prompt produces a document                                       | API attempt `0d1b3502220e4fc3b096928e3f9b7126`; browser `2026-09-07T14-42-20-769Z`, actual HTML bytes/digest and existing viewer.                                                                            | Live.                                                                  |
| 2. Create local CAD model and export files                          | `2026-09-07T16-51-07-946Z`; run `20260907T165221Z-ba111081c541`; native tab/flange calls, `bracket-002.psm`, `bracket-001.step`, hashes and STEP viewer.                                                     | Live; file/feature evidence, not complete design qualification.        |
| 3. Modify workspace model through working copy                      | `2026-09-07T15-19-24-445Z`; native/STEP files, unchanged original digest and 2.5 mm provider readback.                                                                                                       | Live.                                                                  |
| 4. Modify selected open model including unsaved content             | `2026-09-07T16-59-39-809Z`; original unsaved 2.25 mm copied then modified to 2.75 mm; original file/session snapshot preserved; verifier and immutable recheck.                                              | Live on an owned test model.                                           |
| 5. Pass CAD result to another task                                  | `2026-09-07T15-30-02-145Z`; both tasks use the same copied document, 2.5 mm readbacks, native/STEP outputs. `recheck-b1709fa526c34140bc47616f72905a63`. Also JPEG→AI review `2026-09-07T18-18-31-721Z`.      | Live. Original screenshot-export dirty-state finding retained.         |
| 6. Cloud resource with export                                       | Cloud create/copy/revision/export and shared executor contracts in `test_workflow_application_task.py`; resource controls and import offers in simulated browser report `2026-09-07T16-40-01-969Z`.          | Contract/simulated. No configured live Onshape provider.               |
| 7. Async analysis submission and monitoring                         | Shared task/operation-monitor/provider-quantity contract; browser `2026-09-07T17-28-24-274Z` persistent analysis + CSV, progress, cancellation and retained partial output.                                  | Contract/simulated. No configured licensed live solver.                |
| 8. Incompatible/stale inputs, reruns, cancellation, partial failure | Results/application/CAD/content/lease/history/export regression files; real image preflight/catalog failures retained; simulated cancellation and partial-output browser report; indexed native/STEP reruns. | Live evidence where available, otherwise explicitly labeled contracts. |

The CAD export state correction has additional live evidence in
`2026-09-07T18-41-04-407Z`: saved working copy plus JPEG, fresh post-export dirty
state and notice, original file/session snapshot preserved. Repeatable read-only
verifiers passed again and produced immutable attempts
`recheck-ee6e3a88294d4418b094d4d9f9eb6794` (image handoff, original limitation
retained) and `recheck-18d630792b034624b173345b942fc871` (accurate state).

## Test-program preparation

| Explicit requirement                                                                                        | Inspected artifact / evidence                                                                                                                                                                                                                                                               | Conclusion                                                                                      |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Locate real corpus, benchmark plans and criteria                                                            | Existing `benchmark-coverage.json` has target/domain quotas; engineering scenario catalog contains four actual legacy scenarios. Current `artifacts/workflow-campaign/manifest.json` contains 30 saved workspace files, 18 compiling, rehearsal classification and four planned migrations. | No evidence of 100 authored distinct workflows; target is not falsely represented as inventory. |
| Stable IDs, purpose, applications/capabilities, inputs, expected outputs, verification criteria             | Actual manifest fields, legacy scenario assertions, `inventory()` and tests for stable IDs across prompt edits.                                                                                                                                                                             | Actual authored/planned cases described; no duplicates invented to reach the target.            |
| Distinguish planned/authored/runnable/verified                                                              | Manifest conservative availability blockers; dashboard separates run readiness from source-revision evidence; `live-record-recheck` explicitly scoped.                                                                                                                                      | Historical success no longer implies current runnable state.                                    |
| Repeatable workspace setup, fixtures, focused/subset/batch runs and bounded resources                       | `scripts/workflow-campaign.py`, fixtures module/tests, smoke/image bundles and restore evidence, subsets, 1–20 runs / 1–500 model calls / 1–3600 seconds / 1–4 concurrency validation, application serialization.                                                                           | Ready to begin the actual campaign; model-call bound is not a dollar-budget guarantee.          |
| Verify engineering outputs, not narration                                                                   | Structure/hash checks; CAD dimensional assertions from actual provider calls; analysis quantity checks require exact provider/resource/revision, field, units and tolerance. Adversarial tests reject narration, wrong units and stale/unproved inspection.                                 | Geometry/solver qualification is limited to assertions actually run.                            |
| Preserve reproducible input/output/provenance/diagnostics                                                   | Workspace source files and run logs, fixture hashes, browser traces/raw images, immutable attempts, source-bound oracle records.                                                                                                                                                            | Session/application credentials still require explicit setup.                                   |
| Update existing dashboard with separate implementation/UI/contract/live/blocked/user acceptance and history | `coverage.json`, manifest blockers and attempt history, served `/api/workflow-campaign`; existing dashboard collector remains current after reload.                                                                                                                                         | No historical qualification or acceptance counts advanced.                                      |
| Open examples in Codex; exact names, manual sequence, results, limitations and next batch                   | `docs/contributing/engineering-workflow-test-handoff.md`; final workspace report; saved handoff file displayed in existing browser.                                                                                                                                                         | Final handoff names ordinary workspace files and actual next scenarios.                         |

## Current regression evidence

`artifacts/workflow-campaign/checks/` contains:

- `frontend-20260907.xml`: **164 passed**, all 15 editor/service test files,
  including canvas, source, command history, CAD compatibility and result controls.
- `backend-20260907.xml`: **312 passed, 1 failed, 7 skipped**. The failure was
  the source-store lock test's `ready.wait(timeout=10)` while starting its child
  process concurrently with the frontend suite; it did not reach the storage
  transaction assertion. No product code was changed to suppress it.
- `backend-process-startup-recheck-20260907.xml`: the exact failed test passed
  alone, including the deadline, no delayed commit, release and unchanged source
  assertions. The failed whole-suite report remains intact.
- `backend-serial-20260907.xml`: **313 passed, 7 skipped**, running the same
  backend selection without the concurrent frontend workload. This is the final
  complete backend result; it does not erase the earlier startup timeout.
- Seven skips: six Windows symlink-privilege cases and one POSIX descriptor/rename
  race that Windows directory handles do not permit. These are unavailable host
  coverage, not passing tests. The reports preserve exact test names/reasons.
- TypeScript `tsc --noEmit -p tsconfig.app.json` completed with exit code 0.

Tests were selected for the affected editor/runtime/API/model bridge and campaign.
They are not a substitute for repository merge/release gates. Those gates remain
for the authorized consolidated CI batch; no push or merge occurred here.

## Remaining limitations and audit disposition

No new live cloud/FEA result, 100-workflow qualification, external user acceptance,
arbitrary-server adapter support, or production delivery is claimed. These limits
are explicit in the handoff and served coverage. The actual missing integration
prerequisites are recorded in `provider-availability-20260907.json`: inactive and
uninstalled Onshape with unconfigured API keys; inactive/uninstalled PyFluent with
a licensed solver/gateway validation requirement. Unaffected local work continued.

The test program is prepared to start the larger campaign; authoring and qualifying
the remaining distinct scenarios is future campaign work. The final browser report
`2026-09-07T19-05-14-539Z` passed the walkthrough artifact validator. It preserves
an automation limitation: its initial trace was lost when the browser-tool client
timed out after returning from the dashboard. Contemporaneous screenshots/actions
remain; `recovered-handoff.zip` covers the returned saved graph only. No product
error or workflow rerun occurred during that handoff. The existing STEP file
viewer displays exchange-file text; this does not establish a 3D model preview.

The Codex browser-open request targets the saved CAD result handoff and was queued
for this task's panel. The attached browser itself was independently inspected
showing that saved graph. The manual handoff is a local file with exact names and
commands, ready for the next user test. Local implementation, scoped representative
verification and campaign preparation are delivered; the stated unavailable live
providers, broader campaign execution, human acceptance and CI/release are not
silently counted as complete.
