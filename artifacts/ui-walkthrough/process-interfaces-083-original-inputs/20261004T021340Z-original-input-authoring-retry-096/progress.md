# Focus-wheel workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-04T02:13:51.411Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-04T02:13:52.551Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-04T02:13:52.999Z UTC — Workflow file controls

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-04T02:13:53.633Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-mixed-default-071.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-04T02:13:55.529Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-mixed-default-071.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-04T02:13:56.621Z UTC — Shared working view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-04T02:13:59.573Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-04T02:14:00.783Z UTC — Wright interface authoring

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Click Create or choose interface.
Controls: Interface title, How should this interface help the user?, Create interface
Expected: Native authoring controls tied to this exact process.
Actual: Wright interface authoring controls visible.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-04T02:14:25.244Z UTC — Visible interface creation

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Enter Interface title: Wheel evidence. Request: Use the supplied reference UI unchanged except its heading: Wheel evidence. Keep every reference callback and shared component, all exact process bindings and public client scopes. Return only the required source/manifest JSON.. Click Create interface.
Controls: Interface title, How should this interface help the user?, Create interface, Interface creation progress
Expected: Accepted job and visible generation progress.
Actual: Actual interface job accepted; creation progress visible.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-04T02:15:02.783Z UTC — Built comparison ready

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Wait for Preview ready.
Controls: Open preview
Expected: Successful built revision ready for preview.
Actual: Preview ready is visible.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-04T02:15:08.943Z UTC — Managed focus-wheel preparation preview

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=beac4738-c7c8-4c56-89cc-4131f824cf83&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6&processUIKind=preview&processUI=ui-f47e26fbcc2e44a2a7c4dc939aef1948&processUIRevision=revision-fd3eb8640fb4409d8e04a62a2408f503&processUIJob=job-bfb37b924d534dbbab48e2788b5f6a4e
Action: Click Open preview.
Controls: Open preview
Expected: Isolated managed preview renders and reads the process contract.
Actual: Managed preview connected and rendered.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png

## 2026-10-04T02:15:10.460Z UTC — Reusable focus-wheel interface saved

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=de346ab6-0e61-43cf-8a51-c207bcd8ec1d&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Return to the common tab and click Save interface.
Controls: Save interface, Open saved interface
Expected: The exact previewed revision is saved.
Actual: Interface saved with its built revision.
Status: pass
Screenshots: screenshots/raw/S12.png; screenshots/annotated/S12.png

## 2026-10-04T02:15:17.154Z UTC — Saved focus-wheel preparation opens

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=9ee386fb-92cf-4369-bc83-3d9fea26c823&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6&processUIKind=working&processUI=ui-f47e26fbcc2e44a2a7c4dc939aef1948&processUIRevision=revision-fd3eb8640fb4409d8e04a62a2408f503
Action: Click Open saved interface.
Controls: Open saved interface
Expected: Saved working interface connected to the same process/run.
Actual: Saved comparison is connected in a workspace tab.
Status: pass
Screenshots: screenshots/raw/S13.png; screenshots/annotated/S13.png
