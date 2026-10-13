# Right-Angle Bracket Test Plan

## Rules

This plan is fixed before CAD creation. Test only the named `right_angle_bracket` in its part-local/document frame (right-handed, Z-up, origin at minimum X/Y/Z); do not apply bounds to other documents. CAD inspection covers generated geometry and original CAD captures, never source code. Record measured values and observations. Missing evidence = **UNVERIFIED**; measured noncompliance = **FAIL**. Rendering, appearance, export-linkage, and final-document checks remain deferred—not failed—until final review. Pixel inspection cannot verify dimensions.

## Geometric Tests

| Test / stage | IDs | Expected value, tolerance, and numerical comparison | Required actual observation |
|---|---|---|---|
| T01 Document isolation / CAD creation | R01 | Exactly 1 fresh exercise document; earlier documents overwritten = 0 | Provider document ID and evidence earlier bracket artifacts remain intact; workflow identified as accepted preceding-block workflow |
| T02 Frame and bounds / CAD inspection | R02, R05 | mm, right-handed Z-up. Bounds: X `0.00..60.00`, Y `0.00..40.00`, Z `0.00..46.00 mm`; extents `60.00,40.00,46.00 mm`. For every minimum, maximum, and extent: `|actual−expected| ≤ 0.01 mm` | Numerical bounding-box query in the specified frame, including all six limits and three extents |
| T03 Final topology and interfaces / CAD inspection | R03, R04, R10 | Exactly 1 component, 1 body, 1 connected solid, 2 holes, and 0 extra components. Solid equals specified region union minus only those holes | Inventory/connectivity result; visible L silhouette; base region `60×40×6 mm`, upright `6×40×46 mm`, heel overlap counted once; base interface at `Z=0` with `60×40 mm` footprint excluding two openings; upright interface at `X=0`, `40×46 mm`; upright perforations, fillets, chamfers, counterbores, countersinks, text, and logos each count 0 |
| T04 Walls / CAD inspection | R06 | Base and upright thickness each `6.00 mm`; `|actual−6.00| ≤ 0.01 mm` | Separation of actual planar faces at `Z=0/6`, away from holes, and `X=0/6`, above heel; record both measurements in mm |
| T05 Holes / CAD inspection | R07–R09 | Exactly 2 plain cylinders. `base_hole_1`: center `(20.00,10.00) mm`; `base_hole_2`: `(45.00,30.00) mm`; both diameter `4.00 mm`, Z-parallel, traversed material depth `6.00 mm` over `Z=0..6`. For each X, Y, diameter, and depth: `|actual−expected| ≤ 0.01 mm`; axis angular deviation must be reported and be consistent with Z-parallel geometry | Cylindrical-face query recording identifier, axis direction, center X/Y, diameter, start/end Z, through-opening status, and absence of counterbore/countersink |
| T06 Volume / CAD inspection | R12 | Nominal `23,849.20355 mm³`; inclusive acceptance `23,825.35435 ≤ actual ≤ 23,873.05275 mm³` (±`0.1%`) | CAD mass-properties volume for the sole final solid, without density inference |
| T07 Editability / CAD creation inspection | R11 | All exposed editable identifiers lowercase; acceptable proposed names include `right_angle_bracket`, `base_region`, `upright_region`, `base_hole_1`, `base_hole_2` | Editable inventory and lowercase comparison; construction history is not an acceptance criterion |

There are no joints, joint ranges, clearances, fasteners, auxiliary supports, or motion tests. The sole stationary XY footprint is `X=0..60`, `Y=0..40 mm`; observe it only as a footprint, not a motion envelope.

## Deferred Presentation and Review Tests

| Test / evaluation stage | IDs | Expected comparison and required observation |
|---|---|---|
| T08 Metadata / final review | R13 | Renderer-accessible native body color exactly `#607d8b`; inspect metadata or the permitted documented profile mechanism. Do not infer mechanical properties |
| T09 CAD captures / CAD inspection | R15 | Exactly 3 original captures of actual geometry: isometric from `(+X,-Y,+Z)`, top from `+Z`, front from `-Y`. Record view identity/orientation; viewport color is not judged |
| T10 Studio renders / final review | R14, R16, R17 | Exactly 3 realistic renders, corresponding to those views and the accepted export, visibly matte blue-gray `#607d8b`. Compare only visible hole count, L silhouette, orientation, and appearance; no pixel-based metrology or pixel-identity requirement |
| T11 Package/linkage / final review | R18, R19 | Record editable design link and export filename, format, revision/timestamp, and checksum/hash when available. Demonstrate export-to-accepted-CAD correspondence. Review must contain requirements, this plan, numerical observations, 3 CAD captures, 3 renders, identities, and unresolved findings |

## Traceability and Disposition

| Requirements | Tests |
|---|---|
| R01 | T01 |
| R02, R05 | T02 |
| R03, R04, R10 | T03 |
| R06 | T04 |
| R07, R08, R09 | T05 |
| R12 | T06 |
| R11 | T07 |
| R13 | T08 |
| R15 | T09 |
| R14, R16, R17 | T10 |
| R18, R19 | T11 |

No specification conflict is identified. Each requirement receives **PASS**, **FAIL**, or **UNVERIFIED** only at its assigned evaluation stage; deferred outputs remain **UNVERIFIED** until they exist.