# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T05:22:51.240Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T05:22:52.329Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T05:22:52.786Z UTC — Workflow file controls

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T05:22:53.471Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T05:22:54.976Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-repeatable-default-013.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T05:22:55.588Z UTC — Shared working view

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T05:22:59.271Z UTC — Attach the actual heat run

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Reopen the recorded heat run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing heat run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T05:22:59.592Z UTC — Wright interface authoring

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T05:23:08.448Z UTC — Visible interface creation

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Enter Interface title: Heat-spreader candidate comparison. Request: Adapt the supplied reference into a Heat-spreader candidate comparison. Reuse its public components, callbacks, all inputs/readiness, progress, pending interactions, ResultRepresentation viewers and exact evidence/assessment/block navigation. Change the heading and arrange current result cards in a responsive comparison grid. Keep all contract data and manifest identities; work across runs without fixed output filenames or run IDs. Keep source concise by reusing the reference, without new controls, custom viewers, execution, verdicts or protocols. Return only the required source/manifest JSON.. Click Create interface.
Controls: Interface title, How should this interface help the user?, Create interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T05:24:43.454Z UTC — Built comparison ready

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T05:24:48.223Z UTC — Managed heat comparison preview

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=579c0b6e-6098-495a-89d6-3e9ef836b316&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2&processUIKind=preview&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-1307d9f0c2ad4bc78d204efd64c4da91&processUIJob=job-f24cdd3e48684f28a7d306fa6d72cacc
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T05:24:49.337Z UTC — Reusable heat interface saved

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=68b4bb73-959b-43d6-880e-1ee31f19f49c&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T05:24:54.831Z UTC — Saved heat comparison opens

URL: http://127.0.0.1:5244/workspace/083-heat-repeat-013?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processView=bd57575e-4e51-467e-ad33-6002fa9174bd&processPath=workflows%2Fheat-spreader-sizing-repeatable-default-013.workflow.wflow&processDigest=d941977f20b6ec345f0ec8959fddaa76833b9546278c2af5d9f0d71fede5536b&processRun=503a32a91e454a219bcbe2f2da3b99b2&processUIKind=working&processUI=ui-512d6109b37f4c0f89b86d86a34827b2&processUIRevision=revision-1307d9f0c2ad4bc78d204efd64c4da91
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png
