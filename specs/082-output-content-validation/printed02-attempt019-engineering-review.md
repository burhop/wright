# P001 — Printed 02 attempt 019 engineering review

22 September 2026. **Recommendation: request changes for undersized pad rounds, and authorize one additional correction in the existing episode.** All 17 automated checks pass. The previous shoulder and thumb-recess defects are repaired, but actual pad/bore rounds measure **0.969205 mm**, below the supplied 1 mm minimum. The isolated correction already measures **1.010000 mm** while preserving the grip. It has not been dispatched as a campaign successor.

This is correction 2 of 2 in `printed02-final-feature-review`, whose baseline remains attempt 017. A further canonical run requires explicit authority to increase that same episode's limit to 3. History must remain intact; changing an attempt ID does not renew the budget. No successor or physical print is approved.

[Open the actual workflow results](http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical&workflowPath=workflows%2Fcampaign-printed-replacement-part-02-attempt-019.workflow.wflow).

## Demonstrated in the exact current files

The canonical run performed actual Blender authoring, repair, Bambu slicing and a simulated handoff. Its construction matches the audited source except for the two export paths; its repaired STL is byte-identical to qualification 015. All 16 review-file hashes were verified before and after read-only inspection with the unchanged full profile. Mandatory human review remains blocked and the canonical validator step has not run.

| Feature | Actual evidence |
|---|---|
| Envelope | 114 × 24.200000 × 34 mm, within 118 × 28 × 34 mm. |
| Finger clearance | Final-triangle clipping measures 25.000 mm throughout X=15.5..80.5. |
| Shoulders | Perpendicular oval sweep replaces the abrupt shoulders. Measured inner profile radii are at least 3.6939 mm; maximum adjacent-face turn on the bow is 14.55°, compared with the previous roughly 81° shoulder crease. |
| Bow/pad junctions | Explicit tangent root profiles measure 1.0494–1.0505 mm. The root footprint is constrained by the bore lip and flat pad-top boundary, preventing a uniform 3 mm root fillet. Larger blends are used in the shoulders. |
| Thumb recess | Present throughout the central X=28..68 interval, returning to the uncut surface at both ends; measured center depth is 1.5000002 mm in float32 mesh coordinates. |
| Mounting bores | Centers (0,0)/(96,0), spacing 96.000 mm; measured X/Y diameters 4.500 mm at three depths. The faceted minimum centered diameter is 4.4946 mm, explicitly disclosed for review without inventing a tolerance. |
| Mesh and native design | One closed manifold component, 18,320 final triangles, no zero-area triangles; editable native `.blend` included. No voxel remesh, scaling or decimation. |
| Orientation and slice | Pads-down preserves vertical bores and about 649.8 mm² flat bed contact. Side orientations put the bores horizontal and alter grip contact. Actual P1S 0.4 mm/PETG/0.20 mm/five-wall/40% slice has 31,990 extrusion moves, including 4,732 support moves. Support contacts lie beneath the raised bow. No printer connection. |

## Remaining PRINT02-GRIP defect and concrete correction

The retained pad construction requested 1 mm bevels with Blender's default overlap clamping. Actual outer-wall tangencies are Z=0.9692049 and Z=4.0307951 on each 5 mm pad; the quarter-circle construction therefore has 0.9692049 mm radii. Bore-axis tangencies show the same reduction. A nominal modifier setting is insufficient evidence of the final radius.

This retained pad detail was missed by the earlier grip-only qualification. The current audit adds explicit pad/bore tangency measurements and preserves the earlier evidence unchanged. The part is not fully approved merely because all automated checks pass.

The prepared correction changes both pad bevel settings from 1.00 mm with default clamping to **1.01 mm with overlap clamping disabled**. Native qualification 016 and independent final-mesh inspection show 1.00999999 mm pad/bore tangency heights, unchanged 25 mm clearance, the same root/shoulder/recess profiles, zero degenerate triangles and no folded-root finding. The native session exited through guarded cleanup. This qualification supplies evidence for one bounded successor; it does not approve or replace the current package.

- [Exact current full-profile inspection](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-canonical019-review/assessment.json)
- [Current grip measurements](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-019-grip-measurements.json)
- [Current pad-rounding measurements](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-019-final-pad-rounds.json)
- [Canonical construction correspondence](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-019-construction-correspondence.json)
- [Qualified correction source](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-grip-correction-source-v6.py)
- [Native pad-correction proof](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-grip-repair-qualification-v7.json)
- [Corrected pad measurements](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-pad-corrected-round-measurements.json)
- [Corrected grip measurements](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-pad-corrected-grip-measurements.json)

## Review artifacts

- [Native Blender design](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/native-design.blend)
- [Mesh preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/mesh-preview.png)
- [Actual sliced preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/slice-preview.png)
- [Support preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/support-preview.svg)
- [Repaired STL](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/repaired_mesh.stl)
- [Sliced 3MF](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-019/artifacts/slice_package.gcode.3mf)

## Exact decision identity

- Run: `4a16015946e94f898727b0a49b256dc1`
- Checkpoint: `checkpoint-d7c7df4719b1fdaa3993d32c`
- Subject digest: `be9c11d3ccc06abfc80e5958759c4e5d8a032c641174b62901db07747408c916`
- Workflow SHA-256: `03c95f921bfc4569d14af5e626f7806df2a7a510eee55d29298dfd6b38eae1a0`
- Repaired STL SHA-256: `544c4077d68c8454e96db9a5ef62848db43e14b7c21ff0f09c928c9526106e87`
- Sliced package SHA-256: `a82cdbb07581ca0d713fb29a55ac2adb508253e7e7a423c3a862d9fda6d85269`

The [submitted goal](campaign-serial-resolution-goal.md) requires preserving human-review authority and bounded correction budgets. The runtime explicitly requires a human decision for this engineering review. Those requirements are why the exact checkpoint decision and one additional correction need the user's authorization. Displayed retained counts remain 30/30/24/18; current counts remain 30/2/0/0. P001 remains active.
