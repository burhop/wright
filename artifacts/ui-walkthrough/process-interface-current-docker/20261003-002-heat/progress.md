# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T22:07:04.177Z UTC — Workspace offers Workflows

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T22:07:05.002Z UTC — Workflows opens the editor

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T22:07:05.414Z UTC — Workflow file controls

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T22:07:05.870Z UTC — Choose the heat workflow

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T22:07:06.698Z UTC — Heat workflow diagram

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T22:07:07.081Z UTC — Shared working view

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d2347744-3ca3-4f7e-8fe4-2fdb8c45d02f&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T22:07:10.423Z UTC — Attach the actual heat run

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d2347744-3ca3-4f7e-8fe4-2fdb8c45d02f&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T22:07:10.688Z UTC — Common view shows the exact completed digital chain

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d2347744-3ca3-4f7e-8fe4-2fdb8c45d02f&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Inspect all recorded common-view result cards; leave reviews untouched.
Controls: Create or choose interface
Expected: All eighteen exact third-run results, with no substituted earlier evidence.
Actual: All result identities match the third-run API contract.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T22:07:11.380Z UTC — Common view opens the same actual solver samples

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d2347744-3ca3-4f7e-8fe4-2fdb8c45d02f&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Open revision_60_fine in the common view and choose the recorded axes.
Controls: Open representation, View numerical samples, Horizontal column, Vertical column, Value column
Expected: 765 samples from the exact fine-field CSV.
Actual: Common viewer renders all 765 recorded samples.
Status: pass
Screenshots: screenshots/raw/S08B.png; screenshots/annotated/S08B.png

## 2026-10-03T22:07:16.495Z UTC — Saved updated comparison shows identical evidence

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d6a02120-6dec-4db9-9acf-60231cc7f62d&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Choose the saved Heat comparison and click Open saved interface.
Controls: Saved interface, Open saved interface
Expected: The saved updated revision displays exactly the same eighteen third-run result identities.
Actual: Exact common/tailored identity parity and all three comparison groups are visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T22:07:28.083Z UTC — Actual solver field opens inside the saved interface

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d6a02120-6dec-4db9-9acf-60231cc7f62d&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Click Open representation on revision_60_fine; expand View numerical samples and select x_m, y_m and temperature_c.
Controls: Open representation, View numerical samples, Horizontal column, Vertical column, Value column
Expected: 765 samples from the recorded third-run CSV.
Actual: 765 actual samples rendered in the saved interface.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T22:07:36.419Z UTC — Exact held assessment opens

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d2347744-3ca3-4f7e-8fe4-2fdb8c45d02f&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072
Action: Reopen the saved comparison and click Open assessment on revision_60_fine.
Controls: Open assessment
Expected: 25 passed checks, one blocked review, exact requested result focus.
Actual: Full held assessment visible with the exact fine-field result focus.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T22:07:44.818Z UTC — Exact producing step opens in the refined editor

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Reopen the saved comparison and click Open producing step.
Controls: Open producing step, Workflow files
Expected: The accepted source and exact compute_fields producer open.
Actual: Accepted process editor and exact producer focus restored.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T22:07:50.349Z UTC — Entry stopped

URL: http://wright.localhost:8041/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=d6a02120-6dec-4db9-9acf-60231cc7f62d&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=63b639c7a8f446cd90a9285921ab9072&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-c4ac3eb3c1fb487aa14ac04c0b0cbda0
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(received).toBe(expected) // Object.is equality

Expected: false
Received: undefined
Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
