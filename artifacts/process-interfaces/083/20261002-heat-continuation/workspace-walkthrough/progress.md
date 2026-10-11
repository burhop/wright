# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T02:49:34.273Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open Heat-spreader comparison proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T02:49:35.227Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T02:49:35.705Z UTC — Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T02:49:36.383Z UTC — Choose the heat workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/heat-spreader-sizing-live-default-model-001.workflow.wflow
Expected: The accepted heat workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T02:49:37.904Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow
Action: Choose the accepted heat workflow file.
Controls: workflows/heat-spreader-sizing-live-default-model-001.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T02:49:38.701Z UTC — Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processView=0748f16f-ad33-4eb8-8911-fdd7d6b38fab&processPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processDigest=4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T02:49:50.648Z UTC — Durable review wait

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processView=0748f16f-ad33-4eb8-8911-fdd7d6b38fab&processPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processDigest=4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c&processRun=86533be67a404058bc21a633146bd598
Action: Open the exact recorded heat run link in the same workspace.
Controls: Declared basis review, Continue process
Expected: Declared review waiting state, no automatic continuation.
Actual: Actual run waiting for review is visible.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T02:49:50.923Z UTC — Explicit continuation confirmation

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processView=0748f16f-ad33-4eb8-8911-fdd7d6b38fab&processPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processDigest=4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c&processRun=86533be67a404058bc21a633146bd598
Action: Inspect the recorded test decision and confirmation.
Controls: Test review recorded: Approved, I reviewed this action and its evidence
Expected: A synthetic review label and explicit confirmation.
Actual: Test review and confirmation visible.
Status: pass
Screenshots: screenshots/raw/S08a.png; screenshots/annotated/S08a.png

## 2026-10-02T02:49:51.557Z UTC — Synthetic test review is labelled

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processView=0748f16f-ad33-4eb8-8911-fdd7d6b38fab&processPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processDigest=4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c&processRun=86533be67a404058bc21a633146bd598
Action: Inspect the recorded test decision.
Controls: Test review recorded: Approved, Continue process
Expected: Test review label and enabled continuation for this exact run.
Actual: Synthetic decision visible; Continue process enabled.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T02:50:02.031Z UTC — Same run continues

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processView=0748f16f-ad33-4eb8-8911-fdd7d6b38fab&processPath=workflows%2Fheat-spreader-sizing-live-default-model-001.workflow.wflow&processDigest=4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c&processRun=86533be67a404058bc21a633146bd598
Action: Click Continue process.
Controls: Continue process
Expected: The same recorded run becomes Running.
Actual: Continuation accepted; same-run running progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png
