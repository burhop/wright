# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-02T06:07:17.482Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5243/workspace/083-heat-live-005
Action: Open isolated engineering proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-02T06:07:20.143Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-02T06:07:20.674Z UTC — Workflow file controls

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-02T06:07:22.250Z UTC — Choose the wheel workflow

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-live-default-model-004.workflow.wflow
Expected: The accepted wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-02T06:07:23.944Z UTC — Wheel workflow diagram

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow
Action: Choose the accepted wheel workflow file.
Controls: workflows/printed-replacement-part-live-default-model-004.workflow.wflow, Use saved process
Expected: Accepted wheel diagram and working view action available.
Actual: Exact saved wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-02T06:07:24.904Z UTC — Shared working view

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processView=a4eec8da-1b90-4e59-bba0-54a1cbfaada9&processPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processDigest=bb43c03ebc365a77785527a699e807bed060b5caf264b9773804d892a5d798c6
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-02T06:07:28.294Z UTC — Attach the actual wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processView=a4eec8da-1b90-4e59-bba0-54a1cbfaada9&processPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processDigest=bb43c03ebc365a77785527a699e807bed060b5caf264b9773804d892a5d798c6&processRun=adb5cefc54a545eda7abcb9ab9b9fbdc
Action: Reopen the recorded wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-02T06:07:50.052Z UTC — Original wheel waits for its declared basis review

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processView=a4eec8da-1b90-4e59-bba0-54a1cbfaada9&processPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processDigest=bb43c03ebc365a77785527a699e807bed060b5caf264b9773804d892a5d798c6&processRun=adb5cefc54a545eda7abcb9ab9b9fbdc
Action: Open the recorded digital wheel run.
Controls: Review the next action
Expected: Same run waits with one basis result and an undecided review.
Actual: Declared basis review is visible; no geometry or slicing has executed.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-02T06:08:05.658Z UTC — Reload preserves the waiting wheel run

URL: http://127.0.0.1:5243/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processView=a4eec8da-1b90-4e59-bba0-54a1cbfaada9&processPath=workflows%2Fprinted-replacement-part-live-default-model-004.workflow.wflow&processDigest=bb43c03ebc365a77785527a699e807bed060b5caf264b9773804d892a5d798c6&processRun=adb5cefc54a545eda7abcb9ab9b9fbdc
Action: Reload the working tab.
Controls: Review the next action
Expected: The exact declared review remains waiting.
Actual: Same waiting run restored; no review was submitted.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png
