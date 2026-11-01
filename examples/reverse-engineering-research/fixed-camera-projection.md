# Compare an exact CAD mesh in a photograph's coordinate frame

An engineer supplies text, images or existing evidence. Wright reuses that evidence,
researches remaining gaps and develops an editable CAD candidate. When a candidate
exists, this optional measurement utility projects its exact tessellation through
an explicitly supplied camera and overlays the silhouette on a reference raster.
It supports comparison work; it does not generate CAD or decide whether a result
is acceptable.

`project_mesh_to_photo.py` takes a mesh, camera, original image and new output
directory. The mesh includes its source STEP path/hash and tessellation settings.
An independent geometry reader must establish that the mesh actually represents
that STEP: matching the declared hash alone does not establish geometry provenance.
SteveCAD remains the native geometry producer. Existing Wright source runs,
artifact/results storage, validator and declared review mechanisms remain owners
of execution, evidence and acceptance. This local CLI is not a second workflow
executor or a new MCP provider.

```powershell
python project_mesh_to_photo.py --mesh mesh.json --camera camera.json --reference original.jpg --output new_projection
```

The mesh contains `units: "mm"`, `points`, triangle vertex indices, `tessellation`
and `source_artifact: {path, sha256}`. The camera requires all of these fields:

```json
{
  "projection": "perspective",
  "R_world_to_camera": [[1, 0, 0], [0, -1, 0], [0, 0, -1]],
  "t_world_to_camera_mm": [0, 0, 100],
  "fx": 600, "fy": 600,
  "cx_px": 127.5, "cy_px": 127.5,
  "width_px": 256, "height_px": 256,
  "near_mm": 1,
  "distortion": "none_assumed",
  "provenance": "Synthetic fixture camera; not a vehicle photo calibration"
}
```

This example camera belongs only to the retained pocket fixture. A vehicle photo
needs its own documented camera hypothesis. World-to-camera rotation must be
proper and orthonormal; camera axes are right/down/forward. Perspective focal
parameters are pixels; orthographic focal parameters are pixels/mm. The original
stored raster's top-left pixel center is `(0, 0)`. No resizing, cropping, EXIF
rotation, distortion correction, automatic framing or camera fitting occurs.

The utility saves a mask, camera-depth array, visibility shading, silhouette
overlay and exact-input report. The report carries the shared seven-field
`wright.image-coordinate-frame/1` identity. Bind that exact reference raster and
report through Wright's existing result/validation mechanisms when using them in
a process. Changed CAD, tessellation, camera or raster invalidates dependent
comparisons. Missing inputs or unsupported camera/near-plane conditions fail
explicitly; previous output directories are refused. An I/O failure may leave a
partial new directory: retain it and inspect its status rather than treating it
as a successful result.

No photo foreground is inferred and no similarity score or engineering tolerance
is introduced. Open surfaces render double-sided. A depth map can expose geometry
that an outline misses, but it does not measure hidden real-world geometry from
the photograph. Keep independent views and sections for verification. A valid
camera matrix alone does not establish calibration, scale or physical accuracy.

## Audit degenerate tessellation triangles before rendering

A valid native STEP can produce zero-area triangles during tessellation. Keep the
renderer rejection and original mesh evidence. `prepare_visualization_mesh.py`
creates a separate, auditable visualization derivative:

```powershell
python prepare_visualization_mesh.py --mesh mesh.json --output new_mesh_audit
```

It preserves all vertices and metadata and removes only triangles whose stored
binary64 coordinates have an exactly zero rational cross product. Floating-point
zero is only a candidate detector: disagreement with exact arithmetic fails.
There is no area tolerance, vertex welding, hole filling or CAD modification.
Inspect the report and derivative before passing `prepared-mesh.json` to the
renderer. Retain both mesh hashes, the STEP identity and this preparation report
with the projection evidence. A failed or partial output is not usable evidence.

