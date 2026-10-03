# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T05:16:36.618Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T05:16:37.733Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T05:16:38.148Z UTC — Workflow file controls

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T05:16:38.721Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T05:16:40.392Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T05:16:41.090Z UTC — Shared working view

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=33d00110-1e19-4266-a343-2697bd0dc357&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T05:16:44.783Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=33d00110-1e19-4266-a343-2697bd0dc357&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T05:16:45.139Z UTC — Wright interface authoring

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=33d00110-1e19-4266-a343-2697bd0dc357&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T05:16:56.454Z UTC — Visible interface creation

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=33d00110-1e19-4266-a343-2697bd0dc357&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Enter Interface title: Heat-spreader candidate comparison. Request: Create a reusable heat-spreader engineering comparison using the supplied reference template and current interaction contract. The layout must work across runs without depending on output filenames or the first run ID. Keep the supplied manifest identities. Use public Wright components and ResultRepresentation for supported data. Show actual progress, all current result cards arranged for comparing the two candidates, and pending findings/review. Use snapshot data and the template callbacks for exact evidence/navigation. Use shared input/readiness and pending-interaction controls, plus exact result/assessment/block navigation. Do not add native protocols, measurements, engineering verdicts or execution. Return the required source/manifest JSON immediately.. Click Create interface.
Controls: Interface title, How should this interface help the user?, Create interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T05:19:06.547Z UTC — Entry stopped

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=33d00110-1e19-4266-a343-2697bd0dc357&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'Preview ready', exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for getByRole('heading', { name: 'Preview ready', exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
