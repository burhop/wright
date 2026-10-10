# Preserve the editor while saving — 10 October 2026

## User problem and repair

Most workflow editing controls already paused during Save, but Source, Apply,
Undo and Redo did not. Those paths could change the draft and clear the visible
saving state while the original write was still pending. The save response then
replaced the editor with the older submitted snapshot. Closing a tab or choosing
Discard during that write also incorrectly suggested that the pending save could
be discarded with the local draft.

The existing save lock now covers source and history editing as well as the
diagram and inspectors. Source remains readable, with a message explaining when
editing resumes. A synchronous pending flag also protects the shared mutation
callbacks and duplicate save attempts. Success or failure releases the lock.

`WorkflowRecoveryPage` reports its actual pending write to the existing workspace
tab owner. That transient flag holds tab closure and workspace departure until
the request settles. The departure dialog explains that Discard cannot cancel a
save already in progress, disables that action, and keeps its keyboard focus on
the available control. Disabled controls now have consistent styling. The flag
is omitted from saved workspace layouts and is not restored as job state.

The existing source service retains compare-and-swap writes and exact returned
revision checks. This repair adds no autosave, draft store, execution authority,
save cancellation or automatic retry. Model instructions, engineering criteria,
review permissions and execution behavior are unchanged.

## Evidence and scope

- [Before the repair](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-196-pending-save-reproduction/report.html):
  a delayed real save of a newly created blank workflow exposes the still-editable
  Source field. The test stops there and releases the original request for cleanup.
  Walkthrough195 is retained as a separate recorder Unicode-matching failure.
- [Final save journey](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-198-pending-save-final/report.html):
  nine steps cover a delayed real save, readable locked source, disabled history/
  Apply/close controls, held workspace departure, completion, a subsequent edit,
  a second save and reopening the later confirmed revision. Diagnostics are empty.
- [Thermal copy and save failure](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-199-thermal-save-recovery/report.html):
  ten steps repeat the shared behavior on a fresh source-only copy of the existing
  thermal workflow. One save receives an explicitly injected503 response. The
  visible error keeps the source editable; a deliberate retry saves that same
  draft and reopening confirms it. The two diagnostics are exactly the injected
  HTTP503 and its browser resource message. This is a controlled negative test,
  not a claimed backend outage or engineering execution.
- 179 affected tests pass without skips. New tests cover locked source/history,
  save success/failure, exact path notification to the workspace, closure during
  a pending write, native unload events and departure/focus when only saving is
  true. Existing editor, workspace, routing, store and native-dialog checks pass.
- The first test pass exposed an outdated working-view label expectation; the
  test now matches the existing product label. The initial build40 type check
  caught a missing callback type in a test fixture; it was corrected. Build41
  and its eight-step walkthrough197 retain the initial functional repair.
  Final build42 also includes clearer disabled-control styling.
- Type checking and production build42 pass; served HTML and its three entry
  assets match. Raw pending-save and error screenshots were visually inspected.
  Final walkthrough reports and the retained original reproduction validate.
  The existing Vite large-chunk advisory remains.
- All54 prior run records,64 latest wheel outputs and both original engineering
  sources remain byte-identical. Four fresh blank test workflows and one thermal
  source copy were used across the retained recordings. No model call, CAD
  launch, engineering run, input answer, review or external operation occurred.
  The pre-existing Solid Edge process22448 was left untouched.

Current preview: UI5250/PID51996, build42; API8067/PID84296 unchanged. Exact
hashes and identities are recorded in
`.local-run/process-interfaces-083/mechanical-engineering-20261008/save-audit-080.json`.

## User check and remaining work

In the isolated [Wright workspace](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5),
create a blank workflow, rename it and save. During a slow save, Source should
remain readable and editing/closure should wait. After saving, make another edit,
save again, close and reopen the workflow to inspect the latest saved name.
The linked recordings show the delayed and failed-save cases without requiring
the user to manufacture a network problem.

This verifies controlled in-flight save behavior and explicit retry, not general
crash recovery or autosave. Full-page unload remains a browser warning with
event-level coverage; no claim is made that a submitted write can be cancelled.
The overall goal remains incomplete. Slide-deck work stays deferred. The next
shared acceptance item is the interrupted export/import portability audit,
including retained prompts and dependencies, before expanding example work.
