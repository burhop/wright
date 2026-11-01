# Two-view correspondence consistency

Use this optional measurement after the evidence survey has identified the same
visible features in two or more images. It helps expose weak correspondences
before fitting geometry. The engineer still starts with text/images/data; this
technical input is prepared from the inspected evidence, not a mandatory user form.

The utility fits a normalized fundamental matrix (F) and homography (H), retains
all common points and repeats each fit with one identity left out. F predicts an
epipolar line; H predicts a point. Their residuals have different meanings and
must not be ranked as interchangeable reconstruction scores. It performs no
triangulation, camera calibration, outlier deletion, CAD mutation or acceptance.

Run with a deliberately configured Python environment. Qualification used
Python3.13.5, NumPy2.2.6 and OpenCV4.12.0; another environment needs its own checks.
No network, credentials or provider connection is required.

```text
python audit_two_view_correspondences.py --input observations.json --expected-sha256 INPUT_SHA256 --output new-report-directory
python -m unittest test_two_view_correspondences.py
```

The input object has these fields:

- `schema`: `wright.two-view-correspondences/1`.
- `images`: objects with unique `id`, local `path`, exact `sha256`, `width_px`
  and `height_px`. Relative paths resolve against the input file's directory.
- `tracks`: objects with unique `id` and `observations`. Each observation has
  `image_id`, original-raster `uv_px` and positive `uncertainty_px`. An occluded
  observation may be absent or have null coordinates; do not invent it.
- `pairs`: image-ID pairs to compare. F requires eight common observations
  (nine for a leave-one-out fit); H requires four (five for leave-one-out).

The supplied uncertainty is an explicit isotropic weighting-scale hypothesis,
not automatically a measured standard deviation. Images must describe compatible
fixed geometry. Preserve movable-part masks, source dependence, feature identities
and any manual exclusions in the upstream evidence. This utility cannot decide
those semantics for the caller. It verifies hashes and raster dimensions but does
not locate or visually inspect the features.

The output directory must not exist. `report.json` retains input identity, source
image identities, runtime, numerical diagnostics, within-set and leave-out errors.
An integrity failure leaves an error report in the new directory. Exit0 means
report production, not a geometry pass. Degenerate or insufficient fits stay
unavailable. Inputs and existing output directories are preserved.

Bind exact input/report/image files through Wright's existing result and validation
mechanisms when adding this measurement to a workflow. This example is a local
measurement utility, not an installed MCP capability or a new process executor.
Changed images, crops, coordinates, visibility, object configuration or method
invalidate dependent results. A missing Python dependency makes this measurement
unavailable; it does not relax the workflow's required checks. Existing evidence
and the common working view remain usable. No process UI or UI contract changes.

The source is unchanged from an observed Astra/high authoring response. Five
synthetic test methods cover known cameras, planar/near-planar/nonplanar scenes,
unequal scales, wrong held-out points, insufficient data and integrity/preservation.
Real Roadster front/rear audits exposed weak or unstable support. A substantially
different existing pocket-correction artifact also passed a known-coordinate
control using16native STEP vertices and three camera pairs. Those synthetic images
include hidden vertices as X-ray fiducials; they do not qualify optical visibility,
feature detection, physical accuracy or a complete automatic reconstruction loop.
The separate joint camera/shape fitter remains pilot-specific and is not promoted
here. See `provenance.json` for exact source and evidence identities.
