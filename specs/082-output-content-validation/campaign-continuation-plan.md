# Campaign continuation: 30/30/30/30

**Date:** 2026-09-17. **Branch:** `codex/082-output-content-validation`.
**Status:** Active follow-on plan; the saved goal was submitted and approved implementation and campaign execution.

## Objective and authority

Resume the existing 30-case campaign and extend the delivered runtime process
validator until every case produces a complete output set that passes its full,
source-backed digital acceptance scope. Findings must reach the producing AI as
actionable correction feedback and remain readable in the shared report contract.
This is process execution and validation, with tests of the validator itself.

The user's requested `30/30/30/30` is interpreted as **including** the fourth
measure: output correctness and compliance with initial requirements. The phrase
"not taking into account" in the request conflicts with that target; this plan
makes the interpretation explicit for approval through the goal.

The original 082 implementation, T001–T034, is complete. Preserve it and its
demonstration evidence. This follow-on expands the original bounded scope and
authorizes work on the existing generation campaign when the goal is submitted.
It supersedes old campaign instructions to keep `valid_data=0`, stop after one
pilot, or exclude generation work. It does **not** reset exhausted retry episodes,
change engineering requirements, authorize physical actions, or move the reporting
application into this branch. There is no all-30-output prerequisite: advance each
case as its inputs, readers and producer become ready.

## Merge and observed starting point

- Fetched GitHub `dev` at `f3c98a26` and merged it into this branch at `c440e7b9`.
  The merge was conflict-free. It brought CI/test-contract and program-state
  changes; it did not supply the missing family validators or provider repairs.
- The live dashboard at <http://127.0.0.1:8771/?view=recovery> returned
  **30 datasets / 30 combinations run / 24 complete output sets / 0 validated**.
  Its saved status timestamp was `2026-09-17T11:48:29.963+00:00`; the live
  incremental reconciliation was current when inspected.
- SQLite identifies the six cases without a historical complete output set as
  `lightweight-equipment-bracket-01/02/03` and
  `sheet-metal-supplier-handoff-01/02/03`.
- The snapshot marks **0/30 completed for the current input/template revisions**.
  Sampled jig-01, heat-01 and robot-01 historical receipts differ in both hashes.
  Investigate exact source differences before scheduling expensive reruns; the
  historical 24 is not evidence of 24 current completions.
- Packaged coverage has two **bounded** qualified profiles: jig-01 seat centers
  and diameters; heat-01 conduction fields, balance, refinement and selection.
  The other 28 scenarios are unsupported. Even the two pilots need scope expansion
  before they can establish whole-case requirements compliance.
- The runner is paused with no cases in its current summary. The saved queue is
  `.local-run/feature-081-live/campaign-execution/validator-qualified-attempts-082.json`
  (jig-01 attempt-014, heat-01 attempt-010). Those two dataset/template hashes
  matched the inspected current snapshot. Runtime source, grants, resources,
  reader/profile identities and expiry still require preflight.
- The pause sentinel records `selected_model_usage_limit` for
  `openai-codex::gpt-5.6-sol` and an estimated reset of
  `2026-09-19T11:09:44Z`. This is retained state, **not a fresh inference result**.
  Health endpoints and a model listing do not establish available inference quota.

Merge verification ran the seven focused suites listed below: 141 checks passed
and three sheet-metal identity checks initially failed. The working checkout
still contained CRLF bytes despite the existing LF attributes. Thirty affected
tracked text files were refreshed to their exact committed bytes after proving
that line endings were their only difference. No source or receipt content was
rewritten. All six sheet-metal checks then passed using `python -m pytest`.
The final rerun of all seven suites passed: **144 passed in 19.52 seconds**.
The remaining campaign revision mismatch still needs investigation.

Use these existing local records to resume without reconstructing the environment:

