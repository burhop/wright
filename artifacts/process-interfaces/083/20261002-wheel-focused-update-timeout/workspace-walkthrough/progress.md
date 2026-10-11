# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T14:54:15.387Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T14:54:20.902Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T14:54:22.221Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T14:54:26.776Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-001.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T14:54:33.589Z UTC â€” Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-001.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T14:54:36.855Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=5f68181e-f052-4e2b-a43d-74f6d2caa7a3&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T14:54:43.879Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=5f68181e-f052-4e2b-a43d-74f6d2caa7a3&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T14:54:57.917Z UTC â€” Built wheel interface recovered

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=5f68181e-f052-4e2b-a43d-74f6d2caa7a3&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0&processUIJob=job-97f5219a3d74414685cc3f30347a8345
Action: Open the recorded preview tab and click Create or choose interface.
Controls: Create or choose interface, Open preview
Expected: Existing preview ready.
Actual: Existing built preview restored.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T14:55:38.938Z UTC â€” Retained wheel evidence in preview

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=c9469a51-9e5e-4f8f-9993-138a080cb46a&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0&processUIJob=job-97f5219a3d74414685cc3f30347a8345
Action: Click Open preview.
Controls: Open preview
Expected: Read-only preview with actual result cards.
Actual: Preview connected with actual result cards.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T14:55:46.579Z UTC â€” Wheel interface saved

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=c9469a51-9e5e-4f8f-9993-138a080cb46a&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0&processUIJob=job-97f5219a3d74414685cc3f30347a8345
Action: Click Save interface.
Controls: Save interface, Open saved interface
Expected: Interface saved.
Actual: Exact revision saved.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-02T14:55:53.055Z UTC â€” Saved wheel view opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=c9469a51-9e5e-4f8f-9993-138a080cb46a&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=preview&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0&processUIJob=job-97f5219a3d74414685cc3f30347a8345
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved view connected.
Actual: Saved working view connected.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-02T14:57:57.929Z UTC â€” Entry stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=63f13604-eaf5-48fd-b78b-b93ec75cc1a9&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=a87d84b40a244bcaa035d9ed8308ac5a&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 120000ms
  - waiting for locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
