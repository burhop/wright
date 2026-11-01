# Reusable reverse-engineering workflow: Windows pilot implementation plan

## Delivery checkpoint — 1 November 2026

The reusable preparation and diagnostic source is being qualified independently
of Roadster construction. See the [delivery scope and repeatable checks](https://github.com/burhop/wright/blob/dev/examples/reverse-engineering-workflow/delivery-qualification.md).
Current dev already includes the shared frame/container readers from PR #176.
The unchanged pilot checkout remains at `560add59`; its latest preserved Roadster
checkpoint is B26 with an incomplete open shell, not the older revision7 below.
Roadster execution is currently paused by the user. No complete automatic
research/CAD/correction chain or printable model is claimed by this delivery.
The following dated checkpoints and milestone table remain historical evidence.

## Historical Windows checkpoint — 21 October 2026

The dated scope and milestone statements below preserve the original preparation
plan. Later qualification supersedes its old export and pixel-unit blockers for
the controlled Windows pilot. The dedicated worktree now uses source commit
`560add597c67bede1c0bfd06c7e35b5ad0712361` plus preserved local changes.

The small SteveCAD fixture passed native depth correction from0.5to2mm and exact
MCP/browser STEP revalidation under its unchanged bounds and tolerances. Pixel
identity/currentness checks and the different existing Robot Tracking regression
also passed their recorded bounded scopes. Authentication, Workflows, frozen
Astra/high routing, actual rebound workspace tools and durable resume retain their
separate readiness evidence. These checks do not establish a complete automatic
research-to-CAD correction workflow.

The user's later authorization allows continued bounded digital Roadster
construction. The supplied2825mm wheelbase and approximately2000mm width remain
nominal inputs with unverified provenance; separate editable panels are required.
Current revision7 is a58-valid-face native surface model with exact STEP and
front/side/rear comparisons. A measured front-arch interpolation overshoot was
removed while preserving original picks. Native preservation checks also expose
two rear-quarter discrepancies, which remain open. This is controlled hypothesis
construction, not calibrated physical reconstruction or human acceptance.

Next engineering work: separate camera effects from body shape, refine front
fascia/lighting and rear detail using existing evidence, inspect sections and
continuity, compare held-out views, and revalidate every exact changed output.
Keep camera/uncertainty hypotheses explicit and versioned; do not turn them into
vehicle dimensions or silently change accepted instructions. The original
research-first input experience and shared runtime/results/validator ownership
remain unchanged. No Codex UI redesign is included.

Detailed private identities and current work are in the Windows pilot state:
`research/20261020-roadster-goal/STATUS.md`, `CURRENT-WORK.json`,
`READINESS-CURRENT.md` and `roadster-r7-engineering-checkpoint.json`. Historical
readiness snapshots and failed revisions remain retained. The reusable methods
include exact-output projection, interpolation-extrema checks, native face
preservation and explicit failure/uncertainty handling; broader workflow
qualification and human engineering acceptance are still required.


Date: 20 October 2026. Base: `d6eda2b4e562da5304bb92588aff81b5c70fd415`.
Scope: authorized isolated local development, preparation and bounded digital
qualification. Roadster reconstruction is held. No shared services, physical
actions, production release, Codex UI redesign or existing CAD recreation.

## Outcome and existing foundation

The user describes what they want to reverse engineer and can attach images,
drawings, video, measurements, links or other data. Wright's first work step is
to research the subject using that input and collect the information needed to
create the CAD model. Wright organizes the findings, works out what can be
calculated, and asks for essential missing information when research cannot
resolve it. It then builds the editable CAD model in SteveCAD, compares it with
the references, corrects discrepancies and presents the model and remaining
limitations to the user.

The user supplies a starting point; Wright does the research and preparation.
Component indexing, source tracking, measurement calculations and validation are
work performed by the workflow. Keep those details inspectable without requiring
the user to prepare technical registers before research can start.

## User clarification: simple input, research first

Agreed direction, 20 October 2026. The intended experience is:

1. **Describe or upload.** Accept free text, files, links, or a combination. The
   user can include dimensions or accuracy needs they already know.
2. **Research.** Inspect supplied material and look for relevant specifications,
   drawings, photos, videos and other sources. Identify the correct object/version,
   organize information by component where useful, and calculate geometry where
   the evidence supports it. Retain sources and distinguish facts from estimates.
   Reuse supplied research, organized references and applicable experiment results
   first. Search for additional information only to fill a specific gap or resolve
   a conflict. This step can finish without new web research when the supplied
   material is sufficient.
3. **Resolve essential gaps.** After research, ask concise questions only where
   missing information affects the model or its required accuracy. Use the
   existing declared interaction step. Continue independent research meanwhile.
4. **Build the CAD model.** Use the collected information and supplied requirements
   to create editable geometry in SteveCAD.
5. **Compare, improve and deliver.** Check against the references and dimensions,
   correct the actual model within the configured bounds, and show the result
   with any unresolved limitations.

Missing dimensions or tolerances do not prevent the research step from starting.
Research outputs supply downstream inputs through existing workflow mechanisms.
If a critical dimension cannot be established, hold the dependent modeling work
and request the specific observation needed; do not silently invent it. Detailed
engineering records are generated internally and are available on demand.

The next development priority is an Astra-authored **new workflow revision** with
this input and research stage. Acceptance examples: a text-only request; a photo
with a short request; and mixed documents/images/links. Each must begin useful
research without requiring a manually prepared evidence index, coordinate system,
uncertainty register or acceptance profile. Qualification must include actual
research/tool results, then a necessary missing-information question if applicable.

A fourth acceptance case supplies an existing research and experiment package.
The workflow must reuse relevant findings and completed calculations, preserve
their limitations, and avoid duplicate searches, downloads and experiments.
Repeat work only when a changed input, unresolved conflict or missing validation
makes it necessary, with a specific reason. Prior work is an input to the process;
the user does not have to repeat it to satisfy a fixed stage sequence.

For the Roadster, start with the existing Windows-local reference package and
previous experiment results. A local starting prompt points to those directories
and the retrospective. Review the existing material, carry useful findings
forward, and research only remaining modeling gaps. Rebuilding the CAD from
scratch does not mean restarting research or discarding previous lessons.
Earlier model geometry remains an experimental result with its documented
limitations, rather than independent evidence of the vehicle's actual shape.

Implementation status, updated after local qualification on 20 October: the new
`examples/reverse-engineering-workflow/research-first/` bundle contains actual
Astra/high-authored instructions, ordinary Wright source and contract tests.
The text-only reuse run completed without searches or an unnecessary question.
The mixed Roadster run read nine existing documents and one attached image,
produced a schema-checked brief without searches, and persisted its declared
question checkpoint. SDK receipts confirm Astra/high for research and question
classification. These are source-runtime/API checks, not a new UI walkthrough.

The general optional-web path still needs a shared completion mechanism: current
MCP tasks require at least one successful tool-call evidence reference, preventing
valid zero-call reuse. Separate model-only reuse and tool-enabled targeted research
paths preserve evidence meanwhile. An imported-provider null source URL also
caused an exception before dispatch; completing the isolated registration's real
upstream metadata allowed fresh calls. Report both findings to the integration
agent. Actual public search/fetch exposed an additional missing PDF-reading
capability; raw fetched PDF bytes are not read mechanical drawings. No engineering
tool evidence rule has been relaxed. Final per-case status belongs in the private
`state/research/20261020-research-first/STATUS.md` and redacted run receipts.

The existing
`preparation.workflow.wflow` is retained as a technical qualification fixture; its
structured basis form and report-only task do not implement this user journey.
Its successful run remains historical evidence. Existing readiness holds apply to
CAD execution and Roadster reconstruction; they do not define the user experience.

## Existing foundation

Use Wright's accepted source/compiler, instruction snapshots, source-run recorder,
gateway, EngineeringResult/provenance, Feature 082 validator/rework and Feature 083
input/review/common-view mechanisms. Backend owners retain execution and authority.
The flowchart/source remain the authoring experience; the common workspace view is
the working experience. Existing UI compatibility and fallback remain unchanged.
Vendor protocols stay in independent providers. Apply V1–V7; no new executor,
permissions system or vehicle-specific pipeline is introduced.

The retrospective establishes four separate gates: reference fidelity, native CAD
topology/design intent, exact export quality, and optional manufacturing suitability.
Preserve these and separate human acceptance. A valid BRep, plausible image or
successful model response cannot establish dimensions or authorize downstream work.

Existing research assets are in `examples/reverse-engineering-research/` and
[method guidance](reverse-engineering-methods.md). They were proposals, not installed
runtime integrations. The existing synthetic fixture and comparison implementation
are Windows-local inputs, not tracked in this pilot revision. Their manifest and
source hashes must accompany qualification; do not pretend they arrived from Git.

## Ordered work and exit criteria

| Milestone | Deliverable and existing owner | Exit criterion / dependency |
|---|---|---|
| P0 Preserve and inspect | Immutable local before/after inventory, source/service/model identities, retained readiness | Original dirty bytes, pilot basis, historical runs/profiles/evidence preserved; no revision advancement |
| P1 Astra authoring | `examples/reverse-engineering-workflow/`: proposed full plan, versioned instructions, acceptance cases and capability map | Actual Astra/high SDK receipt; schemas accepted by existing instruction contracts; all proposal/qualification scopes explicit |
| P2 Useful preparation workflow | `preparation.workflow.wflow`, bounded declared basis schema, evidence-gap report instructions | Existing authoring-shape validator and compiler pass; instructions embedded and digest checked; missing inputs wait at the declared step; no CAD or export operation |
| P2b Research-first workflow — in qualification | New version with simple prompt/files/links input, actual research stage and declared essential-gap interaction | Text reuse and mixed Roadster inputs exercised; independent targeted web research exercised; optional zero-call completion and document-reading gaps remain. See per-case receipts. Existing P2 remains historical. |
| P3 Evidence and specification basis | Reusable index utility, private Roadster index, component/measurement/unknown register | Verify available original hashes, retain duplicate lineage, object-state/scale/camera gaps and unreviewed annotation status; no guessed dimensions; missing original files separately listed |
| P4 Deterministic method checks | Existing box fixture through actual VTK camera, independent projection math, versioned numerical checks | Positive control agrees; wrong scale/camera/mirror and changed bytes rejected or detected; silhouette-compatible depth remains unverified; scope excludes real-photo accuracy |
| P5 Different-domain proof | Existing Robot Tracking data and unchanged alignment/metric requirements, fresh selected local environment and outputs | Actual CSV→ROS2 bag→independent bag inspection→tracking measurements; original 1% metric and one-sample event rules retained; distinguish direct provider proof from canonical runtime and full assignment |
| P6 Runtime integration and readiness | Existing source/result/file-dependency/validator/rework seams | Wire qualified measurements as actual EngineeringResults with exact subject/profile hashes, require missing capabilities, verify actual helper/recovery routing and current shared negative checks; no prompt-only enforcement |
| P7 Exact CAD correction chain | Retained SteveCAD pocket revision/build and independent exact artifact | Initial unchanged revision STEP export now passes; exact downloaded shape is independently valid with the expected 0.5 mm defect. Bounded correction to 2 mm and corrected-output revalidation remain. Preserve the newly returned export build identity separately from the original build. |
| P8 Roadster entry decision | Fresh readiness report, qualified observations and accepted regional specification | All mandatory Windows readiness checks pass; sufficient calibrated independent evidence and requirements exist. Start from scratch only after this gate; no reuse of historical CAD as truth |

P1–P5 can advance while P7 is held. P6 integration must use qualified actual methods;
do not register research IDs as if they were installed provider tool names. Full
reconstruction cannot be declared complete from P2's preparation graph. After P7,
repeat the complete small-part chain in a second clean registered workspace using
fresh producer outputs, without copying reviews or rewriting historical routing.

## Evidence and calculation rules

Use many-to-many component/feature links. Preserve originals; crops and video
frames reference parent hashes, timestamps/timebase/shot and transforms. Record
source/capture/publication groups, object revision/state, visible/occluded regions,
camera/distortion/crop/mask versions, rights and fitting/development/audit roles.
Duplicate bytes do not establish independent captures; different bytes may still
share a capture or source. Imported metadata is not newly viewed evidence.

Every requirement needs an authority, intended claim, units, coordinate/datum frame,
tolerance and conformity rule. Every measurement needs method, exact subject,
evidence IDs, uncertainty and limitations. Calculated values retain equations,
input revisions and covariance/bias assumptions; unknown uncertainty is not zero.
Keep measured/published/calculated/inferred/assumed/unknown separate. Do not adopt
unverified wheelbase/tire leads as scale anchors, equate nominal tire diameter with
loaded radius, or infer hidden structures from a plausible generated mesh.

Use frozen cameras, scale, masks and references; no automatic refit to hide defects.
Split audit evidence by independent capture/source group before fitting. Audit
cameras must be established independently of the candidate. Once used for tuning,
an audit observation loses holdout status. Report observed-region coverage,
image coverage and sampled surface compliance separately.

## Methods and capability ownership

Start with calibrated projection, named dimensions/sections and bidirectional
surface comparison when an independent 3D reference exists. VTK numerical camera
checks qualify only their tested transform. Raster visibility, distorted optics,
real-photo calibration and MCP bindings require their own tests. Keep visual hull,
SfM/MVS, learned geometry and image-to-3D optional until host, license, input and
accuracy requirements are met. Generated geometry remains a hypothesis.

SteveCAD remains the native editable producer. AgentCAD/native readers may measure
actual exchange artifacts; their results cannot replace the producer's missing
export. Existing Robot Tracking proves a different domain without claiming it
qualifies geometry methods or the entire extended engineering assignment. Later
use the existing Sheet-Metal Supplier Handoff for drawing/section scope, retaining
its requirements and stopping before supplier submission.

New research checks on 20 October: [OpenCV camera model](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html)
supports explicit intrinsics/extrinsics and image-resize handling;
[COLMAP camera guidance](https://colmap.github.io/faq.html#choosing-the-right-camera-model)
warns against overparameterized calibration; [CloudCompare mesh distance](https://www.cloudcompare.org/doc/wiki/index.php/Cloud-to-Mesh_Distance)
requires attention to sampling when comparing meshes. These documents do not
establish that those providers are installed or qualified here.

## Integration, invalidation and boundaries

Save behavioral policy in versioned instructions and accepted source. Use existing
typed instruction policy (`require_specified`) and declared input/review schemas.
New source materializes the existing default protocol/helper bodies and adds scoped
preparation instructions; accepted old workflows remain byte-preserved.

Inputs, camera/mask/scale/reference changes invalidate dependent fits and findings.
CAD changes invalidate geometry-derived exports/assessments; re-export changes
invalidate exact-file findings. Requirement/profile changes invalidate decisions.
Changed model/SDK/profile stops continuation before inference through existing
guards. Record requested alias, actual request model/reasoning and reported model
separately; provider-internal revision remains unknown. Never infer helper/recovery
coverage from a successful primary call. Historical unobservable calls stay unverified.

For the pocket preserve depth 0.5→2 mm, only depth in [0,8] mm, at most three
correction iterations, 0.05 mm surface tolerance, 0.99 global and required-region
coverage, 2048 samples/direction, seed 78237, identity alignment/no masks/no scaling,
and floor residual ≤0.001 mm. Numerical camera-control thresholds are synthetic
diagnostics and do not replace these requirements or establish vehicle tolerances.

Portable bundles contain instruction bodies, source, declared reference/profile
dependencies and compatibility metadata. They exclude credentials, personal media
without rights, live runs/answers/approvals and trusted UI builds. Missing assets or
tools block affected work; local absolute paths are inventory locators, not portable
IDs. Retention budgets are explicit per run; no cleanup/deletion is authorized.

The user reports the SteveCAD bug submitted once. Report ID is pending. Keep the
failed run and build; no duplicate report or uncertain generation/export retry.
No new shared-code defect is established merely by the provider failure or a
sandbox probe stall. Reproducible shared defects go to the Integration Agent with
exact source, inputs, scope and redacted evidence, outside the Codex UI workstream.

## Current evidence and next decisions

### Windows pilot checkpoint, 21 October 2026

P7's bounded native correction and exact-artifact checks now pass locally.
SteveCAD retained revision1 and saved revision2 with pocket depth0.5→2mm; both
native MCP and browser STEP exports were independently revalidated under the
unchanged policy. The floor residual changed from+1.5mm to0mm. This is a controlled
sequence of canonical runs, not proof of an automatically looping accepted
process. The earlier milestone table remains the original staging record.

P6 now has fresh live shared-reader evidence for
[image-coordinate validation](image-coordinate-validation.md): all8 original
numerical controls pass against an exact raster, while wrong image identity,
resolution, units, missing image and a measured defect cannot pass. Changing a
dedicated disposable image makes its assessment stale without rewriting history.
The changed reader also passes the retained Robot Tracking metrics and rejects
its two original negative controls through fresh API runs. These controls do not
measure Roadster fidelity or qualify a complete reconstruction graph.

The isolated goal evidence root is `research/20261020-roadster-goal/` under pilot
state. Its current `STATUS.md` supersedes dated readiness statements. Astra/high
has inspected six existing original Roadster views; I15/I22 were measured as
dependent views. Source-image feature measurements, final scale/configuration
choices and the full Roadster construction/validation work remain outstanding.
No Roadster dimensions, human acceptance or physical accuracy are established.

Execution evidence is additive under the pilot state at
`research/20261020-re-workflow-implementation/`. Its `STATUS.md` and verification
JSON record actual completion and limitations; the proposed Astra acceptance list
is intentionally retained as authored, without rewriting proposals into test claims.
No human engineering acceptance is recorded by this implementation work.

### Subsequent controlled construction checkpoint

The user supplied nominal2825mm wheelbase, approximately2000mmwidth and separate
movable panels. These choices permit provisional digital construction; they do
not establish verified dimensions or physical tolerances. The current Roadster
candidate is SteveCAD revision7, build6ca66c8b-6a82-49ec-bcec-ddc32cf86644, with
58independently valid open STEP faces and zero solids. Native wheel-opening
overshoot and hood/windshield closure improved, while full realism, two protected
rear-face equivalence checks and calibrated multiview fidelity remain incomplete.
The exact candidate and limitations are recorded in the goal's current STATUS;
earlier staging statements above remain historical.

The optional two-view consistency measurement is now an executable reusable
example with unchanged Astra/high-authored source, five passing numerical test
methods and a retained pocket-STEP known-coordinate compatibility control.
The separate bounded four-view camera/shape analysis remains pilot-local:
zero of32starts converged and no inferred coordinates were adopted as native CAD.
Shared runtime, evidence, validation and UI ownership remain unchanged. This is
continued preparation and controlled reconstruction, not a completed automatic
research-to-CAD correction workflow or human engineering acceptance.
