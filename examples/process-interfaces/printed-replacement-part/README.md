# Printed replacement-part working-interface example

**Status:** two runs of one configured saved process complete actual native
construction/repair, external slicing, inspection and the original source gate.
Each has twenty outputs, seventeen passes and mandatory review blocked.
Actual-model generation/preview/save/update and unchanged second-run reuse/parity
are verified. Earlier failed consumers and skipped gates remain intact. Fresh
qualification, migration and final installed acceptance have remaining scope. See the
[proof record](../../../specs/083-process-working-interfaces/evidence/printed-proof.md).

This retains the original focus-wheel assignment, image, dimensions, materials
and full 082 validation profile. It prepares a digital manufacturing package;
it does not certify fit, strength, printer compatibility or physical printing.

## Original drawer-handle scenario

Bindings can explicitly select `"scenario_id":"printed-replacement-part-02"`.
Omitting it retains the existing wheel (`printed-replacement-part-01`). Other
scenario IDs fail before staging. The handle requires
`"orientation_comparison":true` and `"run_path_template":"wright.run-path/1"`.
Its [frozen assignment](scenarios/printed-replacement-part-02.json) and
[versioned instructions](scenarios/printed-replacement-part-02.instructions.json)
preserve the original 96 mm mounting scale, six original input files, exact full
profile, five walls and 40% infill. The wheel's native-inspection and retained-source
bindings are rejected for the handle. A supplied geometry basis must explicitly
declare this handle's scenario ID; provider operations still require independent
qualification.

The handle proposal retains all 10 original requirements and 18 checks. It adds a
declared, persisted local review of the actual repaired mesh, geometry-only preview,
measurements and original requirements before **any** slicing. The original-frame
repaired mesh remains the full-profile validation subject. The auxiliary study
derives pads-down and side (+90° X) candidates from those exact bytes, records
transforms and hashes, checks candidate integrity, and compares actual package
and support-path evidence with unchanged profiles. Rotated side dimensions are
checked against the declared build transform; they do not replace or weaken the
original model-axis envelope checks. Support-contact locations and removability
remain explicit final-review work.

**Qualification:** source preparation and numerical/lineage fixtures are verified;
no live handle run is established by these declarations. Without `slice_binding`,
the existing `slice_model_file` schema, qualified `ok` response and
`actual_local_bambu_slice` contract remain required, with a pads-down final package.
The separate explicit Orca binding below uses its actual response and file contract.
No correction or arbitrary partial recomputation is claimed by preparation tests.

The `replacement-drawer-handle` catalog starter and this prepared process have
different block IDs. Optional `workflow_id` preserves the exact existing starter's
source identifier (lowercase letters/digits/underscores, starting with a letter).
`source-transformation.json` records all seven starter roles and their prepared
task IDs; this is inspectable metadata, not execution or UI compatibility authority.
`scenario-binding.json` records the starter/scenario origin;
`preparation.json` records the original base-template hash and exact proposed-source
hash. Accept this transformed proposal through the normal workflow-source service,
then bind/open its resulting accepted revision and exact subjects. A starter tab
does not automatically become this prepared process, and an interface saved for
the starter needs compatibility checking or the common-view fallback. Neither
preparation nor import transfers run/review authority. See the
[Feature 084 handoff](../../../specs/084-first-contact-experience/evidence/handle-preparation.md).

### Explicit Orca 2.4.2 / standard 3MF binding

For Printed02 only, the selected independent server must expose the fresh exact
`shell_execute` schema. Declare this additional binding, retaining the other
geometry/files/inspection/profile settings:

```json
{
  "slice_binding": {
    "kind": "orca-shell-3mf-v1",
    "engine_version": "2.4.2",
    "executable": "/opt/orca/AppRun",
    "workspace_mount": "/the-qualified-workspace-mount",
    "selected_orientation": "pads_down",
    "original_process_profile": {
      "path": "/path/to/unchanged-original-process.json",
      "sha256": "the exact original file digest"
    }
  }
}
```

