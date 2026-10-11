# Engineering basis and verification plan — revision ME-01

Prepared 8 October 2026, before new geometry. Status: criteria prepared; outputs,
digital assessment and actual human review pending. This adds tool bindings and
engineering deliverables to two existing assignments; it does not alter their
accepted geometry or turn fictional inputs into observed facts.

## A. Barcode-reader wall dock: sheet-metal fabrication study

**Purpose:** store a fictional packing-bench reader on a folded aluminum cradle.
Produce a reviewable fabrication package for four prototypes. It is not a
polymer-printing job. Manufacturing release is HOLD; supplier acceptance is
unverified; physical fabrication is not performed.

**Input authority:** unchanged scenario
`tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock/`,
including prompt, sketch, context, manufacturing policy, stock revision R1, native
CAD choices R3 and company forming capabilities R4. Those documents remain the
full authority; this table is an index, not a replacement. Freeze their hashes
with the accepted workflow revision and later artifact manifest.

**Process/material:** native Solid Edge sheet metal → independently measured
folded geometry → true native developed flat → FreeCAD TechDraw drawing from
the exact folded STEP → locally simulated supplier review package. No slicer.
Select the complete current supplier stock/rule row under R1; no arbitrary
1.5-mm substitute. Requested 5052, supplier temper and installed CAD label stay
separate. Current stock, T/R/K and die-opening evidence are prerequisites, not
facts supplied by this new brief. No structural or anchor capacity assessment
is claimed from a 0.42-kg reader and 15-N fictional concept load.

**Coordinates:** mm, X across width, Y away from wall, Z upward. Folded *outside
virtual-sharp* planes: X=0/110, rear Y=0, front Y=75, bottom Z=0. Shelf inside
Z=T. Rear top Z=60, lip tops Z=12. Native recipe spans must be recalculated
from selected T/R and measured after construction.

| ID | Retained acceptance basis | Method / exact subject | Missing/physical scope |
| --- | --- | --- | --- |
| D01 | Outside 110 × 75; back 60; two upward 12-mm lips; open sides | Native face/feature dimensions and STEP comparison; original R1 ±0.05-mm nominal CAD comparison, ±0.1° angles | Numerical CAD comparisons are not fabrication tolerances. |
| D02 | Vertical slots centered (20,38)/(90,38), 5.5 × 12, end R2.75 | Native slot edges in rear X/Z datum and downstream drawing dimensions | Mounting anchors/wall capacity unspecified and excluded. |
| D03 | Cable opening X46..64, Y55..75, root R3; split front lips, no bridge; feasible external R3 | Exact native cut/fillet topology, open-cut correspondence in flat DXF; disclose infeasible corners | Physical reader stability, cable routing and distortion untested. |
| D04 | Centered 65 × 50 footprint; side clearance ≥6; explicitly accepted footprint/notch overlap | Coordinate layout comparison with unchanged R1/R3 footprint | No fitted commercial reader or support test. |
| D05 | Stock T 1.3..1.7, inside R0.5..2.5, selected complete rule; exact allowed native alloy readback | Fresh cited stock row plus native rule/material inventory/readback | No invented temper/properties or material certificate. |
| D06 | Neutral-factor K controls development; W=max(T,current minimum), D=max(R+T+0.508,current minimum); W,D 0.5..6 | Native rule, relief geometry/developed measurements; BA=(π/2)(R+KT), BD=2(R+T)-BA per actual strip | Preserve separate listed deduction and signed discrepancy; supplier confirmation HOLD. |
| D07 | Constant sheet thickness, continuous topology, full cuts/no slivers; surviving intervals ≥20 and applicable supplier flange/feature limits | Independent native measurements, flat closed cut contours, actual distances to active bend intervals | Missing mandatory native evidence cannot pass via review. |
| D08 | R4 sequence F1/F2/rear; configured die opening10..16; tool access and withdrawal | Frozen R4 scalar checks and actual interval/end geometry; document bounds | No swept tooling collision, springback/force/coupon trial or supplier machine confirmation. |
| D09 | PSM, folded STEP, genuine developed DXF, inspection JPEG and dimensioned drawing | Verify exact producer/document/path/hash, reimport, units and correspondence. TechDraw uses exact STEP; never dimension an AI illustration | JPEG is visualization, not engineering definition. Native flat remains with Solid Edge. |
| D10 | Quantity4, unpainted/deburred requested; two exact local simulator gates | Manifest, design/DFM/inspection package and explicitly synthetic decisions | No supplier communication/upload/order/price/lead time or physical finish proof. |

