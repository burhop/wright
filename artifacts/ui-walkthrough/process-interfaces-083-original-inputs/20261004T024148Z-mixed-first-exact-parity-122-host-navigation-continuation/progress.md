# Printed first-run saved-interface walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-04T02:46:41.431Z UTC — Workspace offers Workflows

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055
Action: Open Repeated focus-wheel preparation proof workspace.
Controls: Workflows
Expected: The workspace loads and offers Workflows.
Actual: Normal workspace and Workflows control visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-04T02:46:43.010Z UTC — Workflows opens the editor

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Use saved process
Expected: Editor and working-view action appear.
Actual: Editor and working-view action visible.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-04T02:46:43.413Z UTC — Workflow file controls

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Workflow files.
Controls: Workflow files, Open workflow
Expected: Open workflow is offered.
Actual: Existing file actions are visible.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-04T02:46:44.060Z UTC — Choose the focus-wheel workflow

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical
Action: Click Open workflow.
Controls: Open workflow, workflows/printed-replacement-part-mixed-default-071.workflow.wflow
Expected: The accepted focus-wheel workflow is listed.
Actual: Exact accepted workflow choice visible.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-04T02:46:45.423Z UTC — Focus-wheel workflow diagram

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow
Action: Choose the accepted focus-wheel workflow file.
Controls: workflows/printed-replacement-part-mixed-default-071.workflow.wflow, Use saved process
Expected: Accepted focus-wheel diagram and working view action available.
Actual: Exact saved focus-wheel source is open.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-04T02:46:46.499Z UTC — Shared working view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589
Action: Click Use saved process.
Controls: Use saved process
Expected: Common working view in a workspace tab.
Actual: Common working view visible.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-04T02:46:48.406Z UTC — Attach the actual focus-wheel run

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Reopen the recorded focus-wheel run link.
Controls: Create or choose interface
Expected: The common working view attaches without starting another run.
Actual: Existing focus-wheel run attached.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-04T02:46:54.418Z UTC — Common view retains the actual review hold and preparation results

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Inspect the common working view of the recorded held preparation run.
Controls: Create or choose interface
Expected: Twenty exact first-run results and the original mandatory human-review hold.
Actual: Common results match the authoritative failed-run contract.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-04T02:47:19.182Z UTC — Common view reads the retained source geometry

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Click Open representation on the repaired_mesh.stl result.
Controls: Open representation, Close representation
Expected: A visible 3D canvas for the actual first-run source.
Actual: Actual repaired geometry is visible in the common view.
Status: pass
Screenshots: screenshots/raw/S08G.png; screenshots/annotated/S08G.png

## 2026-10-04T02:47:22.251Z UTC — Common view exposes actual nominal toolpaths

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Open support-preview.json, select layer two, hide supports, then restore all layers and supports.
Controls: Open representation, Layers, Support paths
Expected: 90 recorded layers with working visibility controls.
Actual: Exact recorded nominal paths and controls render in the common view.
Status: pass
Screenshots: screenshots/raw/S08T.png; screenshots/annotated/S08T.png

## 2026-10-04T02:47:31.605Z UTC — Saved working interface agrees with the common view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=0c60594e-946c-4ae5-a3a0-ca6159da6f39&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6&processUIKind=working&processUI=ui-f47e26fbcc2e44a2a7c4dc939aef1948&processUIRevision=revision-b1d66dc13ace45889297568cd38c6ee0
Action: Select Focus-wheel original-input preparation and click Open saved interface.
Controls: Saved interface, Open saved interface
Expected: Exact same twenty result identities and original review-hold diagnostic.
Actual: Saved working interface agrees with the common view.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png

## 2026-10-04T02:47:47.560Z UTC — Actual repaired geometry remains inspectable

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Reload the saved view and click Open representation on repaired_mesh.stl.
Controls: Open representation
Expected: The exact first-run repaired STL and a visible 3D canvas.
Actual: The shared reader renders the exact repaired geometry through the saved interface’s exact host navigation.
Status: pass
Screenshots: screenshots/raw/S10.png; screenshots/annotated/S10.png

## 2026-10-04T02:48:05.464Z UTC — The original exact held assessment opens

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Click Open assessment on repaired_mesh.stl.
Controls: Open assessment
Expected: 17 passed checks, one mandatory review hold, exact repaired result focus.
Actual: The original full source assessment opens on the exact requested result.
Status: pass
Screenshots: screenshots/raw/S10A.png; screenshots/annotated/S10A.png

## 2026-10-04T02:48:26.005Z UTC — Saved interface exposes the same actual nominal toolpaths

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processView=69d15e67-e8fa-4c89-91e5-b09bab824aa9&processPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow&processDigest=2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589&processRun=85d929ee36e64afdaee61a5cdb0fc2a6
Action: Reopen the saved interface, open support-preview.json and exercise layer and support visibility controls.
Controls: Open representation, Layers, Support paths
Expected: The same 90 recorded layers and controls.
Actual: Identical nominal toolpath evidence opens in the shared viewer from the saved interface.
Status: pass
Screenshots: screenshots/raw/S10T.png; screenshots/annotated/S10T.png

## 2026-10-04T02:48:42.843Z UTC — Exact producer opens in the accepted editor

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-mixed-default-071.workflow.wflow
Action: Return to the saved view and click Open producing step on repaired_mesh.stl.
Controls: Open producing step
Expected: Accepted process and exact repaired-mesh producer selected.
Actual: The original producing block opens in the preserved editor.
Status: pass
Screenshots: screenshots/raw/S11.png; screenshots/annotated/S11.png
