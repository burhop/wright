# Stratum prototype fabrication capabilities and DFM, revision R4

SM-PROT-07-R4, 2026-09-12. This is a fictional company engineer's uploaded
capability statement for the two-tray/two-lid prototype. Every machine,
tooling capability and internal limit below is synthetic company input, not
a SendCutSend statement, a purchased service, a machine measurement or a
fabrication result. No physical fabrication is requested by this workflow.

## Authority and process scope

Preserve the original brief, panel CSV, policy, R1 and R3 without editing them.
This additive revision supplies the previously missing company prototype
tooling and cut-feature criteria. It authorizes an exact-reviewed CAD model
for evaluation of the company's laser-cut and press-brake prototype route.
It does not change the intended supplier, geometry, quantity, stock-selection
bounds, sourced bend rule, native material mapping or supplier requirements.

Keep three distinct assessments in intent, checks and final handoff:

1. Company prototype inputs: these declared capabilities and calculated
   feasibility, with actual geometry verification still pending.
2. Supplier DFM: freshly retrieved rules and their applicability. Company
   limits do not establish supplier-compatible holes, webs or tool access.
3. Observed CAD evidence: actual native measurements and genuine developed
   exports after model creation; never label planning calculations as measured.

R4 clarifies the earlier CAD gate only for missing supplier-specific feature
limits or supplier machine-access confirmation: these may remain explicitly
unverified for the supplier route while complete company prototype criteria
support reviewed CAD creation. A known applicable supplier hard-limit conflict
still blocks this supplier-targeted design; R4 cannot override one. Unknown
company inputs, failed company inequalities or an unsupported native operation
also block. A conditional supplier exception is not supplier acceptance.

## Declared company equipment and cut limits

The fictional prototype shop has a nitrogen-assisted fiber laser with a
1000 by 1500 mm usable bed, and accepts bare 5052 sheet from 1.3 to 1.7 mm
inclusive. Use the same freshly selected R1 stock for both parts. All holes,
slots, panel openings, corner openings and relief notches are cut in the flat
blank before forming. No drilling, welding, tapping or after-bend laser access
is substituted for the specified through-cuts. The shop quotes no production
tolerance or certification in this input.

The following are company design minima for this prototype, evaluated using
the selected thickness T in mm. They are not supplier rules. Apply any freshly
sourced stricter applicable supplier limit as well; do not silently substitute
these values when reporting supplier compatibility.

| Company criterion | Minimum | Worst case at T=1.7 mm | Protected feature |
| --- | --- | --- | --- |
| Circular through-hole diameter | 1.2*T | 2.04 mm | 3.4 mm screw hole; 12 mm controls |
| Through-slot width | 1.5*T | 2.55 mm | 3 mm vent slot |
| Web between parallel cut edges | 1.0*T | 1.70 mm | 5 mm pitch minus 3 mm width = 2 mm web |
| Hole/slot edge to an unbent free edge | 1.5*T | 2.55 mm | Screw-hole edge clearance: 7-1.7 = 5.3 mm nominal |

Retain the two banks of eight 3 by 32 mm slots at the exact R3 centers and
all four coaxial screw through-holes across the two parts. Preserve every CSV
opening. The company uses the freshly sourced selected-stock bend-to-feature,
relief and flange minima; these do not come from this document. Measure those
distances in the actual developed reference frame. Nominal 5.3 mm free-edge
clearance is not the screw-hole distance to a bend and cannot replace that check.

## Declared box-forming setup and sequence

The fictional shop provides a 60-ton press brake with 650 mm usable bend
length, 300 mm open daylight and 600 mm throat depth. Its raised lower-tool
support leaves 110 mm clear below the working plane. Segmented gooseneck
upper tools provide a 100 mm clear pocket height and 110 mm horizontal pocket
depth for a preformed wall. These are clear spaces, not overall tool sizes.
Segmented upper tools and relieved end sections can be set to the actual bend
span, with upper-tool ends at least 2 mm inside adjacent standing-wall inside
faces. The shop supplies fitted end sections where standard segments do not
match; the effective supported bend span and corner relief must be checked.

