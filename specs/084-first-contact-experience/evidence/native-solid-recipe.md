# Native solid construction recipe, version 2

The handle starter now proposes four explicit tool roles: FreeCAD constructs the
solid, Blender repairs and previews its exported mesh, Orca compares printing
orientations, and OASiS performs inspection. This changes the proposed recipe;
earlier accepted sources and failed outputs remain unchanged. Original input
bytes, dimensions, engineering requirements and all 18 baseline checks remain
preserved. The derived printing profile still has 43 checks.

The visible design revision offsets the unchanged pads, preserves bolt centers,
uses circular roots that grow into the nominal oval grip, and specifies actual
native rounds. These are proposal choices to inspect at the declared design
review. Narrower legs do not establish strength, and the provisional washer
reserve does not establish fit with unknown existing hardware.

The [exact construction qualification](../../../artifacts/first-contact/084/provider-readiness/freecad-canonical-construction-001/README.md)
passed native BOP, continuity, intersection and mesh checks in 23.403 seconds.
The fresh exported mesh contains 76,742 triangles. Independent parsing confirms
its closed, wound topology and original envelope and clearance bounds. Independent
repair, full feature measurements, slicing and durable workflow reviews remain
pending. This standalone capability check is not an accepted engineering run.

Expected source mesh, native BREP and observations are published only after
construction checks. Publication is exclusive and atomic per file; a partial
three-file inventory requires reconciliation, never a blind replay. The normal
expected-file contract prevents an incomplete inventory from completing the step.

The setup uses the existing typed validation resource budget: 16 MiB per output,
250,000 entities, 120 seconds and 512 MiB. The default 100,000-entity reader budget
counts triangles and topology edges and therefore blocks this size of closed
mesh. A retained [reader preflight](../../../artifacts/first-contact/084/provider-readiness/native-stl-reader-preflight-005.json)
on the earlier labelled diagnostic demonstrates that failure and a passing
250,000-entity measurement (1.47 seconds, approximately 166 MiB process peak RSS).
The unchanged 80,000-triangle bound and all geometric predicates still apply.
This is explicit configuration of the new source, not a global reader-cap change;
actual full-packet worker qualification remains required.

## Nominal grip fidelity revision

The first exact repair operation failed before export. Read-only inspection of
its retained mesh found section thickness errors of 0.0013–0.01294 mm and a
maximum conservative complete-contour radial bound of 0.02742 mm. Its earlier
proposal checks demanded 0.00005 mm thickness and 0.002 mm contour fidelity,
although the original assignment specifies a nominal grip without those
micrometre tolerances. The failed operation and its values remain evidence.

Proposal revision 3 explicitly uses at most 0.03 mm absolute nominal-grip mesh
fidelity for thickness, height, center and complete-contour radial deviation.
It retains raw signed errors alongside the exact native conic observations.
This changes the authored proposal fidelity checks; it must not be described as
unchanged inspection tolerances or exact STL dimensions. It changes no original
dimension, hard minimum clearance, maximum envelope, bore clearance, round,
topology or capacity predicate. It is not a manufacturing tolerance or physical
fit claim. Existing accepted operation bytes stay unchanged; the new source and
recipe digest require their own qualification and reviews.

Root measurement revision 4 also retains the inscribed mesh endpoints by
expanding only the meridian's radial observation window to 2.48–5.57 mm, with
the same Z=5–8.05 mm span. Separate proposal conformity bounds allow 0.03 mm
endpoint coverage error and 0.02 mm above the nominal 3.05 mm radius. The original
minimum 3 mm predicate and its numeric epsilon remain unchanged. The exact
unchanged STL passes all 32 host-measured meridians: radius bounds
3.04510–3.05113 mm and endpoint coverage at most 0.02001 mm. Raw before/after
values are retained in [the host measurement evidence](../../../artifacts/first-contact/084/provider-readiness/root-mesh-fidelity-001/).
These finite sections and native torus evidence retain their distinct scopes;
they do not certify all local curvature or unsampled touched surfaces. Complete
native repair, reimport and preview qualification remains pending.

## Supplied intent at the basis review

The installed revision-6 walkthrough found that its basis review exposed the
model description and operation assets but omitted the supplied sketch. That
run remains at its basis wait. The handle preparer now attaches all six original
input files, the frozen mandatory requirements and any configured numeric basis
through existing review references. The original PNG retains its image type and
every input retains its exact bytes. Wheel authoring and review authority are
unchanged. Eight focused checks and independent review passed; a fresh accepted
revision and installed image/reference capture are still required.
