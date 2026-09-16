# Bracket recorded structural analysis preparation

Observed 2026-09-12. The selected solver installation and bounded backend
qualification passed. The three full bracket studies remain unexecuted; these
prerequisite checks do not increment campaign completion or correctness.

## Selected installation and evidence

The clean Wright harness used unchanged image
`sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
The separately selected Casys CalculiX container uses release 0.8.6, commit
`f92ac31e4a2a35f023522946b7aa81bac1ce4808`, published image
`ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778`.
Its native dependencies are Gmsh 4.12.1, CalculiX 2.21 and Deno 2.9.6.
No engineering host packages were added to Wright's base image.

`scripts/qualification/qualify-calculix-recorded.py` exercised actual direct and
GatewayService recorded static solves from the clean Wright harness, using a
new Gmsh-created qualification STEP. Each of nine durable resources was read
and checked against its recorded length and hash. The stateless HTTP 2026
adapter is confined to this qualification script. The selected production
registration uses native classic MCP stdio, with a distinct single-writer
archive from the HTTP qualification archive.

Container `wright-calculix-campaign` mounts the selected workspace at `/exports`,
the demo workspace read-only at `/inputs`, and the same demo workspace writable
at `/campaign-workspace` for the separately declared field operation. HTTP
qualification stores `/exports/recorded-runs`; production stdio stores
`/exports/campaign-runs`. Neither route shares a writable run ledger.

Normal API registration installed and enabled only for the demo workspace:

| Selected registration | ID | Relevant tools |
|---|---|---|
| Casys CalculiX campaign container | `91ae7c8e-9b16-45fb-ae96-b08bee1e0d02` | `calculix_mesh_preflight`, `calculix_solve_static_recorded`, `calculix_run_get` |
| CalculiX recorded field expansion | `ef468fc1-cf00-4551-8cc7-0425b8d7052d` | `export_recorded_fields_and_reactions` |

Both registrations have default enablement off. Public catalog qualification
and live-device readiness were not changed. Evidence is indexed in
`docs/mcp-catalog/evidence/campaign-2026-09-12/calculix-recorded.json`.

## Exact engineering contract

The three original semantic stages remain: define the load case, create the
bracket, and solve/compare the revision. Added generic stages review the exact
basis, check a disposable AgentCAD project, author actual build123d/OCP source,
run four recorded studies, and explicitly expand each recorded study's fields.
The complete graph contains eleven stages. Each of four field stages declares
nine essential expected files, within the per-task sixteen-file limit.

Every baseline and revision must be one actual connected STEP solid. The
supplied holes, load patches, manufacturing radii, walls, clearance volumes and
mass targets remain in force. A tight bounding box in Casys selects entire
surfaces; it does not clip a load patch. Source authoring therefore requires
actual face imprints at the specified pad boundaries and an exact centroid
vertex, retaining single-volume topology. A missing or empty selection is an
execution error, not grounds for silently broadening the load.

The selected solver distributes a supplied total force equally among selected
nodes. This is explicitly disclosed as an approximation to uniform patch
traction in the reviewed design basis and results. Fixtures constrain all
translations on selected hole-bearing surfaces. Optional gravity is excluded
rather than represented by an unsupported body-load input. Material values,
load vectors, coarse/fine mesh sizes and target limits are pinned in the
family binding and uploaded scenario documents.

Original Casys recorded output contains the full displacement/stress DAT,
not only extrema, but omits RF and FRD output. The companion operation accepts
only a recorded run identity, its exact STEP hash and confined output directory.
It verifies the nine original sealed resources, preserves them unchanged,
exports the original full fields, and writes an explicit deck diff containing
only additional output directives. A separate native CalculiX solve creates
the FRD and full displacement/stress/reaction data. Original and second-run
deck hashes, commands, source hash and outputs remain separately attributed.
No caller-supplied deck, shell command, material or load is accepted by this
operation. Unknown/incomplete output directories fail closed; an exact
completed receipt can be read idempotently without replaying the solver.

Support force and moment sums derive from actual RF rows. Centroid displacement
is reported only when an actual mesh node matches the exact specified centroid;
missing sampling stays unresolved. The final analysis retains unfiltered stress
fields and distinguishes raw singular peaks from the declared evaluated stress
treatment. Successful files do not establish engineering correctness.

## Remaining execution work

`scripts/prepare-bracket-dataset-campaign.py` prepares source and exact tool pins;
`scripts/enroll_engineering_dataset_case.py` saves normal API-created instances
and enrolls their immutable input/source/output authority. Native initialization
only creates separate empty AgentCAD projects; actual geometry, meshing, solves,
field expansion and comparisons occur during the later canonical campaign run.
The CAD face imprints, mesh selection and final numerical studies have not yet
been proven for these three customer datasets. Their failures must remain
visible and drive new attempts without replacing physics or fabricating files.

All three normal API template instances are now saved and enrolled for
`attempt-001`, with successful separate native initialization and no CAD/solver
dispatch. The local execution manifest is
`.local-run/feature-081-live/campaign-execution/bracket-attempt-001.json`.
An independent staging check verified each current API source digest, all ten
current tool schema pins, all eleven staged input hashes, eleven required
stages and forty-two declared tool-created files. No STEP result was present
at enrollment. Results are retained in
`bracket-attempt-001-staging-verification.json` alongside the manifest.

Eight focused operation tests pass, covering output-only deck preservation,
unexpected-step rejection, path confinement, full DAT parsing and mesh sets.
The direct companion qualification produced 27 files from an actual second
solve, with 1,062 displacement rows and 2,028 stress integration-point rows;
an exact repeat returned the completed receipt without another native solve.

## Primary implementation references

- [Casys release identity](https://github.com/Casys-AI/mcp-calculix/releases/download/v0.8.6/release-identity.json)
- [Pinned analysis contracts](https://github.com/Casys-AI/mcp-calculix/blob/v0.8.6/docs/analysis-contracts.md)
- [Pinned recorded-run resource contract](https://github.com/Casys-AI/mcp-calculix/blob/v0.8.6/docs/recorded-runs-and-viewer.md)
- [Pinned surface selection implementation](https://github.com/Casys-AI/mcp-calculix/blob/v0.8.6/src/api/gmsh.ts)
# Bracket03 attempt007 preparation

After deployment of the missing-output inspection error fix, only Bracket03 was
replaced with fresh attempt007. The immutable one-case manifest is
`.local-run/feature-081-live/campaign-execution/bracket007-provisional-design-replacements.json`.
Staging and ordinary no-dispatch preparation passed: twelve stages, all three
original task IDs and both original edges, eleven current tool pins, eleven
input hashes, complete input mapping, provisional revision authority and direct
literal `show_object(actual_shape)` guidance. All 42 declared tool-created files
and generated response outputs were absent, with no run for the new identity.
Only the isolated empty AgentCAD project initialization ran.

Evidence is in `campaign-execution/bracket007-provisional-design-staging-verification.json`
and `campaign-execution/bracket007-provisional-design-normal-preparation-verification.json`.
The exact before/after source, grant, input, run and output snapshots for all
eighteen prior bracket cases match; this includes Bracket01/02 attempt006.
Preservation proof is `campaign-execution/bracket007-provisional-design-prior-preservation.json`.
No workflow, CAD or solver execution was dispatched, and the worker was not resumed.
