# Test Wright as an engineer

10 October 2026 · working build 45 · **product testing in progress**

Start in [Mechanical design studies](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5).
Use your existing signed-in Wright browser tab. These links contain no token.
If authentication is requested, use Wright's normal sign-in; do not put a token
in a URL, annotation or shared screenshot.

## Where are the model, image and drawing?

**Focus-wheel replacement:** [open its recorded run in Wright](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-native-focus-wheel-051.workflow.wflow&processView=83c04c28-63ca-40c3-85a8-848084aea3c5&processPath=workflows%2Fprinted-replacement-part-native-focus-wheel-051.workflow.wflow&processDigest=cc914d841858eb0c8c4a64f3437c4ab144b6f763cd1425ae021fc37bbc0b8477&processRun=79b02848cf4e481bbee3f7a26a9d19ae).
This saved process connects native FreeCAD geometry, drawing and inspection,
Blender mesh preparation, and offline PETG slicing. The recorded run retains its
actual outputs; opening it does not require starting the CAD applications.

- [CAD preview](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/files/native-design.png)
- [Inspection drawing PDF](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/files/inspection-drawing.pdf)
- [STEP model](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/files/native-design.step) · [editable FreeCAD model](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/files/native-design.FCStd)
- [Requirements and verification matrix](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/files/requirements-matrix.md)
- [Illustrated process and orientation comparison](D:/repos/wright/artifacts/process-interfaces/083/20261010-wheel-post-review-fix/report.html)

**A different engineering process:** [open heat-spreader sizing in Wright](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5?workflow=canonical&workflowPath=workflows%2Fheat-spreader-sizing-thermal-002.workflow.wflow&processView=fbfa1e6c-65a5-47f1-9ef5-b5f963214734&processPath=workflows%2Fheat-spreader-sizing-thermal-002.workflow.wflow&processDigest=2430de4cb970a448febbbf82c3d300957be0cfdb9f0793d7f3836571de5f2e4d&processRun=f01d057d9842441797ef7c803c3a2044).
AgentCAD/build123d geometry feeds OASiS/scikit-fem analysis. Inspect the
[assumptions and analysis basis](D:/repos/wright/artifacts/process-interfaces/083/20261010-thermal-offline-review/files/thermal-basis.md),
[illustrated comparison](D:/repos/wright/artifacts/process-interfaces/083/20261010-thermal-offline-review/index.html),
and [current verification report](D:/repos/wright/artifacts/process-interfaces/083/20261010-engineering-measurement-context/thermal/assessment-dbd4b81f5ded489e8dc3649c1a501e6e/report.md).

Both recorded processes stopped at an unmet mandatory human-review check. Their
digital outputs remain available. The execution state is `failed`; the common
working view labels it **Process needs attention**. Neither run is a completed
engineering release or evidence of a physical print. These retained test records
should be inspected without submitting new reviews or restarting them.

## Short product checklist

Use a **new blank workflow** for editing checks; keep the saved engineering
examples above as read-only references. No printer or supplier action is needed.

| Try this | What should happen |
| --- | --- |
| Open **Workflows** from the workspace activity bar. | A new workflow is blank. It does not silently substitute an example. |
| Add a text input and an MCP task; select an available workspace server and draw the text output into its prompt input. | Real configured servers appear, and the connection is reflected in the inspector/source. An unavailable provider is explained rather than reported ready. |
| Leave a required input unconfigured and inspect **Run readiness**. | The missing item and affected block are identified before execution. **Not started** is distinct from readiness. |
| Edit a block, try closing its tab, and choose **Keep editing**. Then save and reopen. | The draft survives the first action; the saved version survives reopening. Also try switching workspace and refreshing with an unsaved draft. |
| Open the wheel run's drawing, preview and requirements matrix from its results. | Each opens the actual saved file in Wright, with a usable download. No rerun is needed to see outputs. |
| Open a wheel or thermal assessment. | Required and observed values, units, finding, recorded uncertainty and required review are readable. Exact data remains available. A zero uncertainty allowance does not claim zero physical error. |
| Inspect the [earlier correction study](http://127.0.0.1:5250/workspace/a6d46bd6-8b43-4263-ae5f-99d8d9924ee5?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-native-focus-wheel-026.workflow.wflow&processView=246ea758-063e-41ac-af22-3673d0ef44dc&processPath=workflows%2Fprinted-replacement-part-native-focus-wheel-026.workflow.wflow&processDigest=fc93ef77719eb23b0b20258465680a02270413f938d0face8ad8e36c16ef5607&processRun=3843a8c98e0f40e1a15f90790a33b6b8). | The original failed socket/drawing checks and corrected result are both available. Its declared human review stays pending; inspection does not answer it. |
| Close/reopen or refresh a recorded run. | It retains the same results and pending decisions without resubmitting work. If a read fails, refresh reconciles with the saved run. |
| Inspect workflow export/import findings before importing a new copy. | Warnings identify the particular missing provider, profile or other dependency. Export does not convey credentials or earlier approval authority. |

For an annotation, include the action attempted, expected outcome and visible
result. Keep the workflow/run in the link so the exact subject can be found.

## What improved, and what is still open?

Recent shared fixes protect unsaved and in-flight saves, make idle readiness
honest, identify import dependencies, restore historical assessment access, and
make engineering findings and measurement limits easier to read. See the
[current evidence and limits](evidence/mechanical-lifecycle-coverage-085.md).

Progress now distinguishes the whole process from each tool's reported state.
A tool saying it completed cannot hide a missing required output. An unconfirmed
cancellation remains explicit, with actions held until reconciliation. See the
[before/after checks and their software-fixture scope](evidence/process-observation-scope-086.md).
For malformed inspection data, the correction summary now lists each distinct
cause once while preserving every individual failed check in the assessment.
See the [malformed-output repair](evidence/process-malformed-output-087.md).

The full goal remains unfinished. You authorized a separate 130 mm shelf variant
for the dock. Its [separate R5 process and current evidence](evidence/dock-130-variant-088.md)
are now saved. The initial run retained supplier research but timed out preparing
intent; no CAD was produced. A corrected direct material-inventory handoff is
saved and software-tested, with live execution still pending. The original75mm
design remains preserved. The reviewed responsibility/swim-lane
implementation still needs locating. Browser coverage now includes software
fixtures for uncertain cancellation, missing files and nonempty malformed data.
These do not certify live provider behavior. A final pair of fresh engineering journeys remains
due after product changes settle. Keep native application launch/provider
availability separate from the ability to inspect retained results. PPT work is
deferred.

The UI/API and the three exact-run links above were checked on 10 October;
local artifact links were checked for existence and recorded by hash. This guide
is a handoff for user testing, not a claim of user acceptance or a fresh execution
of the engineering examples.
