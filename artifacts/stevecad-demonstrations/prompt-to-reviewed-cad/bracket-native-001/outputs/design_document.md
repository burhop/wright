# Right-Angle Mounting Bracket Engineering Design Specification

## 1. Scope

Create one fresh, editable digital exercise document containing a single one-piece right-angle mounting bracket. Preserve all earlier bracket documents and evidence. The requested work covers digital CAD geometry, geometry export, CAD inspection captures, studio renderings, and design-review evidence. Strength assessment, mechanical-property qualification, process qualification, and physical manufacturing acceptance are outside scope.

## 2. Coordinate System and Part Structure

Use millimetres and a right-handed Z-up coordinate frame. The part-local origin is `(0,0,0)`, at the lower corner shared by the minimum-X, minimum-Y, and minimum-Z bounds. Because this is a single-part document with no assembly placement, part-local coordinates equal document/world coordinates. No assembled-world transform is applicable.

| BOM item | Component | Quantity | Structure |
|---|---|---:|---|
| 1 | `right_angle_bracket` | 1 | One connected solid body; no separate fasteners or auxiliary components |

There is no assembly sequence and there are no joints or joint ranges. The stationary physical footprint of the sole component is its XY projection, `X=0..60 mm`, `Y=0..40 mm`; this is not a motion or reach envelope.

## 3. Final Geometry Definition

The authoritative final solid is the Boolean union of the two closed regions below, minus two cylindrical holes:

- Base region: `X=0..60`, `Y=0..40`, `Z=0..6 mm`.
- Upright region: `X=0..6`, `Y=0..40`, `Z=0..46 mm`.
- Heel overlap: `X=0..6`, `Y=0..40`, `Z=0..6 mm`, counted once in the union.

The finished component is a connected L-shaped solid with a `60 × 40 × 46 mm` overall envelope and nominal `6 mm` base and upright wall thicknesses.

### Dimension and feature table

| Feature/interface | Quantity | Geometry and location in part-local/world coordinates | Nominal value |
|---|---:|---|---:|
| Base region | 1 | `X=0..60`, `Y=0..40`, `Z=0..6` | `60 × 40 × 6 mm` |
| Upright region | 1 | `X=0..6`, `Y=0..40`, `Z=0..46` | `6 × 40 × 46 mm` |
| Overall bracket envelope | 1 | Bounds `X=0..60`, `Y=0..40`, `Z=0..46` | `60 × 40 × 46 mm` |
| Base wall | 1 | Separation of planar faces at `Z=0` and `Z=6`, evaluated away from holes | `6 mm` |
| Upright wall | 1 | Separation of planar faces at `X=0` and `X=6`, evaluated above the heel | `6 mm` |
| Base mounting hole 1 | 1 | Axis parallel to Z through global/part-local `(X,Y)=(20,10)`; traverses `Z=0..6` | Diameter `4 mm`, material depth `6 mm` |
| Base mounting hole 2 | 1 | Axis parallel to Z through global/part-local `(X,Y)=(45,30)`; traverses `Z=0..6` | Diameter `4 mm`, material depth `6 mm` |
| Upright | 1 | Entire upright outside the base intersection | Unperforated |
| Base mounting interface | 1 | Exterior planar face at `Z=0` excluding the two openings | `60 × 40 mm` nominal footprint |
| Upright interface | 1 | Exterior planar face at `X=0` | `40 × 46 mm` nominal extent |

Both holes are plain cylindrical through holes. Do not add fillets, chamfers, counterbores, countersinks, text, logos, or extra components.

Lowercase editable identifiers are required. The proposed identifiers `right_angle_bracket`, `base_region`, `upright_region`, `base_hole_1`, and `base_hole_2` are a recorded design choice; equivalent lowercase editable identifiers remain acceptable if required by the provider.

Modeling operations, construction order, and intermediate stock states are implementation guidance only. Acceptance evaluates the generated final solid and does not require an inspectable intermediate unperforated block.

## 4. Requirements