**Documentation:** design basis + requirements/verification matrix with source,
artifact/feature, expected values/units/frame, actual observation, method,
uncertainty, status and reviewer; assumptions/decision log; separate company
feasibility and supplier DFM findings; folded drawing with sufficient views and
sections, datum dimensions, selected material/thickness, bend/finish notes and
part/revision; flat drawing/cut-and-bend information; inspection plan; revision
manifest. Drawing completeness is checked against the actual geometry.

**Decisions:** intent review before native mutation; measured-design and export
gates retained with original maximum two automatic correction attempts; both
supplier approvals remain simulation-only. Actual product review stays pending.
Known supplier hard conflicts still block the supplier-targeted design; only
the three explicitly deferred R4 supplier issues remain disclosed HOLDs.

## B. Observatory focus wheel: additive prototype study

**Purpose:** replace the hand-turned wheel on a fictional unloaded training
telescope, suitable for gloved handling. Retain every original input in
`tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel/`.
Only new CAD binding and additional engineering deliverables are proposed.

**Process:** editable FreeCAD native solid → independent feature/export check →
controlled mesh → independent orientation/support assessment → actual offline
PETG slice through an existing independent provider → review package and local
simulator receipt. Native STEP/drawing are engineering definition; mesh is its
derived manufacturing input. No real printer transfer/start.

**Coordinates:** mm; shaft/socket axis Z. Declare the model's face datums and
local frame in the accepted CAD task, then record orientation transform into
the build frame. A bore-up build is assessed, not assumed automatically optimal.

| ID | Retained acceptance basis | Method / exact subject | Missing/physical scope |
| --- | --- | --- | --- |
| W01 | Max diameter38; overall18 including raised hub2; six equally spaced shallow scallops, minimum grip diameter33 | Parametric feature tree, exact native sections and neutral model measurement | ±0.25 proposed non-mating manufactured tolerance is separate from numerical export agreement. |
| W02 | Nominal exposed-edge R1; subtle raised grip dots without catch features | Native edge/feature inspection, documented feasible treatment and visual examination | Gloved ergonomics require physical/user test. |
| W03 | Shaft nominal Ø6, across-flat5.2; round radial clearance0.2 and flat clearance0.2; blind depth10; concentric socket | Socket section measured from actual native faces. Shaft radius3; flat position is 5.2−3=2.2 from center. Proposed socket round radius3.2 and flat plane2.4 from center, giving socket across-flat5.6 | Design clearance is not measured printed clearance. No taper/keyway/set screw/insert. |
| W04 | At least3 material above blind socket | Native section/topology and minimum local roof dimension, not just envelope subtraction | Physical porosity, layer adhesion and strength untested. |
| W05 | PETG, P1S0.4 nozzle, layer0.20, perimeters4, infill35% | Actual installed machine/process/filament profile identities and package/G-code contents | No silent PLA substitution. No physical print quality claim from a valid slice. |
| W06 | Valid solid; manifold single printable component; declared mesh conversion quality | Independent reimport/topology checks and deviation measurement of mesh versus exact CAD; freeze conversion criterion in validation profile before evaluation | Mesh tolerance is a numerical parameter, not manufacturing accuracy. |
| W07 | Bore-up if it improves socket, support contact/removal assessment | Actual oriented mesh and sliced support/toolpaths; document datum-to-build transform and supported orientation comparison | Overhang, anisotropy, creep and print variation remain physical questions. |
| W08 | Native editable CAD, STEP, inspection drawing, controlled STL, sliced package and previews | Reopen/change fresh copy, precise artifact identity and independent readers; preserve original source/repaired mesh roles | Files alone do not prove fit or performance. |
| W09 | Intended torque0.15N·m and ambient0..35°C | Design-basis assumptions with physical fit/torque/temperature test plan | No FEA added merely to inflate stages, no bulk PETG strength claim certifying printed part. |