| Record | Location |
|---|---|
| Campaign ledger, status, outputs and retry episodes | `artifacts/engineering-workflow-datasets/` |
| Runner summary and pause sentinel | `.local-run/feature-081-live/campaign-runner-state/` |
| Staged canonical cases | `.local-run/feature-081-live/campaign-execution/` |
| Dashboard process ownership receipt | `.local-run/feature-081-live/dataset-dashboard.session.json` |
| Existing API runtime database | `.local-run/feature-081-live/data/wright.db` |
| Historical generation workspace | `C:/Users/markb/wright-feature-081/engineering-workflow-demos` |

These paths describe the inspected environment, not permission to trust stale
process IDs. Recover current session/workspace and service identity from receipts
and the API. Use the existing runner's documented CLI with the qualified manifest,
state/export roots, pause sentinel and shared retry ledger; do not launch a new
unrelated campaign. No runner launch was performed in this planning task.

## What the four counters mean

Keep the existing historical series and add an explicit current-revision
projection; do not silently reinterpret previous events. All four target bars use
**30** as the denominator. Qualified profile coverage is a separate measure.

| Measure | Evidence required |
|---|---|
| Datasets created | All 30 declared packs have valid manifests, bound original inputs and a recorded identity. |
| Combinations run | Each case has an actual canonical execution receipt; staging, fixtures and diagnostics earn no run credit. |
| Processes with outputs | Each case has a completed required process graph and every required deliverable, with verified provenance and file hashes. Preserve the historical count and separately show current completion. |
| Valid data | The selected current complete output set passes every mandatory requirement in that case's frozen acceptance baseline, through qualified readers and current immutable assessments. |

Completion requires the displayed target `30/30/30/30` **and** 30 current complete
output sets with 30 full-scope, current passes. A newer failed/incomplete candidate
cannot silently inherit an older pass. Select the authoritative candidate by a
documented deterministic rule, show that selection, and invalidate affected credit
when its output, requirements, profile, reader or workflow identity changes.
Historical records remain immutable; current counts may decrease.

Missing evidence, partial scope, unavailable readers, unresolved source conflicts,
pending required review, evaluator errors and stale results cannot count as valid.
A correct infeasibility finding is useful validated analysis, but cannot count as
requirements-compliant design when a feasible design was required. Define that
distinction from each original brief before evaluation. Simulated handoffs prove
only the declared digital/test-destination scope. If the brief requires physical
acceptance, retain that obligation as pending; do not silently exclude it for credit.

## Implementation sequence and exit evidence

### C0 — Reconcile and prepare a safe resumption

- [x] C001 Read this plan, AGENTS, the constitution, 082 quickstart/report contract
  and the compact 081 recovery checkpoint. Inspect the campaign database/status,
  retry ledger, queue and owned-service receipts. Do not repeat branch recovery.
- [x] C002 Save a compact 30-row inventory of current input/template hashes,
  selected producer/run/output identity, output completeness, requirement baseline,
  full versus partial validator coverage, blocker and next action. Compare retained
  input snapshots with the checkout, including Windows line endings. Preserve raw
  identities and historical credit; do not edit receipts, revert requirements or
  broadly rerun everything merely to make hashes match.
- [x] C003 Check actual API, inference and native reader/provider availability.
  Use one small disposable inference request on the configured Sol route. Recheck
  a quota hold at its indicated reset or a material configuration change, rather
  than repeatedly polling the model. Continue offline implementation if unavailable.
  Validate owned process identity, disk headroom and cleanup before startup/restart.
- [x] C004 Reconcile the staged pilot manifest against saved canonical instances,
  all input bindings, current tools/schemas, source/profile hashes and approval
  expiry. Re-enroll only when identity or authority changed. Retain old manifests.
  Clear a pause only after its recorded cause is resolved; never replay an
  uncertain native mutation or ambiguous run-creation POST.

**Exit:** fresh inventory and runnable queue, or precise runtime blockers alongside
an executable offline work list. A runtime blocker does not block C1/C2 development.

### C1 — Make validation credit reliable

- [x] C005 Harden the existing exporter/campaign projection before increasing
  fourth-counter credit. Check exact subject/output revision, producer run,
  scenario, mandatory scope, profile/baseline and reader qualification/currentness.
  Reuse the runtime's authority and currentness logic; do not build a second
  evaluator in the dashboard. Validation errors must not erase separately proven
  generation/output completeness.
