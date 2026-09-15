# Modelica preflight repair and fresh attempt 002

September 12, 2026. All three original Modelica attempt-001 requests were
definitively rejected before a workflow run began. The ordinary production
resolver reports `WORKFLOW_NOT_READY`: the selected MCP tool is unavailable.
The saved direct nodes used bare upstream names such as
`modelica_simulation_manifest_get`, and omitted `mcp_schema_digest`. The runtime
requires the qualified gateway name and its exact schema/authority digest.

This affects 37 direct nodes across the 9-, 9- and 25-step graphs. Their argument
objects satisfy the current tool schemas; the defect is their executable
identity. The read-only reproduction is recorded in
`.local-run/feature-081-live/campaign-execution/modelica-attempt-001-preflight-diagnosis.json`.
No native simulation retry was needed to find the failure.

The Modelica preparer now selects the exact catalog record before building
nodes and writes both its qualified `name` and `schema_digest`. The common
trusted enroller now fetches current workspace tools before any source PUT or
policy enrollment: stale allowlists, mismatched direct identities and agent
tasks without an enrolled server fail before those mutations. This does not
weaken runtime or approval authority.

Eight regression tests in `tests/test_modelica_campaign_binding.py` cover all
three complete generated graphs with the ordinary runtime resolver/preflight,
missing/bare/stale identities, changed current catalog identity and separate
confined mount planning, including refusal of false existing-container mount
readiness before any container mutation. They passed in 1.92 seconds; Ruff passed. The tests use
isolated model manifests for binding verification, not claimed native physics.

## Selected container prerequisite

The existing container only mounted the three attempt-001 output directories.
After proving that its process list contained only `sleep infinity` and its
production native store was empty, the bounded extension preserved the stopped
container as `wright-081-modelica-runtime-before-attempt002`. Its replacement
retains the original name, registry command and exact immutable image
`sha256:e5dc37e5cde7722fa9547962b438548122def738019b85f380f9cb84d4b2bc47`.
All four existing mounts remain; three exact attempt-002 artifact mounts were
added. The old store/output bytes were checked before and after. No provider
source, model, kit, solver, grant or shared API was changed.

`modelica-attempt002-mount-extension.json` records that change under the campaign
execution directory. The new export roots pass the provider's actual real-path
and directory predicates. A separate real stdio MCP read-only probe discovered
all 15 tools and retrieved all six baseline/refined manifests, matching their
original exact hashes and OpenModelica/MSL engine identity. Its evidence is
`modelica-attempt002-mcp-readiness.json`; the native production store remained
empty. No invented export or simulation was used to test readiness.

The installer supports repeated explicit `--attempt` options when creating a
new container, with separate confined dataset/attempt mounts. It refuses to
claim that an already recorded container has additional mounts merely because
different options were supplied. Controlled idle extension remains explicit.

## Fresh canonical handoff

The normal template instance API, source API and trusted enroller created
`.local-run/feature-081-live/campaign-execution/modelica-attempt-002.json`, with
three fresh cases retaining all original task IDs and 9 / 9 / 25 required steps.
Old attempt-001 source bytes and grants remain unchanged and unrevoked.

`modelica-attempt-002-normal-preparation-verification.json` records the strongest
static check: the ordinary `prepare_authorized_workflow_run` service ran with
actual saved-source storage, `DatabaseGatewayCatalog`, `GatewayService`, input
files and policy authority. A lifecycle that rejects all dispatch guaranteed
zero tool calls. All three old failures reproduced; all three new preparations
passed, including required stages, exact tool pins and input hashes. The new
artifact directories were empty. This establishes readiness to attempt the
real workflows, not their completion or engineering-content validity.

## Heater case 01, fresh attempt 003

After the generic initial uploaded-file review correction was deployed, only
case01 received a fresh attempt003. Cases02/03 retain their unstarted attempt002
sources and grants. The selected container was first verified idle, with an
empty native run store, then preserved as
`wright-081-modelica-runtime-before-attempt003`. Its replacement keeps the exact
image, name, registry command, network isolation and limits. All seven old mounts
remain byte-identical; only the case01 attempt003 artifact mount was added.
`campaign-execution/modelica-attempt003-mount-extension.json` records all eight
mounts and the real-path predicate. The actual production stdio probe again
retrieved all six native manifests with exact hashes and discovered fifteen
tools, without a simulation.

The normal template/source/policy APIs produced the one-case manifest
`.local-run/feature-081-live/campaign-execution/modelica-attempt-003.json`.
Ordinary preparation passed with nine required stages, seven direct tool nodes,
six exact tool pins and eleven verified inputs. A no-dispatch lifecycle enforced
zero tool calls. Evidence is
`campaign-execution/modelica-attempt-003-normal-preparation-verification.json`.
The static audit only flagged native exported `scenario.json` filenames sharing
the human input pack's basename; those native kit scenarios have a separate
recorded-run origin. No output or content-validity credit is claimed by setup.

## Complete native evidence bindings for final selection

Case01 attempt003 subsequently completed three actual baseline simulations and
three native exports. Its final model stage failed before its first model call:
the 75,093-character prompt exceeded Hermes' per-item text limit. Each connected
submit response repeated roughly 15,840 characters of run/kit metadata, while
the complete native `evidence.json` contained the relevant computed metrics,
warnings and execution attestation in approximately 1774 characters. The three
actual CSVs, run records, source, logs and evidence remain preserved.

The preparer now gives each baseline export a named `workspace_file` output
mapped by `expected_file_ports` to that exact same-run `evidence.json`. Final
selection reads the complete file through the existing canonical reference
mechanism. Every native export remains required. Original stages and edges,
baseline candidate/loss cases, tighter reruns and final study outputs are
preserved; no runtime special case or derived fixture metrics were introduced.
Eight binding tests and Ruff passed.

After normal API deactivation of the coordinated idle selected server, its
container was preserved as `wright-081-modelica-runtime-before-evidenceports`.
The replacement retains its image, name, command, isolation and all eight old
mounts; three exact new output roots give eleven mounts total. Every old native
store/export file hash remained unchanged. Normal reactivation returned all
fifteen identical tool pins. Evidence is
`campaign-execution/modelica-evidenceports-mount-extension.json`.

The fresh manifest is
`.local-run/feature-081-live/campaign-execution/modelica-evidenceports-fresh.json`:
case01 attempt004 and cases02/03 attempt003. All 9 / 9 / 25-stage plans passed
ordinary preparation with a no-dispatch lifecycle, current tool/input hashes,
and complete immutable input-binding maps.

An offline transport capacity probe used actual runtime/bridge code, all six
real tool input schemas, original context/image, and the largest complete
existing native evidence file repeated at all baseline slots. This repetition
is explicitly a capacity-test fixture, not an engineering observation attributed
to any new case. For the nine-slot case03, the prompt is 42,623 characters,
translation text 80,719 bytes, and largest transported text part 56,322 characters
against the 65,536-character limit. No network/model/native call occurs. See
`campaign-execution/modelica-evidenceports-context-capacity.json`. The actual
future engineering results remain unvalidated and no workflow was dispatched
during this repair.
