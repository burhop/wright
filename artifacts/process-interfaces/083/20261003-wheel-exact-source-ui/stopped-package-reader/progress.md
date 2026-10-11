# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T02:04:31.826Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T02:04:33.338Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T02:04:33.858Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T02:04:34.692Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-003.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T02:04:36.463Z UTC â€” Wheel workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-003.workflow.wflow, Use saved process
Expected: Accepted wheel diagram and working view action available.
Actual: Exact saved wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T02:04:37.982Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=16a7f83d-f3ac-429b-9227-35f3ddcdda59&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T02:04:43.082Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=16a7f83d-f3ac-429b-9227-35f3ddcdda59&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T02:04:44.266Z UTC â€” Exact outputs and original held gate

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=16a7f83d-f3ac-429b-9227-35f3ddcdda59&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83
Action: Inspect results and validation findings without approving or continuing.
Controls: Open representation, Open assessment
Expected: All nineteen actual result identities and the original held assessment are visible.
Actual: Exact 19 working-view result identities match; original assessment is linked and blocked. Full review reason remains in the exact assessment evidence.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T02:06:45.142Z UTC â€” Entry stopped

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=16a7f83d-f3ac-429b-9227-35f3ddcdda59&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: getByRole('img', { name: 'Rotatable 3D toolpaths from all supported layers', exact: true })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 120000ms
  - waiting for getByRole('img', { name: 'Rotatable 3D toolpaths from all supported layers', exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
