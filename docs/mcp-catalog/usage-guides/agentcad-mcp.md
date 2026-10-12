# AgentCAD MCP: standard-format handoff

Recorded12October2026. Independent provider:
[jdilla1277/agentcad](https://github.com/jdilla1277/agentcad), Apache-2.0.
Read the existing [selected-provider recipe](../mcp-server-setup-recipes.md)
and [testing process](../mcp-server-testing-process.md) first. This is a bounded
native Windows Wright → fresh selected Linux provider qualification, not a new
full clean-Wright-container catalog pass or alternate CAD-authoring campaign.

## Version and environment

The cached selected image is `wright-083-agentcad-head-selected:002`, SHA
`d8b9cd78f929bf4e2705127e09f8b69b0bdf339682a6d79c2fdbf9f0c7b3077f`.
Its package reports0.6.0 and Python3.12.12; the actual MCP server source SHA is
`3c263c3e47a6112cec7144fc073bd916070849f128257f8c7159b025882c3caf`.
Treat these selected source bytes as authority, not just the package version or
mutable upstream branch. No host software was added to Wright's base image.

Each stdio instance runs the existing `python -m agentcad.mcp` in a fresh
`docker run --rm -i --init --network none --read-only --tmpfs /tmp` container.
Only the new qualification output directory is writable at `/workspace`; the
exact STEP input is additionally file-bound read-only. This contains native
workers and cache writes. The provider exposes11 tools. Preserve its source,
schemas and platform prerequisites with the actual registered tool identities.

The first registration had an incorrect operator-supplied repository URL. The
installed `Project-URL` and primary repository identified the correct source.
That owned registration was disabled/uninstalled before export; its measurement
receipt remains historical. Correct-source registration is
`09ed0cb8-8031-437a-8cf4-0c7520ed2776`. The connected chain has another explicit
scoped registration, `8de879d3-9c37-463e-a289-3447cd2cd05d`. Do not reuse the bad
source metadata or confuse namespace changes with a native provider revision.

## Verified engineering contribution

Actual SteveCAD revision7 STEP is read through `measure(file,cwd)` via Wright's
authenticated gateway. The measured110 solids,831 faces and783118.7196mm³ volume
match the independently checked CAD basis. The native closed-shell, B-rep and
structure validation pass. This is measured standard geometry, not a model's
description of a successful prior stage.

The supported `export(step_file,formats,cwd,build_dir)` operation then exports
the actual STEP to GLB. With an unconfigured fresh standalone project the output
is beside the STEP. Configured projects have different derived paths; inspect
the returned actual path rather than guessing. This qualification deliberately
uses a supplied immutable STEP, a fresh output folder and `formats:"glb"`.

Run`bbbe2ed4c4bb4ec98d819df649d305ab` completed in4.717seconds. The resulting
1273896-byte GLB hash is
`2f89ab1ea3f7425bc14d43912f582a06b3cf823b2d0f264abd7d552ec65c8d82`.
Its separate mesh validation reports110 closed components, consistent winding,
zero open/nonmanifold edges and no degenerate/duplicate triangles. The actual
native file hash matches the durable result-file binding and independent bytes.

The connected proof run`7f626fb8ae424bfd9ec9d7910ad27be4` automatically hands a
new GLB from this provider to Blender's supported native importer, then produces
a PNG in18.269seconds, with no model call or new runtime implementation. All110
Blender meshes map unambiguously to actual source STEP extents; maximum actual
vertex extent error is0.049864mm. This is tessellated presentation geometry,
not a replacement for the CAD dimensional tests or physical manufacturing.

Evidence roots:

- `artifacts/stevecad-demonstrations/qualification/agentcad-format-export-001/`
- `artifacts/stevecad-demonstrations/qualification/native-mesh-render-chain-001/`
- `artifacts/stevecad-demonstrations/qualification/native-mesh-render-chain-002/`
- `artifacts/stevecad-demonstrations/qualification/automatic-native-render-chain-007/`:
  actual upstream SteveCAD download, validated GLB and three rendered outputs in
  one 62.007-second durable run. Source STEP SHA
  `dbb2b9c25e5cb2d1fcf2ae9e60026ccbcc52ad1903a4198d26283f0c37d7781f`,
  GLB SHA `9383435aa798811db87a0e8ba4356e6017583d7d1f4328ae73ebfab72691049a`.
  The original supplied placement/color reference still bounds that proof.

## Read results at their actual scope

The gateway may retain the native result as JSON in `content[0].text`. Parse the
complete actual JSON; do not look only for fields on its transport envelope.
Check `_exit_code`, native `status`, source `validation.is_valid`, and the written
format's separate `mesh_validation.glb.is_valid`. A successful file write or
source CAD validation does not establish mesh validity. Retain warnings and
unknown checks. Native mesh validation does not check dimensions, material,
self-intersection, printability or operation.

GLB uses a Y-up scene. Apply complete node/world transforms and the declared
Y-up↔CAD Z-up convention before comparing source coordinates. In this selected
export the numbers retain millimetres; Blender import scales them by0.001 to
metres. Never infer units solely from the `.glb` suffix. The passive standard
reader verifies all110 actual node placements against STEP bounds. Fallback
palette colors and anonymous node names are presentation/identity limitations;
use a qualified actual-geometry mapping when restoring supplied CAD colors.

For rotated objects, transforming local bounding-box corners gives conservative
world bounds, which may be too loose for identity matching. Measure transformed
actual vertices. This authoring error failed the first connected import and was
corrected in a new accepted revision/new run with all old evidence retained.
Do not repair geometry to force a mistaken bounding-box comparison to pass.

## Limits, recovery and triage

Earlier offline build123d0.10.0 reads/tessellations used this selected environment
as a library host. They are not historical AgentCAD MCP calls. This qualification
adds actual protocol/gateway/native-export evidence only at the stated scope.
Native create/authoring, CAD diff, viewer services and other tools are not newly
qualified here. Automatic SteveCAD one-use download transfer is still separate.

Do not submit another export on observation timeout until the exact output/native
operation is reconciled. A native file can be complete after a caller times out.
Use fresh output roots and declared file ports; no old mesh substitution. The
current successful runs are terminal. No new AgentCAD bug was reported. Preserve
source attribution and schema identities; use the shared minimal-reproduction
checklist before any supported report.

The old diagnostic STL helper retained a stale loop variable only in its
`native_extent_mm` metadata field. Actual STEP extents, identity matching,
volume checks and mesh bytes were correct. All110 revision7 entries were
reverified against exact native records; see `robot-arm-media/corrected-rev7/`
`mesh-extent-field-addendum.json`. Do not use that original stale diagnostic field
as a dimensional observation or blame this provider for our helper's mistake.