- [x] C006 Use one canonical assessment digest function. Inspection found
  `ensure_ascii=False, allow_nan=False` in the exporter but default JSON options
  in `check_outputs`; cover non-ASCII findings and reject non-finite data consistently.
- [x] C007 Replace reliance on receipt-time `is_current`, a scenario-level
  `qualified` flag and "any completed passing attempt" with checked currentness,
  full required-scope coverage and deterministic candidate selection. The existing
  two partial profiles must not earn whole-case passes. Test foreign profiles,
  wrong subjects, missing mandatory checks, stale baselines, tampered evidence,
  a newer failed attempt after a pass, and changed reader qualification.
- [x] C008 Keep the dashboard available at port 8771. Show historical versus
  current completion, output completeness separately from validator outcome,
  supported scope, blocker, failed requirements and assessment/report links.
  Change the fourth progress bar from the qualified-profile denominator to 30.
  Preserve cached/incremental reconciliation and add an explicit final full audit;
  do not rehash the entire corpus on every browser poll.

**Exit:** focused counter/export tests prove no false pass and honest invalidation;
all dashboard counts and row selections reconcile to the persisted evidence.

### C2 — Freeze all 30 acceptance baselines and reusable checks

- [x] C009 Re-read all complete current packs, including prompts, context,
  images, tables, source references and approved amendments. Use the 081
  acceptance-case seeds as an index, not as a complete requirements specification.
  Build source-linked RTM entries for every mandatory digital requirement and
  deliverable; record explicit exclusions and required human/physical decisions.
- [x] C010 Freeze each baseline independently of candidate output: requirement
  ID, source hash/locator, expected condition, method, feature selector, unit,
  datum/frame, tolerance/uncertainty, subject role and correction owner. Apply
  approved sheet-metal R1–R4 decisions only within their recorded scope and retain
  the current Modelica derivative and manufacturer-source authority rules.
  Ambiguous or contradictory obligations remain blockers with a concrete proposed
  resolution for the user; never derive a tolerance from the candidate.
- [x] C011 Extend packaged readers/profiles using the family map below. Separate
  parse/structure checks, geometry/physics checks, requirements and cross-artifact
  correspondence. A generator's description, success flag, or passing ERC/DRC alone
  cannot establish content correctness. Keep runtime resources out of test-only paths.
- [x] C012 Qualify each added capability with independent valid and alternative
  outputs, targeted valid-file defects, and relevant boundary/unit/frame controls.
  Wrong content must reach the intended check, not merely cause a parsing error.
  Register full-scope coverage only after retained qualification and canonical
  process evidence. Build a pilot, then its siblings; do not wait for all families.

| Family (01/02/03) | Required reusable validation work | Suggested order |
|---|---|---|
| robot-tracking-diagnosis | Raw sample/mask/time/frame readers; recompute RMSE, clock correction, wrapped yaw, event correspondence and evidence-linked hypotheses. | Early local-data wins |
| heat-spreader-sizing | Extend actual coarse/refined field lineage and independent balance/reference checks to every candidate, case-specific load/material, interface resistance and selection; inventory all required deliverables. | Existing heat pilot, then all three |
| sensor-fan-harness | Read endpoint/splice connectivity and wire properties; calculate shared currents, voltage drop, cut lengths, reserve-pin/shield/return rules and required bundle correspondence. | Reuse structured/numeric readers |
| water-heater-sizing | Inspect approved model/parameters and trajectories; independently integrate energy, target crossing, 2 K hysteresis, inverter-side energy and full candidate/loss grids. | After numeric foundations |
| parametric-drill-jig | Extend beyond jig-01 seats to all datum coordinates, stackups, clearances, clamps, windows, keys, protected zones and required output correspondence. | Existing CAD pilot, then siblings |
| printed-replacement-part | Actual geometry/fit for socket, scallops, handle clearances and wedge orientation; model-to-slice/toolpath/material correspondence and required package contents. | Reuse geometry, add slicer reader |
| sensor-interface-pcb | Actual native connectivity/values/footprints/coordinates, separated power domains, widths/clearances, ERC/DRC, and native-to-Gerber/drill/BOM correspondence. | After graph foundations |
| raspberry-pi-enclosure | Manufacturer-backed interfaces, geometry/keepouts/assembly, mesh/loads/BCs/fan curve, thermal field balance/convergence and comparable alternatives. | After geometry and field foundations |
| lightweight-equipment-bracket | Protected geometry, exact loads/restraints/material/mesh, reactions, displacement/stress regions, mass-reduction targets and refinement. | Recover six missing-output group |
| sheet-metal-supplier-handoff | Current approved geometry/material, bends/reliefs/thickness, genuine native developed flats, STEP/DXF/native correspondence, multipart inventory and simulated quantities. | Recover six missing-output group |

