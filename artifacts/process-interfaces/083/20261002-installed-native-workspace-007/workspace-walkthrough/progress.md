# Installed native process workspace walkthrough

Prepared before navigation. Authenticated browser trace remains private.

## 2026-10-02T20:21:17.710Z UTC — Installed workspace loads
URL: http://127.0.0.1:8032/workspace/083-heat-live-005
Action: Open native home and proof workspace.
Controls: Workflows
Expected: Native session bootstrap and workspace entry.
Actual: Installed frontend loads with native HttpOnly session and Workflows control.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T20:21:20.721Z UTC — Established editor entry
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Existing editor in workspace.
Actual: Workflow file menu and editor open within the installed workspace.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T20:21:23.259Z UTC — Saved engineering workflow
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files, then Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-001.workflow.wflow
Expected: Exact accepted wheel source offered.
Actual: Accepted wheel workflow appears in the installed file chooser.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T20:21:25.072Z UTC — Authoring and working views share source
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow
Action: Choose the accepted wheel source.
Controls: Use saved process
Expected: Same accepted source in diagram and working view.
Actual: The original review/repair/slice source is open with Use saved process enabled.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T20:21:25.794Z UTC — Installed common working view
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=d284dfd7-d6fb-4d32-bd0f-efe1c12c4014&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f
Action: Click Use saved process.
Controls: Create or choose interface
Expected: Common view opens as a workspace tab.
Actual: Installed shared common view opens without starting another run.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T20:21:34.024Z UTC — Exact existing run remains waiting
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=d284dfd7-d6fb-4d32-bd0f-efe1c12c4014&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Open recorded second-run link.
Controls: Review the next action
Expected: Existing second run remains at its declared review.
Actual: Common view shows the same second run and pending geometry-basis review.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T20:21:43.999Z UTC — Saved UI independent of authoring compiler
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=d284dfd7-d6fb-4d32-bd0f-efe1c12c4014&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Click Create or choose interface.
Controls: Saved interface
Expected: Unavailable compiler explained; saved interfaces offered.
Actual: Compiler unavailable is explicit and the saved interface chooser remains usable.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T20:21:44.701Z UTC — Existing built revision selected
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=d284dfd7-d6fb-4d32-bd0f-efe1c12c4014&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Choose saved focus-wheel interface and current revision.
Controls: Open saved interface
Expected: Previously generated immutable revision selectable.
Actual: Exact original saved UI/revision selected without generating or compiling.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T20:23:45.345Z UTC — Installed journey stopped
URL: http://127.0.0.1:8032/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=dc75b484-e063-4402-bebe-9a43f34b3214&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Stop at first unexpected state.
Controls: Current workspace control
Expected: Installed common/saved journey remains usable.
Actual: expect(locator).toBeVisible() failed

Locator: locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "to.be.visible" with timeout 120000ms
  - waiting for locator('[data-testid="surface-panel-host"]:visible').locator('iframe').contentFrame().getByText('Connected to Wright.', { exact: true })

Status: blocked
Screenshots: screenshots/raw/STOP.png; screenshots/annotated/STOP.png
