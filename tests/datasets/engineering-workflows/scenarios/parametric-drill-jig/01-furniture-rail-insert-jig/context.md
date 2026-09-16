# Furniture-rail drill-jig basis

## Shop purpose and coordinates
Meadowform's fictional pilot batch contains 24 hardwood assembly rails. The workpiece is a nominal 200 mm X by 60 mm Y by 18 mm thick rectangular rail. Coordinates use the lower-left top-face corner as (0,0,0), with X along the 200 mm length, Y across the width, and positive Z above the workpiece. Drilling travels in negative Z. The material is an unspecified hardwood surrogate; no actual machining feed or speed is provided.

holes.csv defines two 5.0 mm pilot holes at (30,30) and (170,30), depth 12 mm into the workpiece. Depth is an operator setup requirement, not enforced by the generated geometry unless a separately specified stop is designed. Target center-location tolerance is +/-0.20 mm in X and Y; target jig-seat diameter tolerance is +/-0.10 mm. These are internal prototype targets and have not been qualified on the printer.

## Jig and bushing intent
Create a top plate with 12 mm nominal thickness, a left-end datum fence and a lower-edge datum fence, each contacting no more than 8 mm down the workpiece side. Allow 0.30 mm nominal clearance at the non-datum opposite edge; datum surfaces nominally contact the supplied rectangle. Mark an arrow toward +X and the text DATUM LEFT in a noncritical exterior region, avoiding bushing seats.

bushings.csv supplies synthetic replacement data for a would-be customer datasheet: 5.1 mm bore, 10.0 mm outer body, 12 mm body length, 14 mm flange diameter, and 2 mm flange thickness. Use 0.20 mm diametral body-seat clearance and 0.30 mm diametral flange-pocket clearance. Flange pockets are 2.0 mm deep from the jig top; the plate geometry must retain support under the flange while leaving the guide body unobstructed. The designer must expose any stackup issue rather than shortening the bushing silently. Retention relies on the flange and gravity for this digital concept; no press fit or certified retention is asserted.

## Workholding and capability
keepouts.csv defines clamp-pad rectangles occupying the entire Z region from the workpiece top through the clamp top. The jig may have cutouts around them; it cannot intersect their occupied volumes. Proposed jig material is printed PETG, but the workflow output is CAD/drawing data only. The operator has a small drill press and purchased guide bushings in a future physical trial. Actual bushing dimensions must be checked before manufacturing.

## Internal policy and acceptance
Never relocate a hole to simplify the model. Keep all coordinates in the workpiece frame and report any transform into the jig frame. Do not assert physical fit, tool guidance accuracy, clamp safety, or compliance with a standard. Preserve a STEP/STL jig, DXF hole layout, and dimension/clearance report. Initial automated checks verify artifact presence only; separate engineering and machining review is still required. No machine commands or production dispatch are authorized.
