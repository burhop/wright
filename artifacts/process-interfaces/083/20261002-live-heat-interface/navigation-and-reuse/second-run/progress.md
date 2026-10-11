# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T05:12:04.783Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T05:12:06.728Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T05:12:07.217Z UTC — Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T05:12:07.981Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T05:12:09.286Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T05:12:10.798Z UTC — Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=df8d8456-3f86-4c7d-a6d5-bada5691f3e0&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T05:12:16.535Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=df8d8456-3f86-4c7d-a6d5-bada5691f3e0&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T05:12:32.150Z UTC — Second run waits at its declared review

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=df8d8456-3f86-4c7d-a6d5-bada5691f3e0&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Open the second durable run in the common working tab.
Controls: Review the next action
Expected: Actual waiting review with the second run�s exact subject.
Actual: Second run is waiting for the declared thermal-basis review.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T05:12:57.383Z UTC — Unchanged saved comparison follows the new run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=46b8958c-8e14-4fa4-85ec-93138eb86e1c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-13d5997c275849df87ce1cd08bfa0ac2
Action: Open the same saved interface link with the second recorded run selected.
Controls: Review the next action, Open representation, Open producing step
Expected: Same UI revision, second run�s waiting state and one current result.
Actual: Same saved revision connected; second run result and declared waiting review shown.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T05:13:14.927Z UTC — Reload reconciles the waiting second run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=46b8958c-8e14-4fa4-85ec-93138eb86e1c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-13d5997c275849df87ce1cd08bfa0ac2
Action: Reload the saved second-run comparison.
Controls: Review the next action
Expected: No start, regeneration or review response from reload.
Actual: Same second-run waiting subject and single result restored.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
