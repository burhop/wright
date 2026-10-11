# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T11:57:37.667Z UTC — Updated installed workspace

URL: http://wright.localhost:52049/workspace/083-heat-repeat-013
Action: Open the isolated workspace.
Controls: Workflows, Workspace Files
Expected: Existing workspace navigation visible.
Actual: Normal Workflows and Files controls are available.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T11:57:45.083Z UTC — Saved engineering interface and desktop navigation

URL: http://wright.localhost:52049/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Open the saved working link; click Workspace Files if closed.
Controls: Workspace Files, Working tab
Expected: Exact recorded results and docked navigation.
Actual: 18 exact result identities; docked file panel 260px wide.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T11:57:45.413Z UTC — Compact content gets the workspace width

URL: http://wright.localhost:52049/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Resize to 480 by 900.
Controls: Workspace Files, Open workflow
Expected: Navigation closed; document wider than420px; same live frame/results.
Actual: Document 432px; embedded body 382px with 533px scroll width and visible horizontal overflow; same iframe and results.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T11:57:45.617Z UTC — Files remains accessible as compact navigation

URL: http://wright.localhost:52049/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Click Workspace Files.
Controls: Workspace Files, Close workspace navigation, Return to workspace
Expected: Focused close control and overlay navigation; document width unchanged.
Actual: Compact overlay opens; Close is focused; the same iframe keeps its available width.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T11:58:15.827Z UTC — Entry stopped

URL: http://wright.localhost:52049/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: locator.click: Timeout 30000ms exceeded.
Call log:
[2m  - waiting for getByRole('button', { name: 'Return to workspace', exact: true })[22m
[2m    - locator resolved to <button type="button" aria-label="Return to workspace" data-testid="workspace-sidebar-backdrop"></button>[22m
[2m  - attempting click action[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div>…</div> from <div role="region" id="workspace-navigation-panel" data-testid="workspace-sidebar" aria-label="Workspace navigation">…</div> subtree intercepts pointer events[22m
[2m    - retrying click action[22m
[2m    - waiting 20ms[22m
[2m    2 × waiting for element to be visible, enabled and stable[22m
[2m      - element is visible, enabled and stable[22m
[2m      - scrolling into view if needed[22m
[2m      - done scrolling[22m
[2m      - <div>…</div> from <div role="region" id="workspace-navigation-panel" data-testid="workspace-sidebar" aria-label="Workspace navigation">…</div> subtree intercepts pointer events[22m
[2m    - retrying click action[22m
[2m      - waiting 100ms[22m
[2m    55 × waiting for element to be visible, enabled and stable[22m
[2m       - element is visible, enabled and stable[22m
[2m       - scrolling into view if needed[22m
[2m       - done scrolling[22m
[2m       - <div>…</div> from <div role="region" id="workspace-navigation-panel" data-testid="workspace-sidebar" aria-label="Workspace navigation">…</div> subtree intercepts pointer events[22m
[2m     - retrying click action[22m
[2m       - waiting 500ms[22m

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
