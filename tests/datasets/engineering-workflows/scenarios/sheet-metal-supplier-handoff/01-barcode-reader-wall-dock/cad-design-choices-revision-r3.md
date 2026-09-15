# Parcelwood native CAD design choices, revision R3

PW-PROT-03-R3, dated 2026-09-12, is a fictional user-uploaded design decision.
Preserve all original uploads and R1. The choices below resolve prototype CAD
inputs; they are neither supplier specifications nor evidence of a completed part.
Review this addendum with the manufacturing intent before any native mutation.

## Dimension and feature authority

Use folded outside virtual-sharp dimensions throughout. The finished outside
rear-wall plane is Y=0, the finished outside front-lip plane is Y=75, the bottom
outside plane is Z=0, and the left/right outside limits are X=0/110. Rear-wall
free edges reach Z=60; front-lip free edges reach Z=12. Both bend angles are
90 degrees, upward. These are intersections/extensions of outside planar faces,
not bend tangent lengths, neutral-axis dimensions or pre-flange sketch spans.
The shelf inside face is Z=T for selected thickness T. Preserve all nominal
dimensions and the R1 comparison tolerances. Recalculate native sketch spans
from the selected T/R and actual supported native construction; no generic
single-flange offset formula proves the finished two-flange geometry.

Keep wall-slot centers (20,38) and (90,38) in the X/Z frame of the rear outside
face, width 5.5, overall length 12, vertical major axes and radius 2.75 mm.
The notch occupies X=46..64 and Y=55..75 in the shelf plan, opening through
the front lip. Its two inside root corners have radius exactly 3 mm; the
straight notch opening remains 18 mm. Front lips remain on both sides of that
opening. Integrate reliefs at the two interrupted bend ends without reducing
the opening, deleting a lip or moving a mounting slot. Use the square relief
defined below, extending beyond the bend line into the adjoining notch region.
Retain the other bend-end/corner reliefs required by actual geometry.
External non-bend corners use 3 mm rounds where geometrically feasible; identify
any infeasible corner explicitly instead of silently omitting the requirement.
Side edges remain open; there are no side walls or added separate brackets.

The centered 65 by 50 mm reader footprint is a layout reference, not a cutout.
The company explicitly accepts its overlap with the cable-notch projection for
this stored-part geometry study. Do not remove either feature. Physical support,
fit, stability and cable routing remain untested; no structural or safety claim
is authorized. The 6 mm side clearance remains a minimum. Quantity is four.

## Complete native sheet-metal rule

Select actual stock T, inside radius R, K factor K, and exact native material
identity under R1. Retain source row, units and citations. Set native
`bendCalculationMethod=neutral_factor` and `neutralFactor=K`. The company selects
this K-based development as the controlling geometric CAD method. If a separately
listed 90-degree bend deduction differs, record both numbers and the difference;
do not replace K, mix stocks or claim the two developments agree. The discrepancy
remains an explicit supplier-confirmation issue and manufacturing release HOLD,
not an unanswered company choice between two simultaneous CAD methods.

For this prototype choose square bend reliefs with width W=max(T, the currently
sourced applicable minimum width) and depth D=max(R+T+0.508 mm, the selected
row's minimum relief depth). These are company sizing choices above sourced
minimums, not assertions that the supplier mandates W=T. Both W and D must be
within R1's inclusive 0.5..6 mm bounds. Retain actual evaluated numbers in the
intent and native recipe. Measure relief depth in the developed plane from
the bend centerline; satisfy the separately sourced corner-relief distance.
Use `bendReliefType=square`, `cornerReliefType=none`; explicit corner openings
and notch geometry provide separation. Unsupported geometry or a source rule
requiring another treatment remains blocked, not silently substituted.

The company selects these explicit native flat-pattern settings:
`createFlatPattern=true`, `modelType=flatten_anything`,
`outsideCornerTreatment=none`, `insideCornerTreatment=none`,
`outsideCornerTreatmentValue=0.1 mm`, `insideCornerTreatmentValue=0.1 mm`,
`removeSystemGeneratedBendRelief=false`, `simplifyBSplines=false`,
`minimumArcLength=0.01 mm`, `deviationalTolerance=0.001 mm`.
The positive corner values are required native API inputs even with treatment
none. These are software settings, not manufacturing tolerances. Retain native
reliefs and do not heal away intended cutouts. Use mm lengths and degree angles,
unique feature identifiers, explicit top-plane base construction, closed cut
profiles, full through-sheet cuts, and `dimensionSide=outside` for flanges.
The author must translate these physical requirements into supported recipe
coordinates and validate the recipe before creation; later observed native
geometry and the existing independent checks remain authoritative.

## Research and output decisions

Retrieve the original four supplier pages plus the detailed
[relief requirements](https://sendcutsend.com/faq/what-are-your-bend-relief-requirements/),
[channel requirements](https://sendcutsend.com/faq/what-are-your-channel-bend-requirements/),
[bend deformation guidance](https://sendcutsend.com/guidelines/bend-deformation/),
and [processing size limits](https://sendcutsend.com/materials/processing-min-max/).
The relief page's public guidance reviewed during input preparation gives a
minimum width of half the thickness and depth R+T+0.020 inch; the workflow must
retrieve and cite its current evidence before applying it. It must check actual
feature-to-bend distances, bend sequence, channel exceptions and size limits.
These links are research inputs, not passed DFM checks. A supplier statement
that a design may be possible is not unconditional acceptance.

The runtime part label is `wall-dock`; required representations are native PSM,
folded STEP, developed DXF and the separately labeled inspection JPEG. The
prepared workflow supplies each nominal output path; the owning CAD task assigns
the authoritative indexed path at execution. Index allocation is not missing
human input and the intent must not invent a final path or require it in advance.
Unpainted/deburred remains the requested physical finish, but the company accepts
bare-sheet CAD with finish availability and physical deburring unverified.
All existing geometry/DFM checks, correction bounds and export-integrity checks
remain mandatory. No failed or unknown mandatory constraint passes by this
addendum. Keep `manufacturing_release=HOLD`, `supplier_acceptance=unverified`;
both supplier gates are local simulations. No real upload, purchase, payment,
supplier communication or production release is authorized.
