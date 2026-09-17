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
- C009/C010 in progress: 27 source-hashed packaged baselines are frozen for all
  heat-spreader, drill-jig, robot-tracking, water-heater, fan-harness, printed-part,
  PCB, bracket and enclosure cases. They contain 288 atomic mandatory requirements, preserve
  the Modelica selected-kit amendment, validate against the closed runtime
  `Baseline` model, and are reproducible from the reviewed definitions. Baseline
  checks remain green; the initial baseline/distribution check passed 6 tests.

## Next action

C009: freeze the remaining three source-linked sheet-metal baselines, then rerun
baseline/distribution checks for all 30.
