# Installed native process workspace walkthrough

Prepared before navigation. Authenticated browser trace remains private.

## 2026-10-02T20:53:07.473Z UTC — Installed workspace loads
URL: http://wright.localhost:8032/workspace/083-heat-live-005
Action: Open native home and proof workspace.
Controls: Workflows
Expected: Native session bootstrap and workspace entry.
Actual: Installed frontend loads with native HttpOnly session and Workflows control.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T20:53:08.737Z UTC — Established editor entry
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Existing editor in workspace.
Actual: Workflow file menu and editor open within the installed workspace.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T20:53:09.626Z UTC — Saved engineering workflow
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files, then Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow
Expected: Exact accepted heat-spreader source offered.
Actual: Accepted heat-spreader workflow appears in the installed file chooser.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T20:53:10.682Z UTC — Authoring and working views share source
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow
Action: Choose the accepted heat-spreader source.
Controls: Use saved process
Expected: Same accepted source in diagram and working view.
Actual: The original CAD/coarse/fine thermal-analysis source is open with Use saved process enabled.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T20:53:11.308Z UTC — Installed common working view
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cd86aa49-4e3d-45b9-8488-5f437682e5c6&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9
Action: Click Use saved process.
Controls: Create or choose interface
Expected: Common view opens as a workspace tab.
Actual: Installed shared common view opens without starting another run.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T20:53:15.836Z UTC — Exact existing run remains waiting
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cd86aa49-4e3d-45b9-8488-5f437682e5c6&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Open recorded second-run link.
Controls: Review the next action
Expected: Existing second run remains at its declared review.
Actual: Common view shows the same second run and pending analysis-basis review.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T20:53:25.228Z UTC — Saved UI independent of authoring compiler
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cd86aa49-4e3d-45b9-8488-5f437682e5c6&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Click Create or choose interface.
Controls: Saved interface
Expected: Unavailable compiler explained; saved interfaces offered.
Actual: Compiler unavailable is explicit and the saved interface chooser remains usable.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T20:53:25.734Z UTC — Existing built revision selected
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cd86aa49-4e3d-45b9-8488-5f437682e5c6&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8
Action: Choose saved thermal-analysis interface and current revision.
Controls: Open saved interface
Expected: Previously generated immutable revision selectable.
Actual: Exact original saved UI/revision selected without generating or compiling.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T20:53:33.360Z UTC — Installed saved interface mounts
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cb7f9460-fee5-4b09-a666-526a436a48dc&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Click Open saved interface.
Controls: Review the next action
Expected: Saved React UI connected to the exact run through the installed bridge.
Actual: Saved UI renders in its workspace tab with the second run’s single result and waiting review.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T20:53:43.630Z UTC — Installed reopening reconciles
URL: http://wright.localhost:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processView=cb7f9460-fee5-4b09-a666-526a436a48dc&processPath=workflows%2Fheat-spreader-sizing-live-default-model-002.workflow.wflow&processDigest=e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9&processRun=9cfe133164bd4e70b97be9a058d0feb8&processUIKind=working&processUI=ui-8858f2ec2bc24bc588ce5042626503ab&processUIRevision=revision-9c8c8b164ea34a9ba65910567b41b170
Action: Reload the saved interface tab.
Controls: Review the next action
Expected: Same run, saved revision and waiting review after reload.
Actual: Installed tab restores the same waiting run and saved compiled interface.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
