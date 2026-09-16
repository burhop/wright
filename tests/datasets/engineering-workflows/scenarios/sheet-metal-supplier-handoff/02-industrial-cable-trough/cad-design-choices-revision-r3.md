# Fieldbar native CAD design choices, revision R3

FB-MFG-12-R3, dated 2026-09-12, is a fictional user-uploaded design decision.
Preserve every original upload and R1/R2. The following choices fill CAD inputs;
they are neither supplier facts nor evidence that the design has passed checks.
The exact revised intent must be reviewed before native mutation.

## Dimension and feature authority

Use folded outside virtual-sharp dimensions. X=0/400 are the open end planes;
Y=0/80 are the outside wall planes; Z=0 is the exterior bottom plane. Both
walls/returns reach the outside top plane Z=60. The outward left return ends
at Y=-20, right return at Y=100, each measured 20 mm from the corresponding
outside wall plane. Thus the return-to-return outside span is 120 mm. Dimensions
refer to planar-face intersections/extensions, not tangent lengths, neutral
axes or native base-sketch spans. All four longitudinal bends are 90 degrees.
The inner bottom is Z=T and the return undersides are Z=60-T; the nominal
unobstructed interior depth is 60-2T before local bend effects. Verify at least
45 mm actual clear depth and the 25 mm loop path through the full open channel.

Preserve mounting-holes.csv exactly. Slot centers use the exterior X/Y frame;
each through-bottom slot has width 6.5 mm, overall X length 15 mm and radius
3.25 mm. Do not move a slot to clear a bend. Apply 3 mm rounds to the non-bend
outer corners at both open ends of both returns. No end plates, hooks, tabs,
separate brackets, welds or threaded-sheet features are added. End planes
remain open; every intentional bend-end relief is explicit in the native
recipe and flat pattern. Quantity is six.

The physical bend sequence chosen for review is both outward upper returns
first, then the left and right base-to-wall bends. Model feature dependencies
may create a wall before its return; distinguish CAD feature order from press
sequence. Research tooling clearance for the complete four-bend cross-section.
The public channel guidance reviewed during input preparation describes a
1:1 exception for material no thicker than 0.135 inch with flanges no longer
than 3 inches. The requested 80/60 mm cross-section is a candidate for that
exception, not evidence the complete returned channel is approved. Retrieve
the current conditions and evaluate all relevant returns/tool envelopes. An
unsupported press sequence remains a blocker; the company does not waive it.

R2's exact unique native C10 label remains a geometry-only mapping, not supplier
stock equivalence. Keep requested cold-rolled stock, selected supplier row and
native material identity separate. The company accepts bare-sheet CAD while
powder-coat availability, film thickness, hole allowance and coated fit remain
unverified; do not adjust hole sizes or pretend the finish is produced.

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

The runtime part label is `cable-trough`.

Retrieve the original four supplier pages plus the detailed
[relief requirements](https://sendcutsend.com/faq/what-are-your-bend-relief-requirements/),
[channel requirements](https://sendcutsend.com/faq/what-are-your-channel-bend-requirements/),
[bend deformation guidance](https://sendcutsend.com/guidelines/bend-deformation/),
and [processing size limits](https://sendcutsend.com/materials/processing-min-max/).
The workflow must retrieve fresh evidence, cite exact source offsets and apply
selected-stock feature, relief, flange, channel, bend-sequence and size limits.
These links are research inputs, not passed checks or supplier acceptance. Do
not apply a general rule without reading its applicable exception, and do not
promote a conditional exception to unconditional supplier acceptance.

The prepared workflow supplies nominal part/output names. The owning CAD task
allocates authoritative indexed paths at execution. Intent can cite those
nominal paths and the allocation policy; final path allocation is not missing
human input. Never invent a final indexed path or require one before allocation.
Retain separate native PSM, folded STEP, developed DXF and labeled inspection
JPEG outputs per part. All original independent geometry/DFM checks, correction
bounds and export-integrity gates remain mandatory. Unknown or failed mandatory
constraints do not pass by review or HOLD. Keep `manufacturing_release=HOLD`,
`supplier_acceptance=unverified`; both supplier gates are local simulations.
No real upload, order, payment, supplier communication, certification or
production release is authorized.
