# Focus-wheel workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T06:45:50.552Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T06:45:51.873Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T06:45:52.294Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T06:45:52.914Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-repeatable-default-015.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T06:45:54.731Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-repeatable-default-015.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T06:45:55.475Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T06:45:58.391Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T06:45:59.991Z UTC — Wright interface authoring

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Update selected interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T06:46:08.773Z UTC — Visible interface creation

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Enter Interface title: Focus-wheel digital preparation. Request: Make a focused update to the supplied previous source: retain the existing heading and responsive evidence grid, and add this concise limitation beside results: Digital geometry and slice evidence do not establish fit, strength or physical print acceptance. Use existing shared diagnostics to explain a failed upstream model step, preserving every input/readiness, progress, interaction and exact result/evidence/assessment/block callback and ResultRepresentation viewer. Do not invent failure state, retry controls, verdicts, measurements, execution or protocols. Keep new manifest identities and parent revision; reuse across runs without fixed paths or run IDs. Return only required source/manifest JSON.. Click Update selected interface.
Controls: Interface title, How should this interface help the user?, Update selected interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T06:47:05.346Z UTC — Built comparison ready

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T06:47:10.531Z UTC — Managed focus-wheel preparation preview

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=6fce7513-29f0-41e7-9e72-8de3b30978fd&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=preview&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-35cac9bd65794c36a408135a71ac0a65&processUIJob=job-e47145a3281a4c4fb945c3e9d8902e9d
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T06:47:11.873Z UTC — Reusable focus-wheel interface saved

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3d5b18df-ee50-4c17-8e71-a184f03bc854&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-03T06:47:17.934Z UTC — Saved focus-wheel preparation opens

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=45429b41-e751-4570-adb2-4eeb69347dd1&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=working&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-35cac9bd65794c36a408135a71ac0a65
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png
