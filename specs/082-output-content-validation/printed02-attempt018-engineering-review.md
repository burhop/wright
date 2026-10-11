# P001 — Printed 02 attempt 018 engineering review

22 September 2026. **Recommendation: request changes for remaining grip geometry.**
This is correction 1 of 2 in the preserved `printed02-final-feature-review` episode.
The user has not decided this new checkpoint. No physical print or campaign pass is claimed.

The canonical run completed Blender authoring, geometry-preserving repair, actual
Bambu slicing and the authorized simulated handoff. A read-only inspection verified
all 16 review-file hashes before and after applying the unchanged full profile:
**17 automated checks pass; mandatory engineering review remains blocked.**

[Open the actual workflow results](http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical&workflowPath=workflows%2Fcampaign-printed-replacement-part-02-attempt-018.workflow.wflow).

## Corrections now demonstrated

| Rejected-017 gap | Attempt-018 evidence |
|---|---|
| Finger clearance | Final-STL triangle clipping measures **25.000 mm** throughout X=15.5..80.5, against the unchanged 25 mm requirement. |
| Mounting feature evidence | Independent sections at Z=1.5, 2.5 and 3.5 measure centers (0,0)/(96,0), **96.000 mm** apart; bores measure **4.500 mm** across X/Y. Faceted minimum centered diameter is **4.4946 mm**, explicitly disclosed rather than assigned an invented tolerance. |
| Native design | Actual editable `native-design.blend`, 869,895 bytes, is included in the checkpoint. |
| Orientation comparison | Source and repair reports compare pads-down and side. Measured flat bed contact is about 649.8 mm² pads-down versus zero planar area on the side's curved extreme. Pads-down preserves vertical bores; expected support contact is beneath the raised bow. Actual selected support preview is retained. |
| Envelope and topology | **114 × 27.608711 × 34 mm**, one closed manifold component, 6,272 triangles. No forced voxel remesh or envelope scaling. |
| Actual slicing | P1S 0.4 mm/PETG, 0.20 mm layers, five walls, 40% infill; 24,220 extrusion moves, including 3,932 support moves. No printer connection. |

## Remaining PRINT02-GRIP findings

The submitted geometry has sharp shoulder transitions at X=15.5 and X=80.5.
Independent final-STL edge measurements find approximately **81.1° face-normal
changes** across those transitions. The retained construction uses abrupt changes
from rising legs to the horizontal grip and applies no shoulder fillet. Smooth
shading does not add the required touched-edge rounding. The 1 mm pad/bore bevels
were applied before union and do not establish rounded bow/pad junctions or the
required internal blends where space permits.

The thumb recess reaches approximately **1.500 mm centerline depth at X=48**, but
does not extend along the requested central 40 mm (X=28..68). Independent section
measurements, compared with the exact retained uncut construction, show unchanged
upper profiles through X=41.5 and from X=55.5 onward. Only the center portion is
cut. This is a construction-dependent comparison, not a claim of complete grip
validation. The source report itself leaves grip and blend measurement unresolved.

The bounded next correction should preserve the successful clearance, mounting
frame and deliverables; provide smooth shoulder/junction geometry with explicit
rounding/blend evidence; and construct a recess over X=28..68 with measured depth
and extent. Qualify those features before spending correction 2. Requirements,
tolerances, old outputs and the retry budget remain unchanged.

## Review files and evidence

- [Native Blender design](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/native-design.blend)
- [Actual repaired-mesh preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/mesh-preview.png)
- [Actual sliced preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/slice-preview.png)
- [Support preview](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/support-preview.svg)
- [Repaired STL](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/repaired_mesh.stl)
- [Final sliced 3MF](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/attempt-018/artifacts/slice_package.gcode.3mf)
- [Exact-file full-profile inspection](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-canonical018-review/assessment.json)
- [Shoulder and recess measurements](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-018-grip-review-v2.json)
- [Original context](../../tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/context.md)

## Exact pending decision

- Run: `a93d7c564c7544c7afcacaf22808c31c`
- Checkpoint: `checkpoint-36ca29b783528faed96b6456`
- Subject digest: `94e464fcfc14d725da036b7db92edd3e42734b6660efbbe5127d08cf35b76adf`
- Workflow SHA-256: `dd22d1d4c242888c330b047cfeaee6ef49f5d2151f6a753e117864a9c3132bba`
- Repaired STL SHA-256: `85aac165aab97d4160fedc92f7af321eb8364340730f00fbb2f82e329fb4816e`
- Sliced package SHA-256: `406a6f9fd73bcb0528850cbca094cd8894152d327445d6c4907f8413be051a54`

The submitted goal preserves human-review authority. This runtime checkpoint
requires a human decision (`validation_review_requires_human`); the prior decision
on 017 does not decide these changed files. Historical displayed counts remain
30/30/24/18; current counts remain 30/2/0/0. P001 is still active.

## Recorded decision

The user explicitly selected **Request changes and correct grip**. The exact checkpoint records `changes_requested` by `local_workspace_user`; all 21 protected files remain unchanged. The runner terminated and recorded native cleanup. [Decision receipt](../../artifacts/engineering-workflow-datasets/serial-resolution/p001-human-decision-018.json). Correction 2 is authorized within the existing episode; no successor has been approved.
