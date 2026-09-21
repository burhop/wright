# Robot tracking plots for engineering review

The original overlay used equal physical axis scaling for several metres of
travel and a few millimetres of sideways deviation. That flattened the useful
information into a nearly unreadable line. It also omitted wheel odometry and
left the engineer to interpret labels such as `external` without explanation.

## Presentation contract

`scripts/robot_tracking_operations.py` now creates:

- `trajectory-overlay.svg` and a PNG companion: the intended route, external
  position measurement, and wheel-based estimate; a separate signed sideways
  error versus elapsed-time panel; units, event timing, peak values, RMS and
  interpretation limits. The path view explicitly warns that its axes are
  independently scaled and must not be read as a physical scale drawing.
- `alignment-comparison.svg` and PNG: the before/after coordinate comparison and
  applied spatial/clock correction, separate from the principal engineering view.
- `plot-guide.md`: how to read the lines, quantities, signs, gaps, and evidence.

The original external timeline columns and metric formulas are unchanged. Wheel
poses are read from the actual bag and compared with the intended heading at
each wheel timestamp, using the same bounded planned-path interpolation. Planned
and wheel frames must match the declared map frame; unknown frames fail rather
than producing a misleading comparison.

External line segments break at missing intervals. The time chart shades those
intervals without covering the continuing wheel estimate with a text label.
There is no smoothing, synthesized measurement, acceptance threshold, implied
hardware validation, or inferred failure cause. All three examples remain
explicitly synthetic. Peak and RMS are different quantities, and event timing
is not evidence of causation by itself.

The fresh-attempt preparer declares the extra alignment and guide files as real
outputs and directs the diagnosis to link and explain them. The existing
validation profile, requirements, tolerances, and human decision remain intact.
No saved workflow definition is rewritten by this change.

## Retained-attempt preview

`scripts/preview_robot_tracking_plot.py` reads a retained bag and alignment and
writes to a new, separate directory. It refuses existing output directories and
outputs nested under the source input/analysis directories. It records source
and output identities, checks the old timeline bytes and all pre-existing metric
values except implementation identity, and reports any mismatch without changing
the original files. These outputs are not registered campaign results or passes.

Example in the already selected offline robot container:

```text
/tmp/robot-env/bin/python /operations/preview_robot_tracking_plot.py
  --bag /workspace/campaign/robot-tracking-diagnosis-01/attempt-008/artifacts/converted/recording
  --alignment /workspace/campaign/robot-tracking-diagnosis-01/attempt-008/inputs/alignment.json
  --reference-analysis /workspace/campaign/robot-tracking-diagnosis-01/attempt-008/artifacts/analysis
  --output /tmp/<new-unique-preview-directory>
```

The command is shown on multiple lines for reading; supply the arguments as one
invocation or use the shell's continuation syntax. Do not restart or replace a
registered MCP process as part of previewing a plot.

## Verification and boundaries — 2026-09-21

- The standard-library test runner in the selected robot dependency environment
  runs `tests/test_robot_tracking_plot.py`: six tests, including real conversion,
  analysis and rendering of all three input packs. Tests check labels, actual
  millimetre series, missing-data segmentation, frame rejection, curved-path
  wheel residuals, clock correction, unchanged inputs, and overwrite refusal.
- Host regressions cover the preparer, manifest handoff, tracking reader/profile
  and dependency-free segmentation: 18 pass; three selected-dependency tests skip
  on the host and run in the container instead. No host plotting/ROS dependencies
  were installed and no public MCP catalog qualification is claimed.
- Visual previews are under `artifacts/robot-tracking-plot/20260921-r1/` and
  `20260921-r2/`. The first revision is retained; the second moves the dropout
  explanation outside the plotted data so the wheel trace stays visible.
- Robot 008's retained timeline bytes and all original metric values agree with
  the preview. Its original review, files, and approval state remain separate.
  A before/after SHA-256 comparison of all 29 files under attempt-008 found no
  changes. The final read-only runtime check still reports `awaiting_approval`,
  a pending decision with no actor, and a matching current source revision.
- The retained robot-02 attempt-004 comparison intentionally reports a mismatch:
  its historic metric record labels two floating-point roundoff intervals as
  gaps (`0.9999999999999999..1.5` and `15.999999999999998..16.5`). The already
  existing roundoff-safe interval function no longer reports them. Its timeline
  bytes and other original metrics agree. The failed equality receipt is retained
  in `20260921-r1/corner-check/preview-provenance.json`; it is not relabeled a pass.
- Robot-03 attempt-005 preserves the original timeline and metric values,
  including the external-measurement dropout. Its figures were visually checked.

The paused Robot 008 workflow still points to its original output. Replacing
that evidence requires a properly recorded correction/new output revision and
fresh review. This change does not approve, resume, re-enroll, or rerun the
campaign, change counters, or relax any engineering requirement.
# September 21: correction available in the workflow

Robot-01 attempt-009 is a preserved successor of attempt-008, authorized by the
user's request to carry the improved plots into the workflow. It is not an
approval or a replacement of the original receipt. All 29 original files and
the original pending decision remain unchanged. Fresh normalization, bag
inspection, measurement and diagnosis ran through the canonical workflow.

The saved successor is `workflows/validator-082-robot-tracking-diagnosis-01-attempt-009.workflow.wflow`.
Its engineering title is **Investigate cart tracking at a floor seam**. The new
diagnosis separates purpose, plot interpretation, measured findings, unknowns
and the next inexpensive test. Run details exposes hash-verified inline image
previews, full-size opening, findings/reading-guide documents, and collapsed
calculation records. A workflow-purpose section uses the authored description,
never a fabricated summary. This presentation applies to other review packages
without hardcoding Robot output paths.

The normal workspace walkthrough passed all 24 steps at 944 × 791 with no
console/page/HTTP errors. Two cancelled observer requests during navigation are
retained in diagnostics. The report and its structural validator passed:
`artifacts/ui-walkthrough/robot009-engineering-review/20260921-1802-01/report.html`.
This is browser verification, not user acceptance. Existing older-layout and
readiness notices remain; neither source nor layout was saved in the walkthrough.

**Execution blocker found during verification:** the AI-assisted MCP task path
does not apply `expected_file_ports` when publishing multiple generated files.
The direct-tool path does. The live validation ledger therefore lacks the
declared conversion-manifest, timeline, metrics and plot subjects. Attempt-008
must not be assumed healthy either. Do not backfill signed continuation evidence,
approve around this defect, or describe the downstream validation as completed.
Qualify a runtime binding repair and its safe continuation/successor policy
before resuming the saved run.

A separate full, unchanged-profile diagnostic evaluates the actual recorded
files without altering the live ledger: **25 automated checks pass**, while two
checks covering three requirements still require human judgment. The diagnostic
explicitly records the four missing canonical bindings and earns no campaign
credit. It also proves original metrics and timeline bytes unchanged. Evidence:
`artifacts/robot-tracking-plot/robot009-verification-20260921/verification.json`.

The owned observer was stopped at the idle human-review boundary (no active
operation), leaving the saved run paused. No human decision, resume, broader
campaign restart, push or merge occurred. The next implementation action is the
named-file output binding repair, not another request for the user's old review.
