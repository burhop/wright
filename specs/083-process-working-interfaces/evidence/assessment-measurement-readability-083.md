# Readable engineering measurements

10 October 2026. Shared Wright product repair under the active mechanical usability
goal. Presentation/deck work remains deferred. The full goal remains incomplete.

## User problem and change

The common assessment reader showed long numerical tails such as
`41.6666666665829 degC` and `5.600000000000236 mm`. This obscured comparison with
the adjacent requirement. Walkthrough 206 reproduced the thermal case through
the ordinary workspace entry before the change.

The existing backend readable report projection now uses up to six significant
digits for passed numeric range/within observations with matching units and
frames. A changed display is explicitly marked `≈`. The requirement, tolerance,
units, frame, recorded check state and assessment currentness remain unchanged.
Failed, blocked, inconclusive and other nonpassing observations retain full
precision. A display that would land on or cross a configured limit also retains
full precision. This is presentation logic; it does not evaluate compliance.

The existing **Exact assessment record** disclosure and **Download exact file**
keep the original measurement available. JSON, Markdown and CSV exports retain
their existing exact representation. No assessment is rewritten.

Ownership stays with `process_validation.reporting.render_readable_markdown`;
the existing scoped artifact preview and shared reader consume the same report.
There is no new UI contract, executor, vendor branch or model instruction.
Existing result membership, hash, run/workspace identity and currentness checks
remain authoritative. No reader capability or accepted workflow is changed.
UI build 43 remains compatible because the same Markdown preview is returned.

## Verification

- 62 affected tests pass, including 38 new precision cases. Coverage includes
  small/large/negative values, nonnumeric values, finite-number handling, exact
  equality, near-limit cases, mismatched units/frames, nonpassing observations,
  original assessment persistence and unchanged export bytes.
- [Mechanical reader: six steps](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-210-measurement-precision-wheel-verified/report.html):
  corrected drawing value displays `≈ 5.6 mm`; original failed attempt retains
  `5.200000000000176 mm`, the original HOLD and its required correction.
- [Thermal reader: five steps](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-211-measurement-precision-thermal-verified/report.html):
  temperature displays `≈ 41.6667 degC`; the original human-review HOLD remains.
- Both exact downloads match their original files byte for byte. Browser
  diagnostics are empty. Raw compact-value and failed-finding screenshots were
  visually inspected. Both final walkthrough structures validate.
- All 54 retained run records, 64 latest full-wheel outputs, 28 correction
  evidence/source files and both original example sources match their earlier
  hashes. This is the stated preservation scope, not a whole-workspace claim.

The idle, goal-owned API was reloaded after verifying run/job state and its exact
process tree. API 8067 now uses launcher PID 69668; UI 5250/PID 69612 continues to
serve build 43 with matching HTML/assets. Only the existing Solid Edge application
PID 22448 remains among the inspected CAD applications; it was untouched. No
engineering application, model call, new engineering run, review, continuation,
cancellation, supplier action or physical operation was submitted.

## Retained failures and limits

The first test attempt had a missing required source reference in the new fixture
and an inaccessible sandbox temporary directory. A subsequent test expectation
incorrectly assumed rounding crossed a lower limit; it was corrected to an
actual upper-limit crossing. Those reports remain separate from the passing run.

Walkthrough 207 stopped at authentication preflight with HTTP 502 while the API
was starting. It has no fabricated screenshots or trace; its artifact validator
reports the missing image interaction. Walkthrough 208 passed four product steps
but the final recorder allowlist omitted the existing read-only navigation
endpoint. Walkthrough 209 used an exact text selector that did not match the
visible `Check:` label. Both recorder failures remain recorded; 210/211 use the
actual control and scoped navigation owner. These are not additional product
defects or evidence of engineering acceptance.

The correction study remains awaiting its original human review. The passing
digital assessment does not accept that review or prove physical performance.
Six display digits are not a statement of measurement uncertainty or capability.
No CAD rerun was necessary for this report-only change.

## Local receipts and continuation

Control directory:
`D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/`.

- `assessment-precision-audit-083.json`: verified files, exact downloads, tests,
  UI assets, service identities, request scope and application inventory.
- `tests/assessment-precision-083-verified.xml`: final affected test result.
- `assessment-precision-api-preflight-083.json` and
  `assessment-precision-api-restart-083.json`: isolated service reload.
- `prepare-precision-083.py` / `capture-precision-083.mjs`: repeatable browser
  procedure. Private authentication is loaded separately and is not in this report.

Next reconcile the goal-wide remaining acceptance rows with follow-ups 066–083
and produce a concise current user-testing handoff. Do not repeat green native
engineering runs for counts. The unresolved dock requirement and actual reviewed
swim-lane implementation remain separate unfinished obligations; deck production
is excluded by the user's priority decision.
