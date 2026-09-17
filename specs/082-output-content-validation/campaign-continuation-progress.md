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
  layout with no browser errors.

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
  validator coverage `2` bounded qualified, `0` full-scope, `28` unsupported.
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

## Next action

C010–C012: implement the next reusable three-case family profile, preserving the
robot and heat full profiles as implemented checkpoints until their review and
corrected-output evidence can qualify them.
