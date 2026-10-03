# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T14:11:17.252Z UTC — Updated installed workspace

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013
Action: Open the isolated workspace.
Controls: Workflows, Workspace Files
Expected: Existing workspace navigation visible.
Actual: Normal Workflows and Files controls are available.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T14:11:47.674Z UTC — Saved engineering interface and desktop navigation

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Open the saved working link; click Workspace Files if closed.
Controls: Workspace Files, Working tab
Expected: Exact recorded results and docked navigation.
Actual: 18 exact result identities; docked file panel 260px wide.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T14:12:00.765Z UTC — Compact accessibility and editor return

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Open Files, scan navigation, close it and click Open workflow.
Controls: Workspace Files, Open workflow, Diagram, Source, Use saved process
Expected: Zero scoped automated violations and existing editor available.
Actual: Navigation has zero WCAG A/AA violations; Diagram, Source and Use saved process remain available.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T14:12:34.959Z UTC — Compact common working view

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Open the saved working interface and click Use common working view.
Controls: Use common working view, Open workflow
Expected: Same exact recorded results; full available width and no outer overflow.
Actual: 18 exact common results; document 432px with 432px scroll width.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T14:13:08.442Z UTC — Compact read-only preview

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-preview-006&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0&processUIJob=job-1e03b43bc5664e6fa1d9fbea3a264299
Action: Open the retained preview link; open Files and close with Escape.
Controls: Preview tab, Workspace Files, Open workflow
Expected: Read-only preview of the same UI revision/run and exact results; navigation return works.
Actual: Backend read-only binding and 18 exact results verified; preview has the available width and Files returns focus.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T14:13:12.485Z UTC — Actual 200% browser zoom on read-only preview

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-preview-006&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0&processUIJob=job-1e03b43bc5664e6fa1d9fbea3a264299
Action: Set browser Zoom to 200% and scroll to the embedded preview.
Controls: Browser Zoom, Preview tab, Open workflow
Expected: Browser zoom 2, CSS viewport 720px, pinch scale 1, exact read-only preview results.
Actual: Browser zoom 2; viewport 720px; pixel ratio 2; page scale 1; 18 exact results.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T14:14:44.505Z UTC — Entry stopped

URL: http://wright.localhost:63271/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=view-compact-heat-001&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="workspace-process-view"]:visible').getByTestId('surface-panel-host').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })
Expected: visible
Timeout: 90000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 90000ms
  - waiting for locator('[data-testid="workspace-process-view"]:visible').getByTestId('surface-panel-host').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
