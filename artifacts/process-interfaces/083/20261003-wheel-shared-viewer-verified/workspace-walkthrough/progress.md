# Wheel interface viewer continuation walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T02:59:49.362Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T02:59:50.410Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T02:59:50.840Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T02:59:51.510Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-003.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T02:59:52.643Z UTC â€” Wheel workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-003.workflow.wflow, Use saved process
Expected: Accepted wheel diagram and working view action available.
Actual: Exact saved wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T02:59:53.675Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=3396673d-3c6e-411e-995c-ecde7f2486ca&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T02:59:56.618Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=3396673d-3c6e-411e-995c-ecde7f2486ca&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T03:00:07.970Z UTC â€” Built wheel interface recovered

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=3396673d-3c6e-411e-995c-ecde7f2486ca&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687&processUIJob=job-844e87c725754f3d988b2d1cdd26371c
Action: Open the recorded preview tab and click Create or choose interface.
Controls: Create or choose interface, Open preview
Expected: Existing preview ready.
Actual: Existing built preview restored.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T03:00:25.150Z UTC â€” Preview recorded 3D layers

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=2961db1f-11e8-467d-aa09-d14ea0afc91f&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687&processUIJob=job-844e87c725754f3d988b2d1cdd26371c
Action: Open the recorded support-preview representation and drag to rotate.
Controls: Open representation, Layers, Download exact file
Expected: Ninety nominal layers, visible 3D canvas and explicit excluded-machine scope.
Actual: Exact neutral evidence renders ninety layers; setup/shutdown remains unverified and the original assessment remains blocked.
Status: pass
Screenshots: screenshots/raw/Previewa.png; screenshots/annotated/Previewa.png

## 2026-10-03T03:00:27.014Z UTC â€” Preview layer and category controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=2961db1f-11e8-467d-aa09-d14ea0afc91f&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687&processUIJob=job-844e87c725754f3d988b2d1cdd26371c
Action: Focus Layers, press Home and ArrowRight, then uncheck Support paths.
Controls: Layers, Support paths
Expected: Two selected layers and support visibility off.
Actual: Layer two selected; supports hidden without changing artifacts or permission.
Status: pass
Screenshots: screenshots/raw/Previewb.png; screenshots/annotated/Previewb.png

## 2026-10-03T03:00:30.774Z UTC â€” Retained wheel evidence in preview

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=2961db1f-11e8-467d-aa09-d14ea0afc91f&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687&processUIJob=job-844e87c725754f3d988b2d1cdd26371c
Action: Click Open preview.
Controls: Open preview
Expected: Read-only preview with actual result cards.
Actual: Read-only preview matches all nineteen exact result identities and the original blocked assessment.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T03:00:32.827Z UTC â€” Already saved exact wheel revision

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=2961db1f-11e8-467d-aa09-d14ea0afc91f&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687&processUIJob=job-844e87c725754f3d988b2d1cdd26371c
Action: Inspect the saved revision and Open saved interface control.
Controls: Open saved interface
Expected: Same saved revision is available without generation, build or save replay.
Actual: Exact saved revision reconciled; no save repeated.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T03:01:04.949Z UTC â€” SavedReload recorded 3D layers

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=64b247f7-7a02-4031-8420-5a5964cd0f20&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=working&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687
Action: Open the recorded support-preview representation and drag to rotate.
Controls: Open representation, Layers, Download exact file
Expected: Ninety nominal layers, visible 3D canvas and explicit excluded-machine scope.
Actual: Exact neutral evidence renders ninety layers; setup/shutdown remains unverified and the original assessment remains blocked.
Status: pass
Screenshots: screenshots/raw/SavedReloada.png; screenshots/annotated/SavedReloada.png

## 2026-10-03T03:01:06.974Z UTC â€” SavedReload layer and category controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=64b247f7-7a02-4031-8420-5a5964cd0f20&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=working&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687
Action: Focus Layers, press Home and ArrowRight, then uncheck Support paths.
Controls: Layers, Support paths
Expected: Two selected layers and support visibility off.
Actual: Layer two selected; supports hidden without changing artifacts or permission.
Status: pass
Screenshots: screenshots/raw/SavedReloadb.png; screenshots/annotated/SavedReloadb.png

## 2026-10-03T03:01:11.111Z UTC â€” Saved wheel view opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=64b247f7-7a02-4031-8420-5a5964cd0f20&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=working&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-5d5d6defda104980a2455c7ddc95e687
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved view connected.
Actual: Saved view and reload match all nineteen exact results and the original blocked assessment.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
