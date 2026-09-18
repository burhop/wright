# Campaign continuation progress

**Updated:** 2026-09-17. **Branch:** `codex/082-output-content-validation`.
**Model:** `openai-codex::gpt-5.6-sol`; usage telemetry is unavailable. A fresh
registered-session inference probe at `2026-09-17T19:10:49Z` was rejected before
generation with `The usage limit has been reached`. The retained reset estimate
is `2026-09-19T11:09:44Z`. The runner pause remains in force.

## Completed

- C001–C004: reconciled the existing campaign, services, retry records and
  two-case staged queue. The read-only queue preflight passed 2/2 with exact
  sources, input bindings, grants, unexpired authority, tool schemas and stages.
- C005–C008: campaign credit now requires exact current dataset/template,
  producer run, output subject, profile, baseline and declared full scope. A
  newer current attempt supersedes old credit. Export and projection share the
  canonical digest. Output completeness remains independent of validator errors.
- The dashboard was ownership-checked and restarted at port 8771. Browser
  verification passed 30 rows, 30 input images, four chart series and narrow
  layout with no browser errors. Its horizontal axis now uses equally spaced
  persisted update numbers, so unsuccessful/unchanged observations remain flat
  steps without creating time-based gaps. The 17,969-point live history renders
  once per ledger revision instead of redrawing on every poll.
- The Windows restart command now terminates the already-verified owned process
  tree as one unit. This fixes the prior `Stop-Process` child/parent race; the
  corrected script successfully relaunched the dashboard with 30 rows, 17,969
  update events, zero unsupported profiles and unchanged honest campaign counts.

## Evidence and current state

- [30-row inventory](../../../artifacts/engineering-workflow-datasets/inventory-082-20260917.json):
  historical `30/30/24/0`; current runs `0`, current complete outputs `0`, and
  full-scope validators `0`. All 30 selected historical templates differ from
  current templates. Detectable retained input drift is line-ending-only for
  126 files; 51 referenced historical staged files are no longer present and two
  current files were absent from their historical snapshot, so those bytes are
  explicitly unresolved rather than inferred.
- [Queue preflight](../../../artifacts/engineering-workflow-datasets/preflight-082-20260917.json):
  jig-01 attempt-014 and heat-01 attempt-010 both pass, with zero warnings.
- Focused campaign/export tests: `68 passed in 11.92s`.
- Browser check: 30 dataset rows, 30 images, four series, no browser errors.
- Live counters: historical `30/30/24/0`; current `0/0/0` after dataset creation;
  validator coverage `2` bounded qualified and `30/30` implemented full profiles.
- C009 is complete and C010 is in progress: 30 source-hashed packaged baselines
  cover every current campaign case exactly once. They contain 315 atomic mandatory requirements, preserve
  the Modelica selected-kit amendment, validate against the closed runtime
  `Baseline` model, and are reproducible from the reviewed definitions. Baseline
  checks remain green; the initial baseline/distribution check passed 6 tests.
- C010–C012 advanced for the robot-tracking family: three full frozen profiles
  now bind conversion lineage, frame/clock alignment, retained sample scope,
  independently recomputed RMSE/time/gap/yaw observations, event correspondence,
  deliverable presence and authenticated plot/diagnosis reviews. The reusable
  timeline reader rejects malformed, nonfinite, inconsistent and unwrapped data.
  Retained cases 01 and 03 pass every automated check. Case 02 is correctly
  rejected for two false gap records caused by floating-point comparisons.
  All three remain `implemented`, not `qualified`, pending required human review;
  case 02 also needs corrected producer output. Focused validation/resource tests:
  `44 passed in 9.53s`; Ruff passed.
- C010–C012 also advanced for all three heat-spreader cases. Full profiles now
  inspect actual STEP vertex envelopes, independently evaluate every retained
  coarse/refined field, include the case-03 whole-interface contact resistance,
  check balance/refinement/outcomes/selection and require the source-backed basis
  review. All three retained cases pass every automated full-profile check. A
  valid-file ideal-contact substitution reaches and fails the analytical check.
  These full profiles remain implemented pending authenticated reviews; heat-01's
  earlier bounded field profile remains separately qualified. Focused reader,
  profile, coverage and service tests: `47 passed in 12.87s`; Ruff passed.
- C011–C012 began the sensor-fan harness family with a reusable independent
  connectivity/cut/drop reader. It checks required paths through explicit splice
  nodes, rejects cross-net shorts and connected reserve pins, verifies each unique
  cut as installed route plus documented allowance, and refuses copper-only drop
  summaries whose total contact/splice-inclusive drop is null. Reader and service
  regression tests: `29 passed in 5.35s`; Ruff passed.
- All three harness profiles are now frozen and implemented. They bind original
  wiring-schedule connectivity through explicit splice nodes, reserve pins,
  cut/drop evidence, required deliverables and authenticated engineering reviews.
  Each retained case reaches the same actionable `voltage-drop` finding because
  its copper-only result leaves `total_drop_v` null; those cases correctly remain
  invalid rather than receiving credit from their producer success flags.
  Profile/coverage tests: `11 passed in 4.24s`; Ruff passed.
