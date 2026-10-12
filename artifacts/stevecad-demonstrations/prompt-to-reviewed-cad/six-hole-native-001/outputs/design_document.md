# Engineering Design Specification — Six-Hole Rectangular Block

## 1. Scope

Create a digital CAD model of one rectangular block containing six plain cylindrical through holes. Produce geometric inspection evidence, three CAD captures, three corresponding studio renderings, and a design review. This is a pre-construction specification; no model, measurement, image, or test result is claimed to exist yet.

The requested scope contains one part and no assembly, joints, fasteners, text, manufacturing drawing, mechanical-property analysis, physical material assignment, printing deliverable, or neutral-file export.

## 2. Coordinate System and Units

All geometry uses millimetres. The part-local Cartesian frame has its origin at the lower-left-bottom corner of component `block`:

- +X: along the 80 mm length
- +Y: along the 50 mm width
- +Z: upward through the 16 mm thickness
- Solid bounds: X = 0..80 mm, Y = 0..50 mm, Z = 0..16 mm
- `block.top`: planar face at Z = 16 mm

There is no assembly, so no assembled-world location is required. Report all geometric measurements in this part-local frame. Camera directions use the qualified native presentation convention: isometric viewed from (+X, −Y, +Z), top from +Z, and front from −Y.

## 3. Part and Feature Structure

| Item | CAD identifier | Quantity | Definition |
|---|---:|---:|---|
| Solid body/component | `block` | 1 | Rectangular prism, 80 × 50 × 16 mm |
| Hole feature | `h01` | 1 | Ø8 mm through hole at (12,12) |
| Hole feature | `h02` | 1 | Ø8 mm through hole at (40,12) |
| Hole feature | `h03` | 1 | Ø8 mm through hole at (68,12) |
| Hole feature | `h04` | 1 | Ø8 mm through hole at (12,38) |
| Hole feature | `h05` | 1 | Ø8 mm through hole at (40,38) |
| Hole feature | `h06` | 1 | Ø8 mm through hole at (68,38) |

All CAD identifiers shall use lowercase snake_case. Requirement identifiers such as R01 are review references and are not CAD feature names.

## 4. Dimension and Feature Table

| Feature/subset | Local X (mm) | Local Y (mm) | Z extent (mm) | Diameter (mm) | Axis |
|---|---:|---:|---:|---:|---|
| `block` outer solid | 0..80 | 0..50 | 0..16 | — | — |
| `h01` | 12 | 12 | 0..16 through | 8 | Parallel to Z |
| `h02` | 40 | 12 | 0..16 through | 8 | Parallel to Z |
| `h03` | 68 | 12 | 0..16 through | 8 | Parallel to Z |
| `h04` | 12 | 38 | 0..16 through | 8 | Parallel to Z |
| `h05` | 40 | 38 | 0..16 through | 8 | Parallel to Z |
| `h06` | 68 | 38 | 0..16 through | 8 | Parallel to Z |

The six openings are plain cylindrical holes. No fillets, chamfers, counterbores, text, or additional components are permitted.

Implementation guidance: on the non-centred `block.top` face, use the listed positive XY coordinates directly as the `Model.hole` point tuples. Do not subtract (40,25) or treat the face sketch origin as its centroid. Acceptance remains based on actual resulting geometry rather than construction history.

## 5. Requirements

