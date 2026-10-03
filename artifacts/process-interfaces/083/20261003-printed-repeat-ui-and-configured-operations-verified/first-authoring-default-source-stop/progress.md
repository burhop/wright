# Focus-wheel workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T06:39:28.331Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T06:39:29.684Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T06:39:30.154Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T06:39:30.819Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-repeatable-default-015.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T06:39:32.656Z UTC — Heat workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-repeatable-default-015.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T06:39:33.584Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T06:39:37.513Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T06:39:38.372Z UTC — Wright interface authoring

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T06:39:49.054Z UTC — Visible interface creation

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Enter Interface title: Focus-wheel digital preparation. Request: Adapt the supplied reference into a Focus-wheel digital preparation. Reuse its public components, callbacks, all inputs/readiness, progress, pending interactions, ResultRepresentation viewers and exact evidence/assessment/block navigation. Change the heading and arrange all current geometry, package and assessment result cards in a responsive evidence grid. Keep all contract data and manifest identities; work across runs without fixed output filenames or run IDs. Keep source concise by reusing the reference, without new controls, custom viewers, execution, verdicts or protocols. Return only the required source/manifest JSON.. Click Create interface.
Controls: Interface title, How should this interface help the user?, Create interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T06:41:25.966Z UTC — Built comparison ready

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T06:41:31.409Z UTC — Managed focus-wheel preparation preview

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=488489a7-39d0-44f3-b5fa-5278f7035325&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=preview&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-7c446bc5e93e441e8bf651db6d33b83a&processUIJob=job-96a897c75b0e4a5e9406605715171139
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T06:41:32.419Z UTC — Reusable focus-wheel interface saved

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=9c274f3a-c7b9-4cc9-901d-2de0d0b0c8a4&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T06:41:38.461Z UTC — Saved focus-wheel preparation opens

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=8391745e-a4bf-4904-a1a8-3488d25dff67&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=working&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-7c446bc5e93e441e8bf651db6d33b83a
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png

## 2026-10-03T06:41:38.678Z UTC — Entry stopped

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=8391745e-a4bf-4904-a1a8-3488d25dff67&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=working&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-7c446bc5e93e441e8bf651db6d33b83a
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(received).toEqual(expected) // deep equality

- Expected  - 2
+ Received  + 9

  Object {
-   "console": Array [],
-   "failedResponses": Array [],
+   "console": Array [
+     "Failed to load resource: the server responded with a status of 404 (Not Found)",
+   ],
+   "failedResponses": Array [
+     Object {
+       "path": "/api/workspace/workflow-sources",
+       "status": 404,
+     },
+   ],
    "pageErrors": Array [],
  }
Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