`selected_orientation` accepts `pads_down` or `side`. The selected process profile
must differ from the pinned original only in `tree_support_wall_count`, from
`"-1"` to `"0"` for Orca automatic support walls. Any additional difference fails
before staging. Both exact files, original/derived validation references, mapping,
selection and [versioned instructions](scenarios/printed-replacement-part-02.orca-instructions.json)
join the initial review and portable source dependencies. Preparation does not
install or qualify an engine. Use the actual qualified provider/image/profile
configuration described in [provider readiness](../../../specs/084-first-contact-experience/evidence/provider-readiness.md).

The accepted source prepares two standard Core3MF files from the unchanged repaired
STL, keeping model vertices/triangles in original axes and expressing orientation
as a build-instance matrix. It slices each once through the existing MCP runtime,
then independently reads actual native results, effective profiles, engine header,
package geometry and nominal layer paths. It never invokes the unqualified native
rotation flags. The shell's warning text or `isError:false` does not establish a
successful native slice; actual `result.json`, settings and package bytes are
required. Missing/unsupported contracts fail explicitly.

The derived profile retains all 10 requirements and the original checks, changing
only the slice-lineage operation label to the explicit Orca provenance contract
and adding prepared-file identity. It adds independent checks for both candidate
geometries, native results, engine headers, original package inventory and effective
settings: 43 checks total. Model-axis envelope checks still read the original
repaired STL. A 0.0001 mm serialization correspondence bound handles float32
recentering; engineering dimensional requirements are unchanged. See the
[independent reader evidence](../../../specs/084-first-contact-experience/evidence/standard-3mf-reader.md)
for controls and conservative ordering limits.

The selected package remains connected to final review, validation and the clearly
simulated handoff. Changing selection requires an accepted revision and fresh
affected preparation/package/review/receipt subjects. The other candidate never
promotes itself. Real handle outputs, exact required native member names, support
contact review and correction/reuse behaviour still need live proof. Initial
review includes the declared per-block limits and explicitly unknown time/cost
estimates through the common view; no whole-run or spend cap is implied.

## Prepare the process

1. Select an isolated Wright workspace and existing independent geometry,
   offline slicing and engineering Python MCP providers. Qualify their actual
   schemas and native host requirements. This example uses Blender geometry,
   an existing offline slicer capability and passive package inspection through
   the selected Python provider. The inspection is supporting work, not a third
   substantive engineering application.
2. Configure the slicer externally with its complete machine/process/filament
   profiles. Keep the original PETG, P1S 0.4 mm, 0.20 mm layers, four walls and
   35% infill. Export the actual files and their SHA-256 digests; preparation
   verifies their bytes and original structured requirements. Wright does not
   resolve vendor presets or change device settings.
3. Export the selected workspace's workflow-source tools from Wright. Required
   entries include the actual server IDs, prefixed names and schema digests for
   `execute_blender_code`, `slice_model_file`, `run_simulation`,
   `write_text_document` and `inspect_file`.
4. Copy `bindings.example.json` to private configuration, replacing placeholders
   with the exact enabled providers, profile paths/digests, Python provider mount
   and qualified slicer success semantics. Record bounded `geometry_guidance`
   describing the selected native application version, actually qualified
   import/export calls and safety limits. This guidance is frozen as an input to
   geometry stages; it does not establish engineering acceptance or bypass the
   provider's safeguards. Use a `test://` destination. Run:

   ```powershell
   .venv/Scripts/python.exe examples/process-interfaces/printed-replacement-part/prepare.py --workspace ABSOLUTE_WORKSPACE --attempt wheel-ui-001 --tools PRIVATE_TOOLS_JSON --bindings PRIVATE_BINDINGS_JSON
   ```