- All three water-heater profiles are now frozen and implemented. A reusable
  timeline reader validates the exact candidate/loss grid, initial conditions,
  electrical-to-thermal efficiency, complete one-second baseline grid, Modelica
  event-time duplicates, interpolated first 90 °C crossings and lowest feasible
  selection. Retained trajectories pass those independent checks but each
  parameter summary omits the required `wright-water-heater-v1@0.1.0` identity,
  producing targeted `kit-id` and `kit-version` findings. Focused tests:
  `34 passed in 5.17s`; Ruff passed.
- All three drill-jig full profiles are now frozen and implemented. The existing
  native STEP reader directly measures every declared body and flange circle at
  2, 4 and 6 hole locations in the workpiece datum; retained STEP files pass all
  automated checks. DXF/report inventory is bound, while stackup, keepouts, keys,
  access, marking and claim scope require authenticated design review. Jig reader
  and full-profile tests: `13 passed in 6.61s`.
- All three sensor-interface PCB profiles are now frozen and implemented. A
  bounded native KiCad/fabrication reader checks exact pin-to-net mapping,
  source component values and footprints, required placements, the board
  outline and holes, BOM rows, zero ERC/DRC errors or unconnected items,
  required fabrication members and case-03 power-net widths. All three retained
  boards pass the automated checks, while a clean-board connector-pin mutation
  is rejected by the frozen netlist check. Warning disposition, compatibility,
  full design/export correspondence and release claims remain behind
  authenticated engineering review. Focused reader/profile/coverage tests:
  `11 passed in 2.28s`; Ruff passed.
- All three printed-replacement-part profiles are now frozen and implemented. A
  bounded print-artifact reader independently measures binary-STL envelopes and
  manifold integrity, requires distinct source/repaired revisions with stable
  spans, inspects safe 3MF members, and binds the actual slice and simulator-only
  transfer records to the exact repaired-mesh/package digests. Cases 01 and 03
  pass every automated check. Case 02 correctly fails with
  `printing.mesh_not_distinct` because its retained source and repaired meshes
  are byte-identical. Detailed feature geometry, orientation/support choices,
  tolerance statements and physical claims remain behind authenticated review;
  these review requirements are explicitly marked in the embedded frozen
  baselines. Full process-validation regression: `105 passed in 37.81s`; Ruff
  passed.
- All three Raspberry Pi enclosure profiles are now frozen and implemented. A
  bounded CFD evidence reader verifies contract-to-geometry/load hashes,
  comparison-to-archive identity, every archived field digest, binary-VTK source
  temperatures and boundary mass balance. STEP readback enforces each declared
  enclosure envelope, and case 03 binds both solver contracts to every supplied
  fan-curve point. All three retained runs are correctly blocked because they
  explicitly lack supported steady-state convergence and field-derived heat
  balance evidence; case 02 variant B also measures 68 mm high against its 60 mm
  requirement. Manufacturer-source authority, detailed geometry and physical
  qualification remain behind authenticated review. Focused reader/profile/
  coverage tests: `12 passed in 10.78s`; full process-validation regression:
  `113 passed in 46.54s`; Ruff passed.
- All three lightweight-equipment-bracket profiles are now frozen and
  implemented. A bounded structural reader binds the four exact solver requests
  to the two STEP revisions and frozen load/material/mesh contract, verifies
  expansion receipt hashes, independently parses full displacement and stress
  tables, checks force-and-moment equilibrium, coarse/fine sensitivity and
  density-derived mass reduction. The preparer now freezes exact request and
  mass-comparison schemas. Retained attempts correctly return actionable missing
  output-role findings because none reached CAD or solver production; protected
  topology, machining feasibility and stress-region interpretation remain behind
  authenticated review. Focused reader/profile/preparer/coverage tests:
  `22 passed in 3.44s`; full process-validation regression:
  `122 passed in 32.39s`; Ruff passed.
- All three sheet-metal supplier-handoff profiles are now frozen and
  implemented, bringing full-profile coverage to 30 of 30 source packs. A
  bounded reader checks exact installed material identity, evidenced native
  design-check structure, millimetre developed-DXF entities, source-bound
  final-manifest hashes and runtime-generated integration-test receipts. It
  rejects embedded-image/solid DXF substitutes and any network-dispatched or
  wrong-scenario handoff. The preparer now labels native criteria with the
  frozen requirement ID and includes measured checks/material evidence in the
  final manifest. Retained attempts pass their installed-material check and
  correctly block on missing native CAD, exports and handoffs. Three stale local
  image-lineage receipts were refreshed only after the current renderer
  reproduced identical PNG bytes. Focused reader/profile/preparer/coverage
  tests: `15 passed in 2.57s`; full process-validation and preparer regression:
  `133 passed in 52.05s`; Ruff passed.
- Authenticated-review semantics are now consistent across all 30 full
  profiles. Eighteen earlier heat, jig, tracking, harness, PCB and water-heater
  profiles were regenerated so every review check maps exactly to a baseline
  requirement marked `review_required=true`; a coverage-wide invariant prevents
  recurrence. Review/profile regression: `130 passed in 51.21s`; Ruff passed.
