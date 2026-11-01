# Reverse engineering methods and qualification

For the 1 November reusable-source delivery, its tested scopes and historical
source identities, see [delivery qualification](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-workflow/delivery-qualification.md).
The inventory below includes research proposals; it does not assert installed
capabilities or a fully connected reconstruction workflow.

Research revision: 20 October 2026. This is a reusable method-selection and
qualification proposal, not a newly runnable workflow or a claim that the listed
providers have passed Wright qualification. The accompanying
[method inventory](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-research/methods.json)
retains applicability, evidence and qualification requirements for future authoring.
No runtime consumes that inventory yet.

### Camera uncertainty before shape correction

A low calibration residual does not establish a unique camera. Before changing
geometry to remove an image mismatch, retain several bounded camera hypotheses
that satisfy the original calibration observations and reading bands. Project the
same exact geometry into the same original raster under each hypothesis. Record
the prediction spread and whether candidate rankings change. Do not silently
adopt the camera that makes a preferred model look best, or call a finite profile
an exhaustive uncertainty bound.

The read-only helper
`examples/reverse-engineering-research/camera_hypothesis_stability.py` computes
finite prediction spreads with exact geometry hashes and Wright image-frame
identities. A single feasible hypothesis yields an unknown spread, not zero
uncertainty. Changed geometry or image frames are rejected. Calibration bands
remain explicit inputs; the helper grants no acceptance or execution authority.

The Windows Roadster diagnostic retained eight circle/ground camera hypotheses
within the original 3-pixel wheel bands, yet unchanged native geometry produced
upper-outline predictions differing by up to 73.11 pixels. These are conditional
witnesses under nominal circle/ground assumptions, not calibrated physical
cameras. A previously reported fixed-camera roof fit remains a conditional
measurement and cannot alone justify a physical height correction. The older
source explicitly intended a stowed airfoil; pose labels likewise do not prove
actual geometric fidelity. Private evidence: `camera-pitch-sensitivity-1932/`,
`camera-stability-1936/` and `rear-transition-diagnosis-1930/`.

A separate fixed-native-circle diagnostic avoids the earlier free-radius/ground
model: it reads actual B22 rim circles and fits only the original rim points.
Four fits satisfy the retained 3-pixel rim band, with two pose branches that
reverse the B20/B22 body ranking. B22 predictions span up to 66.82 pixels across
these finite witnesses; all fits hit the declared focal bound. This likewise
does not establish a physical camera. See `I15-native-rim-camera-1945/` and
`native-rim-camera-stability-1948/`. Use additional views or independent camera
evidence before treating one branch as geometry truth; do not keep refitting
circles alone or silently rewrite older camera-dependent results.

### Native support and mesh coordinate precision

When a valid native solid exports a mesh with tiny crossing triangles, locate
the exact offending faces before another global repair. Compare their vertices
with the exact parent CAD surface and the export encoding's quantization cells.
An explicit numerical derivative may recover points within those original cells,
while retaining connectivity and every unaffected coordinate. This is an export
precision repair; it introduces no physical tolerance and does not certify the
rest of the mesh-to-CAD distance or print process.

The retained older P5 Roadster body required nine local projections, each inside
its original float32 rounding cell, with maximum movement about 0.00000101 mm.
The independently reopened full-precision ASCII STL has one closed positive
volume, no boundary/nonmanifold/zero-area faces and zero selected intersections.
Its 321034 triangles and all connectivity remain unchanged. This qualifies a
bounded numerical recovery on that exact older derivative, not a print model of
the latest exterior. Private evidence: `P5-native-rounding-diagnosis-1934/`,
`P5-native-local-precision-STL-1939/` and
`P5-native-local-precision-STL-validation-1940/`. Printer/material suitability and
final master correspondence remain separate checks.

Downstream precision matters too: rounding those recovered coordinates back to
float32 reproduces the original source coordinates. A high-precision-only repair
therefore does not establish a robust float32 manufacturing handoff. The subsequent
bounded P5 trial changes one local diagonal across two triangles and moves no
vertices. Its changed four-vertex region has diameter 0.005940 mm, a conservative
two-sided bound relative to the previous mesh; all other triangles remain exact.
The ordinary binary STL round-trips the float32 coordinates exactly and passes
the full saved-output check with zero intersections. Evidence:
`P5-local-quad-retriangulation-1942/` and `P5-local-quad-validation-1943/`.
This is still the older P5 body, with no final master or printer qualification.

An engineer should be able to bring photographs, video, drawings, measurements
or a scan; state the intended use; and receive editable geometry with an honest
account of what is measured, inferred and unknown. Select methods for the evidence
and required accuracy. A reconstructed mesh is one possible intermediate output,
not a mandatory first step for every reverse-engineering job.

## Define the claim before selecting tools

| Intended result | Suitable evidence | Boundary |
| --- | --- | --- |
| Visual reconstruction | Original views, identified object/state, camera estimates and visible landmarks | Supports image-space resemblance; does not establish physical dimensions or hidden geometry. |
| External envelope | Calibrated silhouettes, reference dimensions, scans or section measurements | State covered directions/regions and uncertainty; hidden recesses need additional evidence. |
| Dimensional reconstruction | Traceable scale, datums, measurement uncertainty and sufficiently observed surfaces | Require an uncertainty budget compatible with the requested tolerance. |
| Functional replacement | Dimensional evidence plus mating interfaces, materials, loads and functional requirements | Appearance and CAD validity cannot establish fit, strength or service life. |

Keep reference fidelity, CAD topology/design intent, exact exchanged-artifact
integrity and manufacturing/physical suitability as separate outcomes. Do not
transfer a synthetic fixture's tolerance to an uncalibrated photographic job.
FEA or CFD can evaluate an inferred design under declared assumptions; neither
recovers missing original dimensions, materials or boundary conditions.

## Recommended sequence

1. **Prepare evidence and requirements.** Identify object revision, configuration
   and pose; required regions/features; units/datums; supplied dimensions and their
   provenance; uncertainty; intended use; and permitted assumptions. Record source
   rights separately from technical usefulness. A drawing or patent must be linked
   to the relevant object revision before it becomes dimensional evidence.
2. **Assess observability.** Build a coverage map and a list of unresolved claims.
   Resolve predictable missing inputs before execution or assign them to declared
   upstream producers/input steps. A single view does not uniquely determine a
   three-dimensional object. A model-generated hidden surface is an inference.
3. **Choose and qualify methods.** Use the table below. Require actual input/output
   round trips, correct units/coordinates, semantic error handling, host feasibility
   and capability/schema/version identities. A tool listing is insufficient.
4. **Establish a versioned evaluation basis.** Record reference assets, masks,
   cameras, preprocessing, scale, datums, coverage, regional metrics, tolerances,
   uncertainty treatment, correction bounds and reserved audit sources. Diagnose
   camera/reference ambiguity before using residuals to drive CAD corrections.
5. **Construct coarse editable geometry.** Establish proportions, datums and
   dominant sections before fine details. Maintain native parameters, feature
   ownership and protected regions. Use a generated mesh as a hypothesis where
   useful; converting every triangle into a BRep face does not recover design intent.
6. **Measure and diagnose.** Project the exact candidate into reference cameras;
   compare against independent metric surfaces when available; inspect regional
   features, sections and continuity. Separate geometry faults from camera,
   segmentation, reference-state and export faults.
7. **Correct within the accepted bounds.** Retain every attempt. Stop on acceptance,
   exhausted budget, non-improvement, conflicting requirements or inadequate
   evidence. Do not lower tolerances, shrink masks, change scale or refit cameras
   silently. A justified reference/calibration revision invalidates dependent
   comparisons and follows the existing accepted-source revision mechanisms.
8. **Revalidate and report.** Evaluate the exact native revision and actual exchange
   file, including tessellation error. Run the reserved audit once the candidate is
   fixed. Record pass/fail/indeterminate/not-evaluated per requirement, coverage and
   remaining unknowns. Keep human acceptance and physical qualification separate.

Use fitting data, development validation data and a final audit group with explicit
roles. If an audit result guides another correction, it is development evidence
for that revision; reserve new independent audit evidence or disclose the loss of
independence. Split by capture session/source and object state, not merely by frame
number. Adjacent frames and syndicated image copies share errors. Two algorithms
fed the same images are useful cross-checks, not independent measurements.

Audit camera parameters must be established independently of the candidate under
test. Fitting an audit camera to that candidate can hide shape errors even when
the photograph was withheld. Where independent calibration is unavailable, label
the result a constrained image-fit diagnostic and report the ambiguity.

Budget scale-anchor, calibration, pixel localization, mask, object motion,
registration, reference-measurement, CAD representation and export uncertainty.
Preserve correlations and systematic bias; do not automatically combine all terms
as independent noise. A conformity decision rule belongs to the accepted
requirement profile. This guide supplies no universal accuracy or numeric threshold.

## Organize evidence by component and observable feature

Keep an assembly/component/feature hierarchy with stable IDs and parent
relationships. Index each original photo or video frame against all components it
shows instead of copying it into one folder per part. Preserve assembly-level views
to establish component position and overall proportions. A crop is a derived asset
with its original-image transform; it is not another independent observation.

Each observation records source asset/hash, source-group lineage, image coordinates
or video timestamp/frame, camera and preprocessing revision, object/configuration
state, visible component/feature IDs, viewing direction, occlusion, reflection or
blur concerns, and evidence-use role. Automatic segmentation/tracking can propose
annotations, but review feature identity and masks before accepting measurements.
Part boundaries inferred from color, shadow or reflection are not automatically
physical seams. Left/right symmetry and assembly interfaces need explicit evidence.

Build a component-by-evidence matrix showing useful viewing directions, measurable
landmarks, supported depth/sections, metric anchors, conflicting states and missing
coverage. Count independent useful views, not downloaded files. Choose the next
reference by which uncertainty it can resolve: an oblique view across a recess
often adds more information than another frontal image. A component can have many
images and still lack any observation of its underside or true depth.

For video, preserve source identity, exact timebase, frame index/presentation time,
dimensions, shot segment, crop and object state. Select sharp frames with useful
parallax; do not infer independent evidence from hundreds of adjacent frames. Mark
camera cuts, zoom, rolling-shutter concerns and moving components. Link statements
about dimensions to an exact audible passage or authenticated transcript and its
scope. Metadata/transcripts alone do not prove a feature is visible; a sparse frame
sample does not establish every intermediate event or mechanism motion.

## Write specifications that expose calculation and uncertainty

Use a requirement/measurement ledger. Every entry identifies its component or
feature, property, unit, datum/frame, object state, target or permitted interval,
acceptance tolerance, uncertainty, evidence class, source/observation IDs,
verification method and exact output subject. Keep a design requirement separate
from a measurement estimate: an estimated width does not become an authoritative
width requirement simply because it was placed in a spreadsheet.

Distinguish directly measured, calculated from observations, inferred from a prior,
explicitly assumed and unknown. For calculated values, retain input IDs, formula
or algorithm/version, units, transformation, residuals and uncertainty propagation.
Unknown numeric values remain null; never use zero as a missing-value placeholder.
The [annotation example](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-research/evidence-contract.example.json)
illustrates the proposed data, not a new accepted runtime schema.

Prefer identifiable calculations over visual estimates:

- Use calibrated multi-view correspondences to triangulate visible points. Check
  parallax, reprojection error and sensitivity. A single image plus an unknown
  camera cannot supply arbitrary metric depths.
- Fit planes, lines, circles, cylinders, cones or supported revolved profiles to
  measured points when the feature's geometric type is justified. Retain residuals
  and compare plausible alternatives; a convenient primitive is not proof of the
  original design intent.
- Recover cross-sections and fit constrained curves/surfaces with the fewest
  parameters that explain the evidence. Test parameter sensitivity and degeneracy;
  if multiple shapes fit equally well, retain a family or interval of possibilities.
- Use dimensioned drawings or instrument measurements for scale and interfaces.
  Raster drawings require known scale and orthographic provenance. A scale bar in
  one plane does not calibrate every depth plane of a perspective image.
- Check dimensional closure and independent relationships: a width derived from
  component offsets should agree with an independent overall-width measurement
  within their uncertainties. Detect contradictions instead of averaging them away.
- A verified tire designation permits calculation of a nominal unloaded diameter
  from rim diameter plus twice nominal section height. It does not establish actual
  loaded radius, tire deformation or the dimensions of a different demonstrator.

Prioritize physical interfaces for functional replacement: hole patterns, mating
surfaces, axes, clearances and assembly pose. Keep cosmetic fidelity and functional
requirements separate. Do not invent wall thickness, thread form, material or hidden
fasteners from exterior photographs. A useful result can explicitly identify the
next measurement needed to resolve a critical unknown.

## Method selection

| Method | Useful contribution | Main limitation and qualification requirement |
| --- | --- | --- |
| Camera-matched CAD projection | Compare visible outline, feature placement and proportions directly with photographs. | Qualify camera convention, distortion, crop, scale, occlusion and render-to-artifact identity. Camera-fit error is not geometry accuracy. |
| Silhouette visual hull | Estimate an external envelope without matching paint texture. | Needs consistent calibrated masks; sparse views give a loose bound. Cavities invisible in silhouettes remain unknown. |
| SfM and multi-view stereo | Recover cameras and observed points/surfaces from overlapping views. | Reflective, transparent and textureless surfaces are difficult. Separate moving configurations and recover metric scale independently. |
| Learned multi-view geometry | Initialize camera/depth/point hypotheses when classical matching struggles. | Learned confidence is not calibrated metric uncertainty. Validate against independent observations; qualify model weights and host support. |
| NeRF or Gaussian splatting | Inspect view consistency and synthesize viewpoints from a capture set. | Rendering quality does not certify recovered surface geometry. Qualify extraction separately before using a mesh for measurement. |
| Generative image-to-3D | Suggest coarse shape or alternative interpretations from limited imagery. | Label as inferred; it cannot independently validate CAD based on the same assumptions. Never use invented views as new observations. |
| Bidirectional surface distance | Quantify differences between an independently supported reference and candidate. | Fixed datum alignment, area-aware sampling, regional reporting and coverage are essential. Global averages can hide small defects. |
| Sections and surface analysis | Detect wrong profiles, missing recesses, lumps, discontinuities and invalid feature transitions. | Smoothness alone does not establish fidelity. Distinguish intended sharp edges from surfaces required to be tangent/curvature continuous. |
| Bounded inverse rendering | Propose parameter corrections using projected residuals. | Optimize only allowed parameters on development data; do not let texture, camera changes or arbitrary warping conceal geometry errors. |
| Independent dimensional capture | Add contact measurements, calibrated scans or structured-light observations for metric claims. | Requires physical access, calibrated instruments and declared capture authority. No physical capture is part of this research change. |

### Projecting exact CAD into photographs

