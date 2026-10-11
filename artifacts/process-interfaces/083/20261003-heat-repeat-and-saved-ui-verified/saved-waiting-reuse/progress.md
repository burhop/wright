# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T05:28:47.694Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T05:28:49.036Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T05:28:49.482Z UTC — Workflow file controls

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T05:28:50.157Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T05:28:51.479Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T05:28:52.057Z UTC — Shared working view

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=90c3f3ca-2b63-4342-83f4-b2c55d380994&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T05:28:55.619Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=90c3f3ca-2b63-4342-83f4-b2c55d380994&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=50942bb6d23649b5bbb4d4e51a019af6
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T05:29:03.864Z UTC — Second run waits at its declared review

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=90c3f3ca-2b63-4342-83f4-b2c55d380994&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=50942bb6d23649b5bbb4d4e51a019af6
Action: Inspect the common view; leave its review unanswered.
Controls: Review the next action
Expected: One second-run result and the declared review.
Actual: Second-run waiting state and exact basis result are visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T05:29:16.623Z UTC — Saved comparison reused

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=cf214746-2368-4bfc-b2fb-e58b8e467cae&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=50942bb6d23649b5bbb4d4e51a019af6&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-1307d9f0c2ad4bc78d204efd64c4da91
Action: Select the saved Heat comparison and click Open saved interface.
Controls: Saved interface, Open saved interface, Review the next action
Expected: The same saved revision displays only second-run state.
Actual: Saved comparison displays the second-run basis and declared review.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T05:29:36.208Z UTC — Reload reconciles the same second run

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=cf214746-2368-4bfc-b2fb-e58b8e467cae&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=50942bb6d23649b5bbb4d4e51a019af6&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-1307d9f0c2ad4bc78d204efd64c4da91
Action: Reload the saved working interface; leave Approve untouched.
Controls: Review the next action
Expected: No start, model generation, save or review dispatch.
Actual: Same second-run evidence restored with no authoring/execution mutation.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
