# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T14:46:23.408Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T14:46:27.547Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T14:46:28.821Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T14:46:31.405Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-001.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T14:46:36.913Z UTC â€” Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-001.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T14:46:40.681Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=2224f3d4-545f-45f4-b6e0-cef363f4cbde&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T14:46:48.711Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=2224f3d4-545f-45f4-b6e0-cef363f4cbde&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T14:47:11.976Z UTC â€” Built wheel interface recovered

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=2224f3d4-545f-45f4-b6e0-cef363f4cbde&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-2bf6d4d49c224290a0416503a627d0e7&processUIJob=job-57569905755f41f4bee61da253c03204
Action: Open the recorded preview tab and click Create or choose interface.
Controls: Create or choose interface, Open preview
Expected: Existing preview ready.
Actual: Existing built preview restored.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T14:47:31.327Z UTC â€” Retained wheel evidence in preview

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=b8be9124-a6ae-4507-a12b-3d70b99f696c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-2bf6d4d49c224290a0416503a627d0e7&processUIJob=job-57569905755f41f4bee61da253c03204
Action: Click Open preview.
Controls: Open preview
Expected: Read-only preview with actual result cards.
Actual: Preview connected with actual result cards.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T14:47:35.210Z UTC â€” Wheel interface saved

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=b8be9124-a6ae-4507-a12b-3d70b99f696c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-2bf6d4d49c224290a0416503a627d0e7&processUIJob=job-57569905755f41f4bee61da253c03204
Action: Click Save interface.
Controls: Save interface, Open saved interface
Expected: Interface saved.
Actual: Exact revision saved.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-02T14:47:42.860Z UTC â€” Saved wheel view opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=b8be9124-a6ae-4507-a12b-3d70b99f696c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-2bf6d4d49c224290a0416503a627d0e7&processUIJob=job-57569905755f41f4bee61da253c03204
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved view connected.
Actual: Saved working view connected.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
