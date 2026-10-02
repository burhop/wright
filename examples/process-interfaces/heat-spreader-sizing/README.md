# Heat-spreader working-interface example

**Current status:** declarative preparation and the original live digital
CAD/solver chain are checked. The common results view and an initial actual-model
comparison are browser-verified; focused correction and second-run reuse remain
pending. See the [recorded proof](../../../specs/083-process-working-interfaces/evidence/heat-proof.md).
This example does not grant
reviews, execute a process, install a provider, or claim engineering acceptance.

The original controller-strap assignment compares actual 100×40×2 and 100×60×2 mm
plates. AgentCAD creates and reopens their STEP geometry. OASiS/scikit-fem consumes
the measured rectangular dimensions and exact STEP hashes, computes coarse and
refined temperature fields, and compares temperature, heat balance and refinement.
The original full 082 profile assesses those same outputs. Arbitrary STEP meshing,
material certification and physical thermal qualification are outside this case.

## Prepare a configured process

1. Use a fresh isolated Wright workspace. Install/enable the existing CAD and
   solver providers through their normal setup. Keep the solver's explicit
   workspace mount aligned with this workspace. Read the current
   [provider limitations](../../../specs/083-process-working-interfaces/evidence/provider-qualification.md).
2. Initialize a **fresh empty** disposable AgentCAD build123d project with the
   selected provider's CLI and `--build-dir build`. Keep it inside the workspace.
   Preparation verifies its exact project identity and refuses existing history.
   Native installation and initialization remain provider responsibilities.
3. Export the actual selected workspace's workflow-source tools from Wright's
   existing tools API. The export must contain each tool's `server_id`,
   `tool_name`, prefixed `name` and current `schema_digest`; raw MCP schemas alone
   are insufficient. Required tools are CAD `context`, `docs`, `run`, `measure`,
   workspace `write_text_document`, `inspect_file`, and solver `run_simulation`.
4. Copy `bindings.example.json` to a private configuration file and replace its
   placeholders with those enabled provider IDs, exact CAD project path and
   solver mount. Run from the Wright repository environment:

   ```powershell
   .venv/Scripts/python.exe examples/process-interfaces/heat-spreader-sizing/prepare.py --workspace ABSOLUTE_WORKSPACE --attempt heat-ui-001 --tools PRIVATE_TOOLS_JSON --bindings PRIVATE_BINDINGS_JSON
   ```

Preparation copies the original frozen assignment bytes into a new
`process-proofs/heat-spreader-sizing/<attempt>/inputs` folder and writes a connected
workflow proposal at `process-proofs/heat-spreader-sizing/<attempt>/prepared.workflow.wflow`.
It preserves the three original substantive stages
and adds declared basis/final reviews, source authoring, native read-back and exact
validation. It does not write into historical campaign roots. The manifest records
the source, inputs, selected tool schemas and expected output root.

Accept this proposal through Wright's normal source service before opening it:
`POST /api/workspace/workflow-sources` with the selected `session_id`, the manifest's
`accepted_source_path` as `path`, and the proposal's exact UTF-8 text as `source`.
Use the existing authenticated operator client; do not put credentials in the
workflow or interface. Read the accepted source back through
`GET /api/workspace/workflow-sources` and verify its `storage_digest` equals the
manifest's `source_sha256`. Preparation alone creates no accepted revision history.

Open that accepted workflow file in the Wright workspace. The common working
view prepares immutable run inputs and checks current tool readiness. Use Wright's
UI authoring control to compose a tailored comparison view from the same contract.
Any isolated synthetic reviewer policy must be separately enrolled by trusted
test management for this exact source; preparation creates no such authority.

## Present the job through Wright

Compose the tailored interface from the public client/UI kit:

- Inputs and readiness: original sketch, context, candidate table and thermal
  requirements; no printer or manufacturing section is required.
- Progress: show the current substantive tool operation and declared waiting
  review. Closing the tab leaves run ownership with Wright.
- Comparison: inspect both exact candidate STEP references, coarse/fine raw CSV
  tables and explicit numerical sample projections. Unsupported native views keep
  their download/inspection fallback.
- Findings: actual temperatures and original 45 °C limit, ≤2% analytical rise and
  refinement checks, ≤1% heat imbalance, exact CAD-to-field correspondence, current
  082 assessment and the outstanding independent critic/review.
- Navigation: jump from each result/finding to its exact block, artifact and review.
  Use backend-permitted actions; UI code cannot manufacture a passing assessment.

AgentCAD 0.6.0's creation response can report an error after committing valid CAD.
The workflow retains that raw response and separately measures the actual exports;
it does not turn that response into a successful creation receipt or repeat
creation to obtain measurements. OASiS retains `critic_approved=false`.

Saving/reopening a built UI and reusing it on another run requires no new UI model
call or build. CAD source reuse is explicitly checked against the connected basis;
changed engineering inputs require a revised source. Complete live reuse evidence
has not yet been recorded for this example.