| ID | Supplied mandatory requirement | Responsible stage | Acceptance method and tolerance |
|---|---|---|---|
| R01 | Use millimetres and the specified part-local origin, axes, and bounds. | CAD creation | Inspect coordinate frame and outer geometry; each measured linear dimension or bound shall be within 0.01 mm absolute of nominal. |
| R02 | Component `block` shall be one 80 × 50 × 16 mm rectangular solid before hole subtraction. | CAD creation | Measure X, Y, and Z extents from actual geometry to ±0.01 mm. |
| R03 | Provide exactly six plain Ø8 mm holes, named `h01` through `h06`. | CAD creation | Feature inventory and actual cylindrical geometry show exactly six holes; each diameter is 8.00 ± 0.01 mm. |
| R04 | Hole centres shall occupy the six listed part-local XY coordinates. | CAD creation | Measure each cylindrical axis location at `block.top`; X and Y coordinates shall each be within ±0.01 mm of the applicable nominal. |
| R05 | Every hole axis shall be parallel to Z and traverse the complete Z = 0..16 mm thickness. | CAD creation | Confirm cylindrical-axis direction is parallel to Z and each void opens on both Z boundary faces; measured through depth is 16.00 ± 0.01 mm. |
| R06 | Final model shall contain one solid and no fillets, chamfers, counterbores, text, or extra components. | Geometric validation | Topology/component inspection reports exactly one resulting solid, one component, and no prohibited visible geometry. |
| R07 | Verify final volume against the specified analytical expression with 0.1% relative tolerance. | Geometric validation | Compare measured solid volume with the calculated target; apply the tolerance to component `block` after all six holes. |
| R08 | Confirm each hole's diameter, axis, and through depth from actual CAD geometry. | Geometric validation | Record per-hole measured observations for `h01`–`h06`, using the dimensional criteria in R03–R05. |
| R09 | Capture isometric, top, and front CAD views. | Geometric validation | Three captures are present, use the specified native camera directions, and visibly support geometric inspection. Provider display colours are acceptable. |
| R10 | Produce corresponding realistic studio renderings in neutral matte gray without assigning mechanical properties. | Presentation rendering | Three images correspond to the isometric, top, and front views and visibly show a neutral matte-gray presentation finish. No physical material or mechanical-property claim is required. |
| R11 | Design review shall include requirement checks, actual observations, CAD views, presentation images, and unresolved findings. | Final review | Review contains all five sections and identifies each R01–R11 result as pass, fail, or unresolved. |
| R12 | Follow the previously accepted process while applying this changed block size and hole pattern. | Final review | Review traceability demonstrates that the current numerical geometry and pattern, rather than prior-run values, governed creation and validation. This does not impose a specific CAD construction history. |

## 6. Analytical Checks

Nominal gross volume:

V_gross = 80 × 50 × 16 = 64,000 mm³

Volume removed by one hole:

V_hole = π × 4² × 16 = 256π mm³

Nominal final volume:

V_target = 64,000 − 6(256π) = 64,000 − 1,536π ≈ 59,174.5137 mm³

R07 acceptance interval at 0.1% relative tolerance:

- Allowed deviation: approximately 59.1745 mm³
- Accepted volume: approximately 59,115.3392 to 59,233.6882 mm³

Geometric sanity checks include 28 mm centre spacing along each row, 26 mm row spacing, 8 mm minimum side clearance from each hole edge to the nearest X boundary, and 8 mm minimum clearance to the nearest Y boundary. These are derived checks, not additional independent requirements.

## 7. BOM and Construction Sequence

### BOM

| Line | Item | Quantity |
|---|---|---:|
| 1 | Digital CAD component `block` | 1 |

### CAD sequence

1. Establish the specified millimetre part-local frame.
2. Create the 80 × 50 × 16 mm rectangular solid `block`.
3. Place `h01`–`h06` at the listed positive XY coordinates on `block.top`.
4. Cut each Ø8 mm cylinder through the full thickness parallel to Z.
5. Validate topology, dimensions, locations, axes, depth, and volume from actual final geometry.

No assembly sequence or joint ranges apply because the deliverable is a single fixed component. No printing or export assumptions are introduced because neither a printed part nor an exported CAD format was requested.

## 8. Presentation and Review Deliverables

The three original CAD captures are geometric inspection evidence and may retain provider display colours. The neutral matte-gray finish applies only to the three derived studio renderings; it shall not be treated as a requirement for CAD viewport colours or a physical CAD material assignment.

Presentation fidelity means visual agreement in visible geometry, camera orientation, and appearance. It does not require pixel-identical images or create an additional numerical image-to-geometry tolerance.

The final review shall tabulate nominal values, actual observations, tolerances, and dispositions. It shall embed or reference all six images and list unresolved findings explicitly; if none remain, it shall state “none.”

## 9. Permitted Design Choices

- A01 — Use a light neutral seamless studio background with soft, broad lighting for the three derived renderings. This supports readable matte-gray form without changing geometry.
- A02 — Frame each requested view so the complete component is visible with a modest image margin. This controls presentation only and does not alter the prescribed camera directions.