- C010 and C011 are complete. The robot campaign preparer is the first C013
  integration: all three canonical workflows now expose exact file ports for
  their conversion manifest, timeline, metrics and plot, bind the immutable
  diagnosis response, run the scenario's pinned full profile after the existing
  engineer checkpoint, and hold the final evidence index unless the assessment
  passes. The old instruction forcing correctness credit to zero was removed.
  Automatic revision remains disabled while the five subjects have multiple
  producers. Preparer/profile/runtime regression: `59 passed in 10.77s`; Ruff
  passed.
- Canonical local reviews can now satisfy validator review checks only when a
  resumed checkpoint pins the same profile, the complete declared review
  requirement set and every exact subject digest. The resulting immutable
  assessment records the reviewer, checkpoint and authority digest. Automatic
  integration-test actors are explicitly rejected as human reviewers, so the
  campaign's auto approval mode cannot create correctness credit. AI response
  values now carry their own digest and byte count through continuation, closing
  the identity gap for reviewed text/JSON outputs. The end-to-end continuation
  test proves manual approval releases the consumer while an integration actor
  remains held for review. Combined robot/profile/reporting/rework/continuation
  regression: `82 passed in 14.81s`; the final affected-suite rerun passed
  `73` checks in `11.42s`; Ruff passed.
- All three heat campaign workflows now use their full profiles. Each exposes
  exact candidate STEP, coarse field, fine field, decision and basis subjects;
  the existing basis review pins the matching full-profile review requirements.
  The obsolete instruction forcing the valid-data counter to zero was replaced
  with the actual downstream gate. The full-profile preparer and runtime
  regression passed `52` checks in `11.76s`; Ruff passed.
- All three drill-jig workflows now expose exact STEP, DXF and independent
  dimension-report ports to their full profiles. A new post-inspection engineer
  checkpoint pins the matching profile and every review-required obligation;
  the validator then gates completion on that exact reviewed report plus native
  geometry. Review authority matching now requires the exact subjects used by
  review checks, while the remaining subjects stay under independent automated
  checks. Jig/profile/runtime regression: `37 passed in 6.43s`; Ruff passed.
- All three sensor-fan harness workflows now expose the generated plan, pin
  schedule, cut list, BOM, assembly instructions, case-03 shield record,
  independent netlist, voltage-drop result, design basis and handoff to their
  full profiles. A post-output engineer checkpoint pins every matching review
  requirement and the exact reviewed subjects before validation. The retained
  null total-drop defect can therefore reach the canonical gate as an actionable
  failure once the provider resumes. Harness/profile/runtime regression:
  `44 passed in 6.83s`; Ruff passed.
- All three water-heater workflows now expose the exact timeline, comparison,
  energy summary, curve, report and parameter files to their full profiles.
  Single-loss cases bind the original verification stage; the multi-loss case
  binds the sealed-study stage that actually creates those files. A post-study
  engineer checkpoint pins the energy, refinement and claim-scope reviews before
  validation. This makes the retained missing kit ID/version findings reachable
  through the canonical gate. Modelica/preparer/profile/runtime regression:
  `50 passed in 10.10s`; Ruff passed.
- All three sensor-interface PCB workflows now bind the immutable electrical
  basis response plus the final native board, schematic, BOM, fabrication
  archive and ERC/DRC records to their full profiles. The existing engineer
  basis checkpoint pins the complete review requirement set and exact basis
  digest; the terminal validator consumes the independently created native
  artifacts. PCB/preparer/profile/runtime regression: `44 passed in 7.78s`;
  Ruff passed.
- External integration checkpoints can now declare one exact, uniquely named
  `*receipt` workspace-file output when their approval settings name the receipt path.
  Continuation verifies the persisted bytes, restores the receipt as a normal
  provenance-bearing result and registers it for downstream validation. Local
  reviews retain their prior no-output semantics. A focused continuation test
  proves the verified receipt reaches the next canonical step.
- All three printed-part workflows now expose the source and repaired meshes,
  slicer package/evidence/previews/profiles, immutable source report and exact
  simulated transfer receipt to their full profiles. A post-transfer engineer
  checkpoint pins every detailed geometry, orientation, tolerance and claim
  review before validation. Retained case 02's byte-identical source/repaired
  mesh can now fail the canonical gate with its targeted lineage finding.
  Printed/preparer/profile/approval/runtime regression: `78 passed in 26.52s`,
  plus the receipt-output continuation test; Ruff passed.
- All three Raspberry Pi enclosure workflows now expose the exact manufacturer
  research and reviewed basis values, authored CAD source, both enclosure/fluid/
  board/heat-source STEP sets, both CFD contracts, field archive and comparison
  to their full profiles. The existing design review pins every source, geometry,
  thermal, variant and claim-scope obligation. Retained convergence/heat-balance
  gaps and the case-02 height violation can now reach the canonical gate.
  Pi/preparer/profile/runtime regression: `48 passed in 22.68s`; Ruff passed.
