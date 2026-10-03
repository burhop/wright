# Printed second-run saved-interface walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T07:05:28.873Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T07:05:29.690Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T07:05:30.081Z UTC — Workflow file controls

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T07:05:30.631Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-repeatable-default-015.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T07:05:32.462Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-repeatable-default-015.workflow.wflow, Use saved process
Expected: Accepted heat diagram and working view action available.
Actual: Exact saved heat source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T07:05:33.075Z UTC — Shared working view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=5ef7500e-b042-4ce1-a22b-ef68e4670f46&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T07:05:36.002Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=5ef7500e-b042-4ce1-a22b-ef68e4670f46&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T07:05:37.792Z UTC — Common view retains the actual failure and partial results

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=5ef7500e-b042-4ce1-a22b-ef68e4670f46&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Inspect the common working view of the recorded failed run.
Controls: Create or choose interface
Expected: Two exact first-run results and the recorded model timeout.
Actual: Common results match the authoritative failed-run contract.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T07:05:44.024Z UTC — Common view reads the retained source geometry

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=5ef7500e-b042-4ce1-a22b-ef68e4670f46&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43
Action: Click Open representation on the source_mesh.stl result.
Controls: Open representation, Close representation
Expected: A visible 3D canvas for the actual first-run source.
Actual: Actual partial source geometry is visible in the common view.
Status: pass
Screenshots: screenshots/raw/S08G.png; screenshots/annotated/S08G.png

## 2026-10-03T07:05:49.781Z UTC — Saved working interface agrees with the common view

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3221278d-6ab0-45d2-ba8f-fd56b8ab3e84&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=working&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-35cac9bd65794c36a408135a71ac0a65
Action: Select Focus-wheel digital preparation and click Open saved interface.
Controls: Saved interface, Open saved interface
Expected: Exact same two result identities and model-timeout diagnostic.
Actual: Saved working interface agrees with the common view.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T07:05:58.892Z UTC — Actual source geometry remains inspectable

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processView=3221278d-6ab0-45d2-ba8f-fd56b8ab3e84&processPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow&processDigest=9c782e103202a11bef40a94faa03c6d58eb35d890fdd3653659a78eff9895b82&processRun=86289015177e4d55ab93460101ec1d43&processUIKind=working&processUI=ui-ee4c80bbdfad4b2d9468b37a4dbc0451&processUIRevision=revision-35cac9bd65794c36a408135a71ac0a65
Action: Reload the saved view and click Open representation on source_mesh.stl.
Controls: Open representation
Expected: The exact first-run source STL and a visible 3D canvas.
Actual: The shared reader renders the exact source geometry within the tailored view.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T07:06:13.076Z UTC — Entry stopped

URL: http://127.0.0.1:5245/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-repeatable-default-015.workflow.wflow
Action: Stop at the unexpected entry state.
Controls: Workflows
Expected: Workspace and established editor available.
Actual: expect(locator).toHaveAttribute(expected) failed

Locator: locator('[data-workflow-file="workflows/printed-replacement-part-repeatable-default-015.workflow.wflow"]:visible').locator('[data-semantic-id="create_mesh_repeatable_default_015"]')
Expected: "true"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "to.have.attribute.value" with timeout 5000ms
  - waiting for locator('[data-workflow-file="workflows/printed-replacement-part-repeatable-default-015.workflow.wflow"]:visible').locator('[data-semantic-id="create_mesh_repeatable_default_015"]')

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
