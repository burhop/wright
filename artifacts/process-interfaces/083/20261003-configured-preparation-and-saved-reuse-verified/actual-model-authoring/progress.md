# Focus-wheel workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T07:21:00.725Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T07:21:03.531Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T07:21:04.207Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T07:21:09.222Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-configured-default-016.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T07:21:11.810Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-configured-default-016.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T07:21:12.762Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T07:21:17.749Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T07:21:18.165Z UTC — Wright interface authoring

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T07:21:35.450Z UTC — Visible interface creation

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Enter Interface title: Focus-wheel configured preparation. Request: Adapt the supplied reference into a Focus-wheel configured preparation. Reuse its public components, callbacks, all inputs/readiness, progress, pending interactions, ResultRepresentation viewers and exact evidence/assessment/block navigation. Change the heading and arrange all current geometry, package and assessment result cards in a responsive evidence grid. Keep all contract data and manifest identities; work across runs without fixed output filenames or run IDs. Keep source concise by reusing the reference, without new controls, custom viewers, execution, verdicts or protocols. Return only the required source/manifest JSON.. Click Create interface.
Controls: Interface title, How should this interface help the user?, Create interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T07:23:30.646Z UTC — Built comparison ready

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T07:23:42.686Z UTC — Managed focus-wheel preparation preview

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=d59fcba3-e544-460b-821f-e973640dd702&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-1c498bcb93884514bb6f2c838ed48fb4&processUIJob=job-44b4334d008542c29d6bb5b3e6baee8b
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T07:23:49.612Z UTC — Reusable focus-wheel interface saved

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=f970b86f-8e57-4ecc-add6-c47bb27a5d0d&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T07:24:15.211Z UTC — Saved focus-wheel preparation opens

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=b20365c3-4a8a-48e6-b156-9ebbae3328c5&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=40a732fd2ccb46c2af8a0f466febee00&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-1c498bcb93884514bb6f2c838ed48fb4
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png
