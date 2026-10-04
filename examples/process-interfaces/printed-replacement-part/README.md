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
  The unchanged full 18-check profile then assesses the exact current subjects.
  Mandatory authenticated engineering review remains independent and held.

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