- All three bracket workflows now expose the reviewed mechanical basis and final
  analysis values, baseline/revised STEP and mass/request files, and every exact
  coarse/fine displacement, stress, reaction and field-expansion receipt. A new
  post-analysis engineer checkpoint pins all review-required obligations before
  the terminal full-profile gate. Current missing-output attempts will therefore
  report their absent roles explicitly; recovered runs can be evaluated without
  changing the graph. Bracket/preparer/profile/runtime regression:
  `52 passed in 9.76s`; Ruff passed.
- All three sheet-metal workflows now expose installed-material and manufacturing-
  intent values, every native/check/STEP/DXF/screenshot part artifact, both exact
  simulated supplier receipts, the source-bound final manifest and engineering
  handoff to their full profiles. The supplier evidence is sealed through the
  enrolled same-run copy tool so the original eight HTML/text pairs remain within
  the compiler's 16-file retrieval limit. A final engineer checkpoint pins every
  review-required obligation before validation. The external-action receipt
  contract now permits distinct receipt port names, allowing both supplier gates
  in one canonical graph while continuation maps each verified receipt to its
  declared port. Sheet/profile/coverage/runtime regression: `62 passed in 12.50s`;
  Ruff passed.
- C012 capability qualification is complete. The complete independent reader and
  profile suite passed `100` checks in `34.87s`. It exercises valid and alternative
  geometry/data, targeted parseable defects, missing evidence, lineage/hash
  mismatches, boundary conditions, units and frames across all ten families.
  This qualifies the reusable checks; it does not create campaign pass credit.
- The resumed provider check used the exact registered campaign session and
  configured `openai-codex::gpt-5.6-sol` route. The API returned HTTP 503 with the
  explicit backend reason `The usage limit has been reached`. The preliminary
  newly-created-session probe failed earlier at workspace registration and is not
  treated as quota evidence. No workflow attempt or retry episode was consumed,
  and the pause sentinel was preserved.
- A second exact-route probe after the user indicated the session appeared usable
  again returned the same HTTP 503 usage-limit response at
  `2026-09-17T19:26:42Z`. This was a readiness check only: it created no workflow
  run, consumed no campaign attempt and left the pause sentinel intact.
- The queued current jig-01/heat-01 pilot manifest was audited again read-only at
  `2026-09-17T19:31:25Z`: 2/2 cases passed with zero warnings or failures. Exact
  source bytes, current grants and tool schemas, complete input bindings, required
  stages, declared output roles and absence of prior run records all reconcile.
- The combined campaign/preparer/runtime audit passed `219` checks in `67.26s`.
  It covers campaign evidence and retry semantics, every family preparer, profile
  coverage, validator execution/currentness, bounded rework, review continuation
  and shared reporting. The only warning was the known denied shared pytest cache;
  the private basetemp completed normally. C021 remains open for the final native
  gates and browser audit against actual resumed campaign evidence.
- C014 and C015 are complete based on the retained production-path demonstrations
  already audited in `completion.md`. The configured Hermes structured run sent a
  typed measured correction packet to its owning AI, produced a distinct corrected
  revision, rechecked the complete profile and released the consumer. The isolated
  AgentCAD jig run did the same through the MCP task path. Both retained runs used
  explicit bounded revision policies; the regression suite proves persisted budget,
  exhaustion, no-progress, wrong-owner, invalidation and resume behavior. These
  records satisfy the mechanism and safety work without consuming another provider
  turn. C016 remains open for a current 30-case campaign instance.
- Twenty-seven fresh current cases are now instantiated, source-bound and enrolled
  without dispatch: 24 cases across heat, bracket, jig, harness, Pi, robot, PCB and
  sheet metal, plus the three Modelica cases. The combined queue is
  `.local-run/feature-081-live/campaign-execution/validator-campaign-082/current-ready-27.json`.
  Its read-only preflight reports 24 pass, three review and zero fail; the three
  Modelica reviews are the preserved conservative warnings for provider-generated
  `scenario.json` files sharing an input basename. There are no observed run records.
  The separate 24-case preflight passes 24/24 after the audit learned to read native
  and exported paths from the canonical CAD adapter contract. The focused audit test
  passes 3/3 and Ruff passes. The pause sentinel remains present, the dashboard still
  returns HTTP 200, and no Sol readiness probe or workflow attempt was consumed.
- Printed-part attempts remain intentionally unstaged until dispatch is viable. Their
  qualified Blender repair binding is lifecycle-owned and attempt-specific, so it
  should be launched just in time and cleaned up after terminal execution rather than
  kept alive through the provider quota window. Current campaign credit remains
  historical `30/30/24/0` and current `0/0/0`; enrollment alone earns no credit.
- The retained CalculiX container was found stopped, which exactly explained the
  registered server's `Child MCP transport closed` state. Restarting that same owned
  container and reactivating the same registration restored all eight tools. A direct
  MCP diagnostic then hashed the retained bracket-03 attempt-012 baseline STEP and
  passed an ephemeral 3 mm mesh plus all eight sealed fixture/load selections. Evidence
  is `.local-run/feature-081-live/campaign-execution/calculix-recovery-082.json`;
  no solve, durable CalculiX run or campaign dispatch occurred. The 27-case preflight
  was rerun afterward with the same 24 pass, three review and zero fail result.
