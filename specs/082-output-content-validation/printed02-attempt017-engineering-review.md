# P001 — Printed 02 attempt 017 engineering review

22 September 2026. Human requested changes; no physical printing or engineering acceptance claimed.

The current canonical workflow completed actual Blender source authoring, native
mesh repair, Bambu Studio slicing, and its explicitly authorized local simulated
handoff. All 15 review-file hashes and the saved workflow identity were checked
before and after a read-only full-profile inspection. All **17 automated checks
pass**. The mandatory engineering-review check remains blocked.

Open [the actual workflow results](http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical&workflowPath=workflows%2Fcampaign-printed-replacement-part-02-attempt-017.workflow.wflow).

Actual deliverables:

- [Slicing preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-017/artifacts/slice-preview.png)
- [Support preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-017/artifacts/support-preview.svg)
- [Repaired STL](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-017/artifacts/repaired_mesh.stl)
- [Actual sliced 3MF](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-017/artifacts/slice_package.gcode.3mf)
- [Full immutable read-only inspection](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-canonical-review/assessment.json)
- [Original dimensional context](../../tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md)

The corrected mesh fits the fixed 118 × 28 × 34 mm envelope; the native operation
reports approximately 113.999 × 23.999 × 33.999 mm. Independent automated checks
verify external dimensions, closed nondegenerate manifold topology, source/repair
lineage, exact mesh-to-slice/package binding, fixed slicing profiles and the
simulated handoff. The real slice contains 37,523 extrusion moves, including
4,117 support moves. No printer was connected.

## Concrete review gaps

| Required detail | Available evidence and remaining gap |
|---|---|
| Mounting and finger clearance | Source construction/report specifies 96 mm hole spacing, 4.5 mm bores and 25 mm central finger clearance. These are not independent measurements of those features in the final voxel-remeshed STL. The repair's envelope check does not prove internal feature preservation. |
| Grip, blends, edges and recess | The actual preview shows a bow and two pads; the source includes an oval grip and thumb recess. Minimum internal blends, touched-edge rounding and final recess geometry still need review against the final mesh. |
| Orientation comparison | The context explicitly requires comparing pads-down and side orientations. The recorded repair preserves model axes and places the pads on the bed; actual supports were sliced. The delivered reports do not record the required comparison or identify support-contact locations in prose. |
| Editable native design | The approved renewal brief calls for a native design as well as STL and 3MF. The 15-file review set has no `.blend` file. Canonical tool-call source is retained, but is not a saved native Blender design. |

**Recommended decision: request changes**, requiring the orientation comparison,
editable native design, and final-feature evidence before accepting the digital
prototype. This does not change a requirement or ask for physical testing. Any
changed geometry must be repaired, re-sliced and reviewed with fresh hashes.

The agent may not record the human decision itself without explicit direction.
The submitted goal preserves human-review authority, and this exact runtime
checkpoint reports `validation_review_requires_human`. A request to continue
repair work is not silently treated as an engineering decision on these files.

## Exact decision identity

- Run: `1f472a8acb4a430a816895f1ed85f5cc`
- Checkpoint: `checkpoint-8e310e7cc440f53f219c9ebe`
- Subject digest: `f35423d9cd6951dc046efc2b10867e5eb9941aea4273bda2bf9fb6a142ad0eed`
- Workflow source SHA-256: `27bc09d4273a94b1157c67a40e55790e912ba700e22d709435d88f8833d98705`
- State: pending; actor null at the exact-file inspection.

The dashboard's 30/30/24/18 counts include retained automated inspection. Current
metrics are 30/2/0/0. Neither the successful isolated inspection nor this review
brief completes the canonical validator or earns a full-scope campaign pass.

## Recorded decision and measured defect

The user explicitly selected **Request changes for these gaps**. The exact checkpoint now records `changes_requested` by `local_workspace_user`; all 20 protected input/source/artifact files were unchanged. The runner exported the terminal result and cleaned its owned native runtime.

Independent triangle clipping to the required X=15.5..80.5 mm central span measured **24.814040 mm final-mesh clearance**, below the unchanged 25 mm minimum (source also failed at 24.816831 mm). [Measurement](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-final-clearance.json). [Decision receipt](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-human-decision-017.json). Any successor requires new evidence and its own human decision.
