# Stratum native CAD design choices, revision R3

SM-PROT-07-R3, dated 2026-09-12, is a fictional user-uploaded design decision.
Preserve the original uploads and R1. These are explicit company prototype
choices, not manufacturer facts, physical measurements or a passed design.
The exact revised manufacturing intent must be reviewed before native mutation.

## Dimension and assembly authority

Use folded outside virtual-sharp dimensions. Base outside wall planes are
X=0/430 and Y=0/250, bottom outside face Z=0, all wall tops Z=80. These values
refer to planar-face intersections/extensions rather than bend tangent spans
or native sketches. Keep the original electronics box X=35..395, Y=35..215,
Z=6..75, with no standoffs. Preserve every panel-cutouts.csv face coordinate.
Front/rear cutouts lie on their actual outside surfaces Y=0/250; their Z
coordinates are absolute heights above the exterior bottom. Display and rear
opening corners are radius 3 mm; control holes are diameter 12 mm.

Center the lid on the base: its outside top rectangle is X=-2..432,
Y=-2..252, with top outside face at Z=84. Its two outside skirt planes are
X=-2/432 and free edges at Z=66, giving an 18 mm outside skirt height. Inside
top is Z=84-T. The skirts overlap the tray's height by 14 mm. There are only
two downward side skirts, no front/rear lid flanges. All bends are 90 degrees.

This explicitly revises the ambiguous original '2 mm side clearance' wording:
2 mm is the outside-plane offset on each side, not clear air between sheets.
The corresponding nominal clear air gap is 2-T on each side. The company now
requires at least 0.25 mm actual bare-sheet gap per side, while retaining both
430/434 mm widths and the 84 mm assembly envelope. Record original requested
clearance versus this revised interpretation and evaluate the actual bend
regions for collision. This is a disclosed human design revision, not a claim
that 2 mm internal air clearance was achieved. No coating allowance is claimed.

## Corners, vents and removable screw interfaces

Use open butt corners on the tray, without welding, hems or close-corner
features. Front and rear walls span X=0..430. Left and right wall ends stop
2 mm short of the front/rear wall inside faces: their straight end planes are
Y=T+2 and Y=250-T-2. This defines a 2 mm non-contact butt gap, not a sealed
corner. Add the explicit square bend reliefs below at all four base corners;
where a relief intersects a butt opening, preserve the larger sourced-required
opening. Overall outside footprint and wall height remain unchanged. Do not
extend overlapping flanges and call intersecting solids a valid corner.
Round feasible exposed non-bend corners 3 mm; retain every infeasible corner
as an explicit criterion. Bend the two side walls before front/rear walls for
the proposed physical sequence; evaluate actual press/tooling access.

Place both lid vent banks with slot major axes along Y. All centers have
Y=125. Bank A centers have X=120,125,130,135,140,145,150,155;
bank B centers X=275,280,285,290,295,300,305,310. Each slot is 3 mm wide,
32 mm overall long, with semicircular ends radius 1.5 mm. Thus each bank has
eight slots and the short-axis center pitch is exactly 5 mm. These are company
layout choices resolving previously unspecified locations. Keep the original
slot count, dimensions and visual spacing; verify actual cut-feature and bend
clearances rather than declaring the 2 mm inter-slot web acceptable by fiat.

Provide two removable screw interfaces, one centered on each side at Y=125,
Z=73. Each interface consists of a coaxial 3.4 mm diameter through-hole in the
tray side wall and its matching lid skirt: two holes per part, four total.
Their axes are along X normal to the actual side faces. No threads, PEMs,
tapped holes, counterbores, dimples or invisible captive hardware are modeled.
The fictional assembly uses separately sourced loose M3 screws, washers and
nuts outside the sheet-metal purchase. Inner protrusion is limited to 10 mm
from the base outside side plane, leaving the supplied keepout untouched.
Manual access and assembled retention remain untested. Supplier hole/bend
clearance applies to these holes too; do not shift them silently to pass.

The original accent band is marking/finish-only X=20..410, Z=8..26 on the
front; model no structural pocket or material removal. The company accepts
bare-sheet geometry while finish process, charcoal appearance, physical
marking, coating thickness and coated fit remain unverified. Quantity is two
base trays and two lids. Preserve R1's separate stock/native identity mapping.

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

The runtime part labels are `base-tray` and `removable-lid`; each requires its
own native source, folded model and genuine developed DXF, never a flattened
assembly substitute. Use the same selected stock and native bend rule for both.

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
