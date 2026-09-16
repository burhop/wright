# Parcelwood prototype tooling and review policy, revision R4

PW-PROT-03-R4, 2026-09-12. This is a fictional company engineer's upload for
the four barcode-reader wall-dock prototypes. The equipment, tooling and
company criteria below are synthetic design inputs, not measured machines,
SendCutSend capabilities, supplier approval or evidence of a fabricated part.
No physical fabrication is requested by this workflow.

## Scope and retained requirements

Apply this additive revision after the unchanged original uploads, R1 and R3.
Preserve the 110 by 75 mm outside shelf, 60 mm rear wall, two 12 mm front lips,
both mounting slots, the 18 by 20 mm open cable notch, 3 mm root radii, open
sides, corner rounds, quantity four and all other protected R1/R3 geometry.
Retain the selected supplier stock, exact native material mapping, sourced
radius/K factor and existing measured-design/export checks.

This revision supplies a company candidate forming setup and a distinction
between nominal CAD verification and supplier process acceptance. The company
requests an exact-reviewed native model to evaluate this setup. Missing
supplier machine-access confirmation, an unresolved deformation caution for
an intentionally interrupted bend, and the separately listed bend-deduction
discrepancy may remain disclosed supplier issues while complete company inputs
support CAD geometry verification. This revises the timing of those three
confirmations; it does not declare them resolved or confer a supplier DFM pass.

Keep company input/calculated feasibility, supplier rules/applicability, native
observations and physical process evidence in separate columns. A known
applicable supplier hard-limit conflict still blocks this supplier-targeted
design. Unknown company inputs, failed company inequalities, a conflicting
protected dimension or an unsupported native operation also block. Do not
reclassify a hard requirement as a caution to proceed. Actual supplier upload
and manufacturing release remain blocked until all supplier issues are resolved.

## Declared prototype equipment

The fictional shop has a fiber laser with a 600 by 900 mm usable bed accepting
bare 5052 sheet from 1.3 through 1.7 mm. All mounting slots, notch, rounds and
reliefs are cut in the flat blank before forming. No post-bend drilling,
welding, added bracket, solid-body substitute or deletion of a lip is allowed.
Company minimum slot width and minimum web between separate cuts are both T,
where T is the selected stock thickness in mm. Apply stricter applicable
freshly sourced supplier limits as well; these company minima do not prove
supplier compatibility. Relief width/depth remain the exact R3 formulae and
inclusive 0.5..6 mm limits, with the current supplier minima evaluated.

The company declares a small press brake with 300 mm usable bend length,
200 mm open daylight and 300 mm clear throat depth. Raised tooling leaves
100 mm clear below the die working plane. Segmented gooseneck tools provide
80 mm clear pocket height and 90 mm clear pocket depth, with relieved ends
and an open lateral withdrawal path. These are usable empty spaces, not
overall tool dimensions. The shop can fit independent punch/die segments to
each remaining straight bend interval after reliefs and corner rounds, with
no tool bridge across the cable opening. The minimum supported straight
bend interval for this company setup is 20 mm. Retain actual interval lengths
and end positions as post-CAD measurement criteria.

Selectable lower-die openings span 10..16 mm. Select the freshly sourced
stock-row opening in that range; any different opening needs another input
revision. Nominal inside radius and K remain the selected R1/R3 CAD basis.
The declared equipment is not evidence of springback, force capacity for this
part or physical agreement with that development. Coupon testing and actual
press trials remain unperformed; no physical process pass is requested.

## Complete candidate sequence and clearance criteria

There are two parallel bend stations and three disconnected straight bend
intervals: two front intervals and one rear interval. There are three planned
press operations, not a four-wall box or a four-bend returned channel. They
remain one native sheet-metal part with upward 90-degree bends.

| Operation | Presentation | Required access and support |
| --- | --- | --- |
| F1: left front lip, near Y=75, X below 46 | Rear wall and right front lip still flat | Fit relieved punch/die segments to the actual left interval. The cable opening terminates the interval; no tooling bridges it. The flat remainder clears the throat. |
| F2: right front lip, near Y=75, X above 64 | Translate the workpiece along the tool; rear wall remains flat | Fit segments to the right interval. The previously formed left 12 mm lip remains beyond the relieved tool end, with at least 2 mm lateral clearance from tooling. Keep both front lips and the notch. |
| R1: rear wall, near Y=0 | Rotate the blank in its plane; both short front lips are already formed | Use the full remaining rear bend interval. The opposite 12 mm lips clear the gooseneck pocket/throat. The growing 60 mm rear wall has an open tool exit. Open the ram and withdraw through the open side; no side walls close this path. |