Actual Astra/high authored this helper. Seventeen local controls passed, including
nonzero tiny areas, underflow disagreement, malformed inputs, integrity changes and
preservation of existing outputs. On the independently imported 57-face exterior,
eight of 10,683 triangles were proven exactly zero-area; 10,675 triangles and all
5,707 vertices remained. The existing pocket-defect workflow's corrected STEP mesh
required no removals and its derivative was semantically identical. These are
rendering-preparation checks, not continuity or physical-accuracy acceptance.
Windows tests use an explicit writable local temporary directory; the default
sandbox temporary location denied writes in the first attempt.

This CLI reuses the existing geometry/measurement evidence handoff. Wright's
runtime, results and validator retain their authority; no executor, provider,
review grant or process UI is added. Changed mesh preparation invalidates its
dependent comparisons. Missing or ambiguous inputs fail explicitly while the
original native model and common evidence view remain usable.

## Check protected native faces after a correction

`compare_native_faces.py` compares exact STEP snapshots using the installed
CadQuery/OpenCascade reader and complete native face serialization. It retains
geometry, trim topology, location and orientation, disables triangulation, fixes
the writer format to VERSION_1 and checks actual bytes after hash-based indexing.
Matching respects duplicate multiplicities and does not depend on face order.

```powershell
python compare_native_faces.py --before baseline.step --before-sha BASELINE_SHA --after candidate.step --after-sha CANDIDATE_SHA --output new_native_audit
```

The report records every face and pairing, exact input hashes, runtime and writer
settings. Exit 0 means every before face has a byte-identical counterpart; exit 1
means the audit completed with unmatched faces; exit 2 means an audit error. An
intentional correction normally leaves unmatched faces. Interpret matches against
the declared protected subjects and retain the unmatched evidence. A mismatch
means preservation is **not proven**, since equivalent geometry can have different
representations. This utility does not round, heal or normalize geometry to force
a match. Separate faces do not prove shared assembly topology or component ownership.

Nine controls passed, including a Bezier surface with changed interior poles and
identical boundary curves, duplicate multiplicity, reordered faces, changed location
and orientation, hash mismatch and output preservation. The Roadster comparison
found 50 complete face matches; two other faces whose sampled boundaries agreed
had different trimming representations and remain unproven. On the existing
pocket-depth correction, six faces matched and five on each side remained unmatched.
Neither result establishes whole-model preservation or physical fidelity.

This is another optional measurement artifact in the existing handoff, with no
new execution or review authority. Changed source artifact, reader or writer
configuration invalidates the comparison. The original native model and common
evidence view remain available when a preservation claim cannot be established.

## Bounded Windows qualification, 21 October 2026

Actual Astra/high requests authored the method and a narrow image-frame correction.
Source SHA256 is
`9717ce3453e88f816c2597f1576118486cebc998113b32fa9f6b137efaa2d6b9`.
Python3.13.5, NumPy2.2.6, OpenCV4.12.0.88 and Pillow12.3.0 ran the utility;
CadQuery2.8.0 supplied exact STEP tessellations and VTK9.6.2 supplied the independent
numerical camera reference. No package installation or shared service change was
needed.

Fourteen numerical/visibility controls pass: agreement with the existing VTK
reference under explicit half-pixel conversion, analytic perspective/orthographic
depth, occlusion/order/winding, viewport-spanning triangles, malformed inputs and
the exact retained STEP revisions. The known1.5mm pocket correction changes the
central depth by1.5mm with an identical silhouette. Five additional CLI checks
pass for the closed image-frame schema, exact input/output identities, refusing
overwrite, reference-size mismatch and changed source hash. Overlay and shading
were visually inspected. The metadata-only correction preserves the tested
numerical function ASTs. Ruff passes.

Private receipts are under the Windows pilot's
`state/research/20261020-roadster-goal/mesh-photo-projection-review-01/`,
`mesh-photo-projection-controls-01/` and `mesh-photo-projection-cli-controls-01/`.
These checks do not qualify a real-photo camera fit, a Roadster candidate, a full
automatic correction workflow or a process UI. The existing common working view
and evidence links remain the fallback; no UI code was changed.