| ID | Supplied mandatory requirement | Responsible stage |
|---|---|---|
| R01 | Create one fresh exercise document while preserving earlier bracket documents and evidence; use the accepted preceding-block workflow. | CAD creation |
| R02 | Use millimetres and a right-handed Z-up frame with the final regions at the specified absolute coordinates. | CAD creation |
| R03 | Create the union of the specified base and upright regions, subtracting only the two specified holes. | CAD creation |
| R04 | The `right_angle_bracket` shall be exactly one component/body and one connected L-shaped solid. | Geometric validation |
| R05 | The bracket envelope shall be `60 × 40 × 46 mm`, with each bounding limit and resulting extent agreeing with the defined regions within `0.01 mm`. | Geometric validation |
| R06 | Base and upright wall thicknesses shall each be `6 mm`, measured from actual planar geometry within `0.01 mm`; unavailable measurement evidence must be explicitly reported. | Geometric validation |
| R07 | `base_hole_1` shall be a plain diameter-`4 mm` Z-parallel through hole at `(20,10) mm`, traversing the `6 mm` base thickness. | Geometric validation |
| R08 | `base_hole_2` shall be a plain diameter-`4 mm` Z-parallel through hole at `(45,30) mm`, traversing the `6 mm` base thickness. | Geometric validation |
| R09 | Each hole diameter, center position, and traversed depth shall agree with nominal within `0.01 mm`. | Geometric validation |
| R10 | The upright shall remain unperforated; no fillets, chamfers, counterbores, countersinks, text, or additional components are permitted. | Geometric validation |
| R11 | Editable feature identifiers shall be lowercase. Final geometry, rather than a particular construction history, controls acceptance. | CAD creation |
| R12 | Net solid volume shall be within `0.1%` of the specified analytical value. | Geometric validation |
| R13 | Native body color metadata shall make presentation color `#607d8b` available to the existing renderer. | CAD creation |
| R14 | The three derived studio renderings shall show a matte blue-gray `#607d8b` appearance. This is presentation-only and does not establish physical material properties. | Presentation rendering |
| R15 | Capture original CAD isometric, top, and front views using the provider conventions: isometric from `(+X,-Y,+Z)`, top from `+Z`, and front from `-Y`. | Presentation rendering |
| R16 | Produce three realistic studio renderings based on the corresponding actual CAD views and the exact exported geometry. | Presentation rendering |
| R17 | Qualitatively evaluate visible-feature, camera, and appearance agreement without inferring dimensions from pixels or requiring pixel identity. | Final review |
| R18 | Record the provider-returned editable design link and export identity, and demonstrate that the reviewed export corresponds to the accepted CAD geometry. | Final review |
| R19 | The final review shall include the supplied requirements, this predeclared test plan, numerical CAD observations, all three original CAD captures, all three studio renderings, export identity, editable design link, and unresolved findings. | Final review |

The original CAD captures are geometric inspection evidence and may retain provider display colors. Only the three derived studio renderings are required to exhibit the matte blue-gray finish. No test shall reject a CAD capture merely because its viewport color differs.

If the documented provider API requires a material profile to carry native color, the supplied conditional permission allows use of the existing `fdm-petg` profile with matte finish and `#607d8b`. Such use is only a presentation mechanism and conveys no mechanical, printing, or manufacturing compliance.

## 5. Analytical Checks

Region union before holes:

`V_union = 60×40×6 + 6×40×46 - 6×40×6 = 24,000 mm³`

Two holes:

`V_holes = 2×π×2²×6 = 48π = 150.79645 mm³`

Nominal net volume:

`V_net = 24,000 - 48π = 23,849.20355 mm³`

The `0.1%` volume tolerance is `23.84920 mm³`, giving an inclusive acceptance interval of approximately:

`23,825.35435 mm³ ≤ measured volume ≤ 23,873.05275 mm³`.

## 6. Predeclared Verification Plan

| Test | Requirements | Method | Acceptance evidence |
|---|---|---|---|
| T01 Document isolation | R01 | Inspect document identity and prior-document retention | Fresh document identifier; no earlier artifact overwritten |
| T02 Bounds and frame | R02, R05 | CAD bounding-box query in document coordinates | Numerical X, Y, and Z minima, maxima, and extents; deviations no greater than `0.01 mm` |
| T03 Solid structure | R03, R04, R10 | Body/component inventory and topology query | One component, one body, one connected solid, two holes, no prohibited visible features |
| T04 Wall thickness | R06 | Measure separation of actual opposing planar faces away from holes and heel ambiguity | Base and upright measurements within `0.01 mm`, or explicit unavailable-evidence finding |
| T05 Hole geometry | R07–R09 | Query cylindrical axes, diameters, centers, and traversed material depth | Diameter and depth deviations no greater than `0.01 mm`; each reported X and Y center coordinate deviates no more than `0.01 mm` |
| T06 Volume | R12 | CAD mass-properties volume query without relying on physical material density | Volume inside the stated inclusive interval |
| T07 Editability/naming | R11 | Inspect editable feature inventory | All exposed feature identifiers lowercase; no construction-history shape mandated |
| T08 Color metadata | R13 | Inspect native body appearance metadata or documented profile mechanism | Renderer-accessible `#607d8b` color metadata |
| T09 CAD captures | R15 | Capture actual model in the three specified provider views | Isometric, top, and front CAD images identified and retained |
| T10 Studio renders | R14, R16, R17 | Render exact accepted export from the corresponding views; visually compare | Three realistic images with matte `#607d8b`, correct camera class, and no visible geometry discrepancy |
| T11 Traceability review | R18, R19 | Collate review package | Six images, numerical observations, requirement results, editable link, export filename/format/version or hash, and unresolved findings |

## 7. Export and Review Record

Export the accepted solid using the geometry-export step of the established workflow. Record the export filename, format, revision or timestamp, and provider checksum/hash when available. The exported model used for all studio renderings must be the same accepted geometry represented by the numerical observations. Do not claim geometric dimensions from rendered pixels.

The final review shall mark every requirement pass, fail, or unresolved and shall not claim that construction, validation, export, capture, or rendering occurred until corresponding provider evidence exists.