- Solid Edge was not replayed. The current `CadMcp.Provider.SolidEdge.dll` SHA-256 is
  exactly the one recorded by both retained sheet-02 flange probes, and both already
  ended in the same non-retryable `E_POINTER` result with terminal cleanup. There is
  therefore no documented material fix to justify a successor native attempt under
  C019. The server being active proves discovery only, not flange recovery.
- The first post-quota canonical pilot is now fixed as robot-tracking-01 attempt-006,
  extracted from the enrolled 27-case queue at
  `.local-run/feature-081-live/campaign-execution/validator-campaign-082/pilot-robot01-attempt006.json`.
  Its fresh read-only preflight passes 1/1 with zero warnings, failures or prior run
  records. This case exercises the full validator/review path with deterministic local
  robot tools before spending native CAD retry budget. It has not been dispatched.
- A generic just-in-time printed-case wrapper now exists at
  `.local-run/feature-081-live/campaign-execution/run-validator-082-printed-case.py`.
  It requires the configured Sol model, launches the existing lifecycle-owned guarded
  Blender and fixed repair endpoints, calls the canonical preparer and existing campaign
  runner, requires exact preflight and always performs terminal lifecycle cleanup. Its
  syntax and CLI contract pass; it has not launched Blender or a workflow.
- The remaining enrolled queue is partitioned into immutable serial waves at
  `.local-run/feature-081-live/campaign-execution/validator-campaign-082/execution-waves.json`:
  the one-case pilot, eight structured cases, nine established-native cases, six
  recovered/complex-native cases and three quarantined Solid Edge cases. The union
  covers all 27 enrolled scenarios exactly once. Independent preflights report
  pilot `1/1` pass, structured `5 pass/3 review/0 fail` (the three known Modelica
  basename reviews), established native `9/9` pass, recovered/complex native `6/6`
  pass and quarantined sheet metal `3/3` static pass. Static readiness does not lift
  the sheet-metal native hold. All 27 exact grants are present; their earliest expiry
  is `2026-09-24T19:45:26Z`, five days after the recorded Sol reset. The consolidated
  receipt is `execution-waves-readiness.json`; dispatch count remains zero.
- The pilot's human-review contract is frozen before execution at
  `.local-run/feature-081-live/campaign-execution/validator-campaign-082/pilot-robot01-review-requirements.json`.
  It pins the bound workflow, pilot manifest, full-profile and baseline references,
  validator subjects, review checkpoint and the three exact review requirements:
  `ROBOT01-PLOTS`, `ROBOT01-DIAGNOSIS` and `ROBOT01-ACTION-SCOPE`. Generator
  assertions prove the checkpoint set equals every `review_required` baseline
  requirement and that the profile's review checks cover the same set. The receipt
  records no reviewer or assessment and explicitly denies validator-pass credit from
  the integration-test actor. No approval, workflow attempt or campaign count changed.
- The same review-contract audit now covers every enrolled case at
  `.local-run/feature-081-live/campaign-execution/validator-campaign-082/current-ready-27-review-catalog.json`.
  All 27 bound workflows have exactly one full-profile validator and one matching
  validation-review checkpoint. Their pinned profile and baseline references reconcile,
  every checkpoint names exactly the profile's `review_required` requirement set, and
  the review checks cover all 146 source-backed obligations with zero assertion failures.
  Every entry remains `awaiting_output_and_human_review`, with no reviewer, assessment or
  validator-pass credit. The three printed cases will receive the same audit after their
  lifecycle-owned workflows are prepared just in time.
- The serial runner now treats any checkpoint carrying `validation_review` as an
  unconditional human boundary, even when both the enrolled grant and dashboard prefer
  automatic integration-test approvals. Ordinary test-only checkpoints remain automatic;
  the requirements review persists `validation_review_requires_human` and performs no
  decision mutation until a person acts. This prevents an `integration_test:*` actor from
  consuming the one-shot checkpoint that the validator must authenticate. The complete
  runner suite passes `36` tests and Ruff passes. The dashboard preference is restored to
  `auto`; the final review guard is enforced by the runner. The served workspace is healthy
  at `http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical`.
  At a pending validation review, the person decides in that UI; while the campaign runner
  owns the attempt, the person must leave the separate Resume button to the runner so its
  persisted one-shot operation ledger remains authoritative.
- The post-reset transition is now encoded in the local, campaign-specific launcher
  `.local-run/feature-081-live/campaign-execution/run-validator-082-pilot.py`. Its
  `readiness` action refuses to issue a request before `2026-09-19T11:09:44Z`, permits
  only one POST to the exact registered session, requires the configured
  `openai-codex::gpt-5.6-sol` route and an exact `READY` response, and records even an
  unsuccessful or uncertain attempt so it cannot be silently replayed. Its `pilot`
  action requires that successful receipt, pins the pilot manifest and both human-review
  contracts by SHA-256, preserves the global pause sentinel, reruns the read-only
  preflight, requires one pass with no prior run, and invokes the persistent runner for
  only robot-tracking-01 attempt-006 with the shared retry ledger. The launch deliberately
  omits `--pause-after-current` because its immutable manifest has exactly one case; the
  global sentinel remains in place for every broader queue. Syntax and the read-only
  `status` action pass. A deliberate pre-reset `readiness` invocation was rejected before
  receipt creation or any POST. At `2026-09-17T20:42:25Z`, the service still reported the
  exact Sol model, the pause sentinel was present, and no readiness, pilot state or worker
  receipt existed.
