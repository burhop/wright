# Campaign continuation progress

**Updated:** 2026-09-17. **Branch:** `codex/082-output-content-validation`.
**Model:** `openai-codex::gpt-5.6-sol`; usage telemetry is unavailable. The fresh
gateway preflight is blocked by the provider usage limit, with retained reset
estimate `2026-09-19T11:09:44Z`. The runner pause remains in force.

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

## Next action

C012–C014: integrate the PCB workflows, then prove an actionable retained-output
defect through the canonical gate when the provider resumes.