[OpenCV](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html) provides camera
calibration, pose estimation and point projection. [fSpy](https://fspy.io/) provides
still-image camera matching and an official Blender importer. Its vanishing-point
approach needs usable geometric cues; curved objects alone may not provide them.
Blender is already represented in Wright's
[SteveCAD native render example](https://github.com/burhop/wright/blob/dev/examples/stevecad-demonstrations/prompt-to-reviewed-cad/README.md).
Reuse that exact-artifact handoff and an independently qualified provider, with
camera/mask measurement added through the shared inspection/validation owners.
Historical rendering evidence does not qualify a new local binding automatically.

The proposed measurement chain is exact CAD revision -> bounded tessellation ->
camera-matched visible render -> image-space measurements -> existing validation
report. Record both native/export hashes and tessellation parameters. Correct for
lens distortion either in the source image or in the projection, with the same
coordinate convention. Keep the original bytes and preprocessing transform.
Perspective photos require perspective comparison; use orthographic projection
for an actual orthographic drawing. A flat homography cannot rectify an entire
non-planar object. A wheel ellipse alone is not a calibrated size reference.

Use whole-object and semantic-region masks, visible landmarks and actual geometric
edges. Exclude occluders, cast shadows and reflected patterns from geometry scoring.
Report silhouette intersection-over-union, symmetric contour distances and landmark
residuals per view/region. Retain overlays and residual maps as inspectable evidence.
Image-space measures use pixels or a declared normalized image/object extent; they
do not become millimetres merely because the CAD document has millimetre units.
If camera/mask uncertainty is comparable to a defect, return an indeterminate
finding or an uncertainty interval rather than an unsupported binary verdict.

Do not accept on RGB similarity or attractive shading alone. Silhouette checks
can miss a shallow pocket, rear recess or incorrect interior surface. Add local
edge/feature checks, independent depth or sectional measurements where those
features matter. Background-free depth/normal/part-ID renders can aid diagnosis,
but predicted depth remains a model output unless independently verified.

### Reconstructing an envelope or reference surface

The [visual-hull reference](https://graphics.stanford.edu/~mapauly/Pdfs/SigCourse04.pdf)
explains silhouette-derived bounds and their concavity limitation. Treat an
uncertainty-expanded hull as an envelope estimate; do not call its filled volume
observed surface. Preserve camera/mask uncertainty and view coverage.

[COLMAP's capture guidance](https://colmap.github.io/tutorial.html) calls for
overlapping, varied views and cautions against specular and textureless imagery.
A walkaround with useful parallax can contribute more than many duplicate stills.
Partition sequences at shot cuts, zoom/lens changes, object motion or configuration
changes. A camera rotating in place supplies limited triangulation baseline.
Video compression, rolling shutter and moving reflections require screening.
Unobserved holes filled during meshing remain inferred, even if the result is watertight.

[VGGT](https://github.com/facebookresearch/vggt) offers learned geometry hypotheses.
[Nerfstudio](https://docs.nerf.studio/quickstart/export_geometry.html) documents
method-specific geometry export. Both are research candidates for this workflow,
with local execution, metric reliability and extraction still to qualify.
[TRELLIS.2](https://github.com/microsoft/TRELLIS.2) is a generative candidate whose
documented setup is tested on Linux with at least 24 GB NVIDIA GPU memory. It is
not a prerequisite for the Windows-local pilot and creates no GB10 dependency.

### Measuring geometry beyond the outline

[CloudCompare](https://www.cloudcompare.org/doc/wiki/index.php/Cloud-to-Mesh_Distance)
documents point-to-mesh distance and the risk of undersampling compared meshes.
Measure both directions over explicitly covered regions. Use reproducible
area-weighted samples, regional RMS/P95 and sampled maxima, and verify sampling
stability at finer density. A sampled maximum is not an exact Hausdorff bound.
Unsigned distances are the baseline; signed distances need qualified closed,
oriented geometry. Do not silently use best-fit scaling or unconstrained ICP to
hide dimensional error. Report any optional best-fit diagnostic separately from
the fixed-datum acceptance result.

Retain independent feature dimensions and sections alongside surface statistics.
[Rhino's zebra analysis](https://docs.mcneel.com/rhino/8/help/en-us/commands/zebra.htm)
illustrates continuity inspection; equivalent qualified CAD analysis may be used.
Require numeric continuity checks where the requirement is numeric. Do not smooth
intentional corners. Protect interfaces and feature ownership during correction.

[PyTorch3D's inverse-rendering example](https://pytorch3d.org/tutorials/fit_textured_mesh)
shows fitting geometry against rendered views. It is a candidate proposal mechanism,
not an acceptance authority. Start with a few identifiable native parameters and
check parameter sensitivity; if several shapes explain the evidence equally well,
retain the ambiguity instead of implying a unique reconstruction.

[OpenCV structured light](https://docs.opencv.org/4.x/d1/d90/group__structured__light.html)
is a future capture option when physical access exists. Prioritize traceable direct
measurements of functional interfaces when a replacement part must fit. Improved
lighting, polarization or surface preparation are acquisition proposals requiring
appropriate object access; they cannot repair already missing photographic evidence.

### Numerical construction checks before changing the design

Keep intended geometry separate from numerical construction errors. A native
build can reject a surface because its boundary curves fail to meet, even when
the supplied endpoint coordinates agree. Inspect the failing feature's report
before changing dimensions, adding thickness or declaring a missing capability.
Isolate exact feature subsets while preserving the complete candidate and its
source; a generic outer build error may hide a more useful feature error.

In the Windows pilot, an almost straight curve produced a tiny nonzero cross
product. Normalizing it as a plane normal created an unstable coordinate frame
and displaced the intended endpoints. The retained original expressions and
native feature diagnostics identified this as a generated-source calculation
error, not a reason to replace the CAD provider.

For curve-plane construction, record the numerical collinearity policy separately
from engineering tolerances. A perpendicular-distance test with explicit absolute
and scale-relative bounds is more useful than exact equality to zero. Construct
an orthonormal frame, preserve endpoint coordinates and retain quadratic overshoot
when a control point lies beyond the endpoint chord. A straight segment can match
a collinear curve's geometric locus without preserving its parameter speed; check
whether downstream parameterization matters before making that substitution.

Meaningful controls include near-collinear and clearly curved poles, reversed and
mirrored inputs, outside-chord controls, different coordinate scales, zero-length
chords and the actual failing source curves. Then rebuild with the native producer,
export the exact revision and independently inspect it. Local arithmetic tests
alone cannot establish native surface validity, continuity or vehicle fidelity.

Interpolation through correct landmarks can still create the wrong shape between
them. Check derivative roots and coordinate extrema over each complete curve
interval, especially when point spacing is uneven. Preserve intended extrema and
corners; a smooth-looking interpolant can introduce extra lobes or move a measured
peak. Compare the actual native exported curve with the source calculation before
attributing a visible discrepancy to the interpolator. Keep landmark-relative
overshoot separate from measured photo-contour error and physical dimensions.

Audit the actual call order before applying a reusable curve correction. Reversing
an even-length point list can change grouped interpolation triples and the terminal
straight edge. Support the caller's boundary orientation and retain its exact
endpoint identities; sorting points silently can break a closed fill wire. A
source proposal that fails this contract must be corrected before a native update.
The pilot's forward-arch overshoot was independently confirmed in exported native
quadratic poles; its first increasing-x-only proposal was held before application
because the real builder supplied decreasing-x points. This finding does not yet
qualify a replacement curve or establish a physical vehicle error.

The 21 October pilot retained an Astra/high correction with 62 curve controls and
two degenerate-chord controls, followed by an actual transition build changing
seven failed boundary features to zero and an independently valid ten-face STEP.
Its numerical constants were scoped to that saved CAD revision; they are not
universal reconstruction tolerances or new workflow defaults. Detailed private
receipts are in `rail-plane-correction-01/` under the pilot goal evidence. The
[SteveCAD usage guide](../mcp-catalog/usage-guides/stevecad-mcp.md) records provider
contracts and separates surface capability from this source failure. Execution,
result identity, invalidation and review still use the existing Wright owners.

## Shared ownership and recorded evidence

Reuse accepted workflow source and versioned instructions for method choice and
correction policy; the existing compiler/runtime for execution; gateway/registry
for independent providers; existing artifact storage/handoffs for hashes and host
boundaries; EngineeringResult/provenance and validator/rework for findings; and
durable input/review checkpoints for declared interactions. No new executor or
vendor protocol is proposed. Method identifiers in the research inventory are
descriptive IDs, not installed capability names or executable configuration.

Each eventual measurement result needs exact subject revision and artifact hash,
reference lineage/capture group, object state, units/frame, preprocessing/camera/
mask versions, scale evidence, method/tool/schema/model identities, sampling basis,
coverage, uncertainty, metric/tolerance, finding and linked raw evidence. Reuse
current result owners; assess missing fields before proposing contract extensions.
An evidence file's existence or a provider's outer success flag is not acceptance.

Reference, camera, mask, scale, requirements, native geometry, tessellation or
measurement-method changes invalidate their dependent results. Routing/instruction
changes follow existing frozen-continuation checks. Reconcile uncertain mutations
before continuing; research candidates do not grant retries or model fallback.
Reference rights and availability travel with portable dependencies; credentials,
live runs, approvals and trusted UI builds do not.

Use the existing common working view and linked evidence. A future overlay viewer
can present images/masks/metrics for exact subjects, but owns no execution or status.
Saved interface compatibility and common-view fallback remain unchanged. This
research adds no editor changes or Codex UI work.

## Qualification order and negative controls

First qualify camera-matched projection, feature/section measurement and regional
surface comparison. Add a visual hull where calibrated silhouettes justify it.
Make dense reconstruction, learned geometry and inverse rendering optional until
their local providers and accuracy are demonstrated.

Required controls include an incorrect camera/crop, wrong scale or units, mirrored
frame, a plausible but blocky shape, a missing small recess, a correct outline with
wrong depth, an occluder included in a mask, sparse comparison samples, inconsistent
object states, correlated audit images and a changed final export. Correct geometry
must not be distorted to compensate for a wrong camera. Known synthetic fixtures
test algorithm sensitivity; they do not certify real-photo metric accuracy.

After fixture qualification, use fresh isolated copies of existing examples:

- **Prompt to reviewed CAD:** use the existing bracket/block and actual SteveCAD
  export -> native rendering -> independent measurement handoff. Preserve its
  geometric requirements and distinguish rendered controls from real photographs.
- **Sheet-Metal Supplier Handoff:** test orthographic contour/hole/section comparison
  against its drawing/developed-output basis, preserving all original tolerances,
  provider ownership and review requirements; stop before external submission.
- **Robot Tracking Diagnosis:** test that generic evidence, declared input and
  durable report mechanisms work without reconstruction, cameras or manufacturing.
  This is a shared-mechanism test, not evidence that geometric methods apply to
  time-series diagnosis.

These are proposed qualification cases, not executed runs. Existing campaign
subjects, historical evidence and original examples remain intact.

### Validate native curve extrema after interpolation changes

Preserving sampled picks does not preserve the shape between them. After a
bounded interpolation correction, identify the exported curves by unique endpoint
pairs in their actual source order. Read the native curve degree, poles, knots,
weights and trimmed parameter domain. For a qualified polynomial segment, compute
coordinate extrema from derivative roots over the entire actual domain; compare
those extrema with the declared endpoint intervals. Check adjacent endpoint joins
and mirrored curves independently. A handful of samples can miss overshoot.
Unsupported curves, ambiguous matches or mismatched parameter domains remain
unqualified; do not silently approximate them and call the check exact.

The Windows pilot applied this method to a front wheel-opening correction. Twelve
native quadratic segments preserved the original picks and eliminated a measured
7.364247mm peak overshoot in nominal model coordinates. The complete exact STEP
had58valid faces. This is a construction check, not physical vehicle accuracy or
a photo-fit score. The private inspector currently specializes in this candidate's
six segments per side and58faces; generalizing that implementation requires typed
expected geometry and separate qualification, not hiding these assumptions.

Revalidate protected native surfaces too. In the same correction,54complete faces
matched exactly while two unintended rear-quarter representations differed despite
unchanged source. Keep those differences visible. Feature status, source equality,
matching bounds and visual similarity cannot substitute for exact-output evidence.
The existing result/validator and durable run remain the evidence owners; this
method introduces no executor, UI authority, release grant or relaxed tolerance.

### Audit feature identity before fitting a camera

Before using image points as camera controls, identify the same physical feature
in each view. A silhouette tangency, reflection, apparent width extremum or shadow
is not generally a fixed 3D point. Even a recognizable corner can refer to a
different longitudinal station in another view. Record component, feature,
original raster coordinates, visibility, uncertainty and the proposed native
anchor separately. Leave occluded or unresolved coordinates absent. Check frame
signs and object configuration before assuming mirrored correspondence.

Reuse existing component photographs first. An oblique or elevated view can resolve
a junction that remains ambiguous in a nominal front view. Record common capture
and promotional-source groups; additional views are not automatically independent
validation evidence. Read available camera metadata without changing pixels;
missing EXIF does not establish that an image is synthetic. Keep held-out views
out of fitting and preserve the original evidence manifest when adding references.

A camera fit against image-derived CAD is conditional on that CAD hypothesis,
not an independent calibration. Freeze geometry while comparing explicit camera
hypotheses; expose focal-length, depth, principal-point and shape ambiguity. A
small reprojection residual cannot establish hidden depth or physical dimensions.
Numerical search bounds and estimated pixel uncertainty must be versioned analysis
assumptions, not invented engineering tolerances. When correspondence identity is
unresolved, report that limit instead of widening a fit until it looks convincing.

The Windows pilot's actual Astra/high camera audit rejected several silhouette and
station mismatches before geometry fitting and selected two additional existing
front views for inspection. This qualifies an evidence-review finding, not a
camera solver or physical calibration. Analysis instructions and routing use the
existing versioned instruction and invocation owners. New references, identities,
cameras or geometry invalidate dependent fits and comparisons; the common evidence
view and original model remain usable when a fit cannot be justified.

Pairwise checks can expose inconsistent or weak correspondences before metric
reconstruction. A fundamental matrix predicts an epipolar line; a homography
predicts a point under a different geometric model. Keep their directional pixel
residuals separate rather than ranking their raw objectives. Refit after removing
each checked identity to expose dependence on individual picks. Insufficient or
degenerate point sets remain unavailable; never restore excluded observations to
meet a minimum count. See the [OpenCV epipolar geometry reference](https://docs.opencv.org/4.13.0/da/de9/tutorial_py_epipolar_geometry.html).

The pilot-local Astra/high helper now has five passing synthetic test methods,
including independently constructed cameras, planar and nonplanar cases, unequal
uncertainty/image scales, wrong held-out points and identity/preservation checks.
Its first Roadster calculation found an unstable front/elevated pair and a more
consistent overhead/elevated pair. These are internal consistency findings on
correlated references, not calibrated reconstruction. A subsequent compatibility
control used the retained pocket-correction workflow's exact revision2 STEP:
16 native vertices, one independently valid solid and three known-camera pairs.
Leave-out epipolar residuals stayed below the prospective1e-6px numerical bound.
Those images are synthetic X-ray fiducials, including hidden vertices; they do
not test optical visibility or photo-feature detection. The first camera setup
failed its raster-bounds check and remains preserved. A fresh explicitly aimed
camera setup passed without changing the STEP or comparison bound. This is a
different-example artifact compatibility check, not a new end-to-end process run.
The unchanged helper is available as the optional
[two-view consistency example](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-workflow/two-view-consistency/README.md).
No shared runtime, process UI or acceptance authority changed.

### Separate observable shape defects from ambiguous dimensions

A bounded joint camera/visible-point fit must preserve all starts, failed
initializations, stopped optimizations, numerical bounds and original exclusions.
Record world-to-camera conventions, similarity gauge, positive-depth checks,
per-view residuals and focal assumptions. Compare candidate shapes using
similarity-invariant ratios, not raw coordinates from different gauges. A solver
that exhausts its evaluation budget has not converged. Low residuals, one apparent
solution or a numerical Jacobian rank do not establish physical accuracy.

The pilot's four-view front analysis illustrates the distinction. Seven offline
control tests passed, but none of32 real-image starts converged within the fixed
bound. Four failed initialization and28 retained positive depths. Some residuals
were below one pixel while inferred junction-separation ratios varied greatly.
No fitted coordinates were transferred into CAD. Separately, the photographs show
distinct noncollinear hood/windshield and outer-pillar junctions that the current
native boundary places on one straight line. That observable construction defect
can motivate a bounded, explicitly provisional visible-surface candidate without
pretending the camera fit resolved its metric dimensions. Any such candidate
still requires exact native build/export checks and multiview comparison.

Rear details also need spatially distributed correspondences. Several nearly
collinear frame junctions plus accessory plate corners provide weak support for
surface reconstruction. Keep movable panels out of fixed-body fitting, distinguish
light bloom from lens boundaries, and leave unobserved opening depths unresolved.
Changing point identity, configuration, camera assumptions or geometry invalidates
the dependent fit; retain its evidence rather than rewriting it. These are reusable
analysis rules on the existing instruction, result and validation mechanisms,
not a separate executor or an automatic acceptance policy.

### Diagnose surface preservation and construction seams separately

When an unchanged feature produces a different complete native face serialization,
separate the underlying surface from its trims, topology and placement. For a
B-spline, compare the located degrees, poles, weights, knots, multiplicities and
rational/periodic flags without rounding or changing basis. Identical underlying
data does not establish identical trimmed faces. Retain the complete-face audit;
finite bidirectional distances from accepted interior and edge samples are a
diagnostic, not a continuous Hausdorff bound or a replacement acceptance tolerance.

Along a known shared boundary, report point-to-trimmed-face distances together
with both oriented normal angles and orientation-independent plane angles.
Normal projection onto an underlying surface can leave the intended trim, so
normal angles alone are insufficient. Distinguish artificial subdivisions inside
one intended smooth component from observed creases and joins between components.
Do not demand tangency at every junction or infer curvature continuity from it.

The Windows revision8 investigation found identical underlying B-spline data for
all seven discrepant protected face pairs, while trim equivalence remained open.
Its largest finite sampled distance was about0.000146mm in provisional model
units. Five samples on each artificial internal windshield seam exposed roughly
8degree normal discontinuities despite coincident boundaries. This identifies a
local refinement target; it establishes neither physical accuracy nor complete
surface continuity. Ten diagnostic controls passed. The local helper still
contains Roadster-specific reporting assumptions and has not been qualified as a
general CLI; its measurements add evidence without changing shared validation
authority. No new engineering tolerance or automatic acceptance was introduced.

Keep tool capability limits explicit when choosing a correction method. SteveCAD
documents tangent fills but excludes G2 continuity between faces and Class-A
surfacing from its modeling capabilities. A successful local tangent correction
would therefore require its own exact-output checks and could not establish
Class-A quality. See the [surface capability documentation](https://stevecad.studio/docs/design/surface/)
and [fill feature contract](https://stevecad.studio/docs/design/features/#surface).

### Compare native sections before accepting surface refinement

Use declared longitudinal and transverse planes to inspect an exact export,
especially when replacing several patches with one surface. Freeze the source
hashes, plane definitions and selected native faces. Preserve the native derived
section edges separately from sampled plot polylines; mesh-plane intersections
are useful displays but are a different evidence type. Empty intersections and
computation failures must remain explicit. Plane locations are diagnostic choices,
not new physical measurements or automatically justified dimensions.

The [native section example](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-workflow/native-sections/README.md)
implements this read-only diagnostic on the existing local reader. A Windows
windshield trial built as a valid single face but produced large longitudinal
waves and transverse sag; its five fixed profile-anchor residuals ranged from
about0.085to0.291mm. The trial was retained and rejected rather than replacing the
existing model. The same code recovered the retained pocket fixture's native
center-section floor atZ8mm,12mmwide and2mmdeep, with exterior and empty-plane
controls. Analytic box/open-face and file-identity controls also pass. These are
measurement and different-workflow artifact compatibility results, not a complete
automatic process or physical fidelity qualification. Input changes invalidate
dependent section evidence; shared execution, results and review authority remain
with Wright's existing backend.

### Verify supplied guides against the produced surface

Supplying a complete curve network does not establish exact interpolation. Keep
source-curve identity, provider fitting diagnostics, exported trimmed geometry,
and underlying surface consistency as separate checks. Compare interior guide
samples as well as outline samples. A point-to-trimmed-shape distance can terminate
on a boundary edge; a small value alone cannot certify that the edge's 3D curve,
surface parameter curve and underlying surface agree. Finite samples can disprove
a bound but cannot certify its continuous maximum.

The isolated Windows guided-windshield trial preserved the original source
outline and profile network and avoided the preceding fill's large waves in the
inspected native sections. It nevertheless missed interior guide samples by up
to2.464086mm in provisional model units, while the provider reported a different
G0 fitting diagnostic of0.258189mm. It remains separate from the Roadster because
the fixed numerical identity requirement did not pass. No tolerance was relaxed.
This is a reusable evaluation rule for guided surface reconstruction, not a
claim that every provider's guide algorithm or every candidate behaves this way.

### Visible boundaries without invented hidden depth

When an image establishes a visible panel or lamp-surround outline but not its
depth, a bounded candidate can partition an existing provisional exterior surface
using the image mask and an explicit frozen projection. Preserve the underlying
envelope, original observations and mapping uncertainty. Keep such a patch labeled
as an on-surface hypothesis; it is not a cavity, emitter, wall thickness or verified
physical part. Distinguish numerical cutter volumes from exported vehicle geometry.
Check occlusion and multiple intersections along projection rays rather than
assigning every intercepted surface to the visible feature.

The implementation must account for the remainder as well as the mask patches:
check source coverage, overlapping or duplicate faces, validity, exported solids
and area residuals. Preserve measured residuals on failure, including their source
face and numerical error budget. Passing planar controls does not qualify curved
surfaces. A pilot partition helper passed six planar/invalid-input controls but
failed its area check on the actual curved STEP: the first source face's residual
was about-0.003432mm2 against a computational budget of0.00006509mm2. Adaptive
integration to a requested relative precision of1e-12 retained a residual near
-0.003492mm2. This did not justify weakening the guard or attributing the entire
discrepancy to default integration precision. The method remains a candidate;
no complete native partition or general workflow qualification follows from
those controls. Shared execution, validation and review remain with existing owners.

A subsequent common-split diagnostic passed the contained-triangle, adjacent-face
and overlapping-mask controls, but did not repair that curved-face discrepancy.
Retaining observations for all17 selected front faces exposed invalid fragments
from both fender faces and a total area residual of about-273.694mm2. Both the
separate operations and one common split produced this result. The original
geometry and budgets stayed unchanged; the failed method was not promoted.

Retain diagnostic fragments even when a numerical check fails, with explicit
failed/unclassified status and exact source identities. They can reveal a second,
independent modeling problem: the retained overhead lamp mask also intercepted a
lower front skin, producing an extra lower patch in the front-view projection.
An overhead silhouette match therefore did not establish visible-feature ownership.
Before applying such a partition, identify the intended support faces and resolve
visibility along the projection rays. Keep incomplete classified groups distinct
from a complete feature. Reimport and compare the exact diagnostic exports too;
the pilot observed changed area values after STEP exchange, so in-memory checks
alone would not qualify the exchanged fragments. These findings extend the method's
limits, not Wright's executor or acceptance authority.

### Replace an unstable fill with a bounded surface hypothesis

When a many-sided fill bulges between retained boundary curves or fails downstream
operations, investigate the source surface before trying equivalent cuts again.
If the boundary admits two nonintersecting monotone chains, one candidate is a
sequence of ruled strips. Preserve the original curves with exact polynomial
subdivision rather than sampling new stations and refitting them. Check continuous
curve bounds, complete interval coverage, cap degeneracy and chain separation.
Name the changed interior interpolation explicitly: retaining the outline does
not establish preservation or physical correctness of the interior surface.

Qualify the native result independently. Match the intended surface basis when
available, check trimmed geometry and compare the same native sections and camera
views. Measure seam normals: introducing more valid faces can introduce unwanted
creases. Component-only views do not resolve whole-assembly visibility. Preserve
both the original and new candidate and retain exact exported artifact identities.

In the Windows pilot, this construction produced22 valid open fender faces. All18
ruled faces matched the intended single-span tensor-product basis; sampled points
on all22 faces were within about2.1e-10mm of the intended provisional geometry.
The original fill's sampled section deviation from its endpoint chord reached
51.12mm; the trial's ruled sections reduced that construction deviation to numerical
roundoff. This is not51.12mm of measured vehicle error. Two front seam angles still
reached about29degrees, and physical shape fidelity remained unverified.

The same local partition and exact diagnostic STEP reimport checks then passed
with the original masks and numerical budgets. A separate88-face full-car export
retained all22 trial fender faces byte-for-byte. Of66 protected old faces,64 matched
complete BRep bytes; two rear-quarter faces had equal underlying spline data and
small sampled distances but different trim serialization and area observations.
Complete preservation of those two faces was left unproven. These are bounded
construction and inspection results, not a generic ruled-surface capability claim,
automatic process acceptance or a reason to alter prior verdicts.

A subsequent rear-quarter trial reused the same method with a different original
curve construction: its quadratic through-points use an X-derived parameter,
not an assumed midpoint. Preserve that parameter when reversing and subdividing
curves. The 20-face native trial preserved all 12 boundary curves per side and
matched all 16 intended ruled bases. Ten section planes fixed before authoring
showed the previous sampled chord deviation of 113.34 mm reduced to numerical
roundoff. The overhead outline improved visually, while sampled tail seam angles
reached 61.04 degrees. A straighter section is a construction hypothesis, not a
physical accuracy measurement or proof that every crease is appropriate.

The separate 106-face full-body export retained all 20 trial faces byte-for-byte.
Of 86 protected faces, 76 matched complete BRep bytes. The other ten had equal
underlying spline representations but different trimmed representations; the
largest bidirectional sampled distance was about 2.03e-5 mm. Retain that mismatch
and the original thresholds. Neither an equal underlying surface nor a visually
indistinguishable preview establishes complete trimmed-face preservation. Do not
rebuild repeatedly to seek matching serialization or classify the mismatch as
physical error without further evidence. Private pilot evidence is
`20261020-roadster-goal/roadster-rear-comparison-01-checkpoint.json`.

### Establish visible support before projecting a feature

A mask projected through an assembly can intersect several surfaces. A valid cut,
matching overhead outline, or named component does not establish that a fragment
belongs to the visible feature. Compare the fragment against the full candidate's
depth image with identical cameras, then inspect another view before editing.
Retain all competing layers and disclose tessellation, pixel-center sampling,
camera assumptions and depth comparison sensitivity. Raster visibility is a
diagnostic; near-coincident surfaces need stronger native geometry evidence.

The Windows pilot found that valid fender-only lamp-mask partitions were entirely
hidden by other body surfaces in the overhead projection. They covered only
568 of 899 and 675 of 998 mask pixel centers, and projected below the photographed
lamps in the front view. The edit was held. Selecting fewer components had removed
some unwanted intersections but had not identified the correct visible support.
The original masks, cameras, failed prior cuts and existing CAD were preserved.

For native ray inspection, record every intersection, its source face identity,
depth and boundary state. Preserve nearest-depth ties instead of selecting the
first face in traversal order. Reproject the retained points into other declared
views. Associate native faces with editable source features using corroborated
geometry and exact-output identity, not names or unverified export ordering.
Finite queries do not certify visibility over a whole region; treating every
surface as opaque does not model glazing, photographic occluders or an unknown
camera. This inspection informs a bounded next edit and grants no execution or
review authority.

The optional [native-ray diagnostic](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-workflow/native-rays/README.md)
implements these finite queries for explicitly supplied orthographic cameras.
Its exact promoted source passed 19 controls and recovered the existing pocket
fixture's floor, shoulder and outside miss. Thirty frozen Roadster queries
identified upper hood bands at 28 locations and missed at two mask vertices.
This narrowed the visible support but did not qualify an entire lamp region.
Historical Boolean failures on those same hood faces remain failures: a better
feature association does not repair the surface construction or justify relaxed
area budgets. Source identity, native query evidence and image interpretation
remain separate checks.

### Preserve boundaries when testing a simpler surface construction

When a complex fill resists a feature operation, retain its complete boundary
curves and test a simpler, explicitly declared interior in a separate candidate.
Matching boundary curves does not prove identical interiors or improved physical
accuracy. Compare full curve polynomials, native surface representation, trimmed
geometry, sections and fixed-camera views before integration. Keep original
measurement budgets and failed candidates; do not weaken a check to admit a cut.

The pilot's twelve-patch hood trial preserved all 48 boundary-curve records and
passed native ruled-basis and finite trim checks. The local mask partition then
passed the existing area guards. Sampled interior changes reached 8.40 mm, so the
result remains a different surface hypothesis. Native partition export is still
unqualified: an assembly audit error was corrected, after which a previously
working source face reference failed before the audit. Saved source identity
passed read-back. This distinguishes a local geometry result from a successful
native integration; neither proves visual or dimensional fidelity. Evidence:
`20261020-roadster-goal/hood-qualification-01-checkpoint.json`.

### Qualify component ownership and exchanged partitions

Before diagnosing provider caching, check the installed provider's documented
source-ownership contract. The pilot's native surface provider requires one
component per file. An authored wrapper violated that contract; separating the
source and three partition owners into their own files produced a successful
native export without changing geometry or tolerances. A comment-only source
revision then rebuilt with all 18 exchanged faces byte-identical. This supersedes
the native-export hold above for that exact layout and revision. It does not prove
the internal cause of the earlier failure or every provider cache path.

Validate exchanged partitions against the declared predicates, recording operand
structure as well as tool version. Here 248 of 249 initial checks passed. A single
aggregate compound-tool coverage query reported missing area, while explicit
per-source coverage and per-fragment excess queries passed the original budgets;
group agreement, total area and pairwise overlap passed too. Preserve that
discrepancy and the raw failure. Do not replace it with a blanket pass, relax the
threshold, or treat a finite sampled distance as complete coverage. The bounded
disposition uses the original face-level predicates; general Boolean reliability
remains unqualified.

Check the integrated artifact separately. The full-car export contained all 94
protected non-hood faces and all 18 partition faces byte-for-byte from their
respective qualified inputs. That accounts for all 112 faces in this revision,
but says nothing about older mismatches, vehicle dimensions, lamp contour accuracy
or human acceptance. Frozen multiview comparisons remain necessary. Evidence:
`20261020-roadster-goal/roadster-hood-comparison-01-checkpoint.json`.

### Check camera conventions before joining a missing panel

Project the actual proposed CAD anchors back into every relevant fixed view
before using them as a missing panel's corners. A most-aft center station can be
much narrower than the photographed rear fascia; exact topology does not make
it the corresponding photographed feature. Distinguish the visible fixed panel,
movable assemblies, occluded regions and mere feature-region boxes. Record new
cross-view correspondences as evidence with alternatives and uncertainty.

Also round-trip image coordinates through the declared camera inverse. In the
pilot, the preserved, unplaced rear proxy used the opposite lateral sign from
the frozen rear camera. Direct calculation exposed the mirror before any rear
fascia was constructed. This did not establish a defect in the existing native
model: the proxy was still unplaced data. Preserve historical evidence and use
the explicit camera convention for a new candidate rather than silently rewriting
old coordinates. Numerical inversion checks do not calibrate the camera or
establish physical scale. Related photographs from one promotional source provide
complementary views, not independent physical verification.

If a feature's points lie outside a sampled envelope, first check the envelope's
coverage and ownership. A short aft trace may omit the adjacent quarter contour;
that is different from proving the full body cannot support the feature. Preserve
the failed construction, identify the wider existing evidence explicitly, and
check its range without extrapolation. Do not shrink the required feature or
silently change camera calibration to obtain a pass.

The rear-fascia investigation separated upper-lip, housing-bottom, lower-boundary
and plate-occlusion traces. The existing gradient tool found 167 stable candidates
at 181 stations in four new regions; all uncertain samples remained recorded.
Those observations refine image localization only. The narrow aft-context
construction failed a transverse-range check, including a calculation with the
declared annotation intervals. A separate check using the already available full
rear-quarter outline covered all 20 selected nominal fascia vertices. This admits
a broader construction hypothesis for evaluation; it does not establish depth,
attachment, camera calibration, complete surface coverage or physical accuracy.
Any such family still needs projected-view, interior/occlusion, native validity
and exact exported-artifact checks before integration.

### Verify complete cells before building a proposed surface

Check the union of projected face polygons against the declared visible region
minus its occlusion masks. Record missing area, excess area, pairwise overlap,
degeneracy and convexity separately. Vertex containment alone cannot establish
coverage or exclusion. Keep annotation intervals distinct from numerical identity
guards, and do not use a convex hull to silently fill a concave cell.

The rear-fascia pilot's eleven-cell proposal covered its declared masked region
to numerical roundoff, yet one cell described as convex had a convex-hull excess
of 319.52 square pixels. That finding prompted a source-preserving partition
correction before native construction. A successful coverage check did not prove
the proposed construction assumptions were true.

Screen other views and the current native artifact separately. A projected
wheel-region overlap is an occlusion warning, not a three-dimensional collision.
Read the screen coordinates from their source rather than transcribing them.
For open surfaces, record section curves and distances without calling them
solid interference or a valid attachment. The isolated rear-fascia analytic
reference crossed two existing corner regions and had large construction normal
jumps; neither integration nor physical fidelity was qualified by its coverage.
Evidence: `20261020-roadster-goal/rear-full-family-preflight-02/`.

Validate exported face orientation independently of boundary winding. The
corrected twelve-cell fascia built valid native surfaces with matching footprints,
but four exported normals opposed the declared exterior hemisphere. The provider's
fill contract did not promise that orientation, so this was not sufficient evidence
of a provider bug. An Astra-authored revision used the documented native planar
constructor and existing component-add API. Exact revision-2 STEP revalidation
found all twelve normals correct, with zero missing/excess area in direct
per-face comparisons to revision 1 and maximum centroid change below 5e-10 mm.
This improves representation correctness, not demonstrated vehicle accuracy.
Preserve both revisions and their original findings.

An edge-on surface can have zero rasterized area in a valid view. Inspect projected
native edges in that view instead of interpreting a blank silhouette as missing
geometry or changing the camera to make it visible. Label all-edge plots explicitly
when hidden-line removal is absent. The fascia's overhead projection is such a
case; its side-view mismatch remains visible and unresolved. Evidence:
`20261020-roadster-goal/rear-fascia-native-correction-comparison-04.json` and
`rear-fascia-trial-comparison-04c/` in the same evidence directory.

### Compare depth and competing constraints, not one favorable silhouette score

Keep source identity, masks, camera and observations fixed during a bounded
candidate sweep. Report displacement, native intersections, visible feature
ownership and uncertainty alongside image residuals. Use the same supported
samples when comparing candidates; retain out-of-range observations instead of
clamping them or changing which samples count. An interpretation corridor is
not an engineering tolerance. Preserve negative experiments as decisions about
which construction family to avoid, not as permission to refit the camera.

The fascia investigation tested nine values of an Astra-defined affine rake,
holding its upper lip and complete rear-view domain fixed. The maximum
conditional side-contour discrepancy on thirteen common samples decreased from
63.25 to 9.12 pixels. However, native body-intersection length increased from
78.14 to 227.52 nominal mm, and visible candidate pixels within the tire-context
box increased from145 to2129. None of the nonzero settings was selected for a
new producer build. The contour's feature ownership remains ambiguous, and the
tire box does not establish a physical collision. All cameras and requirements
were preserved. The side image had already informed authoring, so this is a
cross-view diagnostic, not an independently held-out image test.

Depth inspection also exposed a limitation of a whole-object foreground mask:
in the rear view, the fascia replaced42876 visible pixels without adding any
foreground pixels. Existing surfaces farther forward already occupied that
projection through the missing rear panel. A silhouette score alone would miss
this change. Inspect which surface is visible, its depth and semantic ownership.
For read-only comparison, two exact-export render results with identical camera
and image identities can be composited by nearest finite depth; label the result
as a visualization, not an integrated CAD revision. Keep ties and real-photo
occlusion limitations explicit. Pilot evidence:
`20261020-roadster-goal/rear-fascia-visible-context-05/` and
`rear-height-shear-experiment-05/` in that evidence directory.

### Inspect visible feature ownership before refining detail

The reusable [owner visibility helper](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-research/owner_visibility.py)
composes depth/shade arrays from the existing fixed-camera rasterizer. It records
each group's projected, uniquely visible, occluded and nearest-tied pixels.
Default ties require exact equality; an explicitly supplied numerical near-tie
epsilon is recorded separately and is never an engineering tolerance. Tied
pixels stay ambiguous rather than inheriting whichever component was processed
last. Diagnostic colors identify groups, not physical materials or illumination.

Associate groups with the exact exported native faces before rendering. Preserve
the full competing geometry and camera/image identities, and check that grouped
composition reproduces the full-model foreground and nearest-depth arrays.
Missing occluders, copied faces or a different camera can invalidate ownership.
The helper performs no CAD mutation, geometry validation or calibration and adds
no workflow executor. Its controls cover ties, occlusion, order independence,
input preservation and invalid data. The corrected pocket fixture independently
checks known floor/shoulder visibility and duplicate-floor ambiguity with the
same helper and rasterizer.

In the Roadster pilot, all four provisional lamp-mask faces matched the current
full-car export by complete BRep bytes. Grouped front and overhead depths were
identical to the earlier full-model renders. Both lamp groups were wholly
visible, yet front-view overlap with the retained interpreted polygons was only
0.178 and 0.256, compared with 0.917 and 0.915 overhead. These are conditional
raster comparisons with provisional observations, not physical accuracy scores.
They expose a multi-view placement/shape conflict that a material change cannot
resolve. Preserve the existing candidate and assess the source surface, trace
identity and camera assumptions before a separately bounded correction.

Pilot evidence: `20261020-roadster-goal/front-owner-visibility-06/`,
`front-owner-inputs-06/` and `owner-pocket-qualification-06/`. This local helper
is available for future workflow authoring; automatic use by the saved research
workflow remains unqualified.

Compare an added surface with its intended replacement context as separate
experiments. Keeping its old owner can hide the candidate; silently removing
other occluders can exaggerate improvement. Identify every omitted face by exact
native identity and keep the original model intact. A counterfactual display
with old faces omitted does not establish joined geometry or authorize an
unmeasured recess. In the three-value lamp experiment, even excluding the four
old lamp-mask faces left substantial occlusion and crossings with other body
faces; isolated front-view improvement was not sufficient for integration.

Use the native section operation for surface-crossing curves. Boolean common
and a surface section answer different questions. The first local lamp check
incorrectly interpreted an empty Boolean-common edge set as a section result.
A corrected `BRepAlgoAPI_Section` check found crossings in all three candidates;
the failed interpretation is retained and explicitly superseded. An empty
result only supports the operation actually performed. Existing shared native
section diagnostics should be preferred to a new ad hoc shortcut.

Before joining cross-view landmarks, also verify boundary and configuration
identity: a cover seam, aperture edge and illuminated region may be distinct.
Text such as "concealed headlights" is a reason to investigate configuration,
not proof of an observed hinge, motion or hidden depth. Use existing oblique
views to inspect the specific loop adjacency before changing the model or
collecting another broad reference set. Pilot evidence for this unresolved
front-detail case is `20261020-roadster-goal/lamp-family-checkpoint-07.json`.

### Separate camera sensitivity from a geometry correction

When a feature fits one view but fails another, test the camera assumptions on
the unchanged exact export before deforming the feature. Declare a small finite
family, its construction anchor, intrinsic assumptions and parameter bounds.
Freeze all camera objects before scoring. Keep the historical projection, and
report non-target feature behavior before inspecting the feature that motivated
the test. A camera registered to provisional CAD is not independent calibration.

Check the complete camera contract before rendering: rotation handedness, optical
forward direction, camera center, anchor projection, positive depth of every
vertex, and the existing renderer's schema. A mathematically orthogonal matrix
can still encode the wrong pitch sign. Preserve rejected proposals and verify
actual model routing for correction requests as well as initial authoring.

Report feature ownership and visibility, not just whole-object overlap. A roof
surface may be edge-on and therefore have no occupied pixels; an image row
crossing a canopy mask is not necessarily the observed windshield corner or
lower edge. Keep those unavailable or ambiguous comparisons explicit. One
improved support coordinate must not conceal worse neighboring boundaries.

The Roadster sensitivity study retained nine distance/pitch hypotheses and the
original orthographic baseline. A six-degree hypothesis aligned the roof's
upper support, but moved the lamp fragments about 92 pixels too low even at the
weakest tested perspective. No camera was selected as calibrated or as a repair.
Evidence: `20261020-roadster-goal/front-camera-evaluation-10/`. These are image
coordinate observations on provisional geometry, not physical error estimates.

Assembly-aware and plain STEP readers can serialize the same rendered surfaces
differently. Do not claim byte-identical native faces when that comparison fails.
For a rendering-only ownership map, the pilot independently matched all 2,155
triangle coordinate tuples without rounding, then used the original vertex
array, triangle order and winding. Grouped composition reproduced the full
foreground and depth exactly. This establishes that specific render partition;
it does not replace native geometry validation or permit approximate matching
without a separately declared method. The generic projection and visibility
helpers remain shared; the vehicle-specific camera family is local evidence,
not a new workflow executor or an automatic default for other objects.

### Preserve observations when solving a constrained reconstruction

Keep measured or previously indexed image coordinates separate from construction
targets proposed by AI. Record a correspondence hypothesis explicitly. Replacing
an inconvenient source coordinate with a nearby target is not a geometric
correction, even when the new value is labeled plausible.

For a bounded reconstruction, derive the feasible parameter intervals from the
unchanged observation equations and bounds before constructing geometry. With
fixed affine image mappings, interval intersection and constrained least squares
can expose a conflict directly. Retain the unconstrained estimate, feasible
interval, active bounds and residuals. An empty intersection is an explicit
infeasibility; do not widen tolerances to hide it. Arithmetic slack for a floating
point boundary check must remain distinct from measurement uncertainty.

A proposed, unobserved construction target can be revised in a new candidate
when its assumption is rejected. Preserve that target and its failed result,
name the changed assumption, and distinguish the replacement's predicted image
coordinate from a new observation. A calculated prediction must not become an
independent validation target centered on itself. The same distinction applies
to an interpolated comparison envelope: exceeding an assumed line does not by
itself prove that geometry crosses the observed silhouette.

Passing point-coordinate bounds does not establish a good feature shape. In the
joint Roadster front trial, the exact native export passed all46 active image
coordinate checks, while lamp-region overlap improved in the front view and
worsened overhead. Preserve this vector of results rather than averaging it into
a blanket pass. Native source/export identity, valid faces, numerical bounds,
whole-region agreement, contextual visibility and physical fidelity answer
different questions. A qualified separate trial need not become the preferred
full-object candidate. Evidence: `20261020-roadster-goal/front-context-c02-native-validation-13/`
and `front-context-native-overlap-13.json`.

### Separate registration error from reconstruction error

A fixed camera scale or arbitrary image anchor can make a camera experiment
inconclusive. A new, explicitly versioned registration may fit a small declared
set of support roles while keeping the geometry fixed. Freeze its finite camera
family before evaluating other features. Record which parameters were fitted;
those support matches are not independent validation. A fit to provisional CAD
does not establish a calibrated camera.

Inspect complete visible boundaries as well as point and row measurements. A
canopy can have the expected width at an image row while extending far below its
observed lower edge. Nearest-boundary distance can also match the wrong semantic
edge. Preserve both the measurement and the visual discrepancy instead of
turning a convenient scalar into an acceptance rule.

In the Roadster's non-lamp registration experiment, the unchanged exported car
achieved front lamp overlap of .662/.614 under one camera hypothesis, versus
.178/.256 under the historical camera. The overhead geometry and its result did
not change. That is evidence that the earlier front mismatch included camera
assumptions; it does not prove that this hypothesis is the real camera or that
all geometry is correct. Conditional geometry trials must retain the camera
identity, original observations, failed alternatives and unverified scale.
Evidence: `20261020-roadster-goal/front-camera-registration-evaluation-14/`.

A reconstruction can satisfy every point bound yet fold between those points.
Check shared-edge incidence and direction, projected overlap, actual surface
sections and the visible result. In a corrected Roadster trial, two lip points
were changed to follow the actual projected lamp-tip rays rather than the
nominal target rays. Every other vertex and every original observation remained
unchanged. The new export removed the measured fold and retained the observed
overhead lamp coordinates, but still crossed the old body. Thus a qualified
separate patch required further replacement and attachment work before full-car
integration. Matching boundary endpoints alone does not establish a sewn shell,
smooth continuity or physical fidelity. Evidence:
`20261020-roadster-goal/front-context-c04-native-validation-16/`.

### Replace surfaces using their source boundaries

When an improved feature crosses the old body, identify the editable source
surfaces and their complete boundaries before selecting a replacement region.
Finite ray hits show sampled support; misses may indicate a new exterior outline
instead of a recess requiring a closing wall. A source station need not describe
a constant Cartesian coordinate across all rails. Preserve exact lower curves,
including wheel openings, while testing explicit visible-surface interpolation.

Separate original faces, proposed removed pieces, retained pieces and new faces.
Keep area accounting and all slivers. In sequential native subtraction, a fully
removed face is an expected empty remainder: inspect that state before asking
the kernel to intersect it again. Do not interpret an arbitrary kernel exception
as an empty intersection or relax tolerances to conceal a failure.

Inspect local candidates before another native build. The Roadster front-body
prototype produced19 valid new faces with no measured extra interior sections
against its corrected front patch, but the old body still intersected them and
the rear join remained open. Three-view comparisons and exact source-boundary
association made the next correction concrete without replacing the saved car.
This is preparation evidence, not successful integration. Local evidence:
`20261020-roadster-goal/front-integration-inspection-17/`,
`front-integration-projections-17/`, and
`front-all-nose-boundary-associations-17.json`.

Treat native analysis as potentially mutating its in-memory operands. In the
next local extraction, area accounting was unchanged, but complete BRep
comparison found changed vertex tolerances on23 retained faces and all19 new
faces after Boolean diagnostics. A plain export/import control changed none of
the112 original faces. The original STEP files remained intact. Run analysis
against independent copies of both operands and compare protected geometry
before and after; equal areas and a function without file writes do not prove
that its inputs were preserved. Evidence:
`20261020-roadster-goal/front-brep-identity-diagnosis-19/report.json`.

### Keep independent silhouette checks when replacing a feature region

A replacement can resolve intersections and expose a well-matched feature while
making the enclosing object less accurate. Preserve the exterior outline as a
separate constraint from an interior feature boundary. A lamp edge need not be
the fender's highest rail; replacing a broad source region with a lower feature
network can shrink the object's envelope even when every face is valid.

Evaluate the assembled candidate, including retained geometry, in frozen views
before another native build. Use original image observations rather than old
CAD as dimensional truth. Where a high-contrast exterior boundary permits
automatic image tracing, retain the search region, photometric method,
alternative-edge strengths, original image identity and visual trace review.
These are provisional image observations, not a new physical tolerance or
camera calibration. Keep fitted and independently checked views distinct.

The local Roadster assembly21 had no reported extra interior section curves
among its replacement faces or against the retained body. Nevertheless, a
visually checked automatic side-image trace increased mean absolute outline
error from5.85px to17.62px over26 comparable samples, with a41px maximum. The
trial was retained without promoting it over the saved native baseline. These
image-space diagnostics do not establish physical accuracy or a general pass.
Evidence: `20261020-roadster-goal/front-assembly-inspection-21/report.json`,
`front-assembly-projections-21/comparison.png`, and
`front-side-envelope-21/report.json`. The documented method remains a local
pilot analysis; no new shared validator capability is claimed.

Freezing a run's routing and evidence must not turn a provisional geometry
hypothesis into a permanent engineering requirement. Before another correction,
classify each retained constraint as a supplied requirement, original observation,
derived value or construction assumption. If independent evidence rejects an
assumption, supersede it in an explicit new candidate revision, retain its old
value and failed evidence, and revalidate every affected output. Preserve the
original observations and their tolerances. In the Roadster front, a provisional
hood-surround target at front-image v1155 had been retained alongside original
hood-facet upper-edge picks at v1125. The subsequent full-front request explicitly
revises the surround hypotheses; it does not rewrite the earlier successful
lamp-only trial or claim that the new body has passed. Evidence:
`20261020-roadster-goal/front-constraint-diagnosis-24.json`.

### Keep source selection independent of export ordering

Do not use a STEP face index as the identity of a face in regenerated native
source. Source assemblies and exported STEP can enumerate the same regions in
different orders. Associate source regions through stable feature identifiers
where available; otherwise require a unique recorded geometric correspondence.
An association bound is a bookkeeping check, never a dimensional tolerance or
proof of preservation. Independently compare the actual exported protected
geometry afterward. Abort on missing or ambiguous correspondence, and retain
failed candidates instead of weakening exact-output requirements.

The Roadster C05 revision2 built successfully but its independent audit matched
only62 of87 protected faces. It was not promoted. A separate source revision
introduces explicit source/reference correspondence; this repair requires its
own exported-artifact audit. Local evidence:
`20261020-roadster-goal/native-front-26-validation-v2/report.json` and
`full-front-native-29/source/source_face_selection.py`.

### Check the native surface behind a rendered discrepancy

Use exact native ray intersections to investigate discrepancies between CAD and
tessellated comparisons. Retain camera, image, geometry and mesh identities.
Cached triangulations, tessellation resolution and overlapping surface layers
are separate possible causes; do not infer which one failed from an image alone.
When rebuilding a diagnostic mesh, operate on independent geometry, preserve
the CAD and report the meshing parameters. Respect existing rendering resource
limits. A changed triangle mesh is visualization evidence, not a CAD repair or
new engineering tolerance.

After a visibility correction, inspect every overlapping surface layer in the
assembled candidate and recheck other views. Exposing a feature from one camera
does not establish its physical recess or hidden connecting geometry. The local
Roadster trials use the existing provisional camera and actual lamp triangles
to explore visible apertures; they do not claim measured recess depth, complete
lamp visibility, native integration or final acceptance. Local evidence:
`20261020-roadster-goal/aperture-ray-diagnosis-30.json`,
`trimmed-tessellation-control-31.json`, `group-mesh-pixel-33.json` and
`lamp-aperture-visibility-34.json`.

### Separate camera registration from shape correction

Register a new view against named, source-linked features with the object held
unchanged. Retain the original raster, manual correspondence uncertainty,
candidate focal lengths, fixed intrinsic assumptions and every fitted result.
Check additional features that were excluded from numerical fitting and camera
selection. A fitting residual alone cannot establish calibration: a camera can
align a small door while concealing a canopy or rear-envelope error. Do not
adjust camera and geometry together until their disagreement disappears.

The closed/stowed Roadster I12 study used seven door/roof correspondences and
one withheld glass tip, with four fixed focal hypotheses. The preferred fitting
camera still missed the glass tip by about41 pixels. All four retained cameras
had discrepancies; no calibrated camera or physical accuracy was established.
The exact native body was unchanged. The image and semantic picks remain
visible in `20261020-roadster-goal/rear-camera-43/`. Another reference with a
raised airfoil remains fixed-body/component context, not a stowed-state target.

### Use circular features as conditional camera evidence

Local Roadster study1777 uses actual exported front and rear rim circles spanning
the vehicle length. It retains all original-image rim proposals, zero-steering
and steering-nuisance fits, a front-shape holdout, and principal-point variants.
A lower fit residual diagnoses an assumption; it does not prove steering,
intrinsics, physical dimensions or independent vehicle accuracy. The body stays
outside the camera fit. Keep rear-only weak-perspective results scoped to their
original features rather than reusing them as full-object calibration.

The same study traces a source border before intersecting it with CAD. Fourteen
stable candidates and three ambiguous stations remain visible. Native rays show
that the border crosses a trailing skin, cheek and fascia. A cheek-only material
partition improves a limited segment but leaves the fascia join wrong; it remains
a local held trial. Source-edge support, physical seam identity, material labels
and shape correction are separate claims. These are descriptive local examples,
not a registered workflow binding or a new accepted instruction revision.


Wheels, flange rims and other circular features can add constraints when a body
surface has few reliable landmarks. Preserve the selected border pixels and
inspect an ellipse overlay on the original raster. Record whether the selected
edge is a rim, tire, hole or reflection. Do not treat an ellipse's image centre
as the projected three-dimensional centre under perspective, or its axis ratio
as a pose measurement without declaring the projection and plane assumptions.
OpenCV supplies [ellipse-fitting primitives](https://docs.opencv.org/4.13.0/d3/dc0/group__imgproc__shape.html)
and the [pinhole camera model](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html);
their availability does not qualify an engineering reconstruction.

For a declared circular feature plane, project the circle through its plane
homography and compare the resulting conic with original border pixels. Check
that conic against direct three-dimensional circle projection as a numerical
control. Unknown radius, lateral position and centre height can remain nuisance
hypotheses; they must not silently become dimensions in CAD. If transferring
ratios or feature heights from another image, retain the same-configuration,
camera, datum and border-identity assumptions. A shared ground pick creates
correlated uncertainty. Retain alternative fits and checks excluded from fitting.

The Roadster conditional studies91–96 used unchanged actual C08/C09 native
geometry. Adding manual side-view wheel evidence reduced the withheld glass-tip
error from40.59to21.93pixels and C09's independently checked image light-bar
centreline mean discrepancy from27.45to11.55pixels. However, the transferred
rear-rim radius still disagreed, and a separate upper-edge diagnostic did not
improve overall. No new camera was adopted or physical wheel size established.
This is a conditional local study, not a qualified shared camera solver. Preserve
its tradeoffs rather than selecting a camera because one feature looks better.

### Use line directions and feasible projection volumes to diagnose stalled fits

A photographed straight feature can constrain camera orientation without
assigning its hidden depth. Under an explicit hypothesis that a line follows
object direction `d`, its vanishing point is `K R d` in homogeneous image
coordinates. At a measured image point on that line, compare the resulting
projected direction with the observed direction. Keep the object unchanged,
retain independent landmarks, declare the directional prior and numerical
weight, and preserve every camera hypothesis. Image straightness alone does
not prove a straight three-dimensional feature or its object-frame direction.
An improved direction residual can coexist with a failed withheld landmark.

Before refining more surfaces inside a fixed provisional search region, check
whether that entire region can project onto the disputed observations. For a
convex polytope wholly in front of a perspective camera, its projected vertices'
convex hull bounds the image of every contained surface. Observations outside
that hull cannot be reached by changing surface controls inside the same volume.
Retain image/pixel and camera identities and report numerical precision. This
diagnoses inconsistent hypotheses; it does not identify which hypothesis is wrong.
Construction bounds remain distinct from supplied engineering requirements.
Revisit the camera, source correspondence or explicit construction assumption
in a visible new candidate; do not relax user tolerances or silently rewrite data.

In the Roadster local study83, a transverse-line prior improved the direction
agreement but left a withheld glass tip about40pixels away. Study89 found
68 of363 selected rear-quarter red-bar columns outside the original camera's
projection of the entire C09 rear search volume, at most67.35pixels outside.
All four original focal hypotheses and four direction-prior hypotheses had
exclusions. These findings reject continued fit claims within those combined
assumptions; neither study establishes a calibrated camera or physical accuracy.
The source references include moving components in different states: compare
only named visible fixed features or explicit inclusion masks across states.
A rectangular crop and a caption do not establish an exclusion mask.

### Audit surface complexity and shared boundaries before adding more patches

Inspect actual native degrees, control counts, parameter domains and trims.
High-degree filling can obscure a simple intended section/rail construction.
Where the evidence supports a simpler parameterization, create a separate
candidate with named controls and shared boundary curves. Keep original pixel
observations and source hypotheses distinct from native parameterization.
Verify a zero-change construction control, neighbouring interfaces, orientation,
sections and the exact exported basis before attributing an improvement to a
new shape parameter. A lower control count does not establish fidelity.

The local C10 Roadster trial replaced18 canopy/glazing faces with a cubic/
quadratic section construction, reducing6025 native support poles to168. A
bounded crown parameter preserved the source centre/XY construction relative
to its zero-drop control and retained the lower glazing rails. On the actual
export,13 inspected white-outline points improved19.46to14.38pixels;28 original
side-outline points stayed at0.893mean/2maximum pixels and the plan footprint
was unchanged. An alternative uncalibrated oblique camera worsened, so this is
a provisional shape hypothesis rather than uniformly verified vehicle fidelity.
Nineteen front detector samples were actually on the hood seam, not the dark
roof border; their failed classification is retained separately, not counted as
roof accuracy. Do not select observations by their resulting fit residuals.

Position continuity does not imply tangent continuity. The actual new shared
boundaries coincided at21 tested points each, while longitudinal surface-normal
jumps reached about9.4degrees. Panel dihedrals reached about53degrees; whether
these are intended physical corners is a separate evidence question. Preserve
those observations and refine the coupled adjoining curves where smoothness is
required, including interfaces with unchanged surfaces. Do not smooth one patch
while disconnecting its protected neighbour or infer a global G1 result from
validity, shared endpoints or a shaded preview. Local evidence is
`20261020-roadster-goal/native-c10-validation-117/`,
`native-c10-inspection-121/`, `native-c10-joins-122/` and
`native-c10-comparison-123/`.

The subsequent local C11 study couples canopy and adjoining shoulder frames
through shared source-section profiles. Thirty old faces become seven
multi-span surfaces, with347 controls and158 faces in the complete trial. Keep
separate native parts where the evidence requires them; topology need not expose
every mathematical span as a separate part. Shared Hermite derivatives remove
unintended longitudinal canopy jumps without smoothing unrelated physical or
inherited boundary corners. On the actual exchange, finite canopy normal probes
change from about9.4degrees to0.000003degrees. Derivative control vectors are
also compared in a common source parameter, rather than inferring smoothness
from a shaded mesh. The original lower belt curves retain sharp corners; no
global body-smoothness or physical-corner acceptance is established.

Retain parameterization provenance. Large source-image parameters lost several
trailing digits during the first STEP exchange and failed a numerical knot
consistency diagnostic. An explicit new CAD revision normalized each surface's
longitudinal parameter to0..1. Controls, weights, multiplicities and geometry are
unchanged under that affine mapping; local finite checks differ at most6.92e-13
nominal units. The original diagnostic and export remain, and its1e-12 guard is
unchanged. Exact-output requalification is still required after normalization.
This is a geometry representation choice, not a camera/scale correction,
engineering-tolerance relaxation or a provider-protocol workaround.

Feature identity must precede curve merging. In the Roadster overhead reference,
the side-window tip and central rear-glazing edge are separated by visible body
material. Do not collapse them to improve an oblique reprojection residual.
The new envelope leaves glazing/material divisions unresolved. C11's native
front white-edge mean changes14.38to14.62pixels, the28 side observations stay
unchanged, and the plan foreground changes12pixels. Record those tradeoffs
alongside the continuity improvement. Evidence is local under
`20261020-roadster-goal/c11-inputs-127/`, `c11-parameter-normalization-137/`,
`native-c11-validation-142/`, `native-c11-continuity-144/`,
`native-c11-inspection-145/` and `native-c11-comparison-147/`.

### Compare actual native snapshots before diagnosing preservation failures

Import both actual STEP snapshots freshly into the same reader when comparing
native face bytes. An intermediate text BRep export/import can change floating
point representations or tolerances and must not become the identity oracle.
Use intermediate source records only for unique semantic association. Preserve
byte-identity failures, then inspect support geometry and trimmed boundaries
separately on copies. Identical support surfaces do not establish identical
trimmed domains; sampled distances do not certify a global Hausdorff bound.

The direct C05/C06 Roadster audit found115 of140 retained faces byte-identical;
an earlier comparison through intermediate BRep files reported105. The25 direct
mismatches have identical plane/B-spline support definitions. Bidirectional
vertex/edge/inside-UV samples reached0.0002174 nominal mm. These observations
clarify the failure without waiving exact preservation, changing physical
tolerances or accepting the model. Evidence:
`20261020-roadster-goal/direct-native-retention-44/report.json` and
`direct-native-differences-45/report.json`. These are local engineering analyses
using existing readers and evidence owners, not a new shared validator contract.

A nested native reference may also introduce additional placement records whose
composed transform is exactly identity. Diagnose that case without approximating
a nonidentity transform away. The C07 appended rear-band export had0/151 raw
face-byte matches against C06. Requiring every entry of both world affine
matrices to equal identity exactly, then removing only the root identity
location on independent copies, produced151/151 identical complete native face
definitions and preserved orientation. This explains the representation change;
it does not turn the raw-byte result into a pass or change a frozen validation
contract. Record both domains and retain the original exports. Evidence:
`20261020-roadster-goal/native-c07-preservation-52/report.json`.

### Match feature topology before assigning section widths

An engineer supplies text, images/data and any existing research. The authoring
step should reuse that package and identify corresponding feature vertices
internally; the user need not prepare a manual evidence index. Review ambiguous
matches and ask only essential declared questions. Keep the original picks and
their distinct roles even when a previous model used a simpler interpretation.

An outer silhouette, a lower styling crease and an inset window/upper-panel
corner can occupy different lateral positions at the same approximate station.
Assigning the widest plan span to every height produces a different 3D shape.
Inspect original seam topology across views before changing camera or surface
interiors. Calculate intersections of existing feature traces when applicable,
and distinguish those calculations from newly observed points. Coordinate
transfer through an uncalibrated view remains a hypothesis. Retain full image
coordinate residuals, uncertainty, asymmetric-image effects and unobserved-side
assumptions; matching one coordinate does not establish calibrated triangulation.

Rebuild every affected adjoining skin in a separate editable candidate. Reuse
the configured independent CAD provider, canonical runtime/evidence owners and
existing independent readers. Verify exact saved source/export, retained native
definitions, shared boundary controls, regional multiview residuals, sections
and continuity. A new correspondence changes dependent geometry and comparison
evidence; it does not rewrite historical artifacts, cameras, frozen routing or
review authority. Missing correspondence/capability remains an explicit gap.
The same procedure applies to an enclosure seam or fixture edge. Those are
applicability examples, not additional qualified engineering executions.

The local Roadster C13 trial uses distinct original plan seam vertices for
upper door corners and preserves original side-view X/Z. An intersection of
the original rear-door seam and lower white-band trace defines an adjoining
crease endpoint; it is calculated, not newly measured. The actual native
front13-column mean changes14.62to9.92pixels and the maximum50to37 under the
unchanged camera. The28 side outline scores stay unchanged. Full plan corner
error changes34.77to20.88pixels; the remaining longitudinal mismatch is retained.
Plan lateral coordinates supplied the new construction, so their near-zero
residuals are fitting evidence. No physical accuracy or camera calibration follows.

Actual output checks find180 valid open faces and32 new surfaces. Both native
upper-canopy control tables exactly match the retained geometry. All496 new/new
and4736 new/retained section pairs show no extra interior crossing curves.
Strict retained identity remains135/148; all13 differing support/3D-curve tables
match exactly, but sampled boundary agreement does not prove identical trimmed
domains. Internal door subdivision normal jumps reach0.65degrees despite zero
sampled gap. Do not label those construction seams verified styling creases or
claim global smoothness. Prefer a subsequent coupled fairing correction that
retains the source features and adjoining interfaces.

An accompanying bounded camera study includes previously untested negative
pitch hypotheses. Lower body-outline error alone is insufficient when lamp
agreement worsens. No camera from that study was adopted. Evidence is local
under `20261020-roadster-goal/front-joint-pose-164c/`,
`door-correspondence-165/`, `native-c13-validation-178/`,
`native-c13-inspection-181/`, `native-c13-comparison-182/`,
`native-c13-corners-183/`, `c13-retention-measurement-184/` and
`native-c13-door-joins-186/`. These findings extend method guidance and a proposed
versioned instruction asset; they add no shared executor, provider protocol,
accepted workflow update, UI requirement or automatic acceptance.

### Correct a regional envelope while preserving shared boundaries

Reuse the supplied images and previous results before collecting more data.
Separate movable-part states before defining fitting or validation regions.
For a proposed surface correction, freeze the source observations, camera,
scale hypothesis, protected interfaces and named parameter bounds. If an image
informs the correction or selects among alternatives, label it as fitting or
selection evidence; it is no longer a blind validation view.

Under a positive-depth pinhole camera, a convex polygon in image coordinates
can be lifted to world-space halfspaces. Nonnegative B-spline/Bernstein basis
functions and positive weights let control-point halfspace bounds constrain
the supported curve spans. Establish convexity, depth and the exact constrained
domain first. This is a conditional construction bound under that camera, not
a calibrated vehicle envelope or a physical tolerance. A protected interface
may conflict with a whole-object image constraint: retain the conflict, scope
the correction to the supported region and report the unconstrained blend.
Do not claim whole-object containment from a regional calculation.

Calculate continuity on shared curves and rebuild adjoining skins together.
Merge artificial subdivisions where the supported representation permits it.
Check the exact native export for controls, degrees, weights, knot domains,
orientation, retained definitions, joins, section shapes, intersections and
feature visibility. Inspect transverse or longitudinal sections as actual shape
evidence; face-pair intersection counts alone do not inspect section shape.
Preserve raw identity failures even if supporting-surface tables match and
finite boundary distances are small. Keep creases with uncertain feature roles
explicit rather than reporting global smoothness.

The C14 Roadster study replaces34 faces by16, leaving162 valid open faces. A
regional lateral correction is bounded by `rear_inset_blend` in[0,1]; a distinct
window-tip transition ends within the original source-station interval
[1892.7611940298507,1995]. The selected endpoint is1995. Two alternatives retain
the same front/side/plan scores; rear images select the longer transition.
The stowed airfoil and adjoining cheek interface remain protected. The native
front13-column fit changes9.92to6.62pixels, maximum37to16; side and plan-station
scores are unchanged. Both uncertain rear-camera means worsen slightly, so no
all-view or physical accuracy improvement is claimed.

Native C14 door subdivision normal probes are below0.000001degree, and sampled
window-tip joins coincide. The mid-sail crease still reaches22.92degrees and
its styling interpretation is provisional. Strict retained equality is136/146;
all10 differing support and3D-curve tables are exact, without proving identical
trimmed domains. All4494 lamp rays remain unblocked with lamp hits. Six actual
transverse sections were inspected. Evidence under
`20261020-roadster-goal/native-c14-validation-204/`, `native-c14-joins-207/`,
`native-c14-inspection-208/`, `native-c14-comparison-209/`,
`c14-retention-measurement-210/`, `native-c14-transverse-sections-211/` and
`native-c14-lamp-rays-212/` qualifies this local configured study only. No new
executor, provider protocol, accepted instruction revision or generic binding
was added. The method can also guide an enclosure or fairing reconstruction;
those applications have not been separately qualified.

### Derive visible conic boundaries without inventing a tube

A circular-looking rim in a photograph supplies an image conic, not a unique
physical circle, axis, radius, wall thickness or recess depth. Keep manual search
seeds distinct from calculated luminance/gradient samples and robust conic fits.
Retain search windows, raw samples, rejected or ambiguous candidates, fit
residuals and sensitivity settings. Blur and illumination affect the observed
band width; a small fitting residual is not a physical uncertainty estimate.
Do not silently fill missing qualified perimeter measurements.

Where useful, lift the visible conics onto an explicitly provisional existing
skin/placement hypothesis and create editable planar regions and actual trimmed
holes. Inspect the exact native supporting planes, closed ellipse parameters,
trim counts, analytic area, orientation, open centers and intersections. Preserve
all earlier surfaces and candidates. Diagnostic colors remain visual region
classification, not physical material or optical validation.

The local C15 Roadster trial adds four annular visible regions and three adjoining
panel faces. Its169-face native export retains all162 C14 native definitions
byte-for-byte. Four aperture centers remain outside all seven new faces; no
hidden backing or tube interior was added. The surrounding panel perimeter is
still a manual source hypothesis: only19/60 upper-border samples and0/52 lower
samples qualify under the unchanged gradient settings. Those shortcomings remain
explicit; the guide polygon is not relabeled a measured contour.

The new original I12 conic measurements expose a larger cross-view conflict:
even the best inherited placement in[0,1] leaves mean center errors of102.59 and
54.65pixels under the two existing camera hypotheses. The old rear-camera fit
also used C06 door/roof anchors subsequently changed by C11/C13. A fresh study
rebinds current exact native anchors and adds the two outer aperture centers,
with the middle centers and glass tip withheld. The fit improves aperture
agreement but still leaves substantial source-feature discrepancies. No new
camera is adopted, and C14 remains preferred over this separate C15 trial.

When geometry changes, version and rebind a camera's 3D landmark dependencies.
Historical fixed-camera comparisons remain useful controlled comparisons, but
do not establish a current calibration. Keep original image picks/uncertainties
and rejected cameras intact. A conflicting local feature must trigger inspection
of the joint camera/geometry/correspondence hypotheses, not an out-of-bounds
local move or concealment of poor views. The next substantive correction may
need a coarse multiview fit before more surface detail.

Evidence is local under `20261020-roadster-goal/rear-rim-measurement-219/`,
`rear-panel-source-220/`, `rear-rim-measurement-I12-231/`,
`native-c15-validation-230/`, `c15-placement-bound-233/`,
`native-c15-inspection-235/`, `native-c15-comparison-237/`,
`current-rear-pose-238b/` and `native-c15-openings-240/`.
This qualifies a configured local study, not a generic conic provider/reader or
automatic reconstruction capability. Other reverse-engineering workflows need
their own feature, camera, placement and exact-output qualification.

### Partition a visible feature without inventing its depth

After opening or authoring a provisional envelope, an engineer can identify a
visible seam or contrasting region in an original image. Keep the original
trace, camera revision, eligible faces and protected faces explicit. Project the
trace onto the existing skin and partition that skin into editable named
regions. A partition is a visible-region hypothesis; it does not establish a
separate physical part, material, recess, thickness or unseen return. Appearance
colors in a comparison are display classification unless native material and
appearance have been independently established.

Use the existing engineering provider and canonical workflow/result owners for
native save, build and exact export. Independent readers should inspect retained
definitions, orientation, partition coverage, overlaps and other-view envelope
consistency. Record the exact artifact and retain failed candidates. An input
trace's projection fit is fitting evidence; it is not independent validation.
If native splitting is unavailable, retain the annotated observation and report
the missing capability rather than claiming an editable partition exists.

The local C12 Roadster trial partitions seven existing front skins into seven
fascia-region faces and twelve adjoining skin faces. Its actual export has170
valid open faces, no solids, and all151 retained definitions byte-identical to
C11. Seven parent-area checks, finite bidirectional coverage and fragment-pair
overlap checks pass. Same front/side/rear outline scores remain unchanged; the
front trace fit is0.981IoU. Display classification is separate from native
physical material. The local evidence is under
`20261020-roadster-goal/native-c12-validation-159/` and
`native-c12-comparison-161/`. This is a configured engineering study, not a new
generic runtime binding, globally qualified method or accepted vehicle.

An initial local area-closure check failed with default surface-area evaluation.
Explicit adaptive surface integration at1e-12 relative numerical precision
passes the unchanged1e-5 nominal-area arithmetic guard. Keep the first failure;
improve the measurement rather than weakening the guard. This arithmetic guard
is not a physical tolerance. The provider rejected one additional nested link;
the successful separate design composes the unchanged C11 constructor and
parameters directly on its already pinned C10 base. Earlier source revisions,
exports and the rejection remain preserved; no new provider protocol is added.

Before reshaping a surface interior, project its fixed boundary too. Actual C12
shoulder belt samples extend about25 and50pixels above an interpolated front
white-outline hypothesis under the historical camera. A fixed boundary already
outside the image envelope cannot be repaired by changing only its interior.
Reconcile camera, source correspondence and shared boundary hypotheses together
in a visible new study; do not silently distort the body or overwrite source
picks. These finite diagnostic bounds are camera-dependent, not vehicle
dimensions. Evidence: `shoulder-boundary-feasibility-162/report.json`.

### Keep material correspondence and full-object shape checks separate

Two nearby image lines can be located precisely yet name different material
features. Record their incidence and ordering through adjoining regions before
transferring coordinates between views. A new glass-edge intersection must not
silently replace an older body-crease point: retain both pixels and their
versioned subject assignments. A view label alone also does not establish that
a lower corner is visible or hidden. Keep that correspondence unresolved when
the actual source does not establish it.

Explore shape and camera sensitivity with a small editable shared-curve network
before repeated native submissions. Preserve the original cameras and pixels,
report weak parameter modes and bounds, and compare changed geometry under the
same cameras as well as any explicitly fitted camera hypotheses. Add silhouette
and section checks alongside internal feature residuals. A camera refit is
fitting evidence, not independent validation of the changed body.

The local Roadster C16 previews257–264 rebuild30 side/fender/glazing/frame faces
on exact C14 output, retaining132 faces exactly. All226 previously matched
full-edge joins remain coincident in finite probes,190 old shared-vertex
clusters remain unseparated, and435 new/new plus3960 new/retained section pairs
show no extra interior curves. These are local construction checks, not a saved
native revision or complete shell/smoothness proof. The largest preview improves
six rear-quarter feature matches from14.49 to4.84pixels after the same camera-fit
procedure, while overhead station error worsens from2.95 to10.45pixels under the
unchanged camera. Keep the trial held; do not promote it as a whole-object
improvement or add an unsupported flange to conceal that tradeoff. The optional
model review265 used actual Sol/medium requests with three exact original image
payloads; its judgments are hypotheses, not measured correspondence authority.

### Model observed recesses as depth structure

An opened movable component does not invalidate the fixed body visible in the
same image. Identify fixed and moving subjects separately and retain visibility
and occlusion limits. Compare a stowed assembly against stowed references while
using deployed-state views for named fixed features. Do not discard an entire
rear view merely because its airfoil is raised.

A projecting surround, inset fascia, cavity, visible returns and dividers require
separate depth-bearing surfaces when the references support those distinctions.
Flat visual partitions and image-matched apertures cannot represent that shape.
Use visible edge ordering, occlusion and multiple oblique views to constrain
named depth parameters; distinguish a bounded digital interpolation from a
measured metric depth. Darkness alone establishes neither depth nor a hidden
floor. Keep unseen attachment, thickness, mechanism and physical feature
function unknown. Revalidate the exact output, intersections, sections, feature
visibility and multiview comparisons after a depth change.

The user-supplied rear detail retained in
`20261020-roadster-goal/rear-depth-source-266/` explicitly identifies the raised
airfoil and fixed remaining rear body. It supports prioritizing the missing
fixed rear recess over additional door detail. Its original PNG is a separate
untracked local input; the existing I12/I19/I24/I36 references remain preserved.
The second user closeup is retained separately at
`rear-component-source-268/inputs/roadster-2026-1.jpeg`. It resolves additional
visible volume: four projecting tubular bodies, their carrier, sculpted fascia,
lower returns/dividers and inset round-feature regions.269measures the four
front rim image conics from177–180 original-luminance samples each. Their fitted
edge residuals are about0.19–0.46pixels; these are image-fit residuals, not
physical accuracy or measured tube reach.

Separate editable components where visible volumes and interfaces support it.
CAD component separation does not establish a real manufacturing split or
attachment. In particular, distinguish a front rim from a mounting/carrier
plane: making them coplanar turns a projecting feature into a flat hole. Retain
the front profiles and make provisional reach and carrier inset explicit shared
controls. Keep missing collars, unseen inner walls and physical function unknown
rather than adding them for a finished appearance.

Check what geometric construction actually preserves. A ruled-surface operation
can introduce a profile approximation even when its input curves are analytic.
The local C17trial keeps its failed periodic-basis and full-profile checks; the
corrected revision3 uses an analytic ellipse extrusion with the same front
profiles, common reach and bounds. This is an actual geometry correction, not
permission to relax a failed numerical guard. Exact exported support, trim range,
front/back interfaces, retained faces, intersections and multiview appearance
need independent checks. Bounded reach is still a digital hypothesis. Exact
C17r3source/readback, analytic support/complete spans,145-point front/back
interface probes and21new/new plus1162new/retained intersection pairs pass their
stated numerical checks. Its173-face actual export remains open, with no solids.
Strict retained identity passes150/166; all16 differing supporting-surface and
3D-curve tables are equal and sampled boundary differences are below1e-9nominal,
but the trim/encoding failures remain unwaived. Comparisons use all173actual
exported faces, not old-body meshes substituted across those failures. The source
and exact-output evidence are retained in `native-c17-validation-290/`,
`native-c17-intersections-291/`, `native-c17-comparison-297/` and
`c17-retention-measurement-298/`.

These are recorded source interpretations and local component studies, not
completed rear reconstruction, calibrated depth, generic runtime qualification
or human acceptance. Keep the next whole-section correction focused on the
sculpted fascia, surround and deep lower recess rather than repeatedly polishing
the already isolated tubular features.

The subsequent C18 study constructs that missing visible rear section together:
one sculpted fascia, a tilted plate context, perimeter returns, an open lower
recess, three dividers and four rounded inset skins. Component labels describe
editable CAD regions, not verified manufacturing splits. Reuse a common depth
field and boundary equations for adjoining surfaces. For a piecewise bilinear
support, split a straight UV boundary at every knot; its lift within each span
is an exact quadratic curve. A valid individual face does not establish a
joined, correctly oriented or accurate assembly. Preserve and inspect native
interfaces and sections as well as the whole object.

Calculate conditional depth from complementary views when correspondences and
a declared camera hypothesis support it. Record the assumed feature planes,
camera freedoms, initialization sensitivity, parameter rank and original pixel
identities. Compare alternative geometric hypotheses before mistaking a flexible
camera fit for calibration. A withheld feature in the same previously inspected
image is a limited fitting check, not an independent photograph. Project each
paired observation into the second view, solve only the supported unknowns,
then retain residuals and ambiguous semantic matches. Do not force a poor match
to determine geometry. Fit a planar component as a plane when that is the
declared hypothesis; four independently solved depths need not be coplanar.

C18r1's exact exported plate corners improve mean agreement with four manually
paired closeup endpoints from 53.25 to 3.05 pixels under the same frozen camera.
Those endpoints helped construct the plate: this is training correspondence
agreement, not independent accuracy or verified physical depth. The full export
has 188 valid open faces and no solids; its 25 new faces pass the stated native
support/profile checks, and 4,375 new/new and new/retained candidate pairs yield
no extra interior section curves. Strict retained encoding still fails for
16 of 163 faces. Equal supporting-surface/3D-curve tables and finite boundary
agreement do not waive that failure. The actual six-view comparison retains
visible fascia faceting, lower-region disagreement and 124 unresolved side-view
depth ties; no old-body mesh is substituted to conceal them. Evidence is under
`20261020-roadster-goal/native-c18-validation-315/`,
`native-c18-intersections-319/`, `native-c18-comparison-318/`,
`c18-retention-measurement-320/` and `c18-plate-comparison-321/`.
This is a reusable documented method and an unaccepted local candidate; no
general runtime binding or accepted workflow instruction was changed.

The C19 correction identifies the four lower openings independently of the
upper tubes. Nearby repeated features do not establish a common pitch or
alignment. With unchanged image guides and cameras, the exact exported lower
opening centers reduce mean fitting error from 32.28 to 2.99 pixels in the rear
view and from 76.54 to 2.36 pixels in the closeup. All four guides helped construct
the correction. The two-view residuals, provisional weighting and controls at
their existing bounds remain explicit; these numbers do not establish physical
dimensions or independent accuracy. Raise or reshape adjacent floor, surround
and divider surfaces together, then inspect the whole region.

An intersection tool can introduce its own approximation. In C19, Boolean
sectioning returned a degree-one curve with thousands of poles near a roof
crease. Sparse samples appeared coincident with a divider boundary, but testing
every linear span exposed a 0.000173 nominal deviation, exceeding the unchanged
1e-5 numerical guard. That failed approximation remains evidence. For the
supported roof/divider surfaces, a separate check uses the actual native
nonrational degree-one surface controls: roof Y is independent of V and strictly
monotone across U, while each divider lies at constant Y. Their complete
untrimmed support intersection is therefore a calculable polyline. Bound each
entire span against an actual divider boundary; trimming can only reduce the
intersection. Do not generalize this proof to unsupported surface types or
relax a guard because sampled points look close. Explicitly handle equivalent
native single-span B-spline and source Bézier boundary representations.

Normals at a C0 crease are not unique. Compare the source and exact exported
surface on both sides with recorded parameter offsets, retaining the original
crease-query failure. Keep the normal and distance guards unchanged. These are
local numerical geometry checks, not physical tolerances or review grants.
The C19 evidence is in `native-c19-validation-338/`,
`native-c19-intersections-339/`, `native-c19-support-certification-339c/`,
`native-c19-orientation-343c/`, `native-c19-port-comparison-342/` and
`native-c19-comparison-341/`. The workflow/runtime remains unchanged.

### Calculate a visibility correction from the actual surface

When a visible feature remains blocked, identify the nearest native face on
sample rays before enlarging the opening or moving the feature. Keep the camera,
feature coordinates and original observations fixed. A valid Boolean result
does not establish the requested visibility. In the Roadster aperture study,
remaining occlusion was97/269 sample pixels after the first Boolean correction;
native rays named two ruled surround faces whose interiors still entered the
existing lamp cone. Analytic cone membership confirmed that this was actual
surface obstruction, not a rendering-mesh explanation.

For those particular cubic/linear surfaces, signed distances of the outer-rail
Bernstein controls to the cone-side plane decreased strictly across the interval.
The opposite rail lay on the existing lamp edge. This establishes a single
crossing parameter and permits a direct source-parameter trim without moving
the lamp, widening its target or inventing recess depth. The completed local
STEP had0/0 blocked pixel-center rays. This is a camera-dependent digital
aperture construction, not a general physical lamp design or global visibility
proof. Other surface types require their own supported calculation and checks.
Evidence: `20261020-roadster-goal/native-lamp-rays-56/`,
`aperture-remnant-57/`, `front-aperture-evaluation-58/` and
`native-lamp-rays-58/`.

Inspect the native source representation independently of its exchange-file
representation. A source Bézier surface may import from STEP as a B-spline.
Use explicit exact conversion for the supported type, retain degree, control,
weight and domain guards, and reject unrelated types. The local C08 constructor
was checked on both equivalent representations and produced166 identical
corrected face definitions after identity-root normalization. That local proof
does not substitute for the subsequent native exported-revision check. Evidence:
`20261020-roadster-goal/aperture-representations-65/report.json`.

### Separate surface fairness from preview tessellation

Inspect the exact exported surface before changing CAD to fix a faceted preview.
Record the mesher's actual absolute/relative setting, linear and angular controls,
kernel version and source hash. A parameter called tolerance does not establish
an absolute distance bound. In the installed CadQuery implementation,
`Shape.tessellate` invokes relative meshing. Earlier Roadster preview metadata
incorrectly described its 0.1 argument as an absolute nominal distance; preserve
those receipts and explicitly supersede that interpretation.

The C20 trial replaces three adjoining faces with a shared bounded polynomial
depth field. Derivative coefficient checks establish continuity at the new profile
joins; four inherited plan creases remain. Exact native tangent probes improve
from a maximum83.96 degrees to0.001695 degrees at the same eight locations.
This is not evidence of physically correct curvature or global surface fairness.

For this support, affine Y/Z coordinates permit independent surface evaluation
at each mesh vertex and triangle centroid. With the original relative preview,
the maximum sampled centroid displacement was12.025 nominal units. Explicit
absolute0.1 meshing reduced it to0.499, while vertices stayed within3.28e-9.
The residual still exceeds the requested meshing parameter: do not promote a
mesher setting to a verified global error bound. Measure the actual derivative
and inspect the image. This local remesh affects only fascia/surround previews;
other components retain their recorded relative meshes. The CAD is unchanged.

When a finer mesh exceeds a resource limit, partition its unchanged triangle
sequence into bounded batches, retain semantic component identity, and verify
complete ordered coverage. Do not relax the limit, drop inconvenient triangles,
weld boundaries, fill holes or mask discrepancies to improve appearance.

Closest-point solvers also need checks. A direct point on the source support,
with its parameter classified inside the actual trimmed face, can supply a
distance witness without relying on a failed minimizer. Keep the failed result,
unchanged numerical guards and finite-sampling scope. Such witnesses do not prove
whole-domain identity, physical dimensions or review acceptance.

Evidence: `c20-mesh-diagnosis-367/`, `native-c20-absolute-analysis-369/`,
`native-c20-absolute-comparison-370/`, `c20-mesh-diagnosis-371/`,
`native-c20-continuity-363/` and `native-c20-parametric-364/` in the local pilot.
These are reusable diagnostic methods, not a new runtime or provider binding.

### Check feature visibility beyond fitted centers

A feature can fit its image position while remaining hidden by another CAD
component. Identify the actual native occluder, then evaluate the visible feature
extent rather than just its center or small opening. Keep the source camera and
feature geometry fixed while testing a proposed occluder correction.

For the Roadster C21 trial, the inherited rounded surfaces are cubic meridians
revolved about a fixed axis. Their control rings bound the full surface. Under
a conditional camera with projection denominators of one sign, projecting that
convex envelope onto a constant-Y divider plane gives a conservative clearance
bound. Calculate the rational ring extrema rather than guessing a setback.
Restrict this argument to the validated geometry and camera assumptions; a
conservative envelope is not the observed silhouette or a physical measurement.

The resulting three divider setbacks remain inside the existing cavity depth.
Their native exported line boundaries are also convex subsets of the previous
divider domains. This removal cannot introduce a new intersection region, but
does not resolve pre-existing intersections or unrelated retained-face failures.
Recognize straight spline encodings through positive control weights and control
points lying on the endpoint segment; a different curve class alone is not
evidence of different geometry.

On the same6,132 native rounded-surface sample points, the old dividers obstruct
4,599 points and the C21 dividers obstruct zero. This is a divider-visibility
check, not all-body visibility, independent image accuracy or global acceptance.
Inspect the resulting whole region and preserve provisional shape/depth labels.
Evidence: `lower-feature-clearance-379/`, `native-c21-validation-390/`,
`native-c21-divider-subsets-391c/`, `native-c21-rays-392/` and
`native-c20-baseline-rays-395/` in the local pilot.

### Preserve semantic ownership with retained geometry

Retaining a face does not preserve its component meaning if a later assembly
puts every unchanged face into a generic body group. Keep the original component,
feature identity and evidence association alongside geometry identity. When that
association is missing, recover it from source construction and independently
matched boundaries before changing, hiding or deleting the face.

The C21 front inspection initially resembled a covered windshield and blocked
lamps. Exact native rays showed the lamps were unobstructed; diagnostic shading
made them dark. Four lower-windshield faces had instead been grouped as bodywork.
Their complete straight boundary supports matched the historical windshield
constructor, with vertex differences below7.1e-11 nominal units. A corrected
diagnostic grouping restores their meaning without altering geometry. This is
not evidence of physical glass properties or a native styling update.

Similarly, distinguish a construction seam from an intended crease using source
images and native derivatives. The retained hood has ten planar faces and two
bilinear faces; sampled join normals differ by as much as36.7 degrees. A fairing
attempt must preserve or explicitly revise its adjoining interfaces as a coupled
candidate. A successful kernel build alone is insufficient: the first filling
missed its unchanged1e-6 boundary guard, and a constrained height-field test found
incompatible gradients at a fixed rear-center perimeter kink. Keep both failures
and do not call a changed hypothesis a recovered physical surface.

Evidence: `native-c21-front-owners-402/`, `lower-windshield-association-403/`,
`native-c21-front-semantic-405/`, `native-c21-hood-seams-406/` and
`hood-gradient-feasibility-408/` in the local pilot. These findings require no
change to workflow execution, approvals, camera calibration or model routing.


### Refine surfaces while preserving complete interfaces

Use a small number of bounded parametric surfaces when construction patches
create unsupported creases. Preserve complete adjoining curves, including their
degree, parameter domains and orientation. Matching vertices alone does not
preserve a curved boundary. Topological edge direction can differ from the
underlying curve parameter direction; establish correspondence from evaluated
endpoints before transferring controls.

For supported polynomial surfaces, Bernstein control bounds can establish a
positive projected Jacobian throughout each span. Record the projection and
scope: this proves local regularity, not global nonintersection or physical
fidelity. Check full boundary coverage, intended sharp interfaces, intersection
curves, sections and source images separately. Preserve incompatible boundary
constraints explicitly instead of silently claiming global smoothness.

The local Roadster C22 experiment replaces twelve hood patches with two bicubic
surfaces. Actual native export controls, complete polygon-boundary coverage,
positive Jacobian bounds and sampled intersection checks pass their existing
numerical guards. The full assembly still has unresolved retained-face native
serialization differences. A subsequent local fender trial failed because it
substituted chords for curved edges; retaining the actual curves resolved the
flagged contacts in the corrected local trial. That correction is not yet a
qualified native export or a measured physical reconstruction.

Evidence: `native-c22-validation-440/`, `native-c22-polynomial-443/`,
`native-c22-intersections-444/`, `exact-perimeters-453b/`,
`c23-exact-curves-local-454d/`, `c23-exact-regularity-455/` and
`c23-exact-intersections-456/` in the local pilot. These are reusable method
findings, not a new executor, accepted workflow instruction revision or automatic
engineering approval. The common workflow still begins with simple input and
evidence reuse; detailed checks belong to the relevant modeling/validation step.


### Find missing visible components before further surface refinement

After projecting the exact exported assembly, check both residuals and geometry
coverage at important visible features. A dark region can be an open recess,
an absent component, occlusion or a material difference. Record the distinction
before adding a backing surface. Group the visible lip, corner pieces and moving
panels separately when the source supports those boundaries. Reuse the supplied
images; investigate only the newly identified gap.

Derive curves from complementary views under recorded camera hypotheses. Keep
silhouette, highlight and physical edge observations distinct. A curve calculated
from two views can be projected into an unused view as a cross-check; this does
not establish calibrated depth when cameras or feature correspondence are
uncertain. Preserve alternative observations and the failed fit. Change local
curve resolution within a declared bound before considering any change to image
interpretation bands. A failed optimizer is not, by itself, proof that the data
or requirements conflict.

For polynomial B-splines and positive perspective depth, image-band inequalities
can be converted into polynomial inequalities. Subdivide at both spline knots
and observation-interpolation breaks; Bernstein coefficient bounds then cover
each complete interval. Record numerical margins and limitations. This bounds
the selected interpolated observations, not the true photographed edge, hidden
geometry, physical tolerances or camera error. Retain an editable reference
curve separately until its proposed surface and feature correspondence have
been checked.

Local 23 October continuation: the corrected C23 native export now has verified
curved boundary controls, positive local Jacobian bounds and no sampled interior
intersection curves with retained faces. Twelve retained native serializations
remain unresolved. A coverage check identified a missing lower-front component.
The first 27-control curve fit failed; bounded refinement produced a 51-control
curve, then complete interval constraints kept the original 3 px top / 4 px front
bands. Existing side imagery is a cross-check with unresolved feature/depth
ambiguity. This is a local reference curve, not a native panel or physical
reconstruction acceptance.

Evidence in the local pilot: native-c23-validation-473, boundary-controls-475,
regularity-476, intersections-477, native-c23-seams-482b,
native-c23-lower-front-479, front-lower-evidence-481,
front-lip-constrained-fit-484 (failed), front-lip-adaptive-fit-485 and
front-lip-continuous-bounds-486. The observation and fit work ran independently
of exact native continuity analysis. Use one native design writer and exact
revision-bound integration. These are descriptive method findings; no runtime,
accepted instruction, model policy or user interface was changed.


### Compare the same feature, then inspect the complete assembly

Label a proposed observation as a silhouette, part boundary, join, highlight or
occlusion edge before interpreting a residual. Test alternative correspondences
explicitly when the identity is uncertain. Comparing a CAD skin bottom against
a photographed upper highlight can suggest a misleading height correction.
Record where a selected near-side branch is absent; do not extrapolate it from
the far side or relabel a missing correspondence as a successful measurement.

Use exact exported geometry for multi-view checks. Visible-component coverage,
source-trace residual, tool success, unchanged geometry, support regularity and
physical fidelity are different checks. A region can gain coverage while still
having incorrect depth. A new front component can become visible through an
unfinished open rear/underside. Keep those results visible and preserve the
candidate; adding unobserved backing or suppressing backfaces to hide the issue
does not validate the assembly. Continue independent observed regions when one
depth correspondence remains uncertain.

The local C24 native trial adds a separate lip and two corner skins to the C23
assembly. Its exact STEP has173validopenfaces and three checked nonrational ruled
surfaces; no sampled interior section crossings.158of170retained serializations
match strictly;12remain unresolved. Selected source-band coverage increases from
zero to49of49corner samples and176of200lip samples. The unused side view exposes
uncertain highlight/edge correspondence and a missing near-side branch in part
of the requested range. The rear diagnostic shows front geometry through the
unfinished open assembly. These findings prevent a whole-vehicle accuracy or
acceptance claim despite successful native build/export and regional checks.

Local evidence: native-c24-validation-506, native-c24-controls-510,
native-c24-intersections-509, native-c24-view-measurements-512,
native-c24-side-correspondence-511b and native-c24-ownership-513. The failed
branch expectation511, failed dense lip check491 and rejected floor-reflection
trace489 remain available. These descriptive methods use the existing source
runtime and independent SteveCAD provider; they add no executor, UI or model
policy. Keep the general workflow input simple and reuse the evidence package.


### Reconstruct coupled interfaces and check the actual surface

When a photo-supported interface changes, identify every incident face and
shared curve before moving geometry. A face may be trimmed inside its support:
UV bounding-box corners do not necessarily correspond to its actual vertices.
Do not silently omit unsupported neighbors or treat a trimmed face as a full
rectangle. Preserve fixed outside boundaries and represent the modified shared
curves once. Keep high-level shared-vertex parameters editable when compiling
them into the native CAD source.

Check points against the underlying surface as well as the supplied face edges.
A face can contain the requested 3D edge while its fitted support misses the
edge between constrained samples. Tool-reported error, face validity and edge
distance alone do not establish this requirement. Preserve failed fits and use
an independently checked construction while retaining the numerical guard.

The local C26 plate trial reported small constrained errors but independently
missed a boundary by0.000870nominal, exceeding the unchanged1e-6guard. An
overly dense fit was stopped as an owned local computation; all inputs and
partial evidence remain. Algebraic shared-edge Coons construction, with shape-
preserving degree elevation where needed, passed independent support samples
below4.51e-10nominal. The tested API requires at least four poles in each
direction for Coons style; see the [exact OCCT7.9.3 source](https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/V7_9_3/src/GeomFill/GeomFill_BSplineCurves.cxx).

Full-scene visibility matters after the geometry check. The local fourteen-face
C26 junction trial improves its162-column frontal visible transition from
19.62px mean error to0.80px, but worsens the newly measured changed side-profile
region from4.09px to6.28px. The older28-column side check ended at the edge of
this region and cannot establish that the correction preserves the side view.
Keep the tradeoff visible and investigate component/trim identity, geometry and
camera assumptions before promotion. A proposed missing trim component is a
hypothesis requiring evidence, not permission to hide a mismatch.

C25 native correction, by contrast, is independently exported and checked:
0.415/0.476px mean full-trace residuals within the original4px image bands,
197of200selected lip rays covered and49of49corner rays. Twelve strict retention
differences and whole-vehicle uncertainties remain. These are regional visual
checks under conditional cameras, not physical tolerances or acceptance.

Local evidence: native-c25-validation-533, controls-536, intersections-537,
traces-545, current-canopy-audit-529, hood-glass-junction-541/542,
c26-junction-network-543, failed/partial trials546/546b/546c, checked algebraic
trial546d, independent support549d, visible junction551 and side profile554.
C26 source553b is staged only and held pending the side-view assessment.
These descriptive findings preserve the simple input/evidence-reuse journey;
they do not add a process executor, UI or behavioral model policy.


### Separate feature identity and test cross-view feasibility before more CAD

Reuse the evidence package supplied with the initial prompt. When a small region
does not agree across images, distinguish its physical/component hypothesis,
feature boundary, visible state and camera assumptions before adding patches.
A bright outer pillar surround and the dark windshield trim are different
features. A broad strongest-gradient search can select a nearby side-window edge;
retain that failed interpretation and make the component search region explicit.

Propagate the existing interpretation bands through the camera equations. For a
fixed nominal cross-section and an orthographic side camera, its image-height
band bounds Z. In a fixed front perspective camera the denominator is constant
at that X. On each observed piecewise-linear stripe interval, Y is affine in Z;
evaluate interval endpoints to obtain exact conditional extrema. Project these
extrema into the unused top view before another geometry fit. Preserve missing
intervals and configuration/correspondence/camera uncertainty. A conflict under
these assumptions calls for investigating those assumptions; it does not prove
the vehicle or images are impossible, or justify wider physical tolerances.

C27 is a real separately saved/exported native trial:14coupled junction faces
and2pillar skins,31helper sources,175validopenfaces. Exact STEP/source/control
and underlying-support checks pass the unchanged1e-6numerical guard; no sampled
interior section crossings. All175nativefaces participate in four view rasters.
Frontal162column visible-junction mean19.62->0.80px and changed47column side
mean4.09->0.81px improve, but the side maximum5px and3missing frontal columns
remain. The pillar's purported outer curve lies inward in the top projection,
averaging6.02/10.04px from the proposed P/N source trim. Original four-pixel
front/side bands still conflict with the top band in21of23N fixed-X sections
(maximum remaining gap2.64px); P is conditionally feasible. Hold promotion.

This remains local research, not a registered provider, generic runtime binding,
accepted workflow instruction update, physical calibration or human acceptance.
All12strict retained encoding differences remain unresolved. C25 stays the prior
continuation reference; C27 and all failed trials remain editable/preserved.
Evidence: observations558,local skins559,component trim569,exact native577,
support580,all-native views581,intersections582,interval analysis583 and native
measurements584. Broad-gradient568 is retained but superseded for this feature.


### Reconstruct shared landmarks before fitting more surfaces

A camera fit to a provisional CAD corner is useful only when that corner denotes
the same observed feature. A surface's parametric corner need not be the photo's
hood-to-cowl junction. Keep old CAD as an editable candidate and numerical seed,
not dimensional or semantic truth. If camera-only fitting fails, inspect source
feature identity before adding camera freedoms or moving more surface patches.

Track the same endpoint branch on both sides. A nominally triangular lamp can
have a short terminal edge. A broad subpixel-corner window can select its outer
end on one side and inner end on the other. Even a small residual joint fit can
hide that mismatch. Use source-only connected edge tracing and explicit component
review; preserve the wrong branch and create a visible new observation revision.
Keep search-window size distinct from the unchanged interpretation/acceptance band.

The local front study uses four mirrored landmark families and jointly solves
their geometry plus two perspective cameras against24image observations in
three original views. The top XY mapping and one nominal height are explicit
coordinate gauges, not calibrated dimensions. Fixed principal points, symmetry,
bounded coordinate changes, all residuals and all finite optimization starts are
recorded. Jacobian rank does not establish global uniqueness or physical truth.

After the terminal-identity correction, all24observations lie within4px
(maximum2.731px), no parameter is at its bound, and two simple quadratic shared
curves match all442separately traced elevated-view source points within4px
(maximum1.641/2.125px). Those path points were not used to fit landmarks or
construct the quadratics, but are from the same source image; this is not blinded
calibration. One frontalNcurve sample remains4.164px and is not rounded to a pass.
The earlier degree5control correction was unnecessary after fixing identity.

Use the calculated curves as a foundation for a coherent surface/network model;
do not replace the full car or declare an accurate vehicle from a sparse frame.
Curve-only outputs need an appropriate representation. In the actual native
SteveCAD Component.add test, open edges are rejected as producing no solid or
surface body. Editable source was saved, but no native export exists. The local
CadQuery STEP contains2verified open quadratic edges,0faces,0solids. Do not add
unsupported thickness/ribbons solely to pass a capability check, or generalize
this result to every native curve/sketch API. Completed Wright transport runs
and failed provider builds remain separate facts.

Evidence: body correspondences587, failed camera family588b, image tracks590,
mixed-tip fit591 and curves592/593b, source-only paths594, terminal branch
correction595, revised reconstruction596, curves597, withheld-path check598,
editable reference599/C28r2, native failures602/605 and local STEP validation606.
All earlier candidates/cameras/profiles and failed hypotheses remain preserved.
This method is a local descriptive qualification, not a new provider/executor,
general runtime binding, saved workflow policy update or physical acceptance.


### Carry the calculated framework into one coherent surface

Use observable cross-curves and shared longitudinal curves before inferring the
surface interior. Keep feature identity explicit: the lower bright front rim is
a visual boundary, not proof of a physical hood/LED manufacturing split. Preserve
source-only low-contrast observations separately; a quality rule declared before
fitting is different from deleting points that disagree with the model.

The C29 study calculates front/rear quadratic cross-curves from paired original
image profiles, extends its original quadratic sides by a bounded calculated
parameter, and creates one biquadratic Coons skin with nine controls. Five named
cross-curve parameters remain editable. Complete boundary controls and independent
support projections are checked against the actual native STEP. Positive native
Bernstein derivative/Jacobian bounds establish regularity across the parameter
rectangle. Surface interior/crown remain inferred; a smooth valid surface is not
independent physical shape or a verified join to the rest of the vehicle.

Native C29r1 succeeds where the edge-only C28 Component.add reference did not:
it is an actual source-supported surface, not an invented ribbon/body. The exact
native export has one valid open face and zero solids. All1064qualified paired
cross-profile samples pass4px;seven low-contrast source observations remain
uncertain. The442unused elevated-view connected-edge points also pass. One
frontal side-curve sample remains4.164px. Held-out top front-envelope error is
6.22pxmean/7.63pxmax;39of43historical side-envelope columns disagree. Keep these
findings; do not equate paired-view fitting with full-vehicle acceptance.

The reconstructed height gauge used an observed hood junction; old CAD corners
were different features. Historical side-camera absolute placement has not been
independently rebound to that gauge. Investigate global poses/feature correspondence
with independent landmarks before silently carrying old camera translations into
a new reconstruction. Preserve all old cameras and runs. A bounded numerical
correction that finds no feasible point is not a proof of mathematical infeasibility.

Local attempts625/625b keep cameras/source fixed and change only four bounded
parameters. Neither found an admissible correction;the original4px recheck still
missed top containment by0.882px. No failed proposal was submitted to SteveCAD.
C29r1 remains a separate regional study while global poses and adjoining regions
are unresolved. Evidence609-625b and exact export619 remain preserved. This adds
descriptive method evidence,not another executor/provider or workflow policy.


### Source intersections, conditional cameras and bounded tangent corrections

Determine feature junctions from original pixels before using them as CAD
constraints. In the cowl study, intersecting a source-only dark panel-line fit
with the glass boundary corrected an unrefined manual endpoint by about ten
pixels. Preserve the old pick and its provenance. Assign observations to the
central cowl or adjoining glass/fender using those source junctions; retain all
outboard and uncertain points rather than deleting high residuals.

Additional anchors justify an explicit camera revision, with historical cameras
preserved and all affected exact-artifact checks repeated. A fit within a pixel
band does not establish camera calibration. Revision632 fits all30point anchors
within3.30px but reaches its declared camera-distance bound. A leave-one-cowl-view
out test651 misses withheld frontal endpoints by5.565px despite using the same
fixed framework. Its bound-scaled Jacobian condition number is about1102. These
are conditional sensitivity findings, not physical uncertainty or proof of a
unique reconstruction. Acquire independent anchors before whole-vehicle promotion.

C30's exact native hood/cowl export preserves the previous hood's strict face
serialization and shares the complete boundary controls. All439rear-cowl and
251side-edge samples pass the original4pxband. The normal mismatch still reaches
1.51degrees. A separate cubic cowl hypothesis653 retains both cross-curves and
the middle section and sets its front derivative to a positive constant multiple
of the retained hood derivative. This gives a complete polynomial tangent-plane
identity by construction; it is an inferred fairing choice, not measured physical
continuity. Keep G0, tangent alignment, curvature continuity and manufacturing
seams distinct.

Do not widen a movement limit just because a coarse control-hull bound fails.
For this unchanged proposal, delta(u,v)=3u(1-u)(1-2u)D(v). The scalar's exact
absolute maximum is sqrt(3)/6; convex control bounds on D(v) certify the entire
surface moves no more than0.924nominal units, within the original2unit limit.
All251existing side-edge checks also pass. This analytic certificate supports a
native trial; it does not substitute for native export and independent validation.

The first C31 save and one read-only reconciliation both timed out after the
isolated services were restored. Preserve the uncertain remote mutation outcome;
do not replay it. Reconnect through the existing registry/OAuth mechanism, then
search and verify saved source before another write. No new executor, provider,
model policy, accepted workflow revision or generic runtime qualification follows
from this descriptive method evidence.


### Qualify curvature continuity without sacrificing source bounds

Matching tangent planes alone does not establish a fair curvature transition.
The C31 local STEP trial removed the normal-angle mismatch but increased the
normal-curvature jump; preserve that adverse result. A first quartic proposal
matched both derivative orders while retaining cross-boundaries and its middle
section, but exceeded the original movement limit and was not submitted as a
standalone native candidate.

The C33 study adds one quintic bubble q(u)=u^3(1-u)(u-1/2). It vanishes at the
front through second order, at the rear, and at the middle section. Calculate
its quadratic transverse control coefficients by the exact integrated squared
displacement minimum using Bernstein-product integrals. This is a calculated
fairing hypothesis with no extra image-residual fitting. Use the lowest bounded
complexity that meets the declared checks; do not add unconstrained patches.

Positive constant derivative scaling preserves a complete second-order boundary
jet against the retained hood. Verify the actual native STEP's complete surface
and edge controls, knot/trim domains and support. Positive full-domain Bernstein
Jacobian bounds establish regularity. Subdivision control-hull bounds certify
movement over the whole surface, rather than accepting a sampled maximum.

C33 revision1 native evidence679 establishes the two open surfaces, retained
hood strict identity and first/second derivative identities within the unchanged
1e-6 numerical guard. The whole-surface displacement bound is1.722nominal units,
under the original2unit authoring bound. All439rear-cowl and251side-edge source
observations pass the original4pxband using unchanged cameras/observations682.
Four exact-native projections681 and continuity plot683 are retained. The hood's
existing one4.1535pxedge miss, source uncertainties and global pose/scale issues
are not waived. A mathematically smooth join does not establish a physical seam,
actual curvature, manufacturing quality or whole-vehicle acceptance.

This extends descriptive method evidence only. The accepted workflow, shared
executor and provider implementations remain unchanged; runtime_consumed=false.


### Reconstruct a complete glazing envelope from identified source boundaries

Begin with existing photographs and component/feature ownership. A bright rail,
black border, adjacent window seam and rounded corner can describe different
features. Preserve source-only traces and uncertain picks before fitting. A
virtual intersection of fitted image edges is a construction anchor, not proof
of a physical sharp corner. Keep fixed bodywork separate from moving panels.

Additional source anchors can justify a separate camera hypothesis. Preserve
historical cameras, retain the original parameter bounds, and revalidate all
previously passing exact-artifact observations before using the new poses.
The C35 hypothesis696 fits 40 body/cowl/roof/glass anchors within 3.394 pixels;
both camera-distance bounds remain active. All 2,389 previously passing hood/cowl
observations still pass. The old hood miss is now 4.256 pixels and is not waived.
An uncalibrated side camera is diagnostic, not authority to reshape the surface.

Prefer the lowest bounded curve family that meets every qualified observation.
A least-squares minimum can still fail the pointwise band. The glazing study
retained failed quadratic proposals and used a bounded cubic for the side rails;
lower glass wings remain straight. Source branch correction703 precedes 3D fitting
and retains the earlier traces. No point is discarded because of a CAD residual.

A bounded six-edge filling trial700 produced a valid face but failed the unchanged
1e-6 numerical boundary-support guard. It was not submitted or promoted by widening
that guard. C35 instead constructs three exact polynomial spans: a central Coons
surface and two wings with calculated shared curves and positive-scaled tangent
jets. These spans are construction subdivisions of one glazing component, not
observed physical panel seams. Interior curvature remains a hypothesis.

Validate the actual saved native export: full surface/edge controls, trim/support,
positive full-domain Jacobian and coordinate bounds, shared boundary identities,
tangent jets, independent sections and strict identity of retained faces. C35r1
native718 has five valid open faces, zero solids and both C33 faces unchanged.
All 2,537 new source boundary observations pass the original four-pixel band719.
The internal glazing joins pass G1; a measured numerical curvature jump remains
and G2 is not established. Four regional native projections721 were inspected.
They do not establish physical scale, optical material, configuration, whole-car
accuracy or an independently calibrated side view.

This records reusable authoring/verification evidence. It does not register an
executor, provider, accepted workflow or generic runtime capability. The existing
method inventory remains descriptive, with runtime_consumed=false. Reuse the
accepted process, existing runtime/validator/results/storage and independent CAD
provider when integrating a qualified method into a future workflow revision.


### Correct coupled camera and geometry assumptions, then verify exact outputs

An image mismatch can depend jointly on geometry and an uncalibrated camera.
Inspect the original feature first. Source727 confirms that the top-front
discrepancy reaches the visible outline; do not waive it as a material seam.
Finite camera-only and geometry-only attempts728/729/731 failed their original
bands. A conservative center-region ray-box LP730b did not prove incompatibility;
retain this negative finding rather than declaring the references inconsistent.

The next family733 explicitly couples four previously bounded hood parameters
with a provisional orthographic top camera. The existing u-scale/u-offset/pitch
bounds remain; the previously uncalibrated v-axis receives independently declared
counterpart bounds of +/-2% scale and +/-10 pixels. Keep the 4px source bands,
all observations, original geometry bounds, failed families and old cameras.
Correcting a coordinate hypothesis is not a physical calibration or an increase
in engineering tolerance. The top-containment observations become fitting inputs.

Solver success is only a proposal. Reconstruct independently, recalculate dependent
hood/cowl first and second derivative jets and retain the original complete cowl
movement bound of2nominal units. Recheck every original observation, including
withheld connected paths. Read each source profile's declared independent axis;
inferring it from a view name can create false failures. Preserve observer errors
separately from geometry/provider failures and correct the observer explicitly.

C36r1 native743/744 retains all three C35 glazing faces by strict serialization;
both corrected hood/cowl faces have complete control/edge/trim/support/regularity
checks. All4,927source observations and54one-sided top-containment checks pass4px.
The old hood4.256pxmiss is corrected. Maximum top-front overrun decreases from
7.6275px to4.0000px. Native G2 jets pass1e-6 and complete cowl displacement is
bounded by1.8165nominal, under2. Four exact-native projections745 are retained.
The side camera, physical scale/configuration, glass G2, inferred interiors and
whole-car fidelity remain unverified. A passing regional reconstruction is not
whole-vehicle acceptance.

These are descriptive reusable method findings, not a new executor/provider or
accepted workflow capability. runtime_consumed=false. Integrate qualified methods
through a visible workflow revision and existing evidence/validation owners.


### Check full-assembly context and condition source measurements by feature

Regional success does not establish compatibility with an older full model.
Compose actual native parts locally and show all relevant regions with true
depth before promoting the assembly. Trial749 contains166C25faces plus5C36faces;
its roof/side/fender joins remain held. The local STEP has171valid open faces,
but0/171strict serialization matches on re-export. This does not prove geometric
change or a provider defect; it also cannot establish strict retention. Preserve
the native inputs and report exchange, identity and interface findings separately.
Image750rear I19 shows raised doors/airfoil; only fixed rear regions can be
compared with a closed-body candidate. Record component state per reference.

A faint internal seam need not block reconstruction of a clearly observed outer
envelope. Source751-753traces the complete roof/rear-glazing outer boundary and
rear-window end in two existing views. Do not turn an unobserved roof seam or a
highlight into a measured panel boundary. Preserve sharp virtual intersections
separately from unknown physical corner rounding and glass/frame ownership.

Inspect source features at original-pixel scale. Near a horizontal boundary,
horizontal scans can latch onto a competing highlight and impose a poorly
conditioned error metric. Zoom757revealed that failure after curve/camera
attempts754-756were held. Source758replaces the whole I18v<440domain using
vertical gradients and explicit contact with dark glass. It preserves all48old
observations and their provenance, including formerly passing ones. This is a
source-quality revision before acceptance, not deletion by CAD residual. The
original4pxobservation band remains; consume each profile's declared axis.

Corrected quintic curves759fit all1,701new boundary observations and4virtual
corners without changing C36or cameras733/696. A negative derivative Bernstein
coefficient alone does not prove a fold: full-domain subdivision proves positive
Xderivatives. Use complete surface Jacobian/coordinate bounds, exact native
controls/edges/trims/support and independent sections for the resulting canopy.

Continue the existing front crown/jet with an explicit fairing hypothesis that
follows observed outer rails and decays toward the observed rear cross-boundary.
For Dwing=lambda*Dcenter+mu*Gprime and a positive longitudinal rescaling s at a
front where mu=0, transport lambda_prime with s but keep mu_prime unchanged:
Gnew_prime already contains s. The failed local formula760is preserved761;
corrected762passes full coefficient and section checks. These are calculated
interior/tangent conditions, not measured physical curvature.

C38r1 exact native771/772has8valid open faces, all5C36faces strictly unchanged,
and3new calculated upper-canopy spans in one component. Front/internal G1jets,
complete regularity and sections pass1e-6. All1,701new profile checks pass4px;
the4,927original checks and54topcontainment checks inherit exact face identity
with unchanged cameras. G2ofnew joins, physical scale/configuration, inferred
interiors, internal panel seams, side-camera calibration and whole-body integration
remain unverified. The full-frame comparisons774 expose those remaining limits.

This adds descriptive method evidence only. No accepted workflow, shared runner,
provider protocol or model policy changes; runtime_consumed=false. Future method
integration uses a visible workflow revision and existing validator/evidence owners.


### Check image feature identity and camera algebra before expanding curve families

Keep measured image observations separate from AI construction guides. The
side-window tips in779were explicitly manual, unqualified guides. Diagnostic785
can place mirrored points within1.80px of those guides, but this does not establish
physical sharp corners, correct glass/rubber ownership or corner rounding.
In795the guide errors remain visible without making them measured requirements;
all actual profile observations,4pxbands and endpoint authoring bounds remain.
The result still fails and is not promoted. Never remove a user requirement
under the label of an assumption revision.

Distinguish the upper-canopy edge, side-window roof edge and lower beltline.
Review originals at pixel scale; a white rail, dark rubber strip, glass reflection
and shaded body can produce several strong nearby gradients.777/781/788/789
show that ambiguity. Source782re-extracts entire affected features by bronze/gray
color ownership;790corrects a shaded corridor that followed the inner rail;
793uses original-RGB bronze-to-blue contact to avoid a later body-intensity
highlight. All prior points, including passing ones, remain nested/preserved.
Display gain is for inspection only; measurements use original RGB values.
Weak contact, ROI-boundary and neighbor-branch failures remain uncertain. Such
extractor rules are source-specific qualifications, not universal material rules.

Apply cheap camera/source identities before running increasingly complex fits.
For the recorded I02orthographic R, mirrored points have the sameu and exactly
vP+vN=1990.510129166978. Therefore paired observations differing by more than8px
from that sum cannot both meet the original4pxband under that camera/symmetry
hypothesis.786finds27incompatible roof-edge pairs among370, with a necessary
band of6.75506px at the worst pair; all473beltline pairs are compatible. This
is an algebraic finding about the recorded hypotheses, not proof of source or
provider fault. Keep the observations and revise feature/camera/configuration
hypotheses; do not increase the acceptance tolerance or delete by CAD residual.

Finite cubic-through-degree7fits and diagnostic minimax studies779-795remain
held. Added slack measures failure only; it never becomes an acceptance band.
Higher degree alone cannot repair the786contradiction. Local camera trials798,
800and801keep actual C38geometry fixed, recheck3,578I18profile observations at
10,001samples and16source anchors, and preserve the other cameras. The explicit
new hypothesis allows focal scales±2percent and principal points±10px while
holding pose fixed.801also doubles an arbitrary interior-control search box
after800hits six authoring bounds; physical requirements and4pxbands stay fixed.
Its best maximum new-profile error is4.348035px, so it remains held. No proposed
camera is adopted and no historical run is rewritten.

Check an observer against the unchanged accepted artifact before optimizing.
Coarse2,001sample observers796/797report one old error4.00000474px while the
original10,001sample check passes.798uses the original density and all3,578old
checks pass. Merely loading the declared703axes did not fix that undersampling.
802refuses an optimizer seed that misses a numerical safety guard.803starts
from the original camera and performs45bounded sensitivity/linear-programming
iterations with nonlinear rechecks. All old observations/anchors stay within4px,
but new profiles still reach4.352806px; this is not a successful correction.
Stop repeating the same finite families. Next inspect wider pose and independent
side-view correspondences with all affected exact-native checks retained.

This is descriptive method evidence only, runtime_consumed=false. It adds no
shared runner, provider protocol, accepted workflow, UI or model-policy behavior.
Any future accepted process revision must use the existing evidence/validator
owners and distinguish measured inputs, inferred construction and held proposals.


### Verify a complete assembly before polishing regional fits

A saved native whole-vehicle study can expose problems a regional projection
cannot. C39 revision 1 combines 164 retained C25 exterior faces with the eight
C38 front/canopy faces and removes nine superseded old faces. Its actual full
build and STEP export contain 172 valid open faces and zero solids. All prior
models and files remain intact. This is an integrated study, not engineering
acceptance, a closed body, or proof of improved whole-vehicle accuracy.

Read large source packages completely. C39 has 39 helpers (27 old C25 plus 12
C38), not the initially hardcoded report counter of 38. Preserve that clerical
report and its correction. SteveCAD read_design paginates large answers; page
parts use indexed paths and value/text fragments. Assemble complete, ordered
fragments and compare all source bytes at one document revision. The initial
read had model=null while a preview was running; later reads had the completed
preview model id and a different page count. That was a model-state change, not
evidence of missing source or a reproducible paging defect. All 39 helpers and
main source match; the actual full build/export has its own separately verified
identity. Never treat an incomplete first page as complete readback or rewrite
a design to recover apparently missing files.

Actual native retention814 finds all eight C38 faces strictly unchanged and
152/164 C25 faces strictly unchanged. Twelve native serializations still differ.
815 measures all twelve: boundary samples are within 9.66e-10 nominal and eleven
surface supports have a complete parameter/control comparison. One extrusion
support remains outside that comparison. These facts do not turn finite samples
into strict trimmed-face identity. Keep the twelve differences and older
preservation history visible; all prior artifacts remain unmodified.

Compare the complete exact output with all competing geometry present. The five
817 views use actual native faces, absolute 0.1 nominal meshing, lossless bounded
triangle batches and the existing depth/ownership raster. CAD-only images avoid
mistaking photographic wheels visible through an overlay for wheel geometry.
Four views have zero unresolved depth ties. The unbound I15 side diagnostic has
149 ties, the same count as C25; that does not establish identical tied pixels.
I19 has raised doors/airfoil, so only its fixed rear context can be compared with
the closed/stowed model. No geometry masks or artificial backing hide failures.

Regional evidence is not whole-assembly visibility evidence. In the I15 opaque
diagnostic, the new upper canopy projects to 7,562 pixels but owns only 73; the
legacy body hides most of it.818 compares native side-glass and new canopy outer
curves at matched longitudinal stations and finds separations up to 215.151
nominal, predominantly a rear height mismatch. The two edges have a real white
frame between them; their distance alone is not a seam tolerance or evidence
they must coincide. The large ordering/height discrepancy still demands joint
registration and component correction before adding a bridge. A zero minimum
face distance elsewhere can be an intersection, not a complete common edge.

806 broadens the I18 pose within the original 596 bounds while retaining all
affected old checks. It reaches its finite iteration limit, misses one old
profile and does not pass the new beltline bands. No new camera is adopted.
The larger assembly failure now takes priority over more subpixel local fitting.
Register common component landmarks and configuration across side, top, front
and rear views. Preserve earlier candidates as history; do not mistake that
requirement for a mandate to freeze every proposed coordinate in all future
versions. A corrected new version may revise parts/cameras, with all affected
requirements and exact-output checks repeated. Historical CAD remains a seed,
not dimensional truth. Physical scale, configuration, source authenticity and
interior shape remain explicitly unverified.

This is descriptive research evidence only, runtime_consumed=false. It does not
claim new accepted workflow/runtime/UI/provider or model-policy capability.
Future workflow integration uses the existing source, run, evidence, validation
and review owners, with a visible new revision and the user's simple input flow.

### Diagnose visible geometry with exact STEP rays before adding more surfaces

An engineer supplies text, images or existing data; preparation reuses the
evidence package, identifies components/configurations and researches remaining
gaps. At comparison time, a recorded camera and explicit source pixels can ask
which **actual exported face** is visible. This complements projected meshes;
it does not fit cameras or decide whether a feature is physically accurate.

The optional local helper
`examples/reverse-engineering-research/inspect_step_rays.py` reads open STEP
through existing CadQuery/OCCT and reuses the existing projection camera
contract. It requires the expected STEP hash, an explicit unit label/basis,
camera JSON and pixel-list JSON. It returns all trimmed-face intersections,
revision-specific face indices, nearest-depth ties, coordinates, camera depths,
input hashes and runtime identity. It refuses stale hashes, invalid cameras,
out-of-frame/nonfinite pixels and overwriting evidence. Numerical intersection
guards are separate from engineering tolerances. Missing dependencies hold this
optional inspection; a mesh result must not be relabelled as exact STEP evidence.

This is a read-only engineering observer, not another executor, provider adapter,
workflow verdict or UI. Existing Wright source/run/artifact/validator owners must
bind it in any future accepted workflow revision. Vendor operations remain with
the independent provider. A model, export, camera, source registration, pixel
selection or unit-basis change invalidates affected measurements. Portable reuse
requires those dependencies and source provenance; it transfers no credentials,
live runs or review authority. Existing common views remain usable.

The actual C39/C40 exports provide a useful correction example. Original-source
review and 50 exact top-view rays identify two superseded legacy rear-canopy
sheets. C40 removes those two sheets from editable CAD, preserving the previous
model and all39helpers. All50 rays then hit the new canopy first, versus25
occluded in C39. On unchanged camera/crop/source, canopy-owned pixels in the
reviewed top-view region increase from11,739 to23,023 of24,661. This finite
conditional-camera visibility improvement is not a physical accuracy claim.
All8C38faces remain strictly unchanged;158/170retained C39serializations in total
match strictly. Twelve differ; complete surface-support comparisons and boundary
samples below9.66e-10nominal do not establish strict trimmed-face identity.

The generic helper reproduces all100 C39/C40 rays and independently measures the
existing pocket-defect fixture: floor depths0.5 and2mm in both orthographic and
perspective views, with unchanged original policy. This is a substantially
different existing digital case, but remains synthetic local observer proof;
it does not establish a new native provider correction or shared runtime path.
Analytic plane, miss, near/far, stale-hash, reflected-camera and evidence-preserving
CLI controls supplement those actual retained artifacts.

Interpret source anatomy before treating every occlusion or edge separation as
failure. Original side evidence shows rear glass below surrounding white body;
818side-view occlusion and same-X separation alone do not prove an invalid seam.
825/826top-view rays/source review identify the specific duplicate geometry.
Likewise,822paired-rim local-optimum agreement is not camera identification:
824fixed focal hypotheses1000..30000px all satisfy the same16original3pxrim
observations. Additional824bside evidence rejects the held801/806tip proposals;
the old tip also misses its original8pxband. No new camera or tip is adopted.

Local pilot evidence: `c40-correction-summary-838/report.json`,
`step-ray-generality-841/report.json`, `step-ray-tests-842/test-output.txt`,
`native-c40-rear-detail-843/report.json` and
`c40-glazing-intersections-844/report.json`. Research inventory remains
`runtime_consumed=false`; implementation of this optional helper is not a claim
that every listed research method or an accepted generic workflow is qualified.

Final observer qualification848/849 retains every independently imported STEP
root, rather than relying on the first object. A two-root/two-solid control
checks hits on both parts. All28focused tests pass; both retained Roadster
exports and the different pocket case are rechecked after this observer change.
846/847also hold a local four-face ruled framing proposal: valid CAD incidence
does not establish the observed white frame, and projected bands cross glazing
regions. Preserve failed hypotheses and reconstruct component boundaries before
saving additional native geometry. No frame proposal was adopted.

### Test reference consistency before spending more CAD iterations

Given text/images/data, preparation should first reuse the evidence and identify
the object, component, feature and configuration. When reconstruction uses
multiple views, test whether the declared camera and feature hypotheses can
support the original image bands. A gradient is not automatically a physical
edge, and two-view agreement used to construct geometry is not independent
validation. Keep the user input simple; the workflow produces these records.

851calculates source-curve/ray intersections without a CAD seed or polynomial
curve. Missing intersections and multiple solutions are retained.852propagates
the original4pxfront-profile band along each exact top-view ray using
positive-depth projective inequalities. Connected component widths are often
tens of nominal units; they are conditional geometric ranges, not measured
millimetres, confidence intervals or complete two-view uncertainty volumes.
Do not turn one centerline intersection into an exact shape.

An additional image can expose hypotheses that regional fitting conceals.
853/854identify and trace the visible I12near-side upper window/frame and lower
window/body contacts independently of CAD projections.386upper and363lower
samples qualify by source-gradient rules;23lower samples remain uncertain.
Rubber/glass ownership and rounded endpoints remain unresolved. The previous
8pxaft-tip observation and all earlier observations are preserved.

855samples top-band offsets.856then checks the continuous band: at a fixed
original top-image column, write the world point as an origin plus a unit ray
times depth and a second direction times the top-pixel offset. Enforce the
original offset band. Each adjacent qualified source-profile segment, with its
original interpretation band and positive camera depth, becomes linear
halfplanes in those two variables. Convex clipping preserves disconnected
possibilities. A source-derived bound replaces an arbitrary 3D search box.
Projection bounds prune comparisons without changing the feasible set.

For the recorded Roadster hypotheses, none of413near-side upper trace samples
has a three-view witness in the traced bands;321have front-feasible ranges that
overlap the side-view sampled column span. Only18of474lower trace samples have
witnesses. This diagnoses the combined camera/feature/configuration hypotheses
over the observed bands. It is not a physical impossibility claim or permission
to discard observations, relax4px, invent geometry or fit a separate camera for
every patch. Untraced, uncertain and occluded regions remain distinct.
865checks166reported witnesses in original pixel equations and compares146
source cases with an independent linear program, including128infeasible cases.

The next correction must address shared camera/feature registration or a visibly
versioned source-interpretation change. Preserve original source evidence and
failed hypotheses. Do not freeze an experimental CAD gauge as dimensional truth.
If calibration/geometry changes, repeat affected source, visibility, continuity
and exact-output checks. Continue independent supported regions while a region
is held, through the existing accepted process and evidence/validation owners.

This is descriptive method qualification, not a new registered runtime reader,
executor, provider or UI. The current mathematical prototype has only the stated
Roadster scope; a portable shared implementation needs explicit camera/profile
contracts, independently controlled tests and another existing engineering case.
Future workflow bindings retain typed readiness/validation and declared waits;
instruction changes require a visible new revision, never executor prompt prose.

The same campaign demonstrates why actual geometry must be compared with source
updates. C40still contained legacy lamp coordinates although596had revised their
three-view landmarks. Separate C41reuses those existing observations and changes
only the two visible lamp skins. Its actual native export867reduces mean corner
error from19.99to1.65px across18observations; all meet the unchanged4pxband.
868tests all competing exported geometry: front-view lamp ownership improves
from12/56to56/56samples and the prior50canopy rays remain clear. Sampled maximum
lamp-boundary distances to retained geometry improve from80.96/79.23to60.74/61.34
nominal but remain open. These are regional improvements, not joined-shell or
physical fidelity claims.873identifies the14surround supports for a coherent
future correction; do not conceal the gaps with an invented bezel/backing.


## Separate print derivatives at a requested size

An engineer can request a small physical model while keeping the editable master
at its existing scale. Store the requested dimension, units and subject explicitly
(for example, 100 mm **overall vehicle length**). Derive one uniform scale from
the final exact assembly bounds, apply it to every part, and record the transform
and output hashes. Do not make each wheel 100 mm long or silently treat a nominal
master gauge as a verified real-world dimension. Configuration changes can alter
the bounds and invalidate the previous scale and downstream checks.

Keep print-specific underside closure, thickness, connections and simplification
separate from observed exterior reconstruction. These are designed manufacturing
features, not newly discovered hidden vehicle geometry. Preserve the master,
source requirements and prior candidates. Part separation and printing as one
object are different representations; validate the exact selected representation.

Use the existing CAD/export and validation mechanisms and durable artifact
subjects. Check closed native shells/solids and the exported mesh independently:
watertight manifold topology, winding, positive volume, disconnected scraps,
degenerate triangles, units and final extents. Report whether self-intersection
was actually tested. A successful STEP download or one valid component cannot
qualify the whole assembly. Printer, process, material and minimum-feature or
clearance requirements belong to declared inputs; preserve a waiting state at
that boundary while independent modeling continues. Do not infer physical
printing approval from a dimension answer. Existing common views remain usable;
this method needs no separate process UI or execution authority.

Before reusing a print constructor on a newer master, verify every named face,
curve owner, reference revision and coordinate transform. Recompute the selected
assembly extent and inspect its actual free boundaries. A changed inner assembly
can invalidate old backing and floor definitions while the outer silhouette stays
similar. Keep print-only simplifications explicit and preserve the detailed master.

Do not promote basic solid validity or a closed shell to an interference-free
body. A boundary filling can overshoot its boundary envelope, and a nominal face
constructor can return several positive-area pieces. Inspect the actual result,
retain all pieces and attribute faults to exact subshapes before correcting them.
Surface contacts between separate intended parts also need assembly semantics;
blindly sewing every visible plate, rib and body skin into one volume can create
unintended material. Do not select the largest Boolean cell or widen a numerical
tolerance to obtain a pass. Classify material and voids, preserve protected
surfaces, and revalidate the exact changed artifact.

Private P6 studies1954-1970 demonstrate these failure modes on a current-master
print rebase. The camera-cap overshoot is corrected with the existing four-side
construction, but the body remains held by full interference and union checks.
These are descriptive authoring lessons, not a qualified whole-car print result,
new runtime capability or accepted workflow revision.

Roadster evidence 893/894 demonstrates the limited distinction: eight new native
wheel solids and eight STLs pass the stated topology/volume/extent checks at the
scale corresponding to a 100 mm vehicle. Maximum mesh extent difference is
0.00512 mm and relative volume difference 0.0424%; these are numerical export
comparisons, not manufacturing tolerances. Spokes are about 0.501 mm wide. The
170 body surfaces remain open, printer/process is pending and mesh
self-intersection is not independently tested. The whole car is not print-ready.

The method inventory revision research-31 is descriptive authoring guidance,
not runtime configuration or a registered validator. New accepted workflows must
carry their visible instruction revision and required CAD/import/export and
validation dependencies. Diagnose missing capabilities without silent fallback;
transfer no credentials, live approvals or trusted UI builds. Any future shared
implementation must prove its contracts with a substantially different existing
workflow before general runtime support is claimed.


## Own complete shared boundaries before filling a gap

For an established interior crossing between existing surfaces, calculate their
actual intersection before changing control points. Split both surfaces and
identify retained pieces by unchanged owned feature boundaries, such as a wall's
upper rim or a floor's inboard edge. Archive every other positive-area piece and
its identity; never select by largest area. Keep intended separate-part contacts
distinct from crossings requiring a shared seam.

Prove the calculated seam on the actual native export, then inspect neighboring
surfaces, the complete boundary graph and unchanged source views. A local pair
can pass while its surrounding body remains incomplete. The private B23 proof
replaces one rear-well crossing with a shared edge, retains the other294faces by
strict serialization or empty two-way geometric difference, and reduces body
free edges138to136. It establishes this scoped native correction, not whole-body
closure, physical fidelity or an automatically bound workflow capability.


Index the actual anchors and every split edge on each side. Mirrored new design
geometry does not imply symmetric legacy geometry. The Roadster C44 trial failed
because live construction exposed a Bezier edge where STEP had exposed a
B-spline. C45 uses exact conversion and preserves that failed revision. Treat
this as a CAD representation issue in inspectable model source, not a reason to
change Wright's runtime or product roadmap. Preserve domains, knots and weights;
do not silently approximate unsupported rational curves or widen source bands.

Use the exact native output for the subsequent checks. C45 closes the six lamp
edges under numerical sewing while all 18 original corner observations and 218
visibility controls pass. C46 adds one explicitly inferred ruled nose surface
between unchanged native hood and nose-panel boundaries. At identical projected
interior pixels, previously empty rays fall from 47 to zero in the front view
and 35 to zero in the oblique view. Those are finite geometry-gap observations,
not independent photo-accuracy measurements. The nose bridge still has two free
outer edges; a local two-corner hypothesis closes that cluster but is not yet
native-qualified. None of these checks establishes G1/G2, physical scale or a
closed whole-car solid.

Keep the sequence general: provide text/images/data, reuse existing evidence,
research only gaps, own the component/configuration and boundary subjects, then
build and compare the exact revision. The accepted process and existing
tool/export, validation, durable-evidence and common-view owners retain authority.
Missing capabilities must be diagnosed; unsupported representations keep their
failure evidence. Accepted instruction changes need a visible new revision.
Research-32 is descriptive guidance, runtime_consumed=false, with no new executor,
adapter policy, UI or registered validator. A future new shared implementation
still needs a substantially different existing workflow proof.


## Qualify image-to-mesh as a hypothesis, separately from CAD

Preserve original input bytes and the exact conditioning transform, masks, model
source, public weight revisions, inference settings and exported mesh hashes.
Inspect the exact export in multiple flat-shaded views without photographic
texture. Record topology and scale/registration uncertainty before using it.
Input-view resemblance does not establish independent validation. Use held-out
views before deriving CAD guides; reject distorted or noisy geometry rather than
silently treating it as dimensional truth. In Roadster experiment 969, actual
local CUDA inference succeeded but inspection 970 found an open, noisy hypothesis
with 323 boundary edges. It remains unadopted and does not qualify printing.
This is descriptive reusable research-33 guidance, runtime_consumed=false. It
adds no executor, model policy, UI, adapter or validation authority.


## Complete an observed region without inventing hidden geometry

For C48's two continuous rocker skins, identify the faint source trim ridge
before selecting intensity gradients; keep observational uncertainty separate
from engineering tolerance. Hold four of eight columns out of fitting and check
the exact exported curves, not just shaded pixels. Bind all ten upper spans to
actual native boundaries. Zero lateral offset is an explicit completion
hypothesis. The visible ridge does not establish the underside, depth or closure.

For the separate 100mm-car wheel derivatives, overlapping visual rim/tyre parts
are explicitly united into single-piece display wheels. Their old parts stay
unchanged; no separate-part mechanical fit is claimed. Analytical STEP bounds
must disable triangulation on both subjects: cached mesh deflection caused the
992 numerical guard failure. Diagnosis994 preserves that evidence and 995 keeps
the original guard, reuses the first verified export bytes and completes the
package. Independent Trimesh checks pass all four exact STL files. These checks
do not establish print-process suitability, selfintersection absence or a closed
whole car. Research-34 remains descriptive, runtime_consumed=false, and creates
no executor, adapter policy, UI or validation authority.


## Requalify a projection when its dependencies change

A source-fit claim belongs to an exact artifact/component, camera version,
configuration, source/crop/trace identity and band. Unchanged CAD does not keep a
projection claim valid after a camera change. Roadster diagnostic1000 finds that
the inherited C25 lip still passes its old camera but misses the later696camera
by about33px. Correction1001 satisfies the original frontal4px band with complete
conditional Bernstein numerator bounds, yet side diagnostic1004 worsens from
1.36px to21.91px. It stays local and HELD. Camera-only search1005 finds no joint
witness; its best finite minimax result is about19.03px,not a physical
infeasibility proof. Reconsider shared geometry, feature subjects and camera
models together, rather than fitting another camera independently for each patch.

Keep dark side-window, roof, rear glazing and dark deck/cover subjects distinct
where ownership is unresolved. Persistent seams and occlusion order support a
component partition; brightness alone does not establish material or depth.
Review1021 recommends one owned shoulder/window/sail/deck curve network. This is
construction advice, not an executed or qualified new workflow/model.

## Audit closure and numerical integration separately

C48's derived body snapshot has185freeedges in31boundarygraphs and11connected
face components. Some are intentional openings or decorative sheets. A solid
display derivative needs explicit wheelhouse returns, inferred underside and
recess backings; do not cap every loop as a missing flat surface.

Default fender area/centre guards initially fail after sewing. Converged adaptive
surface integration in1009 satisfies the original unchanged area/centre guards,
with identical complete support poles/weights and finite boundary differences
below7e-11nominal. Numerical quadrature tolerance is not a manufacturing tolerance,
and these checks do not prove complete trim identity. Preserve the failed
default observation. Boundary visualization1020 uses native curve parameters and
explicit degenerate-edge points after1016's arc-length failure; hidden-edge plots
are labelled X-rays, not visibility evidence.

Research-35 remains descriptive, runtime_consumed=false. It adds no executor,
adapter policy, UI or validator authority. Existing runtime, tool, artifact,
validation and durable evidence owners remain responsible for execution.


## Own shared curves and invalidate changed subjects

Research-36 records actual editable B1 and B2 construction, not just the earlier
review advice. B1's new roof, side windows, surrounds, sails and rear insert
share a curve network. B2 joins that core to the preserved fixed recessed rear,
wheels and a rebuilt upper front. Six new front surfaces and one rear transition
have no nondegenerate free edges in the exact native B2 sewing audit. The whole
body remains open. Scoped G1 roof controls do not establish all-body G1 or G2.

The first broad front-panel trial retained an unsuitable projected perimeter.
Reparameterizing it alone did not solve the sign reversal. The corrected trial
moves the obsolete inner junction to the actual hood/cowl junction and replaces
the two adjacent lamp surrounds with it. Actual emitter borders remain unchanged;
all 168 visibility rays and 18 original 4px corner controls pass on exact B2.
The 54 old upper-canopy ownership rays are withdrawn because their subject changed;
they are not silently renamed or counted as passes.

Keep numerical validation failures. On a composite C0 boundary, a whole-curve
closest-point calculation missed a point by about 5.37 nominal units. Extracting
the exact bounded knot span gave matching degree-elevated poles and residuals
below 4e-13. Independent actual-face knot-span checks use the unchanged 1e-6
numerical guard. This diagnoses a solver limitation; it grants no physical
tolerance, complete trim identity, or automatic engineering acceptance.

B2 retains all 18 native B1 surface encodings strictly. Of 299 native B2 faces,
238 strictly match their local/prior-native reference representation. The other
61 pass finite boundary checks; 56 have complete-support matches under the
existing comparison, while five still differ in exact spline metadata. Preserve
these distinctions. A saved build can also succeed with failed features: B1's
first Edge-only display additions were rejected and remain historical evidence.

The requested display length is about 100mm. The master remains nominal full
scale. Existing four wheel derivatives are separately checked; B2's open body
is not a printable car. A later closed display derivative must declare inferred
underside, wheelhouse, backing and attachment geometry and revalidate its exact
STL/STEP output. Printer-specific suitability remains separate.

This remains a descriptive methods inventory, runtime_consumed=false. It adds
no executor, adapter policy, UI, capability claim or validation authority.


## Distinguish closed CAD, meshing and printable geometry

Research-37 separates three claims: valid closed CAD, a faithful tessellation,
and a qualified printable output. The 100mm Roadster display derivative has
explicitly inferred underside, wheelhouse returns and rear backings. Its three
closed CAD parts pass kernel interference checks and unchanged STEP round-trip
guards. The two small rear-part meshes pass independent intersection checks.
The main body mesh remains HELD: watertightness alone did not detect its triangle
intersections. Neither a refinement nor a bounded repair grants acceptance.

CadQuery exporters.export passes a relative STL deflection by default. A numeric
tolerance argument is not evidence of an absolute millimetre deflection. Use the
documented Shape.exportStl(relative=False) explicitly when that is the intended
setting, and record angular deflection and actual library versions. Earlier
local Roadster STL absolute-deflection descriptions are withdrawn by diagnostic
1099; original bytes and failed reports remain. STEP and BRep outputs are not
affected. This is exporter usage, not a demonstrated SteveCAD server defect.

The example utility `examples/reverse-engineering-research/measure_mesh_geometry.py`
reads an exact mesh, verifies its supplied SHA-256 before and after measurement,
and records topology, orientation, components, volume, extents and independent
PyMeshLab intersection selections. Its intersection count is selected faces,
not intersection pairs. Units are declared, not independently authenticated.
NumPy, Trimesh and PyMeshLab are optional independently provisioned dependencies;
an absent capability produces `capability_unavailable`, not a pass. It changes
no input geometry, installs nothing and grants no review or execution authority.

Example CLI (replace placeholders with the actual artifact identity):

```text
python measure_mesh_geometry.py part.stl --expected-sha256 <64-hex-digest> --declared-units mm --report fresh-measurement.json
```

Existing workflow validation/result owners consume measurements and determine
which requirements apply to the exact subject. No new executor, MCP provider,
global manufacturing policy or UI is added. Changed output bytes, units, source
geometry, settings or implementation invalidate the associated measurement.
Automatic accepted-workflow binding is not yet qualified. The same read-only
utility was actually exercised on a Roadster rear part and the substantially
different existing corrected pocket fixture; wrong-digest and absent-dependency
controls also ran. These small checks do not establish unrestricted capability.

Bound correction before execution. One MeshFix clean(max_iters=1,inner_loops=1)
did not satisfy the saved displacement/scope limits or topology/intersection
checks on the main body. Its output remains a rejected hypothesis. Do not retain
only a largest component or silently fill meaningful openings to obtain a pass.
Nearest-vertex distance is not complete surface Hausdorff distance. Printer,
material, supports, minimum features, attachments and physical fit remain separate.

For triangular surfaces, a general validity test and a sampled Jacobian can miss
a near-singular endpoint defect. B3 replaces only the two upper lamp surrounds
with an exactly shared-apex ruled construction. Check actual exported control
geometry, whole-domain regularity, CAD interference and original source bands.
Its 18 corner controls and 168 visibility rays pass; whole-body fidelity does not
follow. 251 of 299 face references match strictly, while the remaining 48 have
matching complete supports and passing finite boundary checks. Strict trim
identity for those 48 remains unproved.

Research-37 remains descriptive, runtime_consumed=false. No automatic workflow
upgrade, saved-instruction change, review grant or UI compatibility change occurs.


## Reconcile cameras, source subjects and the complete projected envelope

Research-38 retains new source-only observations: 68 side-view white-cheek/black-
panel junction points and 47 points on each frontal flank. These are distinct
from the earlier lower-panel highlight. Finite RGB/stencil trace variation is
2px, not a certified uncertainty interval or a new engineering tolerance.
Fixed-camera epipolar checks can detect that proposed visible curve segments
do not overlap under a camera pair. This can indicate different visible curve
portions, wrong feature identity or camera incompatibility; it is not physical
infeasibility and cannot be repaired by adding polynomial degree at fixed cameras.

Use original wheel-circle observations as additional conditional camera evidence
where appropriate. The Roadster study retained all26rim/tyre points and obtained
maximum exact projected-circle distance1.371px inside their original3px bands.
Circularity, shared ground, lateral placement, principal point and focal bounds
remain hypotheses. A camera listing or a low image residual is not calibration.

The old front region cut made pale grille bands under the later camera. A local
recolor corrected the front but blackened the side nose; it was not adopted.
Two boundary-driven cheeks and their emitter faces were then actually built and
exported in a separate native SteveCAD study. Its sparse fits passed, but an
unmasked top comparison exposed roughly80.7px outward protrusion. A new bounded
joint correction includes the existing raw top outline as an outside bound on
white cheek projection. It does not reinterpret that outline as lip depth.
The corrected native study preserves original upper4px bands and has no selected
search-bound hits. Endpoint identities and full-body cameras remain unverified.

The read-only example
`examples/reverse-engineering-research/certify_projected_control_hull.py` checks a
projected control hull against a piecewise-linear source front contour. For a
nonnegative partition-of-unity patch with positive rational weights and positive
camera depths, the projected patch lies in the convex hull of projected controls.
The caller must bind and verify those conditions on the exact output. The
calculator checks every shared polygon/contour break, including interior source
breaks; controls inside at their own heights alone are insufficient.

The corrected actual native bilinear cheek supports have at least0.839px and
0.905px clearance to the stated top contour over their full control hulls. This
is a conditional image-geometry statement calculated in floating point, not
interval arithmetic or subpixel physical accuracy. The contour now conditions
the correction and is not blind validation. The162interior junction samples
remained withheld from the fit and have maximum point-to-projected-segment
distance2.563px; no new acceptance tolerance is assigned to those observations.
Full assembly visibility, fender/hood/cowl interfaces and other source silhouettes
are still required. A valid four-face study does not complete a vehicle.

CLI input is JSON containing `control_points`, `camera` and `front_outline`.
Preserve its geometry/source/camera bindings with the accepted workflow assets.
Use a fresh report and exact input digest:

```text
python certify_projected_control_hull.py controls.json --expected-sha256 <64-hex-digest> --report fresh-hull-measurement.json
```

NumPy, OpenCV, Pillow and the existing projection helper must be provisioned in
an isolated environment. Missing dependencies return `capability_unavailable`;
there is no automatic installation or invented result. Wrong input digests are
rejected. A changed camera, source contour, controls, artifact or implementation
invalidates the corresponding calculation. Native support/basis verification
and existing validation/review owners remain responsible for applicability.

The same calculation was exercised on a substantially different existing pocket
fixture's exact STEP bounding polytope using explicitly synthetic image bounds.
Negative controls reject missing source coverage, changed digests and an interior
contour violation despite all controls passing at their own heights. These are
scoped mathematical/measurement checks, not physical or unrestricted workflow
qualification. The older source version is preserved alongside its evidence;
optional-dependency handling changed without changing the mathematical bodies.

One focused Astra/high review informed the new front construction. Actual SDK
request/image receipts were checked, and the private routine Sol/medium profile
was restored byte-exact. Advice creates no geometry acceptance, human approval
or model-routing claim. Research-38 remains descriptive,runtime_consumed=false;
no new executor, adapter policy, automatic workflow upgrade or UI was added.


## Separate feature ownership before forcing a fit

Research-39 adds a source-evidence revision step when a fit fails locally.
Keep the outer envelope, material border, short bright line, inner return and
floor reflection as separate candidate subjects. Trace source branches without
using the desired CAD fit or imposing symmetry. Record the original pixels,
source digest, review window, competing branches, stencil sensitivity and
unresolved occlusion. Pixel proximity does not prove physical correspondence.

Preserve every earlier sample, interpretation band and failed residual. A new
source interpretation has a visible new revision and an explicit old-to-new
subject mapping. It must not silently remove inconvenient data, widen a band or
turn a previous failure into a pass. Geometry constraints reference the exact
evidence revision and feature subject. An AI review supplies advice; it does not
approve a source interpretation or grant execution authority. Continue other
components when ownership remains unresolved.

The local lip evidence demonstrates this distinction: six bounded symmetric
fit starts fail their original front bands. A source-only ownership index keeps
all 802 earlier samples unchanged and separates six candidate image branches.
No physical correspondence or new lip geometry is accepted from that index.

## Independent conforming tessellation with explicit bounds

A closed BRep and a watertight STL can still have intersecting triangles. An
independently provisioned mesher can generate a conforming boundary mesh from
the exact CAD topology. The external mesher owns its implementation and package
compatibility. The [Gmsh manual](https://gmsh.info/doc/texinfo/gmsh.html) documents
STEP/BRep import, surface meshing, import-healing options and mesh APIs.
This example does not introduce a Wright-owned provider or vendor protocol.

Pin the source hash, tool/native-library identities and units. Disable implicit
CAD healing, preserve import diagnostics, and impose wall-time and output-size
bounds before launch. Preserve generated node/face ownership and serialization
precision. A timeout or output bound produces a held diagnostic, not a mesh pass;
terminate only the operation's owned local process tree. Do not repeat an
unchanged failed operation or replace the source shape silently.

Qualify orientation on a different existing fixture and independently measure
the exact saved output for closure, connected components, winding, positive
volume, degeneracy, intersections and source deviation. Default CAD mass can be
misleading on trimmed splines: compare converged adaptive integration where
needed. A matching volume remains insufficient to prove complete shape identity.
Resource or capability failures hold dependent work. A changed master invalidates
its earlier scale, geometry, exports and validation subjects.

The existing pocket fixture's 33,390-triangle STL passes the independent mesh
checks with zero selected intersecting faces and volume 5,808 mm3. This is a
scoped fixture result. The historical Roadster P4 trial exceeded its output
triangle bound; it is rejected. A changed policy has a separate hard process
timeout and remains unqualified until its exact output is independently checked.
Neither trial establishes a printable current B4 body.

These are descriptive method assets, `runtime_consumed=false`. Existing accepted
instructions, execution, validator/results, recovery, reviews and common working
view keep their authority. Any future binding must resolve capabilities first,
freeze its configuration and preserve exact source/output identities. No new UI,
executor, automatic workflow upgrade or physical dispatch is introduced.


Timeout qualification correction: the local 1214 controller expired its wait,
but its cleanup observation also failed. A later authoritative process query
finds the owned workers absent; no output mesh was produced. This does not
qualify hard-timeout termination. Prove cleanup on a harmless fixture before
any future large-mesher binding. Current body completion takes priority.


## Classify open boundaries before adding closure

A free loop can border an aperture, a missing exterior skin, an inferred hidden
closure, or an area already covered by another sheet. Check proposed closure
against existing surfaces for duplicate area and inspect the neighboring
transition geometry. Matching endpoints and nonzero intersection sections alone
do not prove a common full boundary or smooth continuity. Preserve numerical
checking tolerances. Correct a proved overlap or T-junction in a visible new
source revision; do not hide it beneath a second sheet.

The Roadster B7 diagnostic rejected a proposed roof continuation because its
entire area duplicated an existing roof. Three separate plate returns then
closed the actual plate boundary, with no positive duplicate area in 18 scoped
exact-native parent comparisons. The current front-arch diagnostic also
identified folded-back legacy strips before attempting hidden wheelhouse
closure. Those findings guide the next geometry operation; a lower free-edge
count alone is not an accuracy or printability claim.

Preserve pinned native reference links when copying a construction document.
An omitted link is a dependency defect even when all helper files are present.
Requalify the exact new native revision and output after correction. These
remain descriptive methods with no automatic runtime binding or accepted
workflow instruction change.


## Separate opening construction from solid and mesh qualification

Use owned exterior curves, explicit inboard returns/backings and compatible
end/floor joins for each opening. A transverse lip and a longitudinal wheelhouse
need different constructions; a single global flattening map can create folds
or wheel collisions. Keep hidden geometry as a declared derivative assumption.

Recompute shell closure before caching a positive result, then check the whole
solid for interference. Exact contact partition may preserve all material cells
without moving protected exterior geometry; prove per-subject boundary coverage
and retain every positive component. Volume agreement alone is insufficient.

The current local display derivative has one CAD-valid interference-free body
and checked coverage of128protected source faces. Its binary STL still fails
independent mesh checks. A separate double-coordinate diagnostic also fails
manifold/intersection checks after exact-zero-area triangles are removed.
Neither mesh is accepted. CAD validity, coordinate precision and removal of
degenerates cannot substitute for independent checks of the exact saved mesh.
Native qualification and printer-specific minimum features remain separate.

These additions refine the existing descriptive method only. No automatic
runtime binding, accepted-workflow update, new provider or UI is introduced.


## Preserve recesses before preparing a print

A rear fascia, instrument housing or appliance surround can contain an outer
return, a recessed bowl, side pockets and a projecting ledge. Give those regions
explicit boundary ownership and independently editable depth controls. Check
sections and source views before closing or thickening a simplified envelope;
a printable approximation can still have the wrong shape.

When fitting a projected boundary, measure distance in both directions. A curve
can pass near every selected photo point while bulging away between them. Keep
the camera, all observations, correction bounds and uncertainty visible. Confirm
feature identity and reconstruction conditioning before treating a fitted depth
as a measurement. Revalidate preserved attachments and the exact native export.

These refinements have local Roadster CAD/diagnostic evidence in the Windows
pilot (1381–1400). They extend this method proposal; they do not register a new
runtime capability, update accepted workflows or establish general qualification.

Rear enclosure follow-up: name the exact attachment end and datum before joining surfaces. A front mouth is distinct from its recessed carrier. Preserve qualified setbacks and check whole-feature visibility after rebuilding neighboring surfaces; a mathematically valid join can still occlude the intended feature. Reused derived section curves need an explicit geometry-dependency signature. These remain method-authoring guidance, not newly registered runtime capabilities.

Visible junction refinement: trim the owned parents before adding a transition. Preserve failed filling tolerances; explicit spline boundary rows can enforce positional sharing while a tangent field is fitted. Report complete control/trim proofs separately from sampled normal agreement. Map every floor/skin owner and unsupported depth interval before reusing the construction at another junction. Keep visible end-profile surfaces distinct from unobserved backing or manufacturing thickness. These are method guidance and qualified model examples,not newly registered workflow capabilities.


## Respect actual trimmed owners when reusing junctions

Map the actual floor or skin owners before copying a construction. Restrict the
transition to common supported depth. A trim may split one CAD region into
several positive-area pieces; preserve them all and identify the required
boundary semantically. Such a split does not establish manufactured part seams.

Check a boundary against the underlying support as well as its stored 3D edge.
A valid Boolean face can retain an approximate 3D edge that fails a tighter
declared positional check. For supported polynomial types, composition of the
same UV trim with the same surface can repair that representation while keeping
the trimmed region. Reject unsupported types or excessive degree rather than
changing the check. Keep inherited floor creases explicit: averaged tangents do
not prove G1 there.

A face bounding box can include an unused support corner. Before substituting
trim-boundary extrema, prove coordinate monotonicity from the complete validated
control net. Otherwise preserve the conservative result. The private observer
was checked on the existing pocket-defect fixture and an interior-extremum
negative control; this is not a newly registered Wright runtime capability.

Roadster B12 has exact native STEP, shared-control/trim and scoped visibility
evidence (1546-1548). Its source fit is conditional, one reverse residual exceeds
the provisional image-reading band, and the body remains open. These lessons
extend the descriptive method assets only; accepted workflow instructions,
requirements, runtime, validator, reviews and UI keep their existing authority.


## Test the actual shape claim before promoting a CAD-valid trial

Visible background through a wheel opening does not prove that an exterior
panel is missing. Check actual shared boundaries first. Keep source-observed
return height separate from inherited depth amplitude, and preserve declared
attachment bands when testing a local change.

A CAD-valid, regular surface can still have the wrong shoulder shape. The
Roadster pocket trial 1569 passes local construction and attachment checks but
is held by the source-form assessment 1575. No native model was replaced.
Ensure comparison windows actually include the target; label X-ray boundaries
and partial-context renders. These remain descriptive lessons, not a new
runtime capability or an automatic accepted-workflow change.


Wheel-source follow-up: the strongest intensity transition can belong to a
caliper, reflection or bevel. Keep candidate branches and failed residuals when
revising source ownership. Do not extrapolate unobserved inner corners merely
to close triangular regions; individually valid faces can overlap together.
Review seeded appearance masks for leakage and clipping before CAD conversion.
The wheel studies 1576-1581 remain unqualified source/geometry trials, with no
new native model or accepted runtime binding.


## Distinguish missing geometry from reversed face orientation

Verify actual face orientation separately from surface validity and coverage, especially after coordinate reflection. Double-sided renders can hide inward-facing exterior panels. Compare explicit one-sided views and mirrored normal parity, respecting cavity-wall intent; never flip every face by an axis rule. After correction, verify the exact native export preserves geometric records and effective appearance while changing only declared orientation senses. Keep genuine body openings and print closure as separate unfinished claims.

The private Roadster B14 case corrects seven orientations without changing
coordinates, curves, surfaces or finite loops (1598-1600). This extends the
descriptive methods only; no new runtime binding, accepted workflow revision
or general tool qualification is claimed.


Connected orientation follow-up: a mirrored pair can share the same wrong
orientation. On a manifold surface network, use shared-edge traversal parity
and a known exterior anchor; reject inconsistent cycles. Independently verify
the exact exported network. Private B15 has 148 connected faces and 379 coherent
shared-edge constraints; four disconnected open feature skins remain separate.
Six actual CAD rays through remaining rear background hit no geometry. These
are finite observations, not permission to invent unseen physical walls. The
method remains descriptive and has no new runtime binding.


## Separate apparent contours from physical edges before inferring depth

Index the inner pocket crease, outer silhouette and material/highlight boundary
separately. A frontal orthographic trace constrains projected Y/Z but has no
X-depth sensitivity. An oblique image needs an established corresponding
physical feature or a model of view-dependent occlusion; an apparent curve is
not automatically a fixed three-dimensional rim. Retain unowned source picks
and conditional camera limitations.

The private Roadster studies1623-1640 preserve28picks and fit the withheld
source readings to about1.3pixels. They do not establish physical topology or
depth. The cut-only, bounded C1 inset and explicit visible-interior trials are
all held by the independent form comparison. Complete CAD/control bounds are
separate from photographic fidelity. A Boolean split must preserve each
positive-area piece under a unique ID; never overwrite pieces or keep only the
largest. These are descriptive lessons, with no new runtime binding or automatic
accepted-workflow change. Native B15 remains preserved.


## Winding-number print surface studies: experimental, held

The optional local `winding_surface_study.py` uses independently installed libigl
to infer material from an explicitly oriented triangle soup. The
[method paper](https://www.dgp.toronto.edu/projects/fast-winding-numbers/) explains
the approach. This can investigate difficult print representations; it does not
replace editable CAD, certify hidden geometry or register a Wright executor.
Grid, resource bounds, sign method, contourer and any offset are explicit candidate
parameters. Existing runtime, validator, evidence and review owners stay unchanged.

Windows pocket controls preserve 99 strict native inside/outside labels for both
closed and deliberately open inputs. A separately retained boundary point exposed
an incorrect earlier test label. Keep IN/OUT/ON distinct. Exact saved STL controls
still fail topology/degeneracy checks, so this method is held before Roadster use.
The separate `stl_zero_area_derivative.py` preserves every positive-area record
byte-for-byte while dropping only explicitly bounded exact-zero records; that
operation also requires complete independent revalidation. Neither helper is a
qualified workflow capability or a reason to loosen engineering requirements.


## Exact triangle-intersection cross-checks

`exact_mesh_intersections.py` is a local read-only cross-check using independently
installed libigl predicates and CGAL. It retains exact saved coordinates, reports
intersection pairs and separate duplicate/degenerate counts, and records native
binary identities. Four crossing/contact controls and the existing pocket fixture
qualify that local scope. The same unchanged forward-body mesh gives zero pairs
in both kernels while MeshLab selects34faces; retain that disagreement and any
previous held assessment. A new measurement method needs visible result/profile
binding before runtime use. It does not waive CAD fidelity or printer checks.

Projection reports also need numerical sanity checks. A nearest-distance estimate
cannot exceed an on-CAD edge endpoint's distance plus the separation from that
endpoint. The forward study exposed a violated midpoint bound, so those local
stationary projections cannot establish actual shape error. Retain the numerical
failure and use trim-checked constructive bounds or a qualified projection method;
do not treat an unverified solver result as dimensional truth.
