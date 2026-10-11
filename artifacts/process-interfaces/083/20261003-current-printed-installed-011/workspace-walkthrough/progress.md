# Printed second-run saved-interface walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T11:31:29.735Z UTC — Installed preparation workspace

URL: http://wright.localhost:64083/workspace/083-printed-repeat-015
Action: Open the proof workspace.
Controls: Workflows
Expected: Normal workspace available.
Actual: The existing workspace opens.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T11:31:46.225Z UTC — The original exact held assessment opens

URL: http://wright.localhost:64083/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=d3bdd556-2ee0-40bf-97b9-c8fcb0d473d0&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d
Action: Click Open assessment on repaired_mesh.stl.
Controls: Open assessment
Expected: 17 passed checks, one mandatory review hold, exact repaired result focus.
Actual: The original full source assessment opens on the exact requested result.
Status: pass
Screenshots: screenshots/raw/S10A.png; screenshots/annotated/S10A.png

## 2026-10-03T11:32:12.962Z UTC — Saved interface exposes the same actual nominal toolpaths

URL: http://wright.localhost:64083/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=4de074d0-1e86-476c-944d-6c06b9110600&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Reopen the saved interface, open support-preview.json and exercise layer and support visibility controls.
Controls: Open representation, Layers, Support paths
Expected: The same 90 recorded layers and controls.
Actual: Identical nominal toolpath evidence renders in the saved interface.
Status: pass
Screenshots: screenshots/raw/S10T.png; screenshots/annotated/S10T.png

## 2026-10-03T11:32:31.002Z UTC — Exact producer opens in the accepted editor

URL: http://wright.localhost:64083/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Return to the saved view and click Open producing step on repaired_mesh.stl.
Controls: Open producing step
Expected: Accepted process and exact repaired-mesh producer selected.
Actual: The original producing block opens in the preserved editor.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
