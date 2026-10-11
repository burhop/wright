# Protect unsaved workflow edits — 10 October 2026

## User problem and repair

An engineer could edit a workflow and lose the changes by closing its workspace
tab. The editor displayed **Unsaved**, but its state did not reach the workspace
tab owner. Closing the tab unmounted the draft without a choice or recovery.

The existing editor's combined source, semantic, layout and proposal change state
now reaches the existing tab dirty flag through `WorkflowRecoveryPage`. The
workspace uses its existing confirmation dialog to offer **Keep editing** and
**Discard changes** before closing a changed workflow. Saving clears the flag;
clean tabs close normally. The tab also shows its existing unsaved indicator.
The page registers a browser unload guard while any workflow tab is dirty.

The dialog reuses Wright's tokens and keyboard handling. A visual check exposed
that its button styles previously depended on a surrounding native-process page;
the existing stylesheet now styles the dialog's buttons independently, including
visible keyboard focus. No executor, provider protocol, model instruction,
validation rule or review authority changed.

## Evidence

- [Original reproduction](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-185-unsaved-close-reproduction/report.html):
  create a new empty workflow, rename it without saving, close the tab; the draft
  disappears without a decision. Walkthrough 184 had an incorrect tab selector
  and is retained separately as a recorder failure.
- [Final user walkthrough](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-189-unsaved-close-keyboard/report.html):
  eight steps through the normal workspace, covering blank creation, edit, close
  choice, keyboard focus, keep, save/close, reopen, and deliberate discard/reopen.
  Browser diagnostics are empty. The dialog screenshot was visually inspected;
  the walkthrough structure validator passes.
- 142 affected tests pass, including the workspace, canonical workflow page,
  retained editor, passive entry, names and prior native editor confirmation.
  Five new cases cover keep/save/close, Escape/discard, inactive tab identity,
  browser unload events, and page-to-workspace change notification. The initial
  three regression cases fail against the original implementation. A subsequent
  new page test was corrected to await the loaded editor before interacting;
  its earlier failure remains recorded.
- Type checking and production build 37 pass. The served HTML and its three entry
  assets match build 37. API 8067/PID 84296 is unchanged; UI 5250/PID 95700 serves
  this build. The ordinary Vite large-chunk advisory remains.
- All 54 previous run records and 64 latest wheel outputs remain byte-identical.
  Six new blank test workflows were created across the retained walkthroughs.
  No engineering run, CAD application, review or external operation was started.

Walkthroughs 186/187 establish the behavior before the styling correction.
Walkthrough 188 incorrectly expected `:focus-visible` immediately after mouse
interaction; 189 uses actual keyboard navigation and verifies the focus ring.
These are repeated checks of one repaired behavior, not independent engineering
demonstrations. All earlier records remain intact.

Private receipts: `.local-run/process-interfaces-083/mechanical-engineering-20261008/`
contains `unsaved-workflow-audit-077.json`, `ui-build-37.json`, and
`tests/unsaved-{before,after,regression,final}-077.xml`.

## Manual check and remaining scope

Open the isolated workspace at `http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5`.
Click **Workflows**, rename the new workflow and press Enter. Close its tab:
**Keep editing** should retain the name; saving should then allow normal closure.
Reopen the saved file to see that name. A later unsaved edit should be discarded
only when **Discard changes** is chosen.

Browser unload is covered by event-level tests; a live reload-confirmation test,
cross-workspace/router navigation, and closing during an in-flight save remain
separate cases. This repair does not claim general crash recovery or autosave.
The served blank workflow also exposes contradictory readiness wording: its
header reports an item needing attention while Run details says **Ready to run**.
That is the next concrete status defect to investigate through the shared editor.
