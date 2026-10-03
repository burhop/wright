# Focus-wheel workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T07:29:41.053Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T07:29:42.941Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T07:29:43.399Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T07:29:44.016Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-configured-default-016.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T07:29:46.073Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-configured-default-016.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T07:29:46.901Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T07:29:50.901Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T07:29:51.210Z UTC — Wright interface authoring

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T07:30:06.302Z UTC — Visible interface creation

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Enter Interface title: Focus-wheel configured preparation. Request: Make a focused update to the supplied previous source. Retain the heading and responsive evidence grid; add this exact concise limitation beside results: Digital geometry and slice evidence do not establish fit, strength or physical print acceptance. Preserve all shared inputs/readiness, progress, pending interactions, diagnostics, assessment and result/evidence/producing-block navigation callbacks and ResultRepresentation viewers. Use only the backend interaction contract for the engineering-review hold; do not invent retry actions, accepted verdicts, measurements, an executor or protocols. Keep new manifest identities and parent revision; bind across runs without fixed paths or run IDs. Return only required source/manifest JSON.. Click Update selected interface.
Controls: Interface title, How should this interface help the user?, Update selected interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual focused update accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T07:31:25.777Z UTC — Built comparison ready

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T07:31:33.290Z UTC — Managed focus-wheel preparation preview

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=a9624dd4-9615-456b-b7f8-f60b2ec89275&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T07:31:34.968Z UTC — Reusable focus-wheel interface saved

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0aff5feb-33d7-42f1-9847-decf66a803b5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T07:31:42.029Z UTC — Saved focus-wheel preparation opens

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=0da6a838-1b67-49e8-9aaf-2b8fde2cff8d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png
