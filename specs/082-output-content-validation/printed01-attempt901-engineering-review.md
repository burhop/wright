# Printed Part 01: focus-wheel prototype review

22 September 2026. **Pending engineering review; not approved for manufacture.**

## The engineering job

Produce a replacement hand-operated focus wheel for a fictional training
telescope. The useful result is a printable prototype design and its matching
machine-preparation package, not a claim that a physical wheel has been tested.

The connected process is **Blender design → Blender mesh repair → Bambu Studio
slicing → simulated package handoff → engineering review → final validation**.
The repair stage consumes the actual authored mesh; Bambu consumes that repaired
mesh. Recorded hashes tie the slice and simulated handoff to the exact files.
No physical printer was contacted or commanded.

## Open the results

Open [the saved workflow](http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical&workflowPath=workflows%2Fcampaign-printed-replacement-part-01-attempt-901.workflow.wflow).
Choose **Results**, then **Generate supports and slice**, select
`slice-preview.png`, and choose **Open plot or image in tab**.

The saved diagram has a duplicate connection and remains visibly flagged. Its
recorded results are now accessible without editing the definition that ran.
The preparation defect is fixed for future workflows; this original is retained.
The normal-workspace path was verified in the
[nine-step browser walkthrough](../../artifacts/ui-walkthrough/printed01-results/20260922T1932Z-recovery/report.html).

Direct file links on this computer:

- [Sliced-part preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-01/attempt-901/artifacts/slice-preview.png)
- [Repaired printable mesh](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-01/attempt-901/artifacts/repaired_mesh.stl)
- [Bambu 3MF package](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-01/attempt-901/artifacts/slice_package.gcode.3mf)
- [Original engineering brief](../../tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/context.md)

## What has been checked

A separate read-only inspection used the unchanged full validation profile.
All **17 automated checks passed**; the human-review check remains blocked.
This inspection does not execute or replace the workflow's final validation step
and does not increment campaign completion or acceptance counts.

The mesh fits the 38 mm maximum diameter / 18 mm height envelope; its measured
axis-aligned spans are 38.0 × 34.524563 × 18.0 mm. These spans do not independently
prove the minimum grip diameter or internal socket geometry. Mesh integrity and
distinct source-to-repaired lineage passed. The selected profiles match P1S with
0.4 mm nozzle, PETG, 0.20 mm layers, four walls and 35% infill. The actual 3MF
contains G-code, and package/input hashes match. Slicing recorded 5,608 extrusion
moves and no support moves; this is digital preparation, not physical print proof.

## Decisions and gaps for engineering review

| Item | Evidence and remaining decision |
| --- | --- |
| Grip and exposed edges | The preview shows six scallops and raised dots. Inspect glove-catching features and the 33 mm minimum grip. The authored hub bevel uses **0.8 mm**, while the brief requests nominal **1.0 mm** exposed-edge rounds. This discrepancy must be resolved, not silently accepted. |
| Shaft fit | The author's design values are a 6.40 mm cleared round boundary, 5.60 mm flat-to-far-round distance and 10.0 mm blind depth. These interpret the supplied 6.00 / 5.20 mm shaft with 0.20 mm radial and flat clearance. They are not independent internal measurements or a demonstrated physical fit. |
| Socket roof | Confirm at least 3.0 mm material remains beyond the blind socket and no unrequested insert, screw, taper or keyway was added. External mesh bounds alone do not prove this. |
| Orientation and supports | The preview shows the socket facing upward. The slicer generated no support moves. Review that decision for this geometry; it does not establish print success. |
| Tolerance statement | The source report distinguishes design values from measured external bounds and disclaims physical performance. It does **not** explicitly carry the brief's proposed ±0.25 mm non-mating tolerance into the deliverable. This needs correction or an explicit review finding. |

**Recommended disposition: request changes**, specifically resolve the hub-edge
round and add the missing tolerance statement, while retaining all requirements.
Do not approve the whole package merely because its automated checks passed.
Any revised mesh must go through repair, re-slicing, hash-bound review and
validation again. The agent has not recorded a human decision or changed the files.

## Traceability for support

The pending review is `checkpoint-e4ec7f837b7f20acbc7f91df` for run
`8877a99cc7054faab6b4d586b05845cb`. Its subject digest is
`2325cd6d89464536ad478d250a5368dd619ff29fa25f05dbae12ee47829be31a`.
At 19:41:39 UTC the live API reported the same pending review, no actor, and
matching current source. All 15 review-file hashes matched before and after
inspection. Full evidence:
`.local-run/renewal-qualification/printed01-canonical-901/pre-review-inspection/assessment.json`.
