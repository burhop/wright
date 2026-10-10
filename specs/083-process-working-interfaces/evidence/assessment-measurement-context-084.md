# Measurement context and review obligations

10 October 2026. A shared report repair under the active engineering usability
goal. The preceding083 turn made verified progress; this turn also makes a
product change. The full goal remains incomplete. Slide-deck work is excluded.

## What an engineer can now see

Each requirement/check in the common assessment reader now shows:

- The recorded numerical uncertainty allowance, using the observation's unit
  and datum frame.
- Whether the pinned requirement calls for review, independently of its check
  state or the runtime's permitted review actions.
- An explicit missing-measurement or non-numeric label when an uncertainty
  allowance is not applicable.

The report explains that zero can be a default and does not establish zero
measurement error or physical accuracy. It does not invent an uncertainty estimate,
convert units for display, change a tolerance or evaluate a new verdict.

This fixes the gap recorded in074: those facts existed in the assessment but
were omitted from the readable view and matrix export. Browser212 and six failing
regression cases reproduced the omission before the repair.

The existing report owner joins recorded check measurement IDs to their immutable
measurements. The shared reader and authenticated exports consume that projection.
No provider, workflow source, model instruction, execution policy, review authority,
JSON schema or scoped-client contract changes. UI build43 continues to consume the
same Markdown preview; existing artifact membership/hash/currentness checks remain.

## Export compatibility

CSV appends `review_required`, `measurement_uncertainties` and `uncertainty_note`.
The measurement list retains identity, allowance, observed unit/frame and an
explicit numeric flag in observation order. Markdown exports add the same review
and allowance context. Consume CSV columns by header; consumers that require a
fixed column count will need to accept the documented additive columns.

Stored assessments and historical exports remain unchanged. New JSON exports
retain the existing contract and original assessment; live currentness timestamps
remain observations at the time of export. The report-consumer contract and
operator documentation describe these semantics.

## Verified behavior

- 69 affected tests pass, including seven new context cases: zero/nonzero
  allowances, pass/inconclusive/fail, missing reader, non-numeric observation,
  centimetre observation against a millimetre requirement, and datum preservation.
  The existing preview identity, escaping, report/export and precision tests pass.
- [Thermal working view](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-213-measurement-context-thermal/report.html):
  five steps at1159×900; allowance, review obligation, original HOLD and exact
  assessment download are visible through normal workspace entry.
- [Mechanical working view](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-214-measurement-context-wheel/report.html):
  six steps at1600×900; current corrected evidence and the original failed attempt
  retain their values and outcomes. The pending process review is unanswered.
- Both final browser records have no diagnostics, exact original JSON downloads,
  and valid walkthrough structures. Their raw measurement screenshots were
  visually inspected. The before-repair recording212 remains a recorded failure.
- Seven existing assessments were exported in three formats through authenticated
  GET requests. Every one of the117 rows preserves every old CSV column, and
  its new context matches its original pinned requirement and measurement IDs.
  These are117 traceability rows, not117 independent requirements or tests.
- All54 prior runs,64 latest full-wheel outputs,28 correction evidence/source
  files, both original example sources and all21 original074 exports retain their
  recorded hashes. No new engineering run, revalidation, model/CAD operation,
  answer, review, continuation or external action occurred.

The verified idle API was reloaded once: launcher PID93572 on8067. Its first
50-second readiness observation expired, but the same live process progressed
through startup and reported serving; it was not restarted again. UI5250/PID69612
still serves verified build43. The existing Solid Edge applicationPID22448 was
untouched; no FreeCAD or Blender session was started. Startup delay remains a
separate observation, not proof of an execution/recovery defect.

## Reusable evidence and remaining scope

New exact exports are under
`artifacts/process-interfaces/083/20261010-engineering-measurement-context/`.
For example:

- [Thermal matrix](../../../artifacts/process-interfaces/083/20261010-engineering-measurement-context/thermal/assessment-dbd4b81f5ded489e8dc3649c1a501e6e/report.csv).
- [Native wheel matrix](../../../artifacts/process-interfaces/083/20261010-engineering-measurement-context/wheel/assessment-83845361b5f24512b3e48405f8da8ece/report.csv).
- [Export manifest](../../../artifacts/process-interfaces/083/20261010-engineering-measurement-context/export-manifest.json).

Private local control receipts are in
`D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/`:
`measurement-context-audit-084.json`,
`engineering-measurement-context-export-084.json`,
`tests/measurement-context-084-final.xml`, and the API preflight/restart receipts.
The preserved failing test report is `tests/measurement-context-084-before.xml`.

This closes the specific reporting omissions, not completeness of all original
engineering requirements or physical accuracy. The dock conflict/native package,
actual reviewed swim-lane implementation, remaining requirement-to-test mapping,
final affected regression and concise user-testing handoff remain unfinished.
Further independent work should finish that mapping and handoff, adding tests
only where required coverage is genuinely missing. Do not rerun completed native
engineering work merely to increase counts.
