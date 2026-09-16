# Printed replacement workflow: binding research

Initial binding research was observed 2026-09-12 using the canonical compiler
and live Wright tools API. No campaign workflow, printer action or engineering
qualification was dispatched. A later bounded disposable seam proof is recorded
below; it does not receive campaign credit.

## Available tools and exact boundary

`GET /api/workspace/workflow-sources/tools?session_id=wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a`
returned these useful bindings:

| Server | Tool | Arguments | Schema digest |
| --- | --- | --- | --- |
| blender-mcp-ahujasid | blender-mcp-ahujasid__execute_blender_code | `code` required string; `user_prompt` optional string | dd4c594401ccb2fd8d97d1a4694a3aa3eb252d89d617c4e1dac27c0bea5c0ada |
| agentcad | agentcad__run | `script`, `output`, `cwd` required strings; optional `export`, `render`, `build_dir`, `params`, `preview`, `view`, `diff` | 634992e101194e90ba3a4bf770f1dd53c1b81d3ddb774bf69582fc3431628799 |
| agentcad | agentcad__export | `step_file`, `formats`, `cwd` required strings; optional `build_dir` | d02426fa5afbbb2928642829e6fe667fd41f73a1250b39da270013f952e47c3e |

Blender is the smallest legitimate image-to-mesh route: an existing MCP task
receives the actual PNG, prompt and dimensional context, then uses the real
Blender Python API to model and export the part. Record every executed source
string, its hash, the original PNG hash, the input dimensions and output hashes.
The `user_prompt` tool argument should retain the dataset prompt verbatim.
There is no need to introduce a template-ID executor. AgentCAD is useful later
but its run tool requires a pre-existing build123d source file; it cannot author
that source by itself through the currently exposed eleven tools.

The current live tool list does **not** include Bambu P1S. The local protocol
probe exposes `slice_model_file(source, plate=1, output=null, orient=false,
arrange=false, confirm=false)`, but that is not current GatewayService execution
readiness. Its source revision is `7b50d0288fb7b91af8af422b96c4df4db0f1110c`.
Register a narrowly scoped slicer operation or bind an explicit generic local
operation to the actual Bambu executable. Do not enable real printer tools just
to obtain a slicer. Do not make Blender an undocumented subprocess dispatcher.

## Canonical node settings and connections

Retain all five existing canonical stages. Add separately connected input blocks
for the natural prompt and assembled profile/context text. Bind the original
image input to `concept.png`; preserve SVG as an additional original input.

1. `image_and_scale`: input with `input_mode: workspace-file`,
   `workspace_file: <attempt-input-root>/concept.png`; output `reference_images`.
2. `create_mesh`: `performed_by: ai_assisted`; settings:
   `authoring_template: mcp-task`, `mcp_server: blender-mcp-ahujasid`,
   `output_format: json`, `save_output: true`, `output_filename:
   <attempt-output-root>/source-mesh-report.json`, `file_policy: overwrite`,
   `expected_files: <attempt-output-root>/source_mesh.stl`,
   `max_tool_calls: 12`, `timeout_seconds: 600`.
   Keep a nonempty inline prompt describing actual Blender modeling and export.
   Connect PNG to a `reference_images` input; connect prompt and profile/context
   to `engineering_document` inputs. All required inputs must have producers.
   Declare an `engineering_document` response output. Require source units mm,
   source dimensions, boolean/mesh construction decisions and original image
   reference in the response. This is actual image-conditioned model work.
3. `repair_measure_orient`: another Blender `mcp-task` with upstream source report
   and manufacturing context connected as document references; expected files
   `<attempt-output-root>/repaired_mesh.stl` and
   `<attempt-output-root>/mesh-preview.png`. Import the actual saved source STL,
   merge coincident vertices, recalculate outward normals, apply transforms,
   choose orientation, export the actual mesh and render preview. Preserve
   source separately and report measured bounds/topology without claiming fit
   or strength. Keep the original source file hash in the report.
4. `supports_and_slice`: explicitly bound real local slicer operation, consuming
   repaired STL path and immutable profiles. Declare actual 3MF and preview/
   support report files. A reusable local operation can use subprocess argument
   arrays; retain executed source and command identity under run evidence.
5. `authorize_transfer`: preserve exact-digest approval, but bind the campaign's
   named printer simulator destination. The receipt must be produced by the
   approved test handoff and refer to this run's exact final 3MF digest. It must
   explicitly say simulated and never connect to printer MQTT or FTPS.

For deterministic direct MCP code operations the existing compiler uses:
`authoring_template: mcp-tool`, `performed_by: configured_tool`,
`mcp_server`, `mcp_tool`, `mcp_schema_digest`, `mcp_arguments` (JSON string),
`output_format: json`. Whole JSON argument input can use
`mcp_arguments_source: connection` with `mcp_arguments_input: <port-key>`;
individual mappings use `mcp_argument_ports: {"<port-key>":"code"}` as a
JSON string. Image ports cannot connect directly to an exact MCP tool: an AI
task must interpret the PNG or a prior explicit interpretation operation must
produce source/parameters. A deterministic source recipe based only on a known
scenario ID would not meet image-conditioned workflow fidelity.