Select the lower-die setup using the sourced row's die opening and the R1/R3
inside-radius/K-factor design basis. The shop declares selectable openings
from 10 to 16 mm; a source opening outside that range is a missing capability.
The selected source radius and K remain nominal CAD inputs, not a claim that
this machine reproduces the supplier's springback or physical development.
Coupon tuning, bending force and physical tooling trials remain unperformed.

Use an open-top, unwelded tray with the R3 open butt corners and square reliefs.
Do not add returns or reduce the protected 80 mm walls to fit a small-channel
exception. All four wall bends are upward 90 degrees around the bottom:

| Operation | Workpiece presentation | Tool access requirement |
| --- | --- | --- |
| B1: left wall, X=0 | Flat blank; bend line parallel to Y | Keep both future end walls flat and outside the swept punch envelope. |
| B2: right wall, X=430 | Rotate blank 180 degrees in its plane | B1 stands in the open throat, at the opposite side of the wide bottom; it must not enter the ram or backgauge envelope. |
| B3: front wall, Y=0 | Rotate 90 degrees; existing side walls upward | Shorten/relieve tool ends between the two standing side-wall inside faces; each 80 mm wall enters the declared gooseneck pocket without contact. |
| B4: rear wall, Y=250 | Rotate 180 degrees; front wall at opposite side | Repeat the end-clearance setup; the front wall remains in the open throat. Withdraw vertically through the open top after opening the ram. |
| L1/L2: lid skirts, X=-2 then X=432 | Separate flat lid blank; rotate 180 degrees between bends | Two downward 18 mm skirts only; use the raised lower support and keep the opposite skirt clear. |

For the prototype plan reserve 10 mm clearance beyond each preformed wall's
height and pocket intrusion. Thus an 80 mm wall requires at least 90 mm of
the 100 mm vertical pocket and 90 mm of the 110 mm horizontal pocket; an
18 mm lid skirt requires 28 mm below the work plane, within 110 mm. These
scalar checks establish a declared candidate setup, not a verified swept-volume
collision result. Carry the actual tool-end clearance, supported bend span,
corner openings and withdrawal envelope into the post-CAD inspection criteria.
If those observations cannot be made with available tools, report the specific
unverified check; never report that the physical press sequence passed.

Read the ordinary supplier channel ratio before its exceptions. Conservative
clear spans across the R3 tray are 430-2*T and 250-2*T. At T=1.7 mm these are
426.6 and 246.6 mm, giving ratios to the 80 mm wall of 5.3325 and 3.0825.
These calculations support evaluating the ordinary 2:1 condition from fresh
evidence. The 3-inch flange condition belongs to the optional 1:1 exception;
exceeding it does not by itself fail the ordinary 2:1 rule. This document is
not the primary source for any supplier rule, and channel ratios alone do
not establish a complete four-bend box-forming sequence.

## Review and verification timing

Before CAD creation, provide actual sourced stock/rule values, all R3 native
recipe inputs and coordinates, the company-versus-supplier applicability
table, calculated company-limit margins and this explicit sequence. Preserve
the exact manufacturing-intent review before either native part is created.
The intent may state cad_input_status=ready_for_geometry_verification only
when those inputs are complete and no known mandatory conflict exists.

Native bend-centerline distances, genuine flat-pattern extents, relief
intersections, corner topology, sheet thickness, lid clearances, keepout and
part collisions require a generated model. List them as pending post-CAD
verification with measurable criteria; their not-yet-measured status alone
is not missing human input and cannot be required before the first model
exists. They remain mandatory in the existing measured-design and export
gates. Do not change a check to pass, omit a feature, flatten an assembly,
substitute recipe values for observations or export a folded projection as DXF.

Supplier-specific cut limits and full shop acceptance can remain unverified
only with that fact carried into the simulated supplier previews and final
handoff. This never becomes a successful supplier DFM check. Keep
manufacturing_release=HOLD, supplier_acceptance=unverified and
physical_fabrication=not_performed. Finish and coated-fit uncertainties remain
as allowed by R3. Preserve both exact simulated supplier approval gates;
auto review is not engineering validation. No actual supplier upload,
communication, cart change, purchase, payment or production release is authorized.