Operation R1 is a bend label here, not a replacement for stock revision R1.
Reserve 10 mm clearance beyond the heights and intrusions of standing walls.
The conservative largest wall check is 60+10=70 mm, below both the 80 mm
pocket height and 90 mm pocket depth. A 12 mm lip requires 22 mm, below the
100 mm lower clearance. The 75 mm shelf plus 60 mm wall plus 10 mm reserve
is 145 mm, below the 300 mm clear throat. Evaluate these declared scalar
checks and the selected die opening before CAD. They identify a candidate
setup, not a swept-volume collision analysis or measured tooling result.
Check actual tool-end positions, surviving bend intervals and withdrawal
geometry from the native model; never substitute these estimates for them.

As a preliminary interval check only, each nominal front region is 46 mm
wide. Allowing the maximum 6 mm relief width at its notch end and the 3 mm
external round leaves 37 mm, above the company 20 mm straight-span minimum.
This conservative planar allowance does not establish the native bend span,
flange contact or a press result. Measure actual surviving intervals later.

## Cable notch, relief applicability and deformation

Keep the R3 opening at X=46..64, Y=55..75, open through the front, and both
3 mm notch-root radii. Continue the opening through the front lip so the two
front bend intervals end at reliefs; there must be no narrow metal bridge
across the notch. Integrate square reliefs into the existing opening at both
interrupted bend ends, extending beyond the bend into the shelf as R3 states.
Do not reduce the 18 mm opening, shorten the protected lips, move the slots
or enlarge/delete a protected feature to fit the tooling.

Evaluate the supplier's unsupported-bend/relief provisions alongside its
die-width deformation guidance. An intentional bend-end relief is not a
mounting hole required to remain distortion-free across an active bend.
Neither that distinction nor this company policy proves supplier acceptance.
Record every cut boundary inside half the sourced die opening, its purpose,
its relation to a remaining bend interval, the cited applicable rule and the
remaining supplier question. Do not claim that no geometry enters the caution
region. Keep the caution visible in both simulated handoffs.

The company requires nominal CAD inspection of full-thickness cuts, square
relief dimensions/placement, continuous remaining part topology, no unintended
slivers, preserved root radii/opening, supported front intervals and the
supplier minimum flat/formed flange lengths along those intervals. Measure
actual developed distances to active bend intervals, not only to infinite
extended bend lines. The mounting slots must retain their separate sourced
bend-to-feature checks. A known failure of an applicable hard rule blocks;
missing native evidence is unverified, never pass. Actual notch distortion,
surface witness marks, physical cable clearance and springback remain
unverified supplier/prototype-trial issues, not established nominal geometry.

## Controlling development and verification timing

The company confirms R3's single controlling method: neutral_factor with the
fresh selected-row T, inside R and K. For each 90-degree bend calculate
BA=(pi/2)*(R+K*T) and BD=2*(R+T)-BA. Compare the separately published deduction
in the same units; preserve its signed difference without replacing K or
claiming agreement. Do not count the two side-by-side front intervals as two
successive bends along one developed shelf strip. Compare each material strip
through the applicable native flat using its actual bend path.

A difference between the two published calculation bases remains a supplier
confirmation issue and production HOLD; it is not an unanswered company
selection between methods after this explicit choice. No new acceptance
tolerance is introduced, and the discrepancy is not excused as rounding or
a dimensional tolerance. Physical parts and supplier development remain
unqualified. Keep the exact selected-row evidence and discrepancy in intent,
measured check, export handoff and both simulated supplier reviews.

The new intent may report cad_input_status=ready_for_geometry_verification
only after the company inputs/calculated criteria, current stock/rule evidence
and native input contract are complete with no known mandatory conflict.
Bind the existing exact-intent review to this new input revision. An automatic
test review does not overrule needs_input and is not engineering acceptance.

Native dimensions, cut/relief topology, actual developed flange lengths and
tool-envelope applicability require the generated model; mark them pending
post-CAD verification rather than missing pre-CAD human inputs. They remain
mandatory in the independent measured-design and genuine-DXF export gates.
Separate unperformed physical/supplier process confirmation from those CAD
criteria; never turn it into a passing physical or supplier result.

Keep manufacturing_release=HOLD, supplier_acceptance=unverified and
physical_fabrication=not_performed. Both exact supplier approval gates remain
local simulations with no price or delivery claim. No actual supplier upload,
communication, cart change, purchase, payment or production release is allowed.

Research references for fresh retrieval, not preapproved checks:
[deformation and unsupported bends](https://sendcutsend.com/guidelines/bend-deformation/),
[relief requirements](https://sendcutsend.com/faq/what-are-your-bend-relief-requirements/),
[channel requirements](https://sendcutsend.com/faq/what-are-your-channel-bend-requirements/),
[stock-specific calculation basis](https://sendcutsend.com/bending-calculator/).
