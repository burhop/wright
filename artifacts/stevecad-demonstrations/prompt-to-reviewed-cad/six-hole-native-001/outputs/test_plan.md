# Compact Test Plan — Six-Hole Rectangular Block

## Evaluation rules

Inspect actual generated geometry in millimetres in the part-local frame of component `block`: origin at lower-left-bottom, +X along length, +Y along width, and +Z upward. Source code, intended parameters, and rendered pixels are not metrical evidence. A measured value outside tolerance is **FAIL**; unavailable evidence is **UNVERIFIED**. CAD inspection covers geometry and CAD captures only. Rendering and final-document checks are deferred until those outputs exist and are not CAD-inspection failures.

## Traceability and acceptance tests

| ID | Stage; exact subject/subset | Expected value, units and tolerance | Numerical comparison | Required actual geometric observation/evidence |
|---|---|---|---|---|
| R01 | CAD inspection; `block`, part-local frame | mm; origin `(0,0,0)` mm; bounds X `0..80`, Y `0..50`, Z `0..16`, each bound ±0.01 mm | For every bound, `|actual−nominal| ≤ 0.01 mm` | Report frame origin/axis directions and measured minimum/maximum X, Y, Z from geometry. |
| R02 | CAD inspection; `block` outer rectangular solid before hole subtraction | 80 × 50 × 16 mm, each ±0.01 mm; count 1 | `|Xextent−80|`, `|Yextent−50|`, `|Zextent−16| ≤ 0.01 mm` | Measure final outer envelope. Separately observe retained pre-subtraction geometry/state; if unavailable, the “before subtraction” clause is UNVERIFIED, not inferred from code. |
| R03 | CAD inspection; holes `h01`–`h06` only | Exactly 6 plain cylindrical holes; each Ø8.00 ±0.01 mm; exact names | `count=6`; each `|D−8.00| ≤ 0.01 mm` | Inventory six named features and measure six cylindrical surfaces. Observe no counterbore, countersink, or other stepped profile. |
| R04 | CAD inspection; axes of `h01`–`h06` at `block.top`, Z=16 mm | Centres (mm): `h01` (12,12), `h02` (40,12), `h03` (68,12), `h04` (12,38), `h05` (40,38), `h06` (68,38); X and Y each ±0.01 mm | Per hole: `|Xactual−Xnom| ≤ 0.01 mm` and `|Yactual−Ynom| ≤ 0.01 mm` | Record each actual axis intersection with `block.top` in the part-local frame. Do not apply this subset test to the whole solid. |
| R05 | CAD inspection; each of `h01`–`h06` | Axis parallel to +Z; void Z extent `0..16` mm; depth 16.00 ±0.01 mm | Axis cross-components `X=0, Y=0`; `|depth−16| ≤ 0.01 mm`; openings at Z=0 and Z=16 | Observe each cylindrical axis and openings on both Z boundary faces; measure each through depth. |
| R06 | CAD inspection; final `block` only | 1 solid, 1 component; 0 fillets, chamfers, counterbores, text, or extra components | Counts must equal `1, 1, 0, 0, 0, 0, 0` respectively | Topology/component inventory and visible-geometry inspection; do not infer absence from source code. |
| R07 | CAD inspection; final `block` after all six holes | Volume `64,000−1,536π = 59,174.5137 mm³`; relative tolerance 0.1%; interval 59,115.3392–59,233.6882 mm³ | `|Vactual−59,174.5137| / 59,174.5137 ≤ 0.001` | Record CAD-computed solid volume for only the final `block`. |
| R08 | CAD inspection; individually `h01`–`h06` | For every hole: Ø8.00 ±0.01 mm, Z-parallel axis, depth 16.00 ±0.01 mm | Apply R03 and R05 comparisons separately to all 6 holes | Per-hole record of measured diameter, axis direction, Z extent, depth, and two-face opening observation. |
| R09 | CAD inspection; `block` CAD captures | Exactly 3 captures: isometric from (+X,−Y,+Z), top from +Z, front from −Y | `capture count=3`; direction equals specified direction | Original CAD captures must show the complete component and support inspection of visible feature count, silhouette, and orientation. Provider display colours are acceptable. |
| R10 | Presentation rendering, deferred | Exactly 3 corresponding studio renders; neutral matte gray; no mechanical-property claim | `render count=3`; one correspondence for each required view | Final visual inspection of isometric/top/front render orientation, visible holes, silhouette, and appearance. Pixels cannot verify dimensions. |
| R11 | Final review, deferred | 5 sections: requirement checks, actual observations, CAD views, presentation images, unresolved findings; R01–R11 each has PASS, FAIL, or UNRESOLVED | `section count=5`; `disposition count=11` | Review embeds or references all 6 images and lists unresolved findings or states “none.” |
| R12 | Final review, deferred | Current 80 × 50 × 16 mm block and current six-coordinate pattern govern validation | All reported current values must match R01–R08 nominals, not prior-run values | Traceability review of current requirement-to-evidence records; no particular construction history is required. |

## Derived sanity checks

For `h01`–`h06`, record row spacing 26 mm, adjacent X spacing 28 mm, and minimum hole-edge clearance 8 mm to the nearest X and Y boundaries. Compare each derived value to nominal within ±0.01 mm. These checks diagnose placement but do not replace R01–R08 or create new requirements.

No interface, assembly-clearance, joint, or motion test applies: the specified deliverable is one fixed component. Presentation choices A01–A02 remain permitted choices, not supplied requirements.