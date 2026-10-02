# Installed native process workspace walkthrough

Prepared before navigation. Authenticated browser trace remains private.

## 2026-10-02T21:04:16.675Z UTC — Installed workspace loads
URL: http://wright.localhost:8033/workspace/083-heat-live-005
Action: Open native home and proof workspace.
Controls: Workflows
Expected: Authenticated Docker workspace entry.
Actual: Installed Docker frontend loads with the existing authorized HttpOnly operator session and Workflows control.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T21:04:17.481Z UTC — Established editor entry
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Existing editor in workspace.
Actual: Workflow file menu and editor open within the installed workspace.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T21:04:18.123Z UTC — Saved engineering workflow
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files, then Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow
Expected: Exact accepted heat-spreader source offered.
Actual: Accepted heat-spreader workflow appears in the installed file chooser.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T21:04:19.745Z UTC — Authoring and working views share source
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Choose the accepted heat-spreader source.
Controls: Use saved process
Expected: Same accepted source in diagram and working view.
Actual: The original CAD/coarse/fine thermal-analysis source is open with Use saved process enabled.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T21:04:20.463Z UTC — Installed common working view
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=0cddcc41-68bd-4ca8-b046-a4cba46ac357&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9
Action: Click Use saved process.
Controls: Create or choose interface
Expected: Common view opens as a workspace tab.
Actual: Installed shared common view opens without starting another run.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T21:04:23.766Z UTC — Exact existing run remains waiting
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=0cddcc41-68bd-4ca8-b046-a4cba46ac357&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Open recorded second-run link.
Controls: Review the next action
Expected: Existing second run remains at its declared review.
Actual: Common view shows the same second run and pending analysis-basis review.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T21:04:24.612Z UTC — Saved UI independent of authoring compiler
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=0cddcc41-68bd-4ca8-b046-a4cba46ac357&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Click Create or choose interface.
Controls: Saved interface
Expected: Unavailable compiler explained; saved interfaces offered.
Actual: Compiler unavailable is explicit and the saved interface chooser remains usable.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T21:04:25.206Z UTC — Existing built revision selected
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=0cddcc41-68bd-4ca8-b046-a4cba46ac357&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Choose saved thermal-analysis interface and current revision.
Controls: Open saved interface
Expected: Previously generated immutable revision selectable.
Actual: Exact original saved UI/revision selected without generating or compiling.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T21:04:30.643Z UTC — Installed saved interface mounts
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=f6938dcc-9bb7-4d39-935b-b2446aecee0e&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Click Open saved interface.
Controls: Review the next action
Expected: Saved React UI connected to the exact run through the installed bridge.
Actual: Saved UI renders in its workspace tab with the second run’s single result and waiting review.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T21:04:36.755Z UTC — Installed reopening reconciles
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=f6938dcc-9bb7-4d39-935b-b2446aecee0e&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Reload the saved interface tab.
Controls: Review the next action
Expected: Same run, saved revision and waiting review after reload.
Actual: Installed tab restores the same waiting run and saved compiled interface.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