Preparation writes a fresh proposal, frozen inputs and manifest under
`process-proofs/printed-replacement-part/<attempt>`. Existing attempts cannot be
overwritten. Accept the proposal through Wright's normal workflow-source service
using the manifest's `accepted_source_path`; verify the accepted storage digest
against `source_sha256`. Preparation creates no run or review authority.

The example bindings explicitly select `wright.run-path/1`. One accepted process
can then prepare distinct output directories for backend-assigned runs. Geometry
exports, slicer package, retained provider response, package-inspection job and
simulated receipt use that run identity. Requirements, image, profiles, passive
inspection source and any retained mesh remain unchanged supplied inputs.
Legacy private bindings without this declaration retain their earlier paths.

If supplying `geometry_operation_files`, configure construction and repair
recipes with explicit `{{wright.run_id}}` paths and owned object names before
pinning their hashes. Fixed recipes are rejected for a reusable configuration;
Wright does not rewrite vendor code. These template inputs retain their original
hash plus a separate resolved-content hash. Presence of a token does not qualify
native effects or prove that all provider writes remain within the run directory;
qualify those actual recipes through the existing provider process before use.
The connected package representation pins the exact handoff artifact. The receipt
is a declared output bound into the existing approval/dispatcher, rather than
a token in its authority settings. Reopening a view never replays that action.

Open the accepted workflow in the workspace and use its common working view to
prepare immutable inputs and check readiness. Generate and refine a tailored
interface through Wright's UI authoring control. Native/provider readiness and
predictable choices belong before execution; reviews are declared in the process.
Construction and repair each have a bounded 360-second task allowance with at
most two geometry calls. A timeout retains completed native operations and
partial files; their existence does not complete the step or authorize a retry.

## Engineering handoffs

An optional `native_inspection_operation` binds an existing provider's `server`,
`tool`, and `arguments_file` (`path` plus `sha256`). It requires a configured
current construction producer with `native_cad`, `neutral_cad` and `source_mesh`
ports. The preparer connects those exact current-run files to native inspection
and drawing, then applies the versioned `native-inspection-profile.json` before
mesh repair and slicing. Profile version 2 retains the original eleven supplemental
checks and adds nine checks of named functional drawing observations. It does not replace the original eighteen-check profile
or any human/physical requirement. The final review receives the measurements,
native/SVG/PDF drawing, a passive PNG preview, matrix, criteria and assessment from this same run.

The drawing uses native linked dimensions for the envelope, scallop radius,
socket radius/across-flat/depth, overall and hub heights, roof at the axis,
section grip span and exposed round. The full native section carries its cutting
line and hatch; the enlarged socket view uses the actual planar CAD section.
The PNG is a QtSvg rendering of the exact native SVG, with both hashes retained.
No dimension value is overridden and no AI illustration defines the geometry.
The matrix includes the observed dimensions and a proposed physical inspection
plan. Manufacturing tolerances, fit, strength and human drawing acceptance remain
separate. Accepted earlier processes retain their pinned version 1 instructions
and criteria; only a newly accepted revision uses the new drawing and profile.

`wheel-inspection-operation.py` is an authored FreeCAD provider argument, not
Wright execution code. Its default input mode retains pinned upstream hashes.
For a same-run handoff, an explicitly accepted `workflow_dependencies` mode
records the bytes it consumes after Wright verifies declared producer-file
dependencies. Run-path templates allocate new files for each run. Missing native
ports/providers or changed argument files block preparation before staging;
native tool failures and failed checks hold downstream work. These declarations
alone do not establish live capability or engineering acceptance.

- Interpret the original 38 mm wheel, six scallops, D socket and clearance, blind
  depth, front hub and grip features. Persist a declared basis review.
- Use the existing geometry MCP to create actual source STL, then repair, measure
  and orient it. Keep distinct source/repaired bytes and a geometry-only image.
- Pass the repaired STL and exact profile dependencies to the existing offline
  slicing capability. Its actual 3MF is the next stage's package.
