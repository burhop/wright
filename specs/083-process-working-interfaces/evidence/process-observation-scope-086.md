# Distinguish tool observations from process success

10 October 2026. Shared product repair; presentation-deck work remains excluded.

## User problem and repair

A tool can report completion without producing the file the process requires.
In the reproduced case, the runtime correctly failed with
`WORKFLOW_OUTPUT_INVALID` and held the next step, but the progress panel also
said **Process completed**. It used the overall process label for an individual
observation. The contradictory messages made it hard to understand why no result
was available.

The shared `ProgressPanel` now labels each observation **Observed state** and
shows its **Reported by** binding. The overall process status remains separate.
Provider activity, timestamps, staleness, operation identity and backend action
permissions are preserved. No executor, authority, model policy, vendor behavior
or public contract was added or changed.

The repair is in `packages/ui_kit/src/patterns.tsx`, with focused regressions in
`apps/web/src/components/common/ProcessUIKit.spec.tsx`. The common working view
is served in build45 on UI5250. Existing published tailored-interface bundles
were not rebuilt; future builds consume the repaired kit. Previously accepted
bundles retain their identities and the common view remains available.

## Evidence and boundaries

Two labelled software fixtures use snapshots captured from the actual runtime:

- A simulated provider reports completion but omits `inspection.json`. The
  runtime fails, the dependent consumer never runs, and the UI identifies the
  missing file without calling the process completed.
- A cancellation request is durable, but the observer is lost and the provider
  still reports working. Submission and cancellation each occur once; the UI
  retains **Needs reconciliation**, the unconfirmed outcome and disabled actions.

Browser fixtures intercept only their exact snapshot/event reads and remap only
the presentation process context to newly accepted, labelled source copies.
They are not live engineering jobs or saved production runs. Their synthetic
run IDs must not be presented as real saved-run links. No physical cancellation
or arbitrary provider interruption is certified.

| Evidence | Outcome |
| --- | --- |
| [Before the repair](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-217-missing-output-before-fix/report.html) | The strengthened assertion reproduces the contradictory completion label. |
| [Missing required output](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-221-missing-output-final/report.html) | Five final served-browser steps pass; specific diagnostic, separate observation and unavailable actions survive reload. |
| [Unconfirmed cancellation](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-222-cancellation-unknown-final/report.html) | Five final steps pass; no inferred stop, continuation or replay. |
| [Retained wheel results](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-223-wheel-progress-final/report.html) | Six read-only steps pass, including historical failed checks and an exact assessment download. |
| [Retained thermal results](D:/repos/wright/artifacts/ui-walkthrough/mechanical-engineering/20261010-224-thermal-progress-final/report.html) | Five read-only steps pass; exact assessment download and engineering hold remain intact. |
| [Final audit](D:/repos/wright/.local-run/process-interfaces-083/mechanical-engineering-20261008/observation-scope-audit-086.json) | 159 affected tests, type checking, production build and 21 final browser steps pass. Served assets match build45. |

Initial narrow browser assertions passed despite the visible contradiction;
visual inspection found it and the stronger pre-fix assertion failed. All four
new component cases also failed before the repair. An initial fixture declaration
used the wrong output-port type and stopped before execution; the corrected
fixture uses the required workspace-file port. These attempts remain recorded.
Earlier and final walkthrough artifact structures were checked separately.

All 54 previous run records, 64 full-wheel outputs, 28 correction/source files
and both original engineering sources remain unchanged. API8067 was not
restarted. UI5250 now serves build45; no native application was launched or
closed, and the existing Solid Edge process was left untouched. No model call,
engineering execution, review, physical action or presentation task occurred.

## Remaining work

Served-browser coverage for a nonempty malformed provider output remains open;
the current backend mapping covers it separately. Final fresh engineering
journeys after the last product change, the original dock deliverables and the
reviewed swim-lane integration also remain incomplete. This checkpoint is a
verified shared repair, not full-goal completion or user acceptance.