Compiler limitation: `expected_files` currently requires `mcp-task`, and the
direct `step.tool_name` branch does not snapshot/verify/register tool-created
files. If deterministic bindings are selected, support file collection in that
generic branch as well as widening compiler eligibility. The AI task branch
already snapshots, verifies nonempty changed files and retains their provenance.

## Slicing profiles and process values

Portable executable: `.local-run/feature-081-live/tools/bambu-studio-2.8.2.61/bambu-studio.exe`.
All profile paths below are under its `resources/profiles/BBL/` directory.

- Machine: `machine/Bambu Lab P1S 0.4 nozzle.json`.
- Explicit PETG option present and compatible with that machine:
  `filament/Bambu PETG HF @BBL P1S 0.4 nozzle.json`.
  It declares `compatible_printers: ["Bambu Lab P1S 0.4 nozzle"]` and inherits
  `Bambu PETG HF @base`. This is a real PETG profile; the launcher currently
  selects PLA and must not silently retain it for these packs.
- Base 0.20 mm process: `process/0.20mm Standard @BBL X1C.json`.
- Base 0.16 mm process: `process/0.16mm Optimal @BBL X1C.json`.
- Create an attempt-local derived process with explicit `layer_height`,
  `wall_loops`, `sparse_infill_density`, `enable_support: "1"`, and recorded
  support/orientation choices. Actual upstream keys were read in
  `process/fdm_process_common.json`; support default is disabled there.
  `support_type` is `tree(auto)` and `support_threshold_angle` is `30` in that
  source. Supports must be enabled for the operation even if a given selected
  geometry/orientation ultimately needs no support material.

Real upstream slicer invocation is:

```text
bambu-studio.exe --slice 1 --debug 1 --export-3mf <output.gcode.3mf>
  --load-settings <machine.json>;<derived-process.json>
  --load-filaments <PETG-filament.json> <repaired_mesh.stl>
```

Use a subprocess argument array so the semicolon and spaces are one argument.
The previous cube probe produced a 47,207-byte package using PLA; it proves CLI
availability only, not these process settings or these campaign runs. Extract
actual package thumbnail/preview entries or render from the actual emitted
toolpath to meet support preview requirements; never substitute the input sketch.

| Dataset | Governing dimensional intent | Process overrides |
| --- | --- | --- |
| printed-replacement-part-01 | 38 mm OD, 18 mm height including 2 mm hub, six scallops down to 33 mm grip diameter; 6 mm D shaft, 5.2 mm across flat, 0.2 mm boundary clearances, 10 mm blind depth | 0.20 mm, 4 walls, 35% infill, PETG |
| printed-replacement-part-02 | 96 mm screw centers, 18x24x5 mm pads, 4.5 mm holes; 118x28x34 mm maximum envelope, 25 mm finger clearance across central 65 mm, oval 12x9 mm grip, shallow thumb recess | 0.20 mm, 5 walls, 40% infill, PETG |
| printed-replacement-part-03 | 26x38 mm plan, linear 8..17 mm height; holes (13,9)/(13,29) at 3.4 mm, 6.5x2.5 mm counterbores; 16x28x1 mm pad recess and rear-right keepout | 0.16 mm, 5 walls, 45% infill, PETG |

The first PNG was visually inspected: it is an original dimensioned six-scallop
wheel concept with section and D-shaft annotations. Written dimensions govern;
the image explicitly says not to scale. Use an actual multimodal task to read
that image and context; do not infer a manufacturer measurement from pixels.

## Outstanding prerequisites

- Bind actual per-attempt paths and all prompt/context/image inputs.
- Confirm usable existing model provider for image-conditioned MCP tasks.
- Bind the local slicer through normal generic canonical execution and ensure
  same-run artifact collection includes direct tool-created files.
- Select PETG and save derived per-dataset support/process profiles; verify the
  resulting CLI accepts them before dispatching campaign cases.
- Implement scoped approval continuation and test handoff in the root runtime.
- Shared Blender scene is mutable: serialize these cases or use explicit unique
  scene/object names and cleanup only owned objects. Avoid replay after unknown
  tool outcome; reconcile actual source/output files first.

## Prepared implementation and isolated prerequisite evidence

`scripts/prepare-printed-dataset-campaign.py` now generates the three bound
canonical definitions and stages original files plus explicit assembled context,
reviewed operation source/configuration. It never starts a workflow or modifies
the demo definitions. `--instance-source` rebases bindings onto a source returned
by the normal original-template instance API, preserving its real semantic IDs.
Its staging manifest records every original input hash, definition hash, actual
live MCP schemas, explicit expected files and requested integration approval.
The declarative binding is at
`tests/datasets/engineering-workflows/bindings/printed-replacement-part.json`.

All three drafts passed both `validate_workspace_authoring_shape` and
`compile_prompt_workflow`. They retain the four task stages and original image
input; additional context inputs are connected to real task references. The
simulator contract is server `wright`, tool `test_handoff`, schema SHA256 of
`wright.integration_test_handoff.v1`, destination kind `integration_test`, URI
`test://081-engineering-datasets-v1/printer/<scenario-id>`. Root must enroll the
exact source/policy/tool grant and authoritatively implement this destination
before any dispatch. No local script pretends that grant exists.

