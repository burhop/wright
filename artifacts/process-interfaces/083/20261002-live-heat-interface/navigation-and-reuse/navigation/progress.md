# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T05:07:23.108Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T05:07:25.105Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T05:07:25.627Z UTC — Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T05:07:26.365Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T05:07:28.388Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T05:07:29.024Z UTC — Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=6b95af75-6df4-4185-84c2-2dc330df7e6d&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T05:07:32.645Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=6b95af75-6df4-4185-84c2-2dc330df7e6d&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T05:07:47.887Z UTC — Reopen saved comparison

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=46b8958c-8e14-4fa4-85ec-93138eb86e1c&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-13d5997c275849df87ce1cd08bfa0ac2
Action: Open the recorded saved-interface workspace link.
Controls: Open representation, Open assessment, Open producing step
Expected: Saved comparison connects and exposes all eighteen actual results.
Actual: Saved interface connected and eighteen actual results visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T05:07:51.348Z UTC — Exact fine-field evidence opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=6b95af75-6df4-4185-84c2-2dc330df7e6d&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Click Open representation on revision_60_fine.
Controls: Open representation, View numerical samples
Expected: Native common view shows the exact numerical CSV.
Actual: Actual numerical table and temperature column opened from the tailored interface.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T05:07:52.151Z UTC — All recorded field samples

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=6b95af75-6df4-4185-84c2-2dc330df7e6d&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Expand View numerical samples and select x_m, y_m, temperature_c.
Controls: View numerical samples, Horizontal column, Vertical column, Value column
Expected: 765 actual field samples.
Actual: All recorded samples rendered.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-02T05:08:06.745Z UTC — Exact held assessment opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=6b95af75-6df4-4185-84c2-2dc330df7e6d&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=67abaa021ee44972a94e3c9cbaa3dbbe
Action: Reopen the saved comparison and click Open assessment on revision_60_fine.
Controls: Open assessment
Expected: 25 passed checks and one held review, focused on the requested result.
Actual: Exact assessment and fine-result focus retained.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-02T05:08:23.057Z UTC — Producing engineering step opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Reopen the saved comparison and click Open producing step on revision_60_fine.
Controls: Open producing step, Workflow files
Expected: The accepted heat process editor opens at its producer.
Actual: Accepted heat editor opened from the exact result.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png