- A pre-dispatch credit audit found and fixed a stale activation boundary: the campaign
  inventory still exposed the two original bounded profiles as its primary credit scope,
  even though all 30 prepared workflows already bind the qualified full profiles. The
  reproducible coverage builder now activates all 30 full-profile references and their
  exact baselines, 315 mandatory requirement IDs and 304 bound subject roles while
  retaining the two original bounded profiles as historical `bounded_profile` metadata.
  Candidate success is still separate: a row earns no fourth-counter credit without
  current exact outputs, authenticated reviews and a passing immutable assessment.
- The read-only batch preflight now fails any enrolled source that lacks exactly one
  process validator or whose validator profile, baseline or complete subject-role set
  differs from the declared campaign-credit scope. The fresh 27-case audit has one exact
  full-profile validator per workflow, with `24 pass / 3 review / 0 fail`; the reviews are
  the same conservative Modelica basename warnings. Coverage/campaign/preflight tests pass
  `54` checks, the installed-wheel/offline distribution checks pass `2`, the affected
  heat/printed preparer checks pass `9`, and Ruff passes. After an owned dashboard
  restart, its API reports
  `30 qualified / 30 full scope / 0 unsupported`, while actual counters remain historical
  `30/30/24/0` and current `0/0/0`. The read-only browser audit passes 30 rows, 30 input
  images, four update-driven series, 17,971 history points, narrow layout and zero browser
  errors. No provider request or workflow attempt was consumed.
- C022 now has a fail-closed completion auditor at
  `scripts/audit_engineering_campaign_completion.py`. It writes one 30-row JSON
  reconciliation and a matching readable Markdown report, and cannot return complete
  unless historical and current counters reach target, coverage remains 30 qualified/full
  scope, every selected attempt matches the current dataset/template, every required step
  and output identity is complete, every immutable assessment is current/full-scope/pass,
  every selected output was rehashed in a current full audit, and campaign ingestion has
  no issues. Four focused controls cover a complete case, missing current run, failed
  assessment/incremental scan and stale dataset identity; all pass and Ruff passes. The
  present reports are `artifacts/engineering-workflow-datasets/completion-audit-current.json`
  and `.md`. They correctly report `0/30` passing rows: all 30 still lack a current run,
  current output, full-scope assessment and final byte audit. The global state remains
  incomplete at historical `30/30/24/0` and current `0/0/0`.
- The normal workflow approval panel now recognizes `local_review` as the validator's
  human requirements checkpoint. It presents the pinned profile ID, version and digest,
  lists every exact requirement ID in the decision, explains that the decision becomes
  validator evidence for the immutable subject, and tells reviewers to leave resume to
  the campaign runner when it owns the attempt. Malformed local-review subjects show a
  blocking warning and cannot be approved from the panel; generic external-action behavior
  remains unchanged. The full editor component suite passes `43/43`, the production web
  build passes, and ESLint reports no errors (nine unrelated existing hook warnings). A
  served Chromium check entered an ordinary workspace, clicked its Workflows control,
  ran a mocked `awaiting_approval` result and verified the exact requirements-review panel
  on an isolated feature-enabled Vite server. The already-running server on port 5173 did
  not have the canonical recovery feature enabled, so it was left untouched rather than
  treated as evidence. The real checklist remains to be observed against the post-reset
  pilot checkpoint before broader dispatch.
- The post-review runner handoff is now covered directly. A persisted attempt stopped at
  `validation_review_requires_human` was given an authenticated human-approved checkpoint;
  the runner issued exactly one ledger-owned resume, did not auto-decide, did not create a
  second run and reached the existing completion record. The full runner suite passes
  `37/37` and Ruff passes. The local pilot launcher also has a guarded `resume` action for
  the case where its two-hour observation window expires before the person decides. It
  requires the original worker to be terminal, the exact persisted attempt to remain at a
  clean manual-review boundary, no prior resume operation/receipt, the exact checkpoint to
  be human-approved, the configured Sol route and the frozen manifest/review hashes. Its
  SHA-256 is `f39094ecddc8b7e667757ec0d280ffdba68ae067472d3d689e118211d2a703ee`;
  syntax and Ruff pass, `status` remains read-only, and an early `resume` refused before
  any receipt or mutation because no readiness/pilot state exists.
