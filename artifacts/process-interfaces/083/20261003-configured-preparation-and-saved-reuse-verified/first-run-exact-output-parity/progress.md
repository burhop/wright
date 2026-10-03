# Printed second-run saved-interface walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T07:36:04.697Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T07:36:06.346Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T07:36:06.726Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T07:36:07.494Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-configured-default-016.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T07:36:08.947Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-configured-default-016.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T07:36:09.954Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T07:36:12.344Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T07:36:17.641Z UTC — Common view retains the actual failure and preparation results

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Inspect the common working view of the recorded failed run.
Controls: Create or choose interface
Expected: Twenty exact first-run results and the original mandatory human-review hold.
Actual: Common results match the authoritative failed-run contract.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T07:36:27.793Z UTC — Common view reads the retained source geometry

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Click Open representation on the repaired_mesh.stl result.
Controls: Open representation, Close representation
Expected: A visible 3D canvas for the actual first-run source.
Actual: Actual repaired geometry is visible in the common view.
Status: pass
Screenshots: screenshots/raw/S08G.png; screenshots/annotated/S08G.png

## 2026-10-03T07:36:31.906Z UTC — Common view exposes actual nominal toolpaths

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Open support-preview.json, select layer two, hide supports, then restore all layers and supports.
Controls: Open representation, Layers, Support paths
Expected: 90 recorded layers with working visibility controls.
Actual: Exact recorded nominal paths and controls render in the common view.
Status: pass
Screenshots: screenshots/raw/S08T.png; screenshots/annotated/S08T.png

## 2026-10-03T07:36:51.390Z UTC — Saved working interface agrees with the common view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=5dc8c198-ac2b-4635-a7fd-c37a2a0117a2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Select Focus-wheel configured preparation and click Open saved interface.
Controls: Saved interface, Open saved interface
Expected: Exact same twenty result identities and original review-hold diagnostic.
Actual: Saved working interface agrees with the common view.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T07:37:12.997Z UTC — Actual source geometry remains inspectable

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=5dc8c198-ac2b-4635-a7fd-c37a2a0117a2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Reload the saved view and click Open representation on repaired_mesh.stl.
Controls: Open representation
Expected: The exact first-run source STL and a visible 3D canvas.
Actual: The shared reader renders the exact source geometry within the tailored view.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T07:37:47.741Z UTC — The original exact held assessment opens

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=10f853f0-2dfa-4df4-b088-225885d76ec2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Click Open assessment on repaired_mesh.stl.
Controls: Open assessment
Expected: 17 passed checks, one mandatory review hold, exact repaired result focus.
Actual: The original full source assessment opens on the exact requested result.
Status: pass
Screenshots: screenshots/raw/S10A.png; screenshots/annotated/S10A.png

## 2026-10-03T07:38:21.428Z UTC — Saved interface exposes the same actual nominal toolpaths

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=5dc8c198-ac2b-4635-a7fd-c37a2a0117a2&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Reopen the saved interface, open support-preview.json and exercise layer and support visibility controls.
Controls: Open representation, Layers, Support paths
Expected: The same 90 recorded layers and controls.
Actual: Identical nominal toolpath evidence renders in the saved interface.
Status: pass
Screenshots: screenshots/raw/S10T.png; screenshots/annotated/S10T.png

## 2026-10-03T07:38:43.079Z UTC — Exact producer opens in the accepted editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Return to the saved view and click Open producing step on repaired_mesh.stl.
Controls: Open producing step
Expected: Accepted process and exact repaired-mesh producer selected.
Actual: The original producing block opens in the preserved editor.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
