# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T02:05:45.910Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T02:05:48.252Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T02:05:48.925Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T02:05:50.048Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-003.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T02:05:54.787Z UTC â€” Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-003.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T02:05:56.360Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=c07f1fec-76c3-4811-a72e-0d24af5ed7ee&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T02:06:02.386Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=c07f1fec-76c3-4811-a72e-0d24af5ed7ee&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T02:06:17.513Z UTC â€” Built wheel interface recovered

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=c07f1fec-76c3-4811-a72e-0d24af5ed7ee&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-e699e31782df459986a1c795f9c2bf65&processUIJob=job-47c7e3d74681486e9f9f76493c384ee5
Action: Open the recorded preview tab and click Create or choose interface.
Controls: Create or choose interface, Open preview
Expected: Existing preview ready.
Actual: Existing built preview restored.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T02:06:31.297Z UTC â€” Retained wheel evidence in preview

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=68a6f735-0bf5-426a-ac26-b43a812b5154&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-e699e31782df459986a1c795f9c2bf65&processUIJob=job-47c7e3d74681486e9f9f76493c384ee5
Action: Click Open preview.
Controls: Open preview
Expected: Read-only preview with actual result cards.
Actual: Read-only preview matches all nineteen exact result identities and the original blocked assessment.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T02:06:33.684Z UTC â€” Wheel interface saved

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=68a6f735-0bf5-426a-ac26-b43a812b5154&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-e699e31782df459986a1c795f9c2bf65&processUIJob=job-47c7e3d74681486e9f9f76493c384ee5
Action: Click Save interface.
Controls: Save interface, Open saved interface
Expected: Interface saved.
Actual: Exact revision saved.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T02:06:56.115Z UTC â€” Saved wheel view opens

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processView=68a6f735-0bf5-426a-ac26-b43a812b5154&processPath=workflows%2Fprinted-replacement-part-retained-consumer-003.workflow.wflow&processDigest=8bb09ab66acc856bf1b9a8310606422a37a16882c6c2db3dec67645aafd00ca5&processRun=bebf24bcdec44058a46371fa05d7cd83&processUIKind=preview&processUI=ui-ce377446f6d44705846a32f7c3eb94b2&processUIRevision=revision-e699e31782df459986a1c795f9c2bf65&processUIJob=job-47c7e3d74681486e9f9f76493c384ee5
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved view connected.
Actual: Saved view and reload match all nineteen exact results and the original blocked assessment.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
