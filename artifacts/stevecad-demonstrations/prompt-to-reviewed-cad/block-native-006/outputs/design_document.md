# Rectangular Four-Hole Block — Engineering Design Specification

## 1. Scope and structure

Create one digital CAD component, designated `Block_60x40x12` (design choice A01), containing exactly one solid body. There is no assembly, separate hardware, text, or additional component.

BOM: 1 × `Block_60x40x12`, modeled solid.

The stationary footprint is the component’s XY projection: 60.00 mm × 40.00 mm. No mechanical material properties, manufacturing qualification, or physical acceptance are in scope.

## 2. Coordinate frame and geometry

Use millimetres. The part-local origin is the lower-left corner of the bottom face. +X follows the 60 mm length, +Y the 40 mm width, and +Z the 12 mm thickness. Because this is an unassembled single part, local and assembled-world coordinates coincide: world transform is identity.

The rectangular solid occupies X = 0..60 mm, Y = 0..40 mm, and Z = 0..12 mm. Four plain cylindrical through holes have nominal diameter 6 mm, axes parallel to Z, and extend through the complete Z thickness.

| Feature ID | Component | Local/world center (mm) | Diameter | Z extent |
|---|---|---:|---:|---:|
| H1 | Block_60x40x12 | (10, 10) | 6 mm | 0..12 mm |
| H2 | Block_60x40x12 | (50, 10) | 6 mm | 0..12 mm |
| H3 | Block_60x40x12 | (10, 30) | 6 mm | 0..12 mm |
| H4 | Block_60x40x12 | (50, 30) | 6 mm | 0..12 mm |

External planar faces and the four cylindrical bore surfaces are the only geometric interfaces. No mating interface is specified. Fillets, chamfers, counterbores, text, and extra components are prohibited.

## 3. Requirements

| ID | Mandatory supplied requirement | Responsible stage |
|---|---|---|
| R01 | Create the 60 × 40 × 12 mm rectangular block at the stated origin and extents. | CAD creation |
| R02 | Add H1–H4 at the stated XY centers, each Ø6 mm, Z-parallel, and through the full thickness. | CAD creation |
| R03 | Include no fillets, chamfers, counterbores, text, or extra components. | CAD creation |
| R04 | Final CAD topology shall contain exactly one solid. | Geometric validation |
| R05 | Measured linear dimensions, hole diameters, through depths, and hole-center positions shall be within ±0.01 mm of nominal. | Geometric validation |
| R06 | Analytical volume comparison shall satisfy 0.1% relative tolerance. | Geometric validation |
| R07 | Confirm each hole’s diameter, axis direction, and full-depth traversal from actual geometry rather than source intent alone. | Geometric validation |
| R08 | Capture provider-native isometric, top, and front CAD views without changing geometry. | Presentation rendering |
| R09 | Produce three realistic studio renderings, one corresponding to each CAD view, with neutral matte gray presentation appearance and unchanged geometry. | Presentation rendering |
| R10 | Final review shall include every requirement check, actual observations, three CAD captures, three presentation images, and all unresolved findings. | Final review |

## 4. Analytical checks

Nominal volume:

V = 60×40×12 − 4π(3²)(12) = 28,800 − 432π = 27,442.832 mm³ approximately.

Accept when `|V_actual − V_nominal| / V_nominal ≤ 0.001`. Validate one connected solid, four cylindrical voids, Z-parallel bore axes, and bore openings on both Z faces using evaluated CAD geometry.

## 5. Views and appearance

Use the provider’s qualified native view conventions: isometric viewed from (+X, −Y, +Z), top from +Z, and front from −Y. The three original CAD captures are geometric inspection evidence and may retain provider display colors. Neutral matte gray is required only in the three derived studio renderings; presentation fidelity means agreement in visible geometry, camera, and appearance, not pixel identity.

## 6. Final acceptance record

Before approval, record nominal versus actual values, pass/fail status for R01–R10, geometry-derived hole evidence, solid count, analytical volume error, all six images, and unresolved findings. This specification does not claim that CAD, measurements, captures, or renderings already exist.