- A validation-review checkpoint now carries the exact human-readable requirement text,
  content/design scope and every pinned source artifact, locator and SHA-256 alongside its
  existing profile reference and requirement IDs. The runner derives this projection from
  the exact packaged or workspace profile used by the workflow's validator; it refuses to
  create the checkpoint when the profile cannot be resolved or the configured IDs differ
  from the complete `review_required` set. The projection is inside the immutable approval
  subject, so changing requirement text or source identity makes the approval stale on
  resume. The Workflows approval panel requires and renders those details before enabling
  approval. Backend approval/continuation regressions pass `79/79`, the editor component
  suite passes `43/43`, the production build passes, Ruff and `git diff --check` pass, and
  the two served Chromium process-validation journeys pass through the normal Workflows
  entry. A read-only rehearsal compiled the frozen robot-tracking-01 attempt-006 source
  (`b382fd863bb3483d0b917cc9ee65bcc4e656336085394a0d439b0496a4c3fbaf`) from its
  real campaign workspace and reproduced the exact three requirement projections in the
  frozen review package for `ROBOT01-ACTION-SCOPE`, `ROBOT01-DIAGNOSIS` and
  `ROBOT01-PLOTS`. No provider request, workflow attempt, campaign count or existing
  receipt changed.
- The owned API was restarted from commit `360dcd444a76cf65e1ed453b4b3c2889dffcca2e`
  so the post-reset pilot will execute the current validation-review projection. The first
  launcher wait ended at its 90-second bound while startup continued; PID `45172` then
  became healthy and an idempotent rerun restored the qualified AgentCAD bootstrap with
  SHA-256 `ad166be75f44977ed862c37c3b831002cf6e2ad3eed0f6d3dcc6409237a9e994`.
  Both the API and dashboard return HTTP 200.
- That deployment exposed 12 stale AgentCAD grant pins across the three heat, bracket,
  jig and Pi cases. The first guarded repair stopped before manifest promotion and was
  rolled back; its one partially written jig source was restored to the exact prior bytes.
  The second byte-exact, append-only repair enrolled 12 replacement grants while retaining
  all 12 old grants as active. It changed only AgentCAD schema authorities and the embedded
  `agentcad__run` pin in six unrun jig/Pi sources, with all six prior source files retained
  as digest-verified backups. The promoted 27-case manifest SHA-256 is
  `1075e709d790ee7c6e4e08b2d1b70cf2f91600b6913c906e4878e45508a252f6`; the reconciled
  review catalog SHA-256 is
  `91d4f1a5f12c7045fc79ec008826b10587d2e605d72fdf59804152e907537652`.
- A fresh independent audit verifies all 27 bound workflow hashes, all six source backups,
  both active 12-grant sets and all 11 qualified AgentCAD tools. The final full preflight is
  `24 pass / 3 review / 0 fail` (SHA-256
  `a575ccd9170d33e83c7471d0dfcbd5de48c9473e40afcfe6034c2520330847f7`); the frozen robot
  pilot is `1/1` pass (SHA-256
  `4c97f85ffacbd06406ecda9d9695ff59cd2f5f654949f15f40f1f400168fa712`).
  Neither audit found an observed run. The exact Sol model and pause sentinel remain in
  place, historical/current counters remain `30/30/24/0` and `0/0/0`, and no readiness,
  pilot-state, worker or resume receipt exists. The updated guarded launcher SHA-256 is
  `b838916c3e93056fddc7087b8a26143c23d56f0d5adc497f272bbeebaffda28d`.

## Next action

On the user's request, ran validator-only inspection of all 24 retained complete
output sets using the exact currently packaged full profiles (no removed checks or
review requirements). Reports are in
`artifacts/process-validation/retained-24-20260917T222248Z/summary.md`, with per-case
report JSON, Markdown, RTM CSV, isolated assessment databases and hashed byte copies.
Thirteen cases pass every automated check; nine have automated failures and two have
only automated evidence blockers. Every case still requires human review. Failures
are harness voltage-drop numeric evidence (all three), identical printed-02 source/
repaired meshes, Pi-02 enclosure height, robot-02 gap records, and missing water-heater
kit ID/version (all three). All three Pi cases lack convergence and heat-balance
evidence. These detached assessments inspect retained bytes and do not claim original
producer authority or current-generation campaign credit. No inference, generation,
native replay, approval or campaign-counter mutation occurred. Driver:
`.local-run/feature-081-live/campaign-execution/validate-retained-24.py`.

A subsequent isolated-successor pass corrected the two deterministic producer
defects without changing any frozen requirement or validator threshold. Robot-02's
gap record is recomputed from its retained timeline with tolerance-aware boundary
comparison, so the two floating-point representations of exact 0.5-second intervals
are no longer false gaps. The Modelica study summarizer now emits
`wright-water-heater-v1@0.1.0` from the same constants used to authenticate every
native run; the three retained successor summaries add that identity only after
checking every referenced native `run.json`, manifest digest and result digest.
The exact full profiles now report **17 automated passes, 5 failures and 2
blocked-only cases** across the 24 complete output sets. Reports and isolated byte
copies are in
`artifacts/process-validation/retained-successors-20260917T225954Z/summary.md`.
The dashboard pointer now selects that result, so the existing fourth card and chart
show `17/30`; full current approvals remain `0/30` and campaign credit remains
unchanged. The same report directory contains `correction-manifest.json` for all 11
originally affected cases (4 resolved, 7 needing new output) and
`human-review-queue.json` (17 ready, 7 waiting for correction). No historical output
was mutated and no human approval was inferred. The read-only scan of all 72 retained
attempts found no alternate complete attempt that resolves the remaining findings.

