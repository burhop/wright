# Printed replacement-part working-interface example

**Status:** declarative preparation and passive inspection fixtures are checked.
The connected live geometry/slicer run and generated working interface remain
pending. See the [proof record](../../../specs/083-process-working-interfaces/evidence/printed-proof.md).

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

Open the accepted workflow in the workspace and use its common working view to
prepare immutable inputs and check readiness. Generate and refine a tailored
interface through Wright's UI authoring control. Native/provider readiness and
predictable choices belong before execution; reviews are declared in the process.

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

## Intended working interface

Present the original image and requirements, preparation readiness and current
tool operation. Let the user inspect actual source/repaired geometry, nominal
layered toolpaths, material/profile correspondence, measured findings and declared
reviews. Link to exact artifacts and producing blocks in Wright workspace tabs.
Use only backend-permitted actions; retain the common-view fallback. This digital
proof must not expose a physical print command or infer camera/machine status.
