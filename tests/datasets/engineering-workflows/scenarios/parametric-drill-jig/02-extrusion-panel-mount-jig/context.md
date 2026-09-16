# Rectangular-tube drilling jig

## Workpiece and production context
Signhaven's fictional display frame uses a 180 mm X by 80 mm Y by 30 mm high rectangular aluminum tube, with a nominal 3 mm wall. The alloy name is a project assumption of 6061-T6; no material certificate or strength qualification is provided. The production intent is ten prototype frames. Coordinates are relative to the front-left corner of the exterior top face, with X along length and positive Z above that face. Drilling is downward in negative Z through the top wall only. The opposite interior wall lies nominally 27 mm below the top surface; do not use that as an automatic drill-depth setting.

## Hole and fixture requirements
holes.csv contains four 6.6 mm clearance-hole centers at X=30 and 150, Y=20 and 60. Nominal hole center tolerance is +/-0.15 mm relative to the workpiece datum. A depth of 3 mm records the nominal wall thickness only; operator/tool breakthrough allowance remains outside this model. Use external datum fences on the front end and left side, avoiding the end clamp rectangles in keepouts.csv.

Create two bushing bridges linked by a narrow outer rail so an open central chip-removal region remains at X=65..115, Y=15..65. That region is an intentional jig-material exclusion, not a workpiece opening. The jig must not depend on inserting support inside the hollow tube. Use 15 mm nominal local bridge thickness at the bushing seats and at least 6 mm nominal material outside flange pockets, except where datum/service cutouts force review.

The fictional bushing upload specifies 6.7 mm bore, 12.0 mm body OD, 15 mm body length, 18 mm flange OD, and 2.5 mm flange thickness. Use 0.15 mm diametral clearance at the body and 0.30 mm at the flange. This is a removable slip-fit concept, not a press-fit prescription. Model the flange seating and body-length stackup explicitly. Do not silently turn a flanged bushing into a straight sleeve.

## Capability, policy, and limits
Available prototype processes are CNC-machined acetal or FDM PETG; the customer prefers acetal for this digital study but has not approved production. Specify which is assumed in any design note. The external clamps occupy X=0..18 and 162..180 across the whole width and extend 30 mm above the workpiece. Jig geometry must avoid them, including datum fences; use local datum contact outside the clamp-contact region and show that interpretation in the review.

Actual supplier bushing dimensions, finished fit, chip evacuation, spindle clearance, drill runout, tool guarding, and safe operating setup require later human verification. No machine actuation is requested. Return a STEP or STL jig, hole-layout DXF, and JSON dimension/clearance report. Input data, sketch, and operating assumptions are synthetic; no standards-compliance claim is made.

## Authorized prototype design decisions

For this digital prototype, the customer approves a local exception to the preferred 6 mm material around only the end-facing sides of the four flange pockets. The 18.30 mm flange-clearance pockets centered at X=30 and X=150 leave exactly 2.85 mm of jig material between each pocket edge and the nearest X=18 or X=162 clamp boundary. Use that 2.85 mm ligament, do not enter either clamp keepout, and reinforce the bridges toward the clear central side of each hole pair. The 6 mm preference still applies everywhere else that is not a declared datum or service cutout.

Use the following fully defined datum arrangement. Two front-end contact pads occupy X=-4..0, Y=24..32 and Y=48..56, Z=-3..12 and touch the workpiece only on the X=0 plane. A left-side fence occupies X=18..162, Y=-4..0, Z=0..12. Connect the front pads to the left fence through material at Y=-8..0, staying outside the clamp volumes. Boundary contact at X=0 or Y=0 is intended; positive-volume intersection with a clamp keepout is not.

The tube already has a customer-supplied indexing notch through its top wall at the front-left edge: X=0..4, Y=9..15, Z=-3..0. Do not alter that workpiece feature. Add one matching jig key tongue with 0.20 mm clearance on each in-plane side, occupying X=0..3.8, Y=9.2..14.8, Z=-2.8..0 when seated. The tongue must be part of the front datum structure. This is the approved positive wrong-end prevention geometry; also emboss or engrave a front arrow for visual confirmation.

For the removable prototype bushings, use a 12.15 mm cylindrical body hole and an 18.30 mm diameter by 2.50 mm deep top counterbore. The flange bears downward on that seat and the 15.00 mm body spans the remaining bridge thickness. No secondary retainer is required for this downward-only drill-press study; the operator removes the jig before transport and verifies every bushing is seated before use. These nominal CAD clearances are authoritative for this digital run, while purchased-part fit remains a later physical check.

The shop reports 110 mm of vertical clearance from the tube top face to the retracted chuck and a 25 mm minimum clear nose envelope around each drill axis. Keep the modeled jig at or below 17.5 mm above the tube top face and keep non-bushing jig material outside a 25 mm diameter vertical access cylinder at every hole. Guarding, runout, breakthrough allowance, and machine setup remain later human checks and do not block creation of the requested digital prototype artifacts.
