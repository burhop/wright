# Fieldbar prototype forming capabilities and DFM, revision R4

FB-MFG-12-R4, dated 2026-09-12, is a fictional company engineer's uploaded
capability statement for the six cable-trough prototypes. Every machine,
tooling capability and internal limit below is synthetic company input. It is
not a SendCutSend statement, purchased service, machine measurement, or
fabrication result. No physical fabrication is requested by this workflow.

## Authority and assessment boundaries

Preserve the original brief, mounting CSV, policy, R1, R2, and R3 without
editing them. This additive revision supplies the company prototype route for
the previously unresolved complete returned-channel bend sequence. It
authorizes an exact-reviewed CAD model for geometry verification when all
selected-stock and native-rule inputs are complete and no known applicable
supplier hard limit conflicts with the design.

Keep these assessments separate in intent, checks, approvals, and handoff:

1. Company prototype inputs and calculated setup margins from this document.
2. Fresh supplier rules and supplier acceptance, which remain independent.
3. Native CAD observations and developed-file measurements made after creation.

The declared company route may close a missing company tooling input before
CAD. It does not prove supplier tooling access, supplier acceptance, physical
collision clearance, bend force, springback, coating fit, or fabrication.
Unknown or failed company criteria and known applicable supplier conflicts
still block CAD. Supplier-only confirmation gaps may remain downstream when
they are carried as unverified and manufacturing release remains on HOLD.

## Declared cutting and material envelope

The fictional prototype shop has a fiber laser with a 750 by 1250 mm usable
bed and accepts bare cold-rolled low-carbon steel from 1.2 through 1.8 mm
inclusive. Use the exact stock selected under R1 for CAD; the shop declaration
does not establish equivalence between that stock and the native C10 geometry
label. All four slots, return-end rounds, and bend reliefs are cut in the flat
blank before forming. No welding, drilling, tapping, end plates, or added
brackets are part of this route.

The following are company prototype minima, evaluated using selected thickness
T in millimetres. They are not supplier rules. Any stricter freshly sourced
applicable supplier rule also applies.

| Company criterion | Minimum | Worst case at T=1.8 mm | Protected geometry |
| --- | --- | --- | --- |
| Through-slot width | 1.5*T | 2.70 mm | 6.5 mm slots |
| Web between parallel cut edges | 1.0*T | 1.80 mm | No repeated close-pitch cuts |
| Slot edge to an unbent free edge | 1.5*T | 2.70 mm | Nearest slot edge is more than 16 mm from an open end or side edge |

Preserve S1 through S4 at the exact mounting-holes.csv coordinates. Their 15
mm overall length, 6.5 mm width, X major axis, and half-width end radii are
protected. Use the freshly sourced selected-stock bend-to-feature and relief
rules for the developed distance from each slot to either base bend. Planning
coordinates do not count as measured developed distances.

## Declared press-brake and tool envelope

The fictional shop provides a 45-ton press brake with 500 mm usable bend
length, 240 mm open daylight, and 450 mm clear throat depth. A raised lower-die
support leaves 90 mm clear below the working plane. Segmented gooseneck upper
tools provide a 75 mm clear vertical pocket and a 35 mm clear horizontal pocket
for the preformed outward return. These are clear spaces, not overall tool
dimensions. Tool segments can cover the 400 mm bend span while leaving at least
3 mm clearance beyond each open trough end and relief termination.

Select the lower die from the freshly sourced stock row and retain its inside
radius and K-factor basis. The company has lower-die openings from 10 through
16 mm inclusive. A sourced opening outside that range is a missing company
capability. The nominal CAD rule is not evidence of actual springback, force,
or achieved bend deduction. Coupon tuning and physical tool trials remain
unperformed.

For setup review, reserve 5 mm beyond each preformed feature. A 60 mm wall
requires 65 mm vertical clearance, within the declared 75 mm pocket. A 20 mm
return requires 25 mm horizontal clearance, within the declared 35 mm pocket.
The 400 mm bend length is within the 500 mm usable length. These scalar margins
define a candidate company setup; they are not swept-volume collision results.

## Part-specific four-bend sequence

Use R3's physical sequence. CAD feature order may differ, but the manufacturing
intent and checks must retain this proposed press sequence:

| Operation | Workpiece presentation | Declared access condition |
| --- | --- | --- |
| F1: left outward return | Flat blank, left return bend at the outer wall edge | Remaining bottom, walls, and opposite return stay flat; form the 20 mm return with segmented tooling across 400 mm. |
| F2: right outward return | Rotate the flat blank 180 degrees in its plane | The first return remains beyond the relieved tool end and outside the backgauge envelope. |
| B1: left base-to-wall bend | Present the left bottom bend with its preformed return in the gooseneck pocket | The 60 mm wall and 20 mm return use the declared 65 by 25 mm reserved pocket; the opposite half remains flat. |
| B2: right base-to-wall bend | Rotate the workpiece 180 degrees | The completed left wall stands in the open throat across the 80 mm bottom; the right preformed return uses the same pocket. Withdraw through the open ends/top after opening the ram. |

The ordinary supplier channel ratio and every applicable conditional exception
must still be read from fresh supplier evidence. For the protected folded
section, the 80 mm bottom-to-60 mm wall ratio is 1.333. The selected sheet is
within R1's thickness bounds and the 60 mm wall is below 3 inches, but those
facts alone do not establish that a supplier accepts the complete returned
channel or this sequence. Preserve supplier tooling acceptance as unverified.

## Review and downstream verification

Before CAD creation, the intent must contain the complete selected stock row,
native material identity, bend rule, relief sizes, flat-pattern settings,
folded datum definitions, slot coordinates, company calculations, and the four
operations above. It may state
`cad_input_status=ready_for_geometry_verification` only when those inputs are
complete and no known mandatory conflict exists.

Native bend-centerline distances, developed extents, slot-to-bend distances,
relief intersections, open-end topology, material readback, sheet thickness,
60 mm wall heights, 20 mm returns, 80 mm bottom, 120 mm return-to-return span,
45 mm minimum clear depth, and the 25 mm service-loop path remain mandatory
post-CAD observations. Tool collision, force, springback, and physical sequence
execution remain unperformed even if the geometric model passes.

Carry every supplier uncertainty into both simulated supplier approval gates
and the final handoff with `manufacturing_release=HOLD`,
`supplier_acceptance=unverified`, and `physical_fabrication=not_performed`.
Keep finish availability, coating thickness, hole allowance, and coated fit
unverified as allowed by R3. Auto review does not waive a requirement. No real
supplier upload, communication, cart change, order, payment, or production
release is authorized.
