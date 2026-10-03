# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T14:07:57.425Z UTC — Updated installed workspace

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015
Action: Open the isolated workspace.
Controls: Workflows, Workspace Files
Expected: Existing workspace navigation visible.
Actual: Normal Workflows and Files controls are available.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T14:08:11.162Z UTC — Saved engineering interface and desktop navigation

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open the saved working link; click Workspace Files if closed.
Controls: Workspace Files, Working tab
Expected: Exact recorded results and docked navigation.
Actual: 20 exact result identities; docked file panel 260px wide.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T14:08:13.850Z UTC — Compact accessibility and editor return

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Open Files, scan navigation, close it and click Open workflow.
Controls: Workspace Files, Open workflow, Diagram, Source, Use saved process
Expected: Zero scoped automated violations and existing editor available.
Actual: Navigation has zero WCAG A/AA violations; Diagram, Source and Use saved process remain available.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T14:08:27.177Z UTC — Compact common working view

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open the saved working interface and click Use common working view.
Controls: Use common working view, Open workflow
Expected: Same exact recorded results; full available width and no outer overflow.
Actual: 20 exact common results; document 432px with 432px scroll width.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T14:08:44.941Z UTC — Compact read-only preview

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-preview-006&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Open the retained preview link; open Files and close with Escape.
Controls: Preview tab, Workspace Files, Open workflow
Expected: Read-only preview of the same UI revision/run and exact results; navigation return works.
Actual: Backend read-only binding and 20 exact results verified; preview has the available width and Files returns focus.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T14:08:45.989Z UTC — Actual 200% browser zoom on read-only preview

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-preview-006&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Set browser Zoom to 200% and scroll to the embedded preview.
Controls: Browser Zoom, Preview tab, Open workflow
Expected: Browser zoom 2, CSS viewport 720px, pinch scale 1, exact read-only preview results.
Actual: Browser zoom 2; viewport 720px; pixel ratio 2; page scale 1; 20 exact results.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T14:09:02.973Z UTC — Saved working interface at native 200% zoom

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open the saved working interface; open Files and press Escape.
Controls: Saved interface tab, Workspace Files, Close workspace navigation
Expected: Exact saved results; Files restores keyboard focus.
Actual: All 20 exact results remain available; Files opens and Escape restores focus.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T14:09:09.193Z UTC — Common working interface at native 200% zoom

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-compact-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Click Use common working view.
Controls: Use common working view, Open workflow
Expected: Exact results, no outer overflow, no detected WCAG A/AA violations.
Actual: 20 exact results; 672px client and 672px scroll width; zero scoped automated violations.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png

## 2026-10-03T14:09:10.513Z UTC — Editor and source at native 200% zoom

URL: http://wright.localhost:50062/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Click Open workflow, select Source, then Diagram.
Controls: Open workflow, Source, Diagram, Use saved process
Expected: Same accepted source; browser zoom still 2.
Actual: Exact accepted source and existing diagram remain available; browser tab zoom remains 200%.
Status: pass
Screenshots: screenshots/raw/S14.png; screenshots/annotated/S14.png