- Retain the real slicer response through Wright's existing document tool. Passive
  inspection consumes that response, repaired STL, 3MF and profiles as explicitly
  connected, digest-checked workspace files. The existing bounded 3MF/G-code reader
  produces nominal layers with model/support/unclassified paths; it executes no
  machine instructions.
- Summarize measured facts and outstanding limits. A separately enrolled private
  test handoff may write a labelled simulated receipt, with no network dispatch.
  The declared engineering review then presents the exact validation subjects
  and original requirements. Its typed review binding identifies the unchanged
  profile and all six review-required requirements. Only after this review does
  the full 18-check profile assess those subjects. An integration-test response
  cannot supply the mandatory authenticated human review. This order avoids an
  unreachable review after a validator that already requires that decision.

The passive inspection operation records the selected provider's qualified success
contract as the basis for CLI success. That is not an independently observed exit
code or engineering approval. Unsupported package/motion semantics fail explicitly.
Source geometry, slicer success, nominal preview, measured compliance and physical
acceptance remain separate claims.

Inspection also emits `toolpath-summary.json`: at most 64 KiB of actual layer/
classification counts, package identity, reader provenance and the full preview's
path/hash. The report consumes that summary, leaving the large layered path data
for the viewer and exact validation. It does not replace or truncate the preview.

For a large full preview, explicitly qualify the validator's computational
budget before preparing a new source. Optional `validation_resource_budget`
uses the existing `ResourceBudget` contract, for example
`{"max_entities": 1000000}`. Other defaults remain 16 MiB, 120 seconds and
512 MiB; the contract caps entity count at two million. Count actual structured
preview nodes when qualifying the setting. This is a bounded reader capacity,
not an engineering tolerance or acceptance threshold. With no declaration the
original 100,000-entity default remains. Never truncate the full preview or
replace its mandatory subject with the report summary to get a passing check.

If the qualified slicer emits separate startup, layer and shutdown sections,
private bindings may declare `nominal_layer_section` with exact `start_marker`
and `end_marker` comment lines. Inspect those markers in the actual package
first. The passive reader requires one ordered pair and explicit axis/unit/
extrusion modes inside the selected body; unsupported body semantics still fail.
It retains the full package/G-code hashes, selected text hash and excluded line
counts. This is a nominal layer view: excluded machine setup/shutdown, firmware
conditionals and physical execution remain unverified. With no declaration the
original complete-file parser remains strict. Wright has no vendor command table.

## Intended working interface

### Optional frozen native operation inputs

For an isolated repeat of a previously inspected modelling approach, bindings
may supply `geometry_operation_files`, with exactly `basis`, `construction` and
`repair`. Each entry contains a file `path` and its `sha256`. The basis is a JSON
proposal with `proposed_geometry` and `engineering_acceptance: false`; each
operation is the selected geometry provider's JSON `{"code": "..."}` argument.
Files must be bounded and pinned before preparation. Configure output paths and
uniquely owned names for the fresh attempt before pinning them.

The existing scoped AI tasks receive those frozen inputs and are instructed to
use the supplied operations unchanged. They do not run locally in Wright's
preparer. This does not make model compliance deterministic: retain and compare
actual submitted tool arguments, outputs and measurements in the live proof.
Keep provider qualification and any recipe adaptations explicit. The default
AI modelling path remains available when these inputs are absent.

In AI-task mode, construction receives the original prompt, image, use context
and user profile directly alongside the reviewed numeric basis. Repair receives
the original prompt/context/profile and actual upstream geometry. Both tasks
instruct the model to preserve the original prompt in the provider's `user_prompt`
argument. The image is supplied to the AI task; the native code tool does not
accept an image argument. Inspect actual model/tool evidence to establish that
these inputs reached the provider operation; preparation tests alone do not prove
model compliance or geometry correspondence.

