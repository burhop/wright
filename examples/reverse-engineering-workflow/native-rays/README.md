# Native CAD visibility queries

Use this optional read-only diagnostic to identify which native CAD faces a
declared image ray intersects before assigning a photographed feature to a part.
A projected outline alone may overlap a hidden surface. The report preserves
all discrete intersections, nearest ties, misses, native face identities and
reprojections into other supplied views. It neither edits CAD nor certifies
physical feature ownership.

The existing Wright runtime owns execution, artifact handoffs, questions,
reviews and recovery. This example supplies a local measurement command, not
another executor or an installed MCP provider. Save its report as evidence for
the exact artifact, camera and queries. Changed source bytes, camera parameters,
query coordinates or numerical policies require new evidence. Portable workflows
must carry these inputs and declare the CAD reader dependency; they transfer no
credentials, live state or approval authority. The common result view remains
usable without a custom interface.

## Run

```text
python native_ray_support.py --input manifest.json --output new-evidence
python native_ray_support.py --self-test --output new-controls
```

The output directory must not exist; its parent must exist. Only `report.json`
is written. No installation, network access, external action, healing, export or
retry occurs. Missing dependencies and unsuccessful queries are explicit failures.
Exit zero means diagnostics completed or controls passed, not acceptance of a
model. Qualified locally with Python 3.13.5, CadQuery 2.8.0, OCP 7.9.3.1 and
NumPy 2.2.6. Use an isolated environment and preserve immutable source files.

```json
{
  "artifact": {"path": "candidate.step", "sha256": "REPLACE_WITH_EXACT_SHA256"},
  "camera": {
    "projection": "orthographic",
    "R_world_to_camera": [[1,0,0],[0,1,0],[0,0,1]],
    "t_world_to_camera_mm": [0,0,100],
    "fx": 1, "fy": 1, "cx_px": 50, "cy_px": 50,
    "width_px": 100, "height_px": 100, "near_mm": 1,
    "distortion": "none_assumed"
  },
  "queries": [{"id": "feature-point", "uv_px": [50,50]}],
  "ray_interval_mm": [1,200],
  "intersection_tolerance_mm": 1e-7,
  "tie_distance_mm": 1e-5,
  "comparison_cameras": {},
  "provenance": {"purpose": "Declared diagnostic, not a physical measurement"}
}
```

These example values describe a numerical query, not product dimensions or
engineering tolerances. Artifact paths resolve relative to the manifest.
Camera matrices must already be proper orthonormal rotations. Only orthographic
projection with explicitly assumed zero distortion is supported. The helper
does not fit a camera, silently approximate a perspective view, shift pixel
centers or align geometry. Optional camera `provenance` is retained. Comparison
cameras use the same schema, indexed by descriptive labels.

## Interpret

Face indices are zero-based in this exact native import, not persistent feature
names. Associate them with editable source through separately verified evidence.
The nearest set retains all hits within the supplied tie distance of the minimum;
it does not choose an arbitrary face at a seam. Reprojection into another camera
is not a visibility test in that camera. A restricted ray interval can omit a
closer surface. Finite points do not establish coverage of an entire feature.

Geometric opacity does not represent glass, reflections or photographic
occluders. Uncalibrated cameras and nominal scale remain hypotheses. Native
point intersections do not represent continuous ray/surface overlap; coincident
planar queries are conservatively rejected, and general curved overlaps remain
outside the contract. Resource counts and coordinate ranges are bounded, but
individual native kernel calls have no hard wall-clock cancellation here.

Nineteen analytic controls cover depth order, multiple layers, shared-edge ties,
misses, rotations, near/interval clipping, invalid cameras, provenance handling
and hash rejection. The same exact source recovered the existing pocket-defect
workflow's floor at Z=8 mm, shoulder at Z=10 mm and an outside miss. On the Roadster
comparison, 28 of 30 frozen queries identified upper hood support and two missed;
the previous fender-only projection was therefore insufficient for a lamp edit.
This is bounded diagnostic qualification, not a completed reconstruction loop.
See `provenance.json` for exact source and retained evidence identities.
