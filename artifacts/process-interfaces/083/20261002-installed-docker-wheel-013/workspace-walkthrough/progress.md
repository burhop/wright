# Installed native process workspace walkthrough

Prepared before navigation. Authenticated browser trace remains private.

## 2026-10-02T21:03:37.038Z UTC — Installed workspace loads
URL: http://wright.localhost:8033/workspace/083-heat-live-005
Action: Open native home and proof workspace.
Controls: Workflows
Expected: Authenticated Docker workspace entry.
Actual: Installed Docker frontend loads with the existing authorized HttpOnly operator session and Workflows control.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T21:03:37.986Z UTC — Established editor entry
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflow files
Expected: Existing editor in workspace.
Actual: Workflow file menu and editor open within the installed workspace.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T21:03:38.640Z UTC — Saved engineering workflow
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files, then Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-retained-consumer-001.workflow.wflow
Expected: Exact accepted wheel source offered.
Actual: Accepted wheel workflow appears in the installed file chooser.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T21:03:39.705Z UTC — Authoring and working views share source
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow
Action: Choose the accepted wheel source.
Controls: Use saved process
Expected: Same accepted source in diagram and working view.
Actual: The original review/repair/slice source is open with Use saved process enabled.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T21:03:40.380Z UTC — Installed common working view
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=6bf19a18-3bbb-472f-9ced-a8e02a5e5769&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f
Action: Click Use saved process.
Controls: Create or choose interface
Expected: Common view opens as a workspace tab.
Actual: Installed shared common view opens without starting another run.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T21:03:44.843Z UTC — Exact existing run remains waiting
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=6bf19a18-3bbb-472f-9ced-a8e02a5e5769&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Open recorded second-run link.
Controls: Review the next action
Expected: Existing second run remains at its declared review.
Actual: Common view shows the same second run and pending geometry-basis review.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T21:03:45.408Z UTC — Saved UI independent of authoring compiler
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=6bf19a18-3bbb-472f-9ced-a8e02a5e5769&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Click Create or choose interface.
Controls: Saved interface
Expected: Unavailable compiler explained; saved interfaces offered.
Actual: Compiler unavailable is explicit and the saved interface chooser remains usable.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T21:03:45.817Z UTC — Existing built revision selected
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=6bf19a18-3bbb-472f-9ced-a8e02a5e5769&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2
Action: Choose saved focus-wheel interface and current revision.
Controls: Open saved interface
Expected: Previously generated immutable revision selectable.
Actual: Exact original saved UI/revision selected without generating or compiling.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T21:03:51.875Z UTC — Installed saved interface mounts
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=bd6d58cf-674d-49aa-a2a4-cac390f80679&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Click Open saved interface.
Controls: Review the next action
Expected: Saved React UI connected to the exact run through the installed bridge.
Actual: Saved UI renders in its workspace tab with the second run’s single result and waiting review.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-02T21:03:58.933Z UTC — Installed reopening reconciles
URL: http://wright.localhost:8033/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processView=bd6d58cf-674d-49aa-a2a4-cac390f80679&processPath=workflows%2Fprinted-replacement-part-retained-consumer-001.workflow.wflow&processDigest=7323f6ae36f36383fa9da09520c4f785255f46179e07de0331b44ca7af72549f&processRun=00201b136bff4e4e91f097891d96e8e2&processUIKind=working&processUI=ui-1e7b6edb71e74b19a754b7fd2b88633a&processUIRevision=revision-415f9e4911f0447199dd6fbd4bbc46c0
Action: Reload the saved interface tab.
Controls: Review the next action
Expected: Same run, saved revision and waiting review after reload.
Actual: Installed tab restores the same waiting run and saved compiled interface.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png
