# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T15:33:05.322Z UTC â€” Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Focus-wheel comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T15:33:08.202Z UTC â€” Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T15:33:08.920Z UTC â€” Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T15:33:09.842Z UTC â€” Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-001.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T15:33:12.243Z UTC â€” Wheel workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-retained-consumer-001.workflow.wflow, Use saved process
Expected: Accepted wheel diagram and working view action available.
Actual: Exact saved wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T15:33:14.157Z UTC â€” Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=29f175f7-f8db-4bfa-9a24-3a5713fc1f5c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T15:33:18.914Z UTC â€” Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=29f175f7-f8db-4bfa-9a24-3a5713fc1f5c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T15:33:41.102Z UTC â€” Second run waits at its declared review

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=29f175f7-f8db-4bfa-9a24-3a5713fc1f5c&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Open the second durable run in the common working tab.
Controls: Review the next action
Expected: Actual waiting review with the second run’s exact subject.
Actual: Second run is waiting for the declared geometry-basis review.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T15:34:32.807Z UTC â€” Saved interface prepares exact inputs

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=63f13604-eaf5-48fd-b78b-b93ec75cc1a9&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Open saved UI without a run, then click Check inputs and readiness. Leave Start untouched.
Controls: Check inputs and readiness, Start process
Expected: Start disabled before explicit preparation, enabled only after backend readiness for those inputs.
Actual: Prepared inputs and backend-permitted Start visible; no start requested.
Status: pass
Screenshots: screenshots/raw/S08a.png; screenshots/annotated/S08a.png

## 2026-10-02T15:34:57.206Z UTC â€” Unchanged saved comparison follows the new run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=63f13604-eaf5-48fd-b78b-b93ec75cc1a9&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Open the same saved interface link with the second recorded run selected.
Controls: Review the next action, Open representation, Open producing step
Expected: Same UI revision, second run’s waiting state and one current result.
Actual: Same saved revision connected; second run result and declared waiting review shown.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T15:35:39.130Z UTC â€” Reload reconciles the waiting second run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=63f13604-eaf5-48fd-b78b-b93ec75cc1a9&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Reload the saved second-run comparison.
Controls: Review the next action
Expected: No start, regeneration or review response from reload.
Actual: Same second-run waiting subject and single result restored.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
