# Validate image-space measurements

An engineer can supply photographs or other reference rasters with a reverse
engineering request. Reuse those inputs, calculate a comparison, and inspect its
measured residuals against the saved requirements. The comparison must identify
the exact reference image and coordinate convention; a small number measured in
another image is not evidence of agreement.

The shared structured reader supports `px` as an image-distance unit. It does
not convert pixels to millimetres or dimensionless values. Camera calibration,
scale, correspondences and occlusion remain responsibilities of the measurement
method and its inspectable evidence. This check verifies a recorded observation
against its bound frame and constraint; it does not independently reproduce a
projection or establish physical accuracy.

## Bind the evidence

A numeric `structured` check with unit `px` uses `within` or `range` and declares:

- `selector`: the measured number's JSON pointer.
- `parameters.unit_pointer`: the observed unit's JSON pointer.
- `parameters.image_frame_pointer`: the observed frame object's JSON pointer.
- `parameters.image_frame`: the expected `ImageCoordinateFrame` object.
- `frame`: the identifier returned by `ImageCoordinateFrame.identifier()`.
- `parameters.image_subject_role`: the role of the exact related raster subject.
- `parameters.related_roles`: a list containing that role.

The frame schema is `wright.image-coordinate-frame/1`. It contains
`image_sha256`, positive integer `width_px` and `height_px`, `axes`
(`x-right-y-down` or `x-right-y-up`), `origin` (`top-left` or `bottom-left`), and
`pixel_reference` (`centers` or `edges`). These values describe the measurement
convention explicitly. The frame identifier hashes the canonical typed object.
Do not derive an observed unit or frame by copying the expected profile value.

Bind the original raster as a related file subject using the existing subject
resolver. The reader verifies its digest, dimensions, single-frame content and
normal orientation within the inspection budget. Normalize an oriented or
multi-frame source explicitly upstream, retaining the original and the
transformation. A crop, resample or changed image creates a different frame and
requires fresh evidence; it does not silently change a saved tolerance.

## Ownership and failure behaviour

Existing Wright subjects, profiles, assessments, currentness checks, result
storage and configured validation tools own identity and evaluation. Existing
engineering tools own CAD and measurement production. This adds no executor,
vendor protocol, camera solver, review authority or UI. A normal workflow can
produce the measured report and bind its exact output to the validator. An
external inspection uses the existing explicit standalone-import contract;
invented producer identities cannot claim canonical gate authority.

Missing or incompatible frame evidence holds the check as inconclusive or
blocked with a finding. A measurable residual outside its frozen constraint is
a failure retaining the observed value. Changed related image bytes invalidate
the earlier assessment through existing currentness checks. A passing numeric
check does not grant human acceptance, production release or physical validation.

The structured reader's version is now `2`. Historical assessments and their
reader identities remain intact. New assessments record the new reader identity;
old unsupported pixel assessments must not be relabelled. Existing physical-unit
checks retain their semantics. Existing report views and the common working
view remain usable; no new interface dependency or editor change is required.

## Qualification scope

The Windows pilot uses the existing numerical projection controls with unchanged
constraints and a newly bound exact raster. Separate cases change image identity,
resolution, units, related-image availability and the measured number. These
are synthetic validation controls, not Roadster acceptance evidence. Tests also
cover currentness after image changes and forbid pixel/physical-unit conversion.

The materially different existing Robot Tracking workflow retains its motion
recording, ROS2 bag and metric-validation evidence. Its physical-unit validation
must continue to work with this reader revision; the retained prior proof alone
does not qualify a changed live runtime. Report that fresh regression separately
from the image controls and from a complete multi-tool engineering demonstration.
