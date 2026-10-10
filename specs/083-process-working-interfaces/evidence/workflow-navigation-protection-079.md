# Keep workflow edits when leaving the workspace — 10 October 2026

## User outcome

Wright now asks **Keep editing** or **Discard changes and leave** before an
in-app navigation would discard unsaved workflow edits. The dialog identifies
each affected workflow, including background tabs. Keep editing leaves the
editor mounted with its draft intact. Saving allows normal departure. Switching
tabs, results or working views within the same workspace remains available.

The original browser reproduction showed **Back to Dashboard** silently leaving
the editor despite its unsaved state. The earlier tab-close repair did not cover
route navigation. This repair connects the existing tab dirty state to React
Router's navigation blocker and reuses Wright's confirmation dialog.

The app now initializes React Router's browser/hash data router once at its entry
point, retaining its existing routes, providers and workspace surfaces. The
blocker handles both navigation links and router-owned browser history. It does
not intercept history manually or add a draft store, executor or state authority.
A pending save completing while the dialog is open clears the obsolete choice;
save completion does not initiate navigation by itself.

## Verification

- [Original failure](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-192-workspace-departure-before/report.html):
  a new isolated blank workflow loses its unsaved name when leaving for the dashboard.
- [Repaired user journey](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-193-workspace-departure-repaired/report.html):
  ten steps cover create/edit, departure choice, keep, save/leave, dashboard-card
  reopen, browser Back, explicit discard, and reopening the unchanged saved version.
- [Two isolated example copies](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-194-isolated-workflow-departure/report.html):
  six steps check the same protection on the existing mechanical and thermal
  definitions copied through Wright's source-only copy endpoint. Temporary edits
  were discarded. Both copies remain byte-identical to their original sources.
  This is authoring regression evidence; no new engineering execution is claimed.
- 168 affected tests pass, with no skips. New checks cover cancelled navigation,
  exact cross-workspace destinations, multiple/background dirty workflows, same-
  workspace query navigation, browser history, clean workflows, pending-save
  resolution and desktop hash routing. Existing editor, tab and workspace tests pass.
- Type checking and production build39 pass. The served HTML and three entry
  assets match that build. Browser diagnostics are empty, report validators pass,
  and raw dialog screenshots were visually inspected.
- All 54 prior run records, 64 latest wheel outputs and both original engineering
  definitions remain byte-identical. The API remains on8067/PID84296; UI5250/
  PID95944 serves build39. No CAD application was launched; the pre-existing
  Solid Edge PID22448 was left untouched. Vite's existing large-chunk advisory remains.

Automatic approval review rejected the proposed browser check on existing
engineering definitions because of the preservation boundary. That action did
not execute. The approved safer check created fresh source-only copies and
operated exclusively on those copies. No run, input response, review or authority
was copied or submitted. Two separate blank test workflows were created for the
before/after reproduction. No engineering output or original source was modified.

Private receipt: `.local-run/process-interfaces-083/mechanical-engineering-20261008/navigation-audit-079.json`.
It records exact source/build hashes, preserved subjects and test results.

## Try it and remaining limits

Open the isolated [Wright workspace](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5).
Create a blank workflow, change its name, then click **Back to Dashboard**.
Choose **Keep editing**, save it, and return to the dashboard. Reopen the workspace
to check the saved name. A later temporary edit should be discarded only after
the explicit discard choice.

Cross-workspace navigation and a completing pending save have component/router
coverage; dashboard departure and browser Back have live browser coverage.
The existing full-page unload warning retains its event-level tests. A live
reload check, closing during an actual in-flight save, arbitrary crash recovery
and autosave are outside this verification claim. No backend execution,
instruction, validation, permission or recovery semantics changed. The overall
goal remains incomplete; slide-deck work remains deferred.