For qualified supplied operations, private bindings can explicitly select
`"geometry_operation_mode": "configured_tool"`. Construction and repair then
use the existing configured MCP binding with the pinned JSON as its connected
arguments, a 360-second allowance and retained provider response. The original
scaled image is consumed by AI basis interpretation before the declared review;
it is not passed to a tool that only accepts code. The review includes unchanged
copies of both operation templates and the application qualification guidance.
Those review documents are distinct from the run-resolved argument inputs:
their original bytes remain frozen, while the actual call retains its resolved
content identity. Required source/repaired/preview files and the source-file
dependency remain explicit. The operation executes through the normal provider
gateway, never in the preparer. The provider still owns native implementation
and safeguards. This option requires all three pinned operation inputs; a missing
or unsupported mode fails before staging. The default remains `ai_task`.

This is for replaying an explicitly configured and qualified modelling approach,
not for converting an arbitrary new prompt into geometry without AI. Qualify the
recipe against its proposed design and application before selecting this mode;
the final engineering gate still measures the actual output. Current evidence
proves preparation/compilation/run-path binding and actual configured016
construction-to-source-gate execution in two isolated runs. Each uses its own
output paths and assessment; original mandatory human review remains held.

The supplied basis still waits at this run's declared review; all original
assignment, profiles, native file dependencies and full 18-check validation
remain. The AI-task mode retains its two-call bounds; configured calls invoke
the supplied operation once. A recipe hash is not measured compliance or engineering
acceptance. This mechanism supplies provider inputs; it adds no device protocol,
local code executor or new process runner.

Construction and repair can also select their existing bindings independently:

```json
"geometry_operation_modes": {
  "construction": "ai_task",
  "repair": "configured_tool"
}
```

When present, this complete two-entry selection overrides the scalar mode for
those stages. The scalar mode and default remain supported. Both values must
be `ai_task` or `configured_tool`; unknown, incomplete or invalid selections fail
before staging. Any configured stage requires the same three pinned inputs.
Its unchanged operation template and qualification guidance join the declared
basis review. An AI construction stage retains the original prompt/image/context
handoff; a configured repair stage imports that run's actual source STL through
the existing file dependency and gateway. This allows a qualified repair to run
without asking AI to retranscribe its code. It does not permit fallback after
an uncertain or failed operation, replay a run, or weaken the final checks. Choose
and accept the stage bindings before a fresh run; preserve previous failures.

### Independent native construction provider

A fresh configured construction can explicitly select a different existing MCP
provider while retaining the Blender repair/orientation stage and offline slicer:

```json
"geometry_operation_modes": {"construction": "configured_tool", "repair": "configured_tool"},
"construction_binding": {
  "server": "your-enabled-native-cad-server",
  "tool": "execute_code",
  "outputs": {
    "source_mesh": "source_mesh.stl",
    "native_cad": "native-design.FCStd",
    "neutral_cad": "native-design.step",
    "cad_preview": "native-design.png",
    "native_measurements": "native-measurements.json"
  }
}
```

This is an explicit example configuration, not a provider fallback. Preparation
requires the fresh exact tool/schema and the pinned construction recipe before
staging. The recipe must actually produce every declared output in the run's
unique directory; output declarations do not execute CAD or establish compliance.
Its supplied basis and recipe still join the declared review. Native API calls
remain in the accepted operation supplied to the independent provider, not in
Wright's executor or gateway. The original source STL handoff, repair ownership,
PETG profiles, simulated-only destination and eighteen-check gate remain intact.

Additional native artifacts have inspectable file ports and required-output
checks. Their engineering criteria must be assessed by an explicit additional
validation profile; they are not extra subjects silently added to the original
profile. Without this binding the previous producer remains unchanged. A retained
source consumer cannot also select a new construction producer. Different run
bindings allocate different output paths through the existing run-path contract.

### Explicit repair completion before slicing

