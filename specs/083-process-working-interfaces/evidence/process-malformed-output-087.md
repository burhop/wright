# A readable failure when a provider returns malformed data

10 October 2026. Shared Wright repair; no presentation-deck work.

## What a user can now understand

When an inspection provider returns a nonempty file that cannot be parsed, the
process stops at validation and retains the file and its assessment. The main
correction summary now shows each distinct explanation once. Previously, one
unreadable file caused the same sentence to appear twenty times in Progress.

The existing validation owner now removes exact duplicate explanations before
applying its existing twenty-item summary limit. Distinct explanations keep
their original order and wording. All individual checks, findings, selectors,
requirements, output identities and engineering holds remain in the complete
assessment. This changes the summary for future runs; earlier immutable run
diagnostics are not rewritten.

The change is confined to `process_validation/process.py`. It introduces no
executor, model policy, prompt, vendor branch or new interaction contract. The
canonical runner still decides whether downstream work can proceed; the UI
continues to display its diagnostic and permitted actions.

## Reproduction and verification

The runtime fixture uses the actual saved wheel inspection profile and a
simulated tool that succeeds after creating the incomplete JSON file
`inspection.json`. There is one tool invocation, no model call, twenty failed
checks with `output.invalid_json`, and no dependent consumer execution. All
twenty individual findings remain after the repair.

For the browser check, its actual runtime snapshot is captured and only its
presentation process context is bound to a newly accepted, labelled software
fixture source. Exact fixture snapshot/event reads are intercepted. No production
run exists for those synthetic IDs; this is not native CAD qualification or a
live engineering execution. Process mutations are forbidden during the walkthrough.

- [Before: twenty repeated corrections](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-225-malformed-output-before/report.html). The assertion fails on the repeated message; the original screenshot and trace are preserved.
- [After: one correction, retained failure and unavailable actions](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-226-malformed-output-after/report.html). Five served-browser steps pass, including workspace entry and reopening the same fixture state. Raw screenshots were visually inspected.
- [Final audit](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/malformed-audit-087.json). **82 affected tests pass**, including validation, mechanical handoffs, feedback, reporting and bounded rework. Ruff passes on the changed files. One focused regression failed before the repair.

Focused summary tests additionally preserve distinct reasons after many repeated
ones, first-seen order, the existing limit, exact wording and an empty summary.
The existing mechanical regression checks that the summary has one explanation
while the full assessment still contains twenty findings and holds its consumer.

Fixture preparation initially stopped on missing authoring fields, then an
incorrect port quantity, then a missing repository lookup in the test owner.
These setup attempts are preserved and are not product defects or successful
malformed-output tests. The final audit initially compared Windows CRLF fixture
bytes with the publisher's decoded submitted text; that audit comparison was
corrected. Before/after fixture source bytes are also checked identical.

## Served state and remaining scope

API8067 was reloaded once after confirming the goal-owned service was idle.
The same new process remained alive during initialization and became ready;
it was not restarted because the first observation expired. Its launcher PID is
26028. UI5250 remains build45/PID65072, with identical served assets. All54
previous run records,64 full-wheel outputs,28 correction files and the original
example sources remain unchanged. No native app was started or closed; the
unrelated Solid Edge process was left untouched.

This closes the missing malformed-output browser diagnostic case in its stated
software scope. Final fresh engineering journeys remain required. The user has
now authorized a **separate 130 mm shelf variant** for the dock; the original
75 mm design remains protected. Variant preparation and manufacturing checks
are next, followed by its actual deliverables. The reviewed swim-lane location
is still pending. The full goal remains active and PPT work stays excluded.