The reusable `scripts/engineering_dataset_slice.py` operation is staged as an
explicit same-attempt source input and invoked outside Blender by the generic
configured MCP tool `wright-printed-part-slicer/slice_model_file`. Its confined
wrapper is `scripts/engineering_dataset_slice_mcp.py`. The wrapper accepts only
the staged configuration and exact staged operation source, verifies both are
in the same attempt, compares the source bytes with the executing fixed module,
and then calls that operation. The operation invokes only configured Bambu
Studio with a fixed argument array, no shell, bounded timeout and no printer
connection.

The image-conditioned create and repair tasks remain on the pinned guarded
`blender-mcp-ahujasid__execute_blender_code` route. Their instructions forbid
raw file I/O, hashing, `runpy`, subprocesses, text datablocks and persistent
callbacks. Blender performs only allowed `bpy`/`bmesh`/`mathutils` modeling,
repair, rendering, save and STL import/export. Model-authored JSON reports are
explicitly non-authoritative. The canonical Wright step record outside Blender
is execution lineage: `tool_calls[].arguments.code` retains the exact guarded
request, `references[].sha256` retains the actual input bytes and
`produced_files[].sha256` retains independently verified post-call outputs.
The dataset manifests promise source mesh, repaired mesh, slice package and
printer-transfer receipt roles; they do not promise a separate Python source
artifact.

A separate cube prerequisite probe (not a campaign run) exposed incomplete
leaf-profile inheritance in Bambu CLI. The operation now resolves every named
inherit/include dependency, retains the complete derived machine/material/
process JSON files, pins Textured PEI for this synthetic process, and records
each source profile hash. The corrected real probe produced a 49,008-byte 3MF,
2,818 positive-extrusion moves, actual package PNG, support-toolpath SVG and
slice evidence at
`.local-run/feature-081-live/print-binding-research/petg-prerequisite_resolved/`.
Emitted G-code confirms `filament_type = PETG`, density 1.28, nozzle temperature
245, `enable_support = 1` and Textured PEI plate. The cube needed zero support
moves, which is explicitly reported. This is a local prerequisite test only;
no input pack/process counter was incremented and no geometry fixture is used
by the campaign definitions.

Normal API application sequence: create an isolated workspace/session; call
the original-template instance endpoint with current template version/digest;
read its accepted source to a temporary file; rerun preparer for that scenario
with `--instance-source`, isolated `--workspace-root`, and a fresh attempt ID;
save returned draft through canonical source PUT using current storage digest
and real semantic validation; enroll exact input/source/tool hashes and test URI;
only then submit the ordinary run request with its approved integration policy.

## Bounded native seam acceptance

`artifacts/engineering-workflow-datasets/diagnostics/recovery-20260913/printing-binding-proof-004/acceptance.json`
proves the prepared boundary without dispatching a campaign workflow or
contacting a printer. The pinned safe-mode server rejected `open()` and `runpy`
before socket access. It then sent one recorded `execute_blender_code` request
to owned Blender 4.5.10 LTS process 26252 on dedicated endpoint
`127.0.0.1:56467`. The exact code SHA256 was
`7ca62a217f613035c7dd6e57951ce2c7aefb5aed676da85dd1db6239037c12a4`.
The actual 764-triangle STL measured 20 x 20 x 10 mm and both retained STL byte
hashes were `4e8ebbf8685c4b57b18b63b00ed6a5371c02c0e23244d3b3da793d7b439b44d1`.

The separate configured wrapper then called the fixed Bambu operation with only
`configuration_document=diagnostic/inputs/slice-operation.json` and
`operation_source_document=diagnostic/inputs/slice-operation.py`. Bambu Studio
exited 0 and produced a 98,985-byte package with SHA256
`b6fa6bd3a205508c18f49d6533061d8a1a428ba27c797fa69d21806b570492cf`,
10,980 extrusion moves, PETG, and supports enabled. The selected disposable
geometry needed zero support moves; that observed value is retained rather than
claimed as generated support material. The lifecycle saved the owned scene,
verified its recovery hash, closed the document, and gracefully quit the exact
process. Its session is `exited`, its lease is `released`, the dedicated port is
closed, and no Blender or Bambu Studio process remains.

The journal-ready verification is
`artifacts/engineering-workflow-datasets/diagnostics/recovery-20260913/printing-binding-recovery-journal-ready.json`.
It reconciles the two prior native attempts, independently recomputes code,
input, output and recovery hashes, and records the ready binding as
`blender-mcp-ahujasid/execute_blender_code` with schema SHA256
`bec31364a19bfcd0fcd3225a8b78742a7655279f0fd0f3710945b0b8846e6170`
plus `wright-printed-part-slicer/slice_model_file` with schema SHA256
`7ce7883b5f77424933e87fc6b27b67b813c15dcbaec7125e830b03def7bbbf3e`.
The full pilot is ready only after root registers that exact slicer server and
the owned Blender lifecycle binding in the restored runtime.
