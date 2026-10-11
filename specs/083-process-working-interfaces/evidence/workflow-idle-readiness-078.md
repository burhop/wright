# Clear run status and setup guidance — 10 October 2026

## User problem and repair

The shared workflow editor used **Ready to run** as its default when no run
existed. It could therefore disagree with a warning in **Run readiness**. A
saved empty definition could also show **Authoring checks pass** because none of
the existing checks required a processing step.

Both collapsed and expanded Run details now say **Not started** for an idle
workflow. The expanded view has **View run readiness**, which opens and focuses
the existing setup panel. An empty workflow or one consisting solely of input
blocks receives explicit guidance to add a processing step and connect its inputs.
The existing backend remains responsible for preflight and permission to execute.
No runtime, provider protocol, model instruction or engineering criterion changed.

The change reuses `AuthoringRunReadiness` and `NativeRunPanel` in the canonical
editor. Run history loading, unavailable/unknown status, active work, reviews,
failures and completed runs retain their current state projections. The new
readiness link appears only in the idle panel.

## Evidence and user check

- [Before](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-190-idle-readiness-before/report.html):
  an existing isolated empty workflow reports **Ready to run** without having run.
- [After](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-191-idle-readiness-repaired/report.html):
  the same saved workflow reports **Not started**. Expanding Run details and
  clicking **View run readiness** exposes **Processing steps: None defined** and
  a specific next action. Three browser steps pass, diagnostics are empty, the
  screenshot was visually inspected, and the report validator passes.
- 154 affected tests pass across the editor, status observer, MCP discovery and
  workspace integration. Three new cases cover empty/configured idle workflows,
  focus/navigation to the existing readiness panel, and input-only definitions.
  The original two idle-state tests fail before the repair. These counts overlap
  prior suites and are not independent engineering demonstrations.
- Type checking and build38 pass. The served HTML and three entry assets match
  that build. API8067/PID84296 is unchanged; UI5250/PID66248 serves build38.
- Both browser checks only open the existing workspace/workflow. No workflow
  write, run, review or model request was submitted. All54 prior run records and
  64 latest wheel outputs remain byte-identical.

To check manually, open an existing workflow with no runs, expand **Run details**,
and click **View run readiness**. The run state should remain **Not started**;
the setup panel should describe the definition's actual authoring issues.
Passing authoring checks still does not certify live provider availability.

Private receipts under `.local-run/process-interfaces-083/mechanical-engineering-20261008/`:
`readiness-audit-078.json`, `ui-build-38.json`, and
`tests/readiness-{before,after,final}-078.xml`. The full revised goal and the
remaining product/engineering cases remain open.
