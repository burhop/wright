# Desktop instrument foot brief

## Product and use assumptions
The fictional synthesizer is a 1.8 kg desktop instrument supported by four feet on a flat desk. This dataset covers one rear-left replacement foot. It does not authorize instrument modification, electrical work, or design of a carrying attachment. Operating temperatures are 15 to 35 degrees C. A matte curved silhouette should make the repair look intentional.

## Dimensioned intent
Coordinate origin is the front-left corner of the mounting rectangle. X is left-to-right, Y front-to-back, and Z extends down from the instrument mounting face. The controlling reference is 38.0 mm along Y. The mounting rectangle is 26.0 mm X by 38.0 mm Y. Height below the mounting face increases linearly from 8.0 mm at Y=0 to 17.0 mm at Y=38; preserve a flat mounting face at Z=0. Maximum outer width remains 26.0 mm; sculpt the visible sides with 3 mm corner fillets.

Two clearance holes are at (13,9) and (13,29), diameter 3.4 mm, axes normal to the mounting face. From the exposed sole side, provide 6.5 mm diameter by 2.5 mm deep counterbores; do not create a conical countersink or tapped hole. Leave at least 2.0 mm material between counterbore and external wall.

A separately purchased rubber strip seats in a 16 by 28 mm recess centered at (13,19), 1.0 mm deep measured normal to the sloped sole. It is an internal synthetic pad specification; no rubber geometry needs to be printed. Round pocket corners 2 mm. The rear-right cable keepout removes the region X=21..26, Y=31..38 for the full body depth, with a 2 mm internal fillet; see the hatched notch in the sketch.

## Manufacturing capability and policy
Target P1S, 0.4 mm nozzle, PETG, 0.16 mm layers, five perimeters, 45% infill. Human review must confirm installed profile identities; a PLA test package must say PLA. Supports are permitted on the outer sculpted sides but should avoid the screw clearance bores and pad seating face if orientation allows. Keep source and repaired meshes separate. A local receipt may be generated only by the test simulator. No credentials, real printer transfer, print start, or material certification is provided. Geometry existence tests are the first phase; stability, screw fit, creep, and surface finish remain unvalidated.
