# Silent sign-controller thermal-link study

## Product context
Finchline's fictional studio is exploring a silent desktop e-ink status sign. The controller's heat would be carried through a conduction strap to a temperature-controlled backing rail. This pack intentionally reduces the product to a bounded conduction-only verification case. The 4 W load is an invented design value; there is no physical test log or actual chip model.

## Geometry and boundary definitions
Use X along the conduction length. Every candidate is a rectangular solid with X=0..100 mm, Y=0..W mm, and Z=0..2 mm. alternatives.csv defines W=40 and 60 mm. X=0 is a fixed 25 degrees C cold face. Apply total heat 4 W uniformly over the full X=100 end face. The four longitudinal faces are perfectly insulated. No convection, radiation, screw hole, interface resistance, heat sink, or local chip footprint is part of this model. All heat flux and geometry must be converted consistently to SI units inside the solver.

The assumed constant conductivity is 200 W/(m K); density 2700 kg/m3 is supplied only for comparative mass. These are synthetic model constants, not certified alloy data. The applicable analytical model is a steady one-dimensional bar with thermal resistance L/(k W t); compare numerical hot-end temperature against that declared baseline. An analytical calculation alone is not a numerical field output.

## Engineering objective and shop capability
Choose the narrowest candidate that satisfies the internal hot-end limit of 45 degrees C in this idealized model. The available design envelope permits up to 65 mm width. The assumed process is profile-cut flat aluminum sheet with no bending or surface finish requirement in this study. Prototype quantity is two. Mounting holes and thermal interfaces are deferred and must not be added to the simulation without creating a new case.

## Reporting policy
Retain each candidate STEP geometry, solver field, heat balance, mesh sizes/refinement evidence, and decision rationale. The template's later physics qualification aims for 2% analytical agreement and mesh sensitivity and 1% heat imbalance; current dataset acceptance only checks required output files. Do not mark physics-valid merely because these files exist. The synthetic input diagram must not be reused as a result contour. No material purchasing, manufacture, or device action is requested, and no standards compliance is asserted.
