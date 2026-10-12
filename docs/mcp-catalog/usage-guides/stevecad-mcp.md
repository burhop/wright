# SteveCAD MCP: practices proved with Wright

Recorded 11 October 2026. Server ID `stevecad-mcp`; official hosted endpoint
`https://stevecad.studio/mcp`. See [connection qualification](../followups/stevecad-mcp.md),
[setup recipes](../mcp-server-setup-recipes.md),
[provider working guidance](https://stevecad.studio/docs/agents/working-with-steve/)
and [feedback documentation](https://stevecad.studio/docs/collaborate/feedback/).
Native qualification reported STEVE CAD 4.0.10 and 26 tools. A hosted server can
change; rediscover current contracts instead of assuming that version is fixed.

## Proven scope

The existing Wright gateway has built editable blocks, inspected actual B-rep
geometry, returned three revision-bound CAD images, and passed those images into
three presentation renderings and a design review. The qualification coupon also
has an actual STEP export. Native Windows and clean-container qualification have
separate receipts. No physical printing, assembly, load-bearing acceptance or
hardware motion is established by these digital results.

Useful evidence:

- [Four-hole block](../../../artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-008/run-summary.json)
  and [actual geometry audit](../../../artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-008/independent-geometry-audit.json).
- [Six-hole reuse](../../../artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/six-hole-005/run-summary.json)
  and [actual geometry audit](../../../artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/six-hole-005/independent-geometry-audit.json).
- [Qualification coupon STEP](../../../artifacts/stevecad-demonstrations/qualification/native/coupon.step).
- [Provider skills discovery](../../../artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/provider-guidance/guide-skills-20261011.json).

## Discover, then build

Call `api_reference` without a name, then read the precise classes/methods needed.
For specialized work, call `list_skills`, then `read_skill` with an exact returned
name. `working-with-steve` is a documentation URL, not a discovered skill name.
Single-part modeling does not require a guessed skill. Assemblies and printing
should consult discovered `steve-designs`, `steve-motion`,
`steve-motion-studies`, `steve-standard-parts` and `dfam-3d-printing` as relevant.
Their discovery alone does not qualify those capabilities.

Create a new run-owned document. Batch its source in `write_design`, preserve the
receipt and generate that exact saved revision. Read both MCP status and the
build's actual status and every component's feature errors. A successful transport may contain a failed build;
queued work and stale model metadata are not completed geometry.

Use lowercase snake_case feature IDs, distinct from requirement IDs such as R01.
The following pattern produced the measured four-hole block at revision 1:

```python
from steve import Model
model = Model("rectangular_four_hole_block")
model.box("block", length=60, width=40, height=12,
          at=(0, 0, 0), centered=False, name="block")
model.hole("h01", on="block.top", points=[(10, 10)],
           diameter=6, depth=None, kind="simple", name="h01")
model.hole("h02", on="block.top", points=[(50, 10)],
           diameter=6, depth=None, kind="simple", name="h02")
model.hole("h03", on="block.top", points=[(10, 30)],
           diameter=6, depth=None, kind="simple", name="h03")
model.hole("h04", on="block.top", points=[(50, 30)],
           diameter=6, depth=None, kind="simple", name="h04")
result = model.result()
```

These are the explicit hole operations from the retained successful source.
For this non-centered XY box, positive global XY points on `block.top` worked
directly. Subtracting half the box dimensions produced incorrect cuts. Do not
generalize this observation to arbitrary faces, sketches or transformed parts;
read the relevant references and measure the resulting geometry.

Keep face references as literal selector strings: `on="block.top"`. Do not
assign `block = model.box(...)` and then access `block.top`; the observed box
operation returns `None`. A 12 October first build made this authoring mistake
and returned an explicit `AttributeError` before generating geometry. Another
run used `on="XY"` at the block bottom and removed too little material. These
are our construction errors, not established provider defects.

The gateway's 12 October `read_design` annotations contain only its title, with
no `readOnlyHint` or `idempotentHint`. Wright therefore rejects an identical
completed call repeated within the same agent task. The explicit contract is
retained in `qualification/generic-render-binding-001/read-design-current-contract.json`.
Consume successful write/edit/generate receipts for their revision and native
metadata. Read the source when a revision-safe correction actually needs it;
do not add redundant post-generation reads or vary arguments to evade the guard.
This is an integration constraint, not a claim that an optional MCP annotation
is a mandatory protocol requirement.

Do not invent a physical material just to tint a body or pass `None` as a
required material name. With a declared material or reference-material assumption,
native appearance is supported by `component.material(material, bodies=None,
finish=None, color=None)`. Read the discovered `steve-materials` skill first.
It documents hex colors and finishes including matte/brushed; those affect
appearance while the library material supplies physical properties. IDs include
`stainless-304` and `abs`; validate any chosen ID through returned material
problems. A board/servo envelope using a labeled representation material does
not establish its physical composition or mass. Studio rendering/capture fidelity
remains separately qualified. The early blocks used downstream presentation
finishes; that does not establish a general absence of native appearance controls.

## Validate the exact revision

Record document ID, source revision and build ID. Confirm current source with
`read_design`. `inspect_model(view="isometric", checks=["machining"])` returned
actual bounds, solid counts, volume and cylindrical hole targets for these
blocks. Each hole included `diameter_mm`, `at_mm`, `axis` and `length_mm`.
The top point was at Z=thickness with axis [0,0,-1]; its other endpoint was Z=0.
Compare observations with the predeclared test plan, not only the source intent.

The four-hole result was 60 × 40 × 12 mm, one solid, four Ø6 × 12 mm bores and
27442.831973649212 mm³. The six-hole result was 80 × 50 × 16 mm, one solid, six
Ø8 × 16 mm bores and 59174.51368408604 mm³. Independent audits recompute volume,
positions, axes, revision identity and capture hashes from retained tool data.

Save returned MCP image bytes through declared Wright output ports. Check their
hashes and revision/build identities. Use isometric, top and front views. A front
view can correctly hide Z-directed holes. Renderings are visual derivatives;
numerical geometry must be checked from CAD measurements. Record each render's
actual capture input and resulting output hash; do not claim pixel equivalence.

Evaluate presentation after rendering and document completeness in the final
review. Those later checks should be explicitly deferred during CAD inspection.
Keep source-history provenance and workflow-reuse checks distinct from geometric
tests; their evidence belongs to saved source/run records. Do not invent extra
acceptance criteria merely to investigate a tool convention.

## Recovery and exports

On 12 October the discovered `generate_model` schema includes optional
`wait_s` (0–600 seconds). The selected Wright gateway call remains bounded to
120 seconds, so the qualified direct export uses 100. A still-pending result
does not authorize downloading or rendering. Both old and new build IDs may
report full mode at unchanged revision: retain the actual returned identity and
native geometry, and do not claim byte-identical STEP or an explained cache policy.
Run `646d7a74c124431e8979c3acea4b01de` completed automatic export, private file
transfer and three native views in 62.007 seconds. Its revision-7 STEP differs
in bytes from the earlier export while observed geometry agrees.

`read_design` in the current contract accepts the document ID, not a `revision`
argument. Check the returned document revision and model currentness. The
rejected extra-argument probe is retained as our authoring error. Native
`model.metadata.modeling.bodies` contains single-part body bounds. For an
assembly, `model.metadata.modeling.design.instances[].bodies` contains world
bounds, with colors/materials in `design.components[component].bodies[body]`.
These are actual built observations. They permit a renderer to match imported
surfaces without treating source code or repeated STEP labels as geometry proof.

Reconcile an existing document/build after timeout or queued status. Do not
create a second document to repair an uncertain submission. After a confirmed
failed build, a permitted correction reads the exact current revision and edits
one uniquely matching fragment. A multiple-match `edit_design` error explicitly
saved nothing in the observed failure; correct the unique match rather than
assuming an edit succeeded. Respect the accepted process's correction budget.

`generate_model` explicitly documents that the same revision joins its existing
pending build. The v7 bracket exposed a Wright replay-guard gap that rejected
this status observation as a completed mutation. The existing build later
completed with unchanged ID. The v8 process adopts a saved, bounded
[reconciliation contract](../../demos/mcp-pending-operation-reconciliation.md)
instead of introducing vendor logic into the executor. This is a Wright issue,
not a confirmed SteveCAD defect. Include the exact fixed arguments required by
the saved contract; never change revision or create a new document to poll.

The bracket's second box was already fused into `base_plate`; its subsequent
`combine` tried a nonexistent separate body and recorded a feature error even
though the top-level build succeeded. Read exact `op`/`body` behavior before
mixing implicit joins and explicit Boolean operations. Inspect component errors,
not just the final envelope and volume.

Avoid download tickets unless an export is actually needed. Use the documented
transfer origin and format, confine the destination, and keep credentials and
one-time commands out of evidence. The coupon STEP was checked for STEP
physical-file syntax and independently measured in the qualification records.
An export receipt alone does not prove valid or printable geometry.

The full robot revision-4 and revision-5 STEP downloads succeeded quickly through
the existing gateway, after separate native bodies_mesh timeouts. This qualifies
STEP at those revisions; it does not turn the timed-out mesh calls into success.
The revision-5 STEP SHA-256 is
`828f28cfdd4e3d50d59587f180e102616f5b85af8ffce83e81f9ac92ed296a55`.
An independent standard-format reader in the existing selected CAD environment
matches native volume and reports 119 solids across 110 placed children.
Five printed cradles have disconnected cylindrical bosses. Their single named
body, `op="join"`, feature status `ok` and top-level valid shape are insufficient
to prove one connected printable solid. Give added bosses finite joining volume,
then check actual connected topology. Tangent contact can leave separate solids.
These are source geometry defects, not confirmed SteveCAD bugs.

Repeated-instance STEP labels also repeat the first name. For these exports,
diagnostic meshes are matched uniquely by actual world bounds and native rounded
volume; labels alone do not establish identity. Preserve the matching evidence.
The selected reader was used as a library without network, not through AgentCAD
MCP, and does not qualify a new MCP installation. See
`artifacts/stevecad-demonstrations/robot-arm-media/corrected-rev5/`.

One multi-file `edit_design` batch adding new paths with empty `old_text` saved
the actual robot revisions. Inspect all retained files after the edit: a planned
hole or placement is not evidence it reached the saved CAD source. Revision 5
omitted palm holes and retained Y18 posts against Y23 bolts. Its cap bolts also
put heads on the wrong end when reusing a vertical profile with Y+90 rotation.
These are authoring defects with actual native overlap witnesses.

Use `Design.contact(a,b,kind="seated",max_overlap_mm3=0.0)` for each specified
zero-penetration bearing interface. `rigid` does not declare contact. Never use
threaded/wildcard allowances to hide missing clearance holes. Measure joint axes
as oriented geometric lines: changing a representative point along the same line
does not change the joint. A yaw representative Z40 is geometrically equivalent
to Z14 on the same vertical line; ±9.4 pitch X coordinates lie on their -X lines.
Preserve historical coordinate-only FAIL findings and test line equivalence in
new prospective plans instead of moving correct joints.

Robot FDM screens completed but included purchased items and reported unmeasured
bridges, positive features and support volume. Separate actual printed instances
from purchased washer/standoff wall findings. Whole-design success does not prove
all print orientations, support feasibility or physical fit. Revision-4/5 whole
native CAD captures also succeeded; this extends the earlier focused-capture
evidence without erasing previous whole-view timeouts. Continue visually checking
render derivatives against the actual captures: generated details/colors can
change even when an automated final review calls fidelity PASS.

Revision 6 corrects those source defects: all five absolute native poses clear,
33 saved motion samples clear, and independent STEP topology confirms 110 valid
solids across 110 placed instances. All printed instances are connected. The
actual standard-format meshes are closed and match native geometry within the
recorded tessellation volume error; fit/topology evidence is separate from FDM,
supports, physical printing and load/operation acceptance. See
`robot-arm-media/corrected-rev6/{manifest,mesh-verification}.json` and its native
STEP receipt. Actual CAD motion can be presented from these triangles and the
recorded native joint tree/axes/couplings/keyframes; label a neutral viewer and
retain both geometry and motion provenance. Never present animation as a new
collision or physical-operation test.

As assemblies grow, the latest complete read/build observations can exceed a
saved workflow's typed context allowance even after lossless representation.
Preserve the completed build and failed run, measure the recorded mandatory
context, and revise explicit configuration prospectively if justified. The
revision-6 continuation required 411321 transport bytes against a 400000 budget;
v13's versioned allowance is 1048576, within the existing supported contract.
No hidden prose policy, vendor workaround, evidence truncation or new executor
was added. An offline context check is evidence about representation only; a
fresh live process must still prove continuation and completion.

Fresh v13 completes all eight tasks and the six-image review in1117.18 seconds.
Execution completion differs from engineering acceptance. State exact count
subjects explicitly: five cradle instances reuse four definitions; six guide/
stand Palm bolts differ from the two additional gripper-retainer bolts. Do not
duplicate working geometry or silently alter a frozen plan to satisfy a wrongly
counted subject. Preserve the failed criterion and record a scope clarification
or prospective corrected plan. Hardware bearing contacts also need explicit
documentation, not only a native absence-of-overlap result.

One revision7 STEP request timed out without a transferred file. Keep verified6
exports labeled6, and reconcile the exact completed revision/build under the
provider contract before another request. Viewport show filtering did not scope
whole-design FDM, which used+Z; it does not prove all declared local print
directions. Record exact analysis scope and unresolved orientation/support work.
Three more attractive renderings still change board/base colors and details,
so verify final marketing selection visually against actual CAD.

## Carefully report real bugs

No SteveCAD bug has been confirmed or reported in these block attempts. Wrong
skill names, uppercase IDs, centroid subtraction, invalid material arguments and
ambiguous edits were authoring mistakes. Premature checks of future rendering
outputs were workflow instruction mistakes. Preserve them as lessons.

Follow the shared [bug evidence checklist](README.md#bug-report-evidence).
Do not guess a bug-report MCP operation: none was discovered among the 26 tools.
The documented route is signed-in **Feedback → Report a bug**, or **Report this**
on an error. Supply what happened and what was expected; optionally attach the
canvas capture. Inspect **What's sent with your report** before submission.
The form includes technical context, document/revision identifiers and recent
errors; document source is not automatically included. Add only the minimal
owned reproduction needed. **Saved / Waiting to send** means accepted for
queuing, so do not resubmit. Track the receipt through **My reports** and retain
its ID/status. Use the separate feature-request route for missing capabilities.

## Current limits

A later **confirmed visibility/identity defect** has an isolated two-instance
reproduction: document `17b6718f-d0e5-4a13-bcf7-48f3d963b7e8`, revision 1,
full build `627de50c-cdf4-40f5-ac77-7bccbd4e8b9d`, two error-free solids.
`show=["second_marker"]` draws extent X100..110 but reports
`drawn.instances=["first_marker"]`. The first-instance control reports extent
X0..110 rather than X0..10, including both instances. Current live
`api_reference("inspect_model")` promises selection by instance and exact drawn
identities. Native text/structured responses agree; the build/source contain
correct distinct instance names and placements. This is distinct from the
robot's legitimate collision findings and the unconfirmed timeout causes.

The minimal source, requests, responses, native images, checksums and report
instructions are under
`artifacts/stevecad-demonstrations/qualification/stevecad-visibility-repro/`.
`visibility-reproduction.zip` is prepared **not submitted**; no report ID exists.
Use the supported signed-in Feedback route and inspect its payload before one
submission. No reporting MCP operation or signed-in Studio browser-control
runtime was available in this session. Do not invent a report receipt.
Until corrected, treat repeated-instance visibility labels as unreliable;
retain actual extents/source placements and do not claim a selected instance
is verified from `drawn.instances` alone. The robot gripper capture audit
preserves its corresponding label failures.

Block geometry passed independently. The generated reviews retain provenance
findings; inspect the exact reports rather than treating process completion as
an engineering acceptance. One six-hole HTML review also overflows horizontally
at the tested desktop viewport. The bracket's v8 run completed with six images
and a review without browser overflow; envelope, holes and volume pass, while
upright thickness is unverified. The joint's v9 run now completed with six
images and a review; its independent arithmetic/identity audit passes geometry
and reported sampled motion. The generated review preserves an axis-convention
FAIL against its own generated specification and unverified FDM screening.
Do not substitute the arithmetic audit for that original verdict. A 12-second
neutral CAD-viewer clip uses the actual native STL meshes and returned joint
keyframes; it is not a SteveCAD Studio screen capture or physical operation.
The robot's v11 correction generated revision 3 with 51 solids, no component
feature errors and valid `fdm-petg` material assignments. It stopped on genuine
native fit/motion failures; no robot acceptance is established. The earlier
`petg` ID was unknown; the actual successful correction confirms `fdm-petg`.
Native images for the larger arm have timed out, as has one revision-3 mesh
download request. Preserve those error receipts; do not repeatedly request the
same unavailable export or substitute viewer images as Studio captures.

Focused revision-3 native captures succeeded quickly with documented `show`
selectors: `show=["upper_arm"]` and
`show=["palm","finger_*","guide_cover","servo_gripper","horn_gripper","saddle_gripper"]`.
The returned `drawn.instances` and extents describe only the visible subset;
the general `measurements` still describe the whole assembly. Preserve both
scopes. These actual MCP images retained uniform coloring despite native
`fdm-petg` color/finish metadata. Native material assignment and rendered Studio
appearance are separate qualifications. One whole revision-3 view still timed
out; the focused successes do not establish whole-assembly capture or exports.
See `artifacts/stevecad-demonstrations/robot-arm-media/corrected-rev3/`.

Use absolute fit results as well as animation results. The revision-3 animation
reported moving clashes separately from `at_rest` pairs; all five fit checks
included `rest` plus their requested pose. A small moving-collision list does
not establish a clear home assembly. Closed box cradles can trap a motor even
when envelope gaps pass. Offset faces and rigid-group membership do not prove
physical attachment; inspect actual seats, mounting webs and retained hardware.

The assembly, motion and DfAM skills have now been read and their receipts saved
beside the discovery record. They document exact-solid fit and sampled collision
checks, geometry-derived joint axes and per-instance print settings. The Print
set, simulation-model and video exports are Studio UI operations; no MCP tool
for those exports was discovered. `generate_model` supports downloadable STEP,
per-component STEP and per-body STL artifacts. Do not claim a print-set or video
export from an MCP receipt that lacks it.

## Purchased hardware references

Use `find_standard_parts` before inventing detailed purchased geometry. Actual
queries for the robot returned `servo_micro_metal_mg90s_envelope` (analytic
simplified, MIT catalog source) and no `MG996R` result. An envelope match is not
evidence of mounting-ear, horn or shaft accuracy. Preserve query receipts under
`artifacts/stevecad-demonstrations/robot-hardware/provider-discovery/`.

`api_reference("Model.import_step")` reports uploaded STEP by import ID or
SHA-256, with one body per solid unless `solids` restricts it. For local files,
`request_upload` requires the exact filename, byte count and checksum; its ticket
is single-use and expires in ten minutes. Consume its documented transfer in
memory and omit the ticket/command from shared evidence. Verify `list_imports`
reports ready, then generate and inspect the resulting reference. A downloaded
manufacturer file, an upload receipt and a validated built part are distinct.
The CM5 upload is ready and the owned reference document
`9ad39028-139c-4810-8410-06b5b826933d` revision 1 has a successful preview:
1076 solids, 55 × 40 × 4.621 mm, build
`f3e4d6ce-9c84-423b-86da-ed220642a83f`. Full generation and capture requests timed
out. A successful preview is not a verified full export. Preserve the existing
document rather than creating another; use a declared clearance envelope for
initial dependent designs when detailed reference qualification is unavailable.

The first joint's combined machining/image request timed out. Separate
image-only views and machining with `view=null` subsequently succeeded quickly
at the same revision/build. Accepted v9 separates these observations and reuses
actual built fit/animation metadata when it already covers declared tests. FDM
screening still timed out; it remains unverified, and this alone does not prove
a provider defect. Never repeat an unavailable screening until it appears green.

## Exact export reconciliation and actual print orientations

Revision7's first STEP-download observation timed out. A subsequent `read_design`
of the exact revision/build reported the already cached STEP artifact and a
successful build; one documented retrieval then delivered the exact STEP.
Preserve the original timeout and reconciliation receipt. This read establishes
why retrieval is safe; a timeout alone does not justify another build or design.
Consume transfer credentials in memory, verify the STEP signature/bytes, and
omit one-time commands and tickets from shared evidence. See
`artifacts/stevecad-demonstrations/robot-arm-media/corrected-rev7/`.

An independent standard-format reader measured110 valid placed solids at this
revision. STL tessellation is a downstream presentation/print-format operation;
its imported shape must match actual native instance bounds and volume. Repeated
STEP labels still name first instances, so do not map by label alone. Actual
unique bounds plus rounded volume match all110 instances. Each of18 printed
definitions is one connected solid; this supersedes the failed revision5
export only for revision7, not historically.

Native print directions are local to the component. Inverse the actual world
placement before applying the proper rotation into printer+Z, then translate the
bed minimum to zero. Tray uses−Z; links, palm, fingers, caps and cradles use+X;
the other declared printed definitions use+Z. The18-file/28-piece kit verifies
closure, winding, connectivity, transform roundtrips and the220×220×250mm build
envelope. These checks do not prove supports, slicing or physical fit. Whole-design
DfAM with `show` did not scope its selected parts; that observation is not an
acceptance of each declared orientation.

The existing [Blender MCP](blender-mcp.md) consumes the checked exact meshes and
produces three native geometry renderings, preserving simple board/motor shapes.
The original screenshot-derived AI images changed geometry and remain diagnostic.
Supplemental native rendering is not yet a proven saved-process handoff. The
curated review and unpublished marketing files keep these scopes separate.

## Native workflow presentation and requirement provenance — 12 October

The generic main-process handoff is now exercised on actual blocks. V16 and
v18 each export the newly inspected revision through the private transfer,
AgentCAD mesh validation and three Blender views, with actual file hashes and
body matches checked. See `prompt-to-reviewed-cad/block-native-003/` and
`block-native-005/`. This supersedes the earlier pending statement for those
block runs only; assembly reuse and final overall acceptance remain separate.

The first renderer fallback `#a8b4be` failed the original neutral-gray finish
requirement. V18's `#aaaaaa` fallback fixed the three derived renders, but its
generated plan expanded rendering finish into a six-image CAD-capture color
test. The original raw CAD images are green/cyan. Preserve that original failed
review and record the requirements-authoring conflict; it does not establish a
SteveCAD defect. `Model.material` documents physical material assignment with
optional appearance metadata; the retained inspection contract does not promise
a color-control option for its returned images. Do not invent one.

Pass the supplied prompt to specification, test planning and final review. Keep
supplied requirements distinct from implementation and presentation choices;
do not invent an assembly-transform test for a stationary part or a different
signed camera direction when only a named view was requested. If a user does
explicitly require a CAD display finish or camera, preserve it and report any
missing capability. A prospective authoring correction must not rewrite a
completed plan or change a failure to PASS retroactively.

V19's original four-hole assignment now completes with 8 CAD-stage PASS and
10 final-review PASS in 617.248 seconds. Exact source, original provider
observations, independent numeric/handoff audits, six image files and separate
visual/browser checks are under `prompt-to-reviewed-cad/block-native-006/`.
The returned `write_design` and `generate_model` URL uses `?document=`; preserve
that provider-returned URL rather than replacing it with the `?model=` form
seen in some browser sessions. Its authenticated browser destination was not
independently exercised by this report check. Changed-prompt reuse of v19 and
assembly-main-process qualification remain separate at that checkpoint.

Same-source six-hole reuse subsequently completed in 542.533 seconds; all
supplied final-geometry numeric checks and native image-pair checks pass.
`six-hole-native-001` preserves an extra generated intermediate-stock-state
requirement as UNVERIFIED. Do not turn a geometric definition such as union or
subtraction into a mandatory historical CAD snapshot unless the user requests
that history. Test the final artifact using the required measurements. A missing
unrequested intermediate state is a planning-provenance issue, not a SteveCAD
geometry defect. Exact reuse evidence is `qualification/generic-render-binding-001/v19-reuse-audit.json`.
### Sampled collision results versus actual clearance

An animation's `clear:true` / zero new collisions is not a measurement of every
required minimum distance. Preserve its documented baseline and sampling scope.
The robot's five absolute native fit checks and 33-sample motion evidence were
supplemented on 12 October by a passive exact-STEP audit: 28 printed instances,
353 non-seat and 25 declared-seat pairs at 38 total states. All 14,364 pair checks
pass, with a minimum non-seat distance of 0.400 mm and zero measured overlap.
See `qualification/robot-sampled-clearance-001/` for every measured pair, input
hashes, native kinematics, selected reader and numeric kernel tolerances.

That audit uses the existing selected CAD library directly, not SteveCAD or
AgentCAD MCP. Keep this attribution distinct from native server results and the
original durable workflow review. It resolves the sampled numerical evidence
gap without changing CAD; it does not prove continuous collision freedom,
physical fit or hardware stack completion. Never relax a declared clearance or
invent intended contacts to make a measured interference disappear.