For a fresh configured repair recipe that declares the final `W083_FINAL_REPORT`
record, supply an optional `repair_completion_operation` binding with `server`,
`tool`, and `arguments_file: {path, sha256}`. This is an authored operation for an
existing independent Python-capable provider. The preparer freezes the arguments
and checks capability availability before staging. It does not infer success from
free-text error wording or the existence of partial exports.

The new steps retain the actual repair response as `repair-provider-response.json`,
inspect its final record and exact files, and run the original five mesh checks
plus the explicit completion check before slicing. The original full 18-check
profile and final engineering reviews remain unchanged. A missing completion
receipt or failed required check holds dependent work. These checks establish
their declared digital scope only, not physical fit, strength or human acceptance.

`repair-completion-operation.py` needs the inspector's paths for `response_path`,
`source_path`, `repaired_path`, `preview_path` and `output_path`. Also declare
`producer_path_style` (`windows` or `posix`) and `producer_output_paths` containing
the exact producer paths for `repaired_mesh_stl` and `geometry_only_preview_png`.
The producer and inspector may use different mounts or operating systems. Compare
complete declared producer paths using that convention, not just their filenames.
Use the existing run-path token in all run-specific argument paths and preserve
previous failed runs. A retained-source consumer needs its own explicitly bound
early gate; this optional fresh-producer declaration does not invent that binding.

### Native preview and drawing identity

The authored native construction recipe binds the exact document's view and
allows bounded display updates before capture. It retains blank attempts and
fails if all three captures are blank. Its sampled pixel check detects an empty
frame; it does not verify geometry or replace visual review. Construction is
never retried by this display check.

The downstream `wheel-inspection-operation.py` recipe requires `drawing_number`
in its accepted configuration (1–20 uppercase letters, digits or hyphens). Each
new inspection retains the exact native/STEP/STL hashes and its own drawing
identity, so another run's title-block revision is not inherited silently.

### Separate consumer of retained geometry

If a producer created useful geometry before a later technical failure, do not
replay that producer or rewrite its terminal record. An explicitly prepared new
consumer may supply `retained_geometry_source` with exactly `mesh`, `observations`
and `origin`, each pinned by `path` and `sha256`. The mesh must be an actual binary
STL with at most 80,000 triangles; observations are a bounded JSON object containing
the actual native construction response. Origin must contain:

```json
{
  "producer_run_id": "the-original-durable-run",
  "producer_source_path": "workflows/original.workflow.wflow",
  "producer_source_sha256": "64 lowercase hex characters",
  "producer_status": "failed",
  "mesh_sha256": "64 lowercase hex characters",
  "observations_sha256": "64 lowercase hex characters",
  "engineering_acceptance": false
}
```

These are supplied lineage records, not authenticated engineering acceptance.
Use a fresh attempt and configure/pin the repair operation for that attempt. It
must import `inputs/retained-source.stl`, export unchanged imported geometry to
`outputs/source_mesh.stl` before repair, then actually produce
`outputs/repaired_mesh.stl` and `outputs/mesh-preview.png`. The first export is
derived native geometry; byte identity with the retained input is not implied.
Inspect the actual provider response and original/derived measurements.

This mode omits fresh construction and invokes the explicit repair operation
through the existing configured MCP operation, rather than asking AI to repeat
a supplied recipe. It still reviews the supplied proposed basis, slices through
the existing provider, preserves original profiles and the full eighteen-check
gate, and retains final mandatory engineering review. Required outputs must
actually be updated by their producing task. The supplied origin and observations
remain inputs to the final report. Preparation, source acceptance, readiness and
starting the new consumer are separate operations; preparation itself executes
no code and grants no physical authority.

Present the original image and requirements, preparation readiness and current
tool operation. Let the user inspect actual source/repaired geometry, nominal
layered toolpaths, material/profile correspondence, measured findings and declared
reviews. Link to exact artifacts and producing blocks in Wright workspace tabs.
Use only backend-permitted actions; retain the common-view fallback. This digital
proof must not expose a physical print command or infer camera/machine status.