### C3 — Connect findings to safe producer correction

- [x] C013 Extend the existing canonical preparers and explicit validator bindings
  rather than introducing another process runner. Preserve every required production
  stage, source input, native/tool grant and simulated approval. Remove obsolete
  preparer instructions that force `valid_data=0`. Use direct/local validation where
  sufficient and MCP/native readers where needed.
- [ ] C014 Send the existing bounded correction packet to the actual producing
  AI: requirement/check, expected/observed, units/frame/tolerance, evidence/feature,
  output owner, acceptance target and recheck IDs. Preserve satisfied constraints.
  Export JSON, Markdown and RTM from the same immutable assessment using the shared
  report contract. Do not develop a competing reporting application.
- [ ] C015 Enable at most two automatic producer revisions for eligible explicitly
  configured replayable segments. The currently queued pilot checks use zero
  revisions; change source and re-enroll intentionally if enabling repair. Keep
  the existing v1 single-producer/check restriction. Multi-owner failures require
  safe staged fixes, not arbitrary graph replay. Persist budgets through resumes;
  stop on no progress, unchanged repeated defects or unsafe mutation.
- [ ] C016 Prove changed integrations in isolated disposable runs first, then
  execute qualified current campaign instances. Retained output may be inspected
  read-only when exact provenance permits; a detached inspection or downstream-only
  diagnostic is labelled as such and does not invent a completed full workflow.
  New corrections create new revisions and invalidate dependent results/approvals.

**Exit:** current campaign evidence shows producer → check → useful feedback →
authorized correction → new output → recheck → downstream release. A partial pilot
demonstrates the mechanism while its whole-case fourth-counter credit remains zero.

### C4 — Recover outputs and advance every case

- [ ] C017 Prioritize ready cases that add full-scope validation credit, sharing
  readers across families. Run serially by default; preserve native leases and the
  campaign's durable operation/approval reconciliation. Keep progress event-driven.
- [ ] C018 Recheck the six missing-output cases against actual merged/runtime
  capability. The retained blockers are missing bracket-01/02 geometry authority,
  a bracket-03 CalculiX `child_unavailable` failure, and a Solid Edge flange
  `E_POINTER` failure. These are historical diagnoses, not proof of present failure.
  Prove provider recovery with a small owned diagnostic before a full process.
  Do not overwrite or redeploy another task's provider worktree.
- [ ] C019 Preserve exhausted episodes, including `bracket03-late-native-recovery`
  at 2/2. The submitted goal permits a successor episode only after a documented
  material repair and successful isolated proof; link its predecessor and changed
  dependency. A new attempt, prompt, grant or model session alone is no new budget.
- [ ] C020 Stop an individual defect after two unsuccessful correction cycles,
  quarantine it with evidence and continue independent cases. After three expensive
  attempts with no new complete output or full-scope pass, pause expensive dispatch,
  diagnose the cause and resume only after a material fix with focused proof.
  Preserve unresolved requirements/provider/quota decisions explicitly. Never
  weaken acceptance or declare the campaign complete just to satisfy the target.

### C5 — Audit and hand off

