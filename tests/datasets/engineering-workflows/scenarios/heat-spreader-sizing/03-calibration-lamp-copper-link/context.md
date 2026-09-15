# Calibration-lamp link design basis

## Application and model boundary
Ashford's fictional prototype is a low-voltage lamp calibration fixture with a separate cooled mounting rail. This study concerns a passive conduction link only; it does not design a lamp driver, optical exposure system, temperature controller, or safety interlock. The lamp and rail performance are synthetic assumptions. The load is steady 18 W, not a measured heat trace.

## Candidate geometry and material inputs
X=0 is the cold-end link face and X=120 mm is the uniformly heated face. All plates are 2 mm thick. alternatives.csv supplies widths of 60, 80, and 100 mm; the permitted outer envelope is 125 mm long by 104 mm wide. The assumed constant conductivity is 385 W/(m K) and density is 8960 kg/m3, representing a copper-like analysis material without claiming an actual grade or certificate. Plate faces remain unperforated and the four longitudinal faces insulated. No convection or radiation is included.

## Contact-resistance requirement
The cooling rail is held at 35 degrees C, but the plate's cold face is separated from it by a prescribed total thermal contact resistance of 0.15 K/W. This is a lumped total resistance per complete end-face interface, not an area-specific m2 K/W value and not a measured grease property. Preserve that distinction during boundary conversion. For each width, derive the area-specific resistance as R_total times that candidate's end-face area, or use an equivalent mathematically consistent boundary formulation. Do not assign the same unconverted number to a heat-transfer-coefficient field.

The analytical reference for this deliberately one-dimensional setup uses the sum of plate resistance L/(k W t) and total interface resistance. It is an input model definition; it is not a computed temperature field. Apply total 18 W uniformly over the X=120 face. If a numerical backend cannot implement the interface boundary, report the actual unsupported requirement and produce a separately labeled ideal-contact comparison only if it cannot be mistaken for the required case.

## Objective and fabrication context
Choose the lowest-mass candidate meeting hot-end temperature <=75 degrees C under the specified model. If no candidate passes, keep the failure visible; do not change the heat load, contact resistance, or limit. The prototype process is cut flat plate with no bends. Coating, brazing, fasteners, contact pressure, and thermal-pad sourcing are outside this case and must not be invented.

## Evidence, review, and limits
The design review must confirm contact-resistance units, per-candidate interface area, material constants, and boundary names before solving. Preserve all candidate CAD, actual solver fields, total input/removal balance, mesh comparison, and a machine-readable sizing decision. Current test acceptance measures file presence only. Later validation must assess correctness, including whether the interface condition was converted correctly. Do not promote this to a real lamp temperature, safe-surface-temperature assessment, cooling-system qualification, or standards-compliance claim. No physical operation or external transaction is authorized.
