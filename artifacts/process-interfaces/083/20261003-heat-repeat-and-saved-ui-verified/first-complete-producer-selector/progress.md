# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T06:02:09.476Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T06:02:10.369Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T06:02:10.757Z UTC — Workflow file controls

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T06:02:11.300Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T06:02:12.816Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T06:02:13.494Z UTC — Shared working view

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=6bbf3348-a428-4a3e-be5c-70faddc84c67&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T06:02:15.953Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=6bbf3348-a428-4a3e-be5c-70faddc84c67&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T06:02:21.556Z UTC — Common view shows the exact completed digital chain

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=6bbf3348-a428-4a3e-be5c-70faddc84c67&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Inspect all recorded common-view result cards; leave reviews untouched.
Controls: Create or choose interface
Expected: All eighteen exact third-run results, with no substituted earlier evidence.
Actual: All result identities match the third-run API contract.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T06:02:22.643Z UTC — Common view opens the same actual solver samples

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=6bbf3348-a428-4a3e-be5c-70faddc84c67&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Open revision_60_fine in the common view and choose the recorded axes.
Controls: Open representation, View numerical samples, Horizontal column, Vertical column, Value column
Expected: 765 samples from the exact fine-field CSV.
Actual: Common viewer renders all 765 recorded samples.
Status: pass
Screenshots: screenshots/raw/S08B.png; screenshots/annotated/S08B.png

## 2026-10-03T06:02:28.617Z UTC — Saved updated comparison shows identical evidence

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=9b803b92-b54e-4a62-a145-1627d52370c6&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Choose the saved Heat comparison and click Open saved interface.
Controls: Saved interface, Open saved interface
Expected: The saved updated revision displays exactly the same eighteen third-run result identities.
Actual: Exact common/tailored identity parity and all three comparison groups are visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T06:02:37.710Z UTC — Actual solver field opens inside the saved interface

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=9b803b92-b54e-4a62-a145-1627d52370c6&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Click Open representation on revision_60_fine; expand View numerical samples and select x_m, y_m and temperature_c.
Controls: Open representation, View numerical samples, Horizontal column, Vertical column, Value column
Expected: 765 samples from the recorded third-run CSV.
Actual: 765 actual samples rendered in the saved interface.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T06:02:47.504Z UTC — Exact held assessment opens

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=6bbf3348-a428-4a3e-be5c-70faddc84c67&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Reopen the saved comparison and click Open assessment on revision_60_fine.
Controls: Open assessment
Expected: 25 passed checks, one blocked review, exact requested result focus.
Actual: Full held assessment visible with the exact fine-field result focus.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T06:03:02.113Z UTC — Entry stopped

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-workflow-file="workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow"]:visible').locator('.react-flow__node.selected[data-id="compute_fields_repeatable_default_013"]')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 5000ms
  - waiting for locator('[data-workflow-file="workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow"]:visible').locator('.react-flow__node.selected[data-id="compute_fields_repeatable_default_013"]')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
