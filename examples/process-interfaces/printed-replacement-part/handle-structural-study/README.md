# Printed02 native structural preparation

Status: **native preparation observed**,27October2026. Source revision3/run
6d06c9a3ea5443bfa2fc7f5bc9acee8b completed through Wright in19.86seconds, producing
the original-handle CAD, declared boundary objects and a66,134-node quadratic
mesh. A fresh two-stage workflow then prepared and solved the same original CAD
in78.48seconds (runb73a4604), with66,734nodes. Results are preliminary; refinement,
comparison, review and website-success remain open. See the [readable native
result](../../../../artifacts/first-contact/synthetic-beta-003/operator-retries/partition-045/README.md).
This extends the existing handle family and retains its original geometry and
printing requirements. Read the campaign's
[study basis](../../../../artifacts/first-contact/synthetic-beta-003/handle-study-basis.md).

The intended contribution is FreeCAD CAD → native Gmsh mesh → native CalculiX
analysis through the existing independent FreeCAD MCP. Read its
[usage guide](../../../../docs/mcp-catalog/usage-guides/freecad-mcp.md), setup recipe
and exact discovered contracts first. Current installed schema evidence exposes
`execute_code` and `run_fem_analysis`; an available name is not an execution proof.

`prepare_analysis.py` is an authored engineering operation for `execute_code`.
Append an explicit `prepare_analysis(CONFIG)` call to its versioned bytes and
save those exact arguments with the accepted workflow. The configuration names
an actual workspace-contained native BREP, its SHA256, unique native document,
new output directory, study revision and mesh sizes. No default host paths,
credentials, replay, review grant or second process executor are supplied.

The operation uses a native parameter-space surface partition to select the declared rear
half of the central grip. It retains the original BREP, checks single-solid and
partition correspondence, identifies unchanged bore barrels, and creates actual
material/support/load objects and a quadratic volume mesh. It records exact face
sets, area, expected resultant/moment and native files. The first native use must
establish the APIs and geometry behavior; a partition/selection/mesh failure
remains a readiness obstacle. No silent whole-face or point-load fallback.

Call the actual discovered `run_fem_analysis` only for that exact prepared native
document/analysis. Its pinned client socket timeout is150seconds even though the
exposed dispatch parameter defaults to600seconds. Reconcile native state and
files after a timeout before another call. Retain actual INP/FRD/DAT/logs and
solve response before closing the provider or guest. Solver summaries alone
cannot satisfy reaction balance, field inspection or mesh sensitivity.

The proposed initial global mesh settings are2.0/0.75mm and1.4/0.5mm. These
requests do not prove achieved local refinement or element quality. Actual
outputs must satisfy the study's numerical checks; missing quantities stay
unresolved. Compare the same loads, supports, material, regions and methods for
baseline and revised CAD. A revision follows observed evidence and retains the
fixed96mm interface and all original geometry/review requirements.

The owning Wright workflow must declare artifact handoffs, readiness, exact
output checks, reviews, affected revision invalidation and result presentation.
Reuse the existing runner/gateway/validator/storage and common or compatible
working view. These files do not add runtime/UI authority. Existing human
approvals cover their original subjects only. Software regressions remain deferred;
normal engineering checks and genuine human review remain required.


## Observed partition correction, 27 October

The initial Boolean split wrapped a spline parameter interval and sewing inflated
the maximum CAD tolerance from0.000003535mm to8.855mm. It is retained as failed.
Trimming the same native BSpline surface into its front/rear parameter intervals
preserves the original maximum tolerance. The operation now also rejects tolerance
inflation and retains correspondence measurements before a failed gate.

FreeCAD's ordinary Area/Volume properties call the default, non-adaptive native
integration overloads. Differently trimmed spline faces produced misleading
mass-property differences. The corrected operation uses FreeCAD's bundled
pythonocc7.8.1.1 and its native conversion to OCCT7.8.1, requesting1e-11 adaptive
relative error and enforcing the returned estimates. Original numeric
correspondence limits are unchanged. Actual differences were9.923e-8mm³ and
3.298e-7mm², below0.000123054mm³ and0.0000597599mm². This is CAD correspondence,
not material/strength validation.

Primary implementation sources: [FreeCAD property calls](https://github.com/FreeCAD/FreeCAD/blob/1.1.1/src/Mod/Part/App/TopoShapePyImp.cpp#L2807-L2826)
and [OCCT integration overloads](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/src/BRepGProp/BRepGProp.cxx#L181-L195).
Native bindings and the actual two-accuracy diagnosis are retained in the campaign's
045 evidence. An installation missing the bundled native binding cannot silently
fall back to the inaccurate measurement or weaken the gate.
