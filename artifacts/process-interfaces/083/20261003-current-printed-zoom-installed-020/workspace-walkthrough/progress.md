# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T13:56:45.827Z UTC — Updated installed workspace

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015
Action: Open the isolated workspace.
Controls: Workflows, Workspace Files
Expected: Existing workspace navigation visible.
Actual: Normal Workflows and Files controls are available.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T13:56:54.158Z UTC — Saved engineering interface and desktop navigation

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open the saved working link; click Workspace Files if closed.
Controls: Workspace Files, Working tab
Expected: Exact recorded results and docked navigation.
Actual: 20 exact result identities; docked file panel 260px wide.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T13:56:56.538Z UTC — Compact accessibility and editor return

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Open Files, scan navigation, close it and click Open workflow.
Controls: Workspace Files, Open workflow, Diagram, Source, Use saved process
Expected: Zero scoped automated violations and existing editor available.
Actual: Navigation has zero WCAG A/AA violations; Diagram, Source and Use saved process remain available.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T13:57:07.172Z UTC — Compact common working view

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open the saved working interface and click Use common working view.
Controls: Use common working view, Open workflow
Expected: Same exact recorded results; full available width and no outer overflow.
Actual: 20 exact common results; document 432px with 432px scroll width.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T13:57:19.001Z UTC — Compact read-only preview

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-preview-006&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Open the retained preview link; open Files and close with Escape.
Controls: Preview tab, Workspace Files, Open workflow
Expected: Read-only preview of the same UI revision/run and exact results; navigation return works.
Actual: Backend read-only binding and 20 exact results verified; preview has the available width and Files returns focus.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T13:57:24.910Z UTC — Entry stopped

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-preview-006&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="workspace-process-view"]:visible').getByTestId('surface-panel-host').locator('iframe').contentFrame().getByText('Preview - process controls are read-only.', { exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for locator('[data-testid="workspace-process-view"]:visible').getByTestId('surface-panel-host').locator('iframe').contentFrame().getByText('Preview - process controls are read-only.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
