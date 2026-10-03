# UI evidence negative walkthrough

Prepared before the first browser action. The authenticated trace is kept privately; published diagnostics omit credentials. Synthetic authoring and producer responses are fixture scaffolding, not live AI or engineering acceptance.

## 2026-10-03T21:02:51.662Z UTC â€” Normal installed workspace

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e
Action: Open isolated workspace
Expected: Normal Workflows control, installed frontend
Actual: Workspace loads from the current installed wheel.
Status: PASS
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T21:02:55.232Z UTC â€” Existing editor retained

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Click Workflows
Expected: Refined editor inside workspace
Actual: Established editor and workflow-file controls are present.
Status: PASS
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T21:02:57.457Z UTC â€” Saved workflow listed

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical
Action: Workflow files → Open workflow
Expected: Exact accepted fixture listed
Actual: The synthetic saved workflow is available through normal file selection.
Status: PASS
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T21:02:59.443Z UTC â€” Accepted workflow opened

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical&workflowPath=workflows%2Fui-evidence-negative-001.workflow.wflow
Action: Choose ui-evidence-negative-001.workflow.wflow
Expected: Accepted diagram; no execution
Actual: The accepted diagram opens inside the workspace.
Status: PASS
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T21:03:00.861Z UTC â€” Common view available

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?workflow=canonical&workflowPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processView=570bb821-aa7f-4498-80cf-52b93241d417&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7
Action: Click Use saved process
Expected: Common working tab using same process
Actual: Common view opens without starting a run.
Status: PASS
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T21:03:15.198Z UTC â€” Retained saved UI baseline

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-93289359a4-run-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=93289359a42dd8ec077255622aa337b5361686875f77579494eeeb48feec2cb7&processRun=1ed6c2e1302a4eb18ff7575a3fbe5be0&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open saved UI for original exact run
Expected: Original exact pending review visible
Actual: The saved UI presents the original pending review; no decision is made.
Status: PASS
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T21:03:34.284Z UTC â€” Compatible saved UI reused

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-4803e02247-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=4803e02247fc01285793c13552afc9a162e68941ddfbb73468f09ccdead74147&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open saved UI on changed accepted revision without old run
Expected: Exact same saved build, current process context and no old decision
Actual: Saved UI loads without model/compiler; current backend snapshot has no old run, outputs or reviews.
Status: PASS
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T21:03:45.286Z UTC â€” Compatible reuse survives reopening

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-4803e02247-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=4803e02247fc01285793c13552afc9a162e68941ddfbb73468f09ccdead74147&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Reopen interface view
Expected: New isolated presentation, current accepted context
Actual: Saved UI reconnects without generation/build or starting a process.
Status: PASS
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T21:03:46.704Z UTC â€” Current common view has no old permission

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-4803e02247-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=4803e02247fc01285793c13552afc9a162e68941ddfbb73468f09ccdead74147&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Use common working view
Expected: Same current process; no old run review
Actual: Common preparation view does not inherit the historical run or review.
Status: PASS
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-03T21:03:54.733Z UTC â€” Required binding change blocks saved UI

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-f22cd0b676-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=f22cd0b6761428be6cadb03902bf3ff7b7fc0aeb832a47224377cb7c5fbd36b6&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Open saved UI for renamed required output
Expected: No generated frame; exact incompatible binding and fallback
Actual: Wright contains the incompatible saved revision and explains the required binding mismatch.
Status: PASS
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-03T21:03:56.228Z UTC â€” Focused update and resource limit visible

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-f22cd0b676-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=f22cd0b6761428be6cadb03902bf3ff7b7fc0aeb832a47224377cb7c5fbd36b6&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Create or choose interface
Expected: Selected old UI, update control, explicit missing authoring capability
Actual: Update selected interface is unavailable with the missing compiler/model; saved metadata and the common view remain usable.
Status: PASS
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-03T21:03:57.230Z UTC â€” Common fallback remains usable

URL: http://wright.localhost:61679/workspace/06ac6649-2ca2-4b6c-88db-02cc9b69ff4e?processView=view-revision-working-f22cd0b676-prepare-001&processPath=workflows%2Fui-evidence-negative-001.workflow.wflow&processDigest=f22cd0b6761428be6cadb03902bf3ff7b7fc0aeb832a47224377cb7c5fbd36b6&processUIKind=working&processUI=ui-f1ca33c61df74d2ea8a96a3f284f2692&processUIRevision=revision-619a6260b1e64c51807c7fb2ed823879
Action: Click Use common working view
Expected: Current accepted inputs without old permission or replay
Actual: Common view opens for the changed accepted source. No old run/evidence/decision authority is transferred.
Status: PASS
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png