The remaining output corrections are therefore bounded and explicit: all three
harness cases need a sourced or explicitly declared contact/splice-resistance basis
and recomputed total branch drops; printed-02 needs a genuinely distinct repaired
mesh followed by dependent slicing evidence; Pi-01 and Pi-03 need supported
steady-state convergence and field-derived heat balance for both alternatives; Pi-02
also needs enclosure B reduced to at most 60 mm and all dependent CAD/CFD outputs
regenerated. These seven cases must not receive automated-pass credit from edited
labels or weakened checks. The 17 automated-pass successors are ready for the normal
authenticated review checkpoints, but the detached review queue itself grants no
approval.

The CFD convergence path is now executable rather than a producer-supplied boolean.
The fixed Pi producer records the final five solver iterations, maximum initial and
final equation residuals, relative maximum-temperature change, fixed thresholds and
the exact solver-log digest. The `cfd-evidence` reader independently recomputes those
values from each archived log before accepting a convergence claim. Applying that
reader to the retained runs proves that every 300-iteration Pi solve is still
unsettled; their reports now return `cfd.convergence_failed` with the measured values
and a continue-solve action. Heat balance remains blocked because the retained fields
do not contain a complete field-derived external heat-flow balance. Future Pi runs now
derive `grad(T)`, archive per-face area, outward velocity, density, temperature,
normal temperature gradient, heat capacity and conductivity, and report the external
sensible-enthalpy-plus-conduction balance. The validator independently integrates that
CSV and rejects a mismatched summary or digest. The latest isolated report is
`artifacts/process-validation/retained-successors-20260917T233614Z/summary.md`:
**17 automated passes and 7 failed cases** among 24 complete output sets, with each Pi
case also retaining its heat-balance blocker. The dashboard pointer selects this
report; validator pass credit remains `17/30`, review credit remains `0/30`, and no
historical artifact or campaign counter was changed.

The new boundary-energy producer path is now qualified against an isolated copy of
the native Pi-01 variant-A OpenFOAM case. The first read exposed that the OpenFOAM
`polyMesh/boundary` header was being mistaken for a physical patch; the producer now
filters the `FoamFile` header and coupled `sampleRegion` interfaces before integrating
external faces. The corrected native extraction wrote 13,830 per-face observations.
It measured 6.0 W input and 0.0151271109 W net outward heat, for 0.997478815 relative
imbalance against the fixed 0.01 limit. The independent `cfd-evidence` reader reproduced
the heat flow to floating-point precision from the CSV, so this retained 300-iteration
case correctly fails instead of receiving convergence credit. Evidence is under
`artifacts/process-validation/cfd-boundary-energy-qualification-20260917/`; focused
producer/reader/profile tests pass 18 checks and Ruff passes. The dashboard API still
reconciles to the selected report with 24 complete outputs and 17 validator passes.
The campaign ledger now supports an explicit `update` event with an optional displayed
validator-pass count, so a material change that leaves all four counts unchanged still
adds one equally spaced chart step. The CFD qualification recorded update 17,972 at
`30/30/24/17`; the dashboard orders that event after the retained-result snapshot and
keeps the validator line flat at 17.

The harness producer now accepts contact and splice-port resistance only through a
closed `reviewed_engineering_assumption` record with positive bounded values and a
written basis. When present, independent verification counts every supply/return
termination, calculates contact/splice and copper drops separately, and reports the
total while preserving the production-measurement release hold. With no reviewed
record, resistance remains unknown and total drop remains unavailable; the current
three retained cases therefore remain failed rather than receiving invented values.

The authority refresh also required successor execution waves: the previous wave plan
still contained the original 12 AgentCAD grants. Use the local
`validator-campaign-082/execution-waves-authority-refreshed.json` (SHA-256
`0d9542191c6b90b85a68e9bf7f2356aba27e3940944b0e4b363f43dbda5a3a6f`)
instead of `execution-waves.json` for subsequent batches. Its union matches all 27
current manifest cases exactly once. Only source and integration-policy digests differ
for 12 cases in two successor wave manifests; ordering, pilot, printing lifecycle and
Solid Edge quarantine gates are preserved. Independent read-only preflights pass 9/9
for refreshed wave 02 and 6/6 for refreshed wave 03, with zero warnings, failures or
observed runs. Original wave manifests, plan and readiness evidence remain intact.

C016–C018: after the recorded reset window, run the launcher's `readiness` action once.
If its receipt is successful, run its `pilot` action and inspect robot-tracking-01's human
review plus full-profile assessment before expanding the queue, using the frozen pilot
receipt and 27-case catalog as the exact checklist. Then launch/enroll/run the three
attempt-017 printed cases one at a time with
the lifecycle wrapper, and resume the remaining audited queue serially without resetting
the retry ledger. Use the recovered CalculiX registration for fresh bracket runs. Keep
the sheet-metal flange episode quarantined until an actual provider repair is identified
and passes a focused owned diagnostic.