**Important interpretation:** W03 documents the arithmetic implicit in the
original D-shaft input; actual native cross-sections must verify that interpretation.
Clearance applies separately to the round wall and flat. Do not use a 6.4-mm
circular bore or infer a new mating standard. Hub and blind-socket side are
documented in the native construction and drawing before assessment.

**Documentation:** design basis, requirement/verification matrix, measured
native/export assessment, manufacturing orientation/support/material assessment,
dimensioned drawing including socket section, functional inspection plan,
assumptions/decisions and exact revision manifest. Fit gauge/caliper procedure,
torque test, glove handling, roof inspection and environment/creep evaluation
are proposed physical tests, not test results.

## Common proof and review rules

- Freeze acceptance profiles before each test. Actual observers supply results;
  no AI-authored pass substitutes for mandatory geometry/profile measurements.
- Use separate fresh defective copies: e.g. W03 flat plane offset deliberately
  outside the accepted bound. The exact feature check must fail, hold dependent
  slicing/review and record a specific finding. Correct only within the accepted
  bound; retain attempts and regenerate/reassess downstream artifacts.
- A meaningful variant must preserve this assignment's critical interfaces.
  Cosmetic label changes are not an engineering variant. Select and document
  an eligible stock/rule case for the dock and a permitted grip/detail choice
  for the wheel after provider scope is known; do not silently change frozen
  dimensions, shaft clearance or PETG.
- Declared input responses differ from engineering approvals. Observe actual
  waiting state before exact-subject attributed synthetic test responses. Leave
  a separate exact final review pending for the user.
- Original supplier/company policy, general reference practices and actual
  manufacturing evidence occupy separate columns. Public ASME/ISO descriptions
  can establish reference scope, not standards compliance; research editions
  and accessible primary sources before relying on them. No clauses invented.
- Final package status is digital study/review, not manufacturing release.

This brief prepares the criteria; it does not claim that CAD, drawing, slicing,
engineering verification or user acceptance has succeeded.

## Substantially different regression: controller conduction strap

The 9 October continuation reuses the original
`heat-spreader-sizing/01-eink-sign-controller-strap` assignment and its full
Feature 082 profile. This is the additional analysis journey required by M4;
it does not replace either primary mechanical assignment.

**Engineering job:** compare two flat rectangular straps for a fictional e-ink
controller and select the narrowest candidate that meets the declared thermal
limit. AgentCAD/build123d produces and reopens the actual STEP solids. The
independent OASiS/scikit-fem provider uses their measured rectangular dimensions
and exact STEP hashes to solve a bounded three-dimensional conduction problem.
This is rectangular meshing from measured dimensions, not arbitrary STEP meshing.

**Frozen basis:** X=0..100 mm, Y=0..40 or 60 mm, Z=0..2 mm; k=200 W/(m K);
4 W uniformly applied to the full X=100 face; full X=0 face fixed at25°C;
four insulated longitudinal faces. Density2700kg/m³ is for comparative mass
only. Heat input and material constants are synthetic dataset inputs. No
convection, radiation, interface resistance, holes or local chip footprint are
introduced. The supplied65mm width envelope and two-prototype quantity remain.

**Verification:** native STEP read-back and measurements; exact CAD-to-field
correspondence; coarse and fine numerical fields; analytical temperature-rise
agreement and refinement sensitivity≤2%; heat imbalance≤1%;45°C inclusive
hot-end limit. The existing profile expects the40mm candidate to exceed that
limit and the60mm candidate to satisfy it. Preserve both observations. The
profile, numerical operation and original assignment bytes remain unchanged.

**Deliverable and limits:** candidate STEP files, raw CSV/VTU fields, analytical
and mesh comparison, heat balance, sizing decision, assumptions and exact-output
assessment. This supports a decision within the idealized model. Independent
critic/human acceptance remains separate; no physical controller performance,
certified material, manufacturing release or standards compliance is claimed.

The added configuration maps the local CAD project to an explicit provider
workspace mount. Wright file paths, CAD-native paths and solver-native paths
remain distinct and recorded. Existing source acceptance, durable run,
declared basis review, gateway, unique run-output paths and validator are reused.
No engineering operation is performed by the preparation script.