### Native drawing projection readiness

The accepted inspection operation must wait for actual TechDraw projected edges
before selecting dimension references. A fixed sleep failed on a fresh isolated
FreeCAD host although the views became available later. The example now services
GUI callbacks while checking every required view, with a 30-second deadline and
an explicit diagnostic naming any unavailable views. It records wait timing in
the measurement report. Existing feature, dimension and geometry checks remain
required; projection availability alone is not drawing verification. Adopt this
operation through a new accepted argument/source revision and fresh run, retaining
failed attempts and their native documents.

### Orca response handoff and report inputs

The explicit Printed02 Orca binding saves each actual successful shell MCP
response through Wright's existing response-file owner. The slicer declares
`saved_response_file_port`, `save_output: true`, its exact `output_filename`, and
`file_policy: "publish_overwrite"` with `run_path_template: "wright.run-path/1"`.
The response becomes a hash-bound file output before the inspector runs; the
native package, native result and effective settings remain separately verified
provider-created outputs. Both response files also feed comparison and review.
No separate workspace document writer or file-read tool is required by this
Orca preparation.

The source report is an ordinary AI task with exact construction/repair records,
original requirements, slice evidence, nominal toolpath summary and orientation
comparison references. Version 2 of the Orca instruction asset limits each
inline reference to 32768 bytes and requires explicit unresolved findings when
contents or observations are unavailable. It grants no engineering acceptance;
the declared reviews and all original/derived validation checks remain required.
The existing synthetic transfer is still an explicitly separate test-only
boundary, not a customer printer connection or physical authority.

The shared response-file declaration also supports `publish_indexed`, using the
actual exclusively allocated indexed filename as the downstream file identity.
The existing `indexed` and `overwrite` settings retain their previous timing.
Older runtimes reject the new policies; use a compatible runtime and accept an
explicit source revision before running this binding. Already accepted workflows
and legacy wheel preparation retain their saved instructions and behavior.

### Installed drawer-handle setup

The installed application includes the Printed02 Orca setup recipe and its
canonical versioned assets. Open an unchanged **Replace a broken drawer handle**
starter in the workflow editor and choose **Set up this job**. Setup lists exact
compatible tools already enabled in that workspace. It requires the same absolute
managed POSIX workspace mount in all selected providers; this recipe does not
infer equivalent mounts or provision native applications.

Select four JSON files already present in Files: the P1S 0.4 mm machine profile,
the original process profile, its Orca-compatible copy, and the PETG filament
profile. No slicer profile is redistributed by this recipe. The compatible copy
must retain every original process value except string `tree_support_wall_count`
changes from `"-1"` to `"0"` for Orca's automatic support-wall setting. All original
engineering requirements remain, including 0.20 mm layers, five walls and 40%
infill. Setup copies the exact selected bytes into an immutable proposal inventory;
subsequent edits to the original files do not alter those inspected snapshots.

Inspect the proposed source, exact tool/schema identities and dependency hashes,
then explicitly accept the revision. Acceptance preserves the workflow identity,
starter origin and saved workflow instructions through the normal source CAS.
The proposal binds only shipped trusted construction/repair operations; the HTTP
setup route accepts no Python code. It makes no model or engineering-tool calls,
does not approve reviews, and does not start a run. The customer route uses the
manual local simulation capability for the final digital receipt; repository
examples retain their explicit private test binding. Neither route prints a part.

This first recipe supports an unchanged starter. Preserve edits and use a fresh
starter rather than overwriting an authored process. A changed tool schema,
recipe, accepted source or staged dependency requires a fresh proposal. Missing
providers remain actionable setup requirements, and native/engineering
qualification still requires actual subsequent evidence. The source, common view,
reviews and original/derived validators remain the execution and evidence owners.
