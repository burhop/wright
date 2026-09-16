# Circular-fixture drill-jig specification

## Workpiece and frame
The fictional Meridian lab is preparing five non-safety-critical tabletop fixture plates. Each is a flat circular aluminum surrogate, 152 mm diameter and 10 mm thick. The top-face center is (0,0,0). +X points to an existing rectangular rim notch, +Y is 90 degrees counterclockwise in plan, and drilling is in negative Z. The existing notch removes X=70..76 mm, Y=-4..4 mm through the plate thickness. This is a supplied datum feature, not a new cut to make.

Six clearance holes lie on a 100 mm diameter bolt circle. holes.csv contains the controlling rounded Cartesian coordinates to three decimals; use them as input, not a re-derived rounded angle table. Requested drill size is 6.6 mm through the 10 mm plate. Center-location tolerance is +/-0.10 mm in X and Y relative to the center and keyed orientation. The drilling process and breakthrough allowance are not prescribed by the jig geometry.

## Jig construction and fits
An annular plate is preferred, with a central circular opening at least 55 mm diameter for debris removal. Use 16 mm nominal local thickness at bushing seats, and preserve at least 5 mm nominal wall outside the flange pockets where not interrupted by reviewed clamp/service cutouts. The outer collar registers over the workpiece rim with 0.20 mm radial clearance. A tab entering the existing notch uses 0.15 mm clearance per side and no interference fit. The tab may not extend below the workpiece base.

The synthetic bushing dimensions are 6.7 mm bore, 12 mm body OD, 16 mm body length, 18 mm flange OD, and 2.5 mm flange thickness. Allow 0.20 mm diametral clearance in body seats and 0.30 mm diametral clearance at flange pockets. Keep the flange seated from above; record the body/plate stackup and any proposed counterbore depth. A flange is not proof of retention during tool withdrawal; that issue remains for physical review.

keepouts.csv marks asymmetric top clamps near the -X rim and lower-right rim. These volumes are excluded from jig material. The top-view drawing includes them as hatched rectangles. Do not move holes away from clamps; add local jig cutouts or document an unresolved intersection. Mark +X DATUM adjacent to the notch in an accessible exterior region.

## Lab policy and validation boundary
This is a digital manufacturing aid concept. It is not a certified precision fixture, rotating workholder, lifting device, or machine guard. Prototype material may be machined acetal; no substitution to metal or FDM is implied without a recorded decision. The supplied bushing table mimics an upload but does not identify a real purchased item. Confirm real supplier dimensions, spindle/tool clearance, chip evacuation, clamp stability, and achievable tolerance before fabrication.

Expected workflow files are CAD/mesh, DXF hole drawing, and a measurement report. File-presence acceptance is the only current metric; actual geometric correctness remains unvalidated. No machine motion, drilling, procurement, or external delivery is authorized by this dataset.