- [ ] C021 Run the required focused regressions, package/resource checks and
  appropriate native qualification gates. Browser-check the existing dashboard's
  30 rows, four denominators, progress, failures, freshness, links and narrow layout.
  If the product editor changes, follow its integration guide and verify through
  the served workspace Workflow/Workflows control. Verify report consumers against
  `wright.process-validation-report/1` without importing evaluator internals.
- [ ] C022 Full-audit all 30 selected current candidates, their complete required
  process graphs, output bytes, full RTMs, scope/profile/baseline/reader identities,
  assessments, currentness and any repair lineage. Save a machine-readable 30-row
  reconciliation plus a readable completion report. Snapshot the final dashboard.
  Persist work in focused local commits and a compact next-action handoff.

**Exit:** 30/30/30/30 with independently reconcilable current evidence, or an explicit
incomplete checkpoint with exact blockers, exhausted budgets and remaining tasks.
An incomplete checkpoint is never a successful goal completion.

## Ownership and constraints

Reuse `scripts/engineering_dataset_campaign.py`,
`scripts/engineering_dataset_evidence.py`, `scripts/run_engineering_dataset_campaign.py`,
the existing family preparers, and `scripts/engineering-dataset-dashboard.html`.
Runtime contracts remain in `core`, persistence in `data_vault`, and
evaluation/readers/feedback in `workspace_service/process_validation/`.
Transport routes remain thin. Use the existing currentness/report services.

Pre-design and post-plan checks against constitution v3.1.1:

| Principle | Application |
|---|---|
| Architecture/offline | Extend existing modular services; deterministic local readers work offline; no cloud-only evaluator. |
| Serving/distribution | Package profiles/readers for shared native/Docker runtime; manager-neutral integration; keep optional provider prerequisites explicit. |
| Storage | Existing embedded SQLite WAL and immutable file vault; campaign remains a development harness, not a second runtime ledger. |
| Security/identity | Preserve auth, origins, RBAC, root confinement, explicit grants and actual review authority. |
| Tool protocol | Reuse BaseTool/MCP adapter; CLI/local invocation shares the same service; no GUI-only validation. |
| UI/testing | Preserve authoring and report boundary; focused correctness/security tests and applicable UI tiers. |
| Observability | Preserve trace/run/step/attempt identity through reads, findings, feedback, repair and exports; structured logs and bounded metrics. |
| Agent workflow/governance | This is planning only. Goal submission approves these milestones and routine local implementation/run decisions; push/merge/release remain separate. |

Use one agent and the configured Sol inference route; do not silently switch models.
Do not add MCP-specific host software to the base image. Respect the clean-container
qualification process for MCP claims. Physical printer dispatch, supplier orders,
external publication and edits to another task's services are outside this plan.
Local commits are authorized by the submitted goal; any later push or merge follows
the current contributor runbooks.

## Verification and continuation records

Use `uv run python -m pytest` from the repository root with a private basetemp and
cache directory. The merge-focused suites were:

```text
tests/test_engineering_dataset_campaign.py
tests/test_engineering_dataset_evidence.py
tests/test_run_engineering_dataset_campaign.py
tests/test_heat_campaign_validator.py
tests/test_printed_dataset_bindings.py
tests/test_sheet_company_capabilities.py
tests/release/test_dev_push_process.py
```

The follow-on also needs the existing runtime validation/currentness/rework/report
tests and family-specific controls for each change. Full tests or demonstrations
are not rerun without a changed dependency, failure or unresolved concern.

At implementation start create `campaign-continuation-progress.md` beside this plan.
Record completed C IDs, exact commands/results, selected model, actual usage when
available, unknown telemetry, current counters, new evidence and exactly one next
action. Keep it short; link detailed artifacts under
`artifacts/engineering-workflow-datasets/`. Update the checkboxes in this plan as
work is proven. Preserve the completed original 082 task list and all prior receipts.

Start from [the saved goal](campaign-continuation-goal.md). Saving these files and
merging `dev` have not started the campaign or activated a goal.
