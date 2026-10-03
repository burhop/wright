# Selected-provider qualification progress — T043

**Date:** 1 October 2026. **Status:** partial; remaining qualification and full
engineering runs are pending. No public catalog entry is promoted.

Fresh isolated probes exercised existing independent providers through actual
stdio and native `GatewayService`, using controlled catalog/workspace ports.
These are backend probes, not the Hermes-facing `wrightgateway` proxy or complete
engineering processes. The selected native hosts and retained OASiS dependency
image are explicitly recorded; this is not a fresh clean-base installation claim.
Safe summaries and raw-record hashes are in
`artifacts/process-interfaces/083/20261001-engineering-readers/provider-probes.json`.

| Provider | Selected runtime and probe | Observed result |
|---|---|---|
| Existing Blender MCP | Upstream `5f8ddaf6e987c4aa0c3467fcc548838b28f64477`; Blender 4.5.10 LTS; fresh hidden factory profile/addon on private port 19983 | 28 tools; actual scene and owned 10×8×6 geometry/STL; recovery saved and native owner closed. |
| AgentCAD | 0.6.0 with NumPy 2.5.2/build123d 0.10.0; version-checked existing Windows preload bootstrap; resolved Python 3.12.11 | 11 tools; actual tiny 2×3×4 CAD and STEP/source/meta output. |
| Independent slicing MCP | Upstream `7b50d0288fb7b91af8af422b96c4df4db0f1110c`; selected portable CLI 2.8.2.61; dotenv disabled; only loopback dummy printer configuration | 11 tools; actual offline direct/gateway sliced 3MF. No printer tool or real printer connection. |
| OASiS | Upstream `7c184d5b7ca5cda6086f3912d1c7923c58307780`; retained selected dependency image SHA `49ad6b866d93cf85fa4c82c175241be5e0e7c17239773c658e550b50e0580f8d` | 17 tools; fresh network-disabled container, one isolated mount, actual fixed-temperature/Robin conduction and CSV/VTU. Native `critic_approved=false` retained. |

The OASiS container `wright-083-oasis-t043-001` was verified by ID/feature label
and stopped after probing. Existing campaign containers/processes were untouched.
Blender used the existing native application lifecycle owner, fresh exclusive
lease/document, hashed recovery and identity-checked close. MCP stdio owners were
stopped after each probe.

## Problems and bounded corrections

**AgentCAD startup:** initial offline dependency resolution consumed the startup
deadline. The second attempt used the already-resolved, explicitly version-checked
interpreter and passed. The raw second record mistakenly names an old source URL;
the correct catalog source is `https://github.com/jdilla1277/agentcad`. Its original
record is retained with that metadata limitation; no historical evidence rewritten.

**Slicer presets:** leaf JSON preset inheritance was not resolved by the external
provider. Its first file used PLA, density zero, two walls, 20% infill and no
supports despite PETG preset filenames. That file is only backend probe evidence.
Complete existing prerequisite flat JSON was copied as configuration data into
a fresh isolated provider root. No profile resolver, vendor protocol or execution
wrapper was added to Wright. The actual third-attempt sliced settings are PETG,
density 1.28, four walls, 35% infill, 0.2 mm layers and supports enabled. Both direct
and gateway routes passed exact configuration comparison. The intervening second
attempt could not spawn its cached base interpreter inside the sandbox; the
authorized selected-runtime retry passed. Failed roots were preserved.

**Remaining qualification:** complete the normal agent-facing gateway proxy and
selected-host/clean-container provenance checks before checking T043. Catalogue
promotion, public setup recipe changes, physical dispatch, campaign execution and
engineering acceptance are outside this checkpoint. T045–T047 will use original
assignment geometry, meaningful handoffs and exact 082 checks rather than these
small qualification artifacts.

## Production gateway checkpoint — 2 October UTC

The actual `python -m api.gateway_stdio` launcher, official MCP framing, database
catalog/workspace authorization and production engine lifecycle now list and proxy
safe backend operations for all four selected providers. Summaries and exact raw
record/response/artifact hashes are in
`artifacts/process-interfaces/083/20261001-production-provider-gateway/`.

| Provider | Actual production gateway result | Scope and limitation |
|---|---|---|
| Blender | 28 prefixed tools; `execute_blender_code` exported owned STL | Fresh hidden native session on private port 19984; native owner saved recovery and closed its exact session. |
| Slicer | 11 prefixed tools; `slice_model_file` emitted actual PETG package | Four walls, 35% infill, 0.2 mm layers, supports enabled. Read-only reconciliation of the retained successful third call corrected private harness summary checks; zero additional dispatches. |
| OASiS | 17 prefixed tools; `run_simulation` produced CSV/VTU and numerical checks | Fresh network-disabled selected-dependency container, stopped after use; `critic_approved=false`. This does not establish a fresh clean-base install. |
| AgentCAD | 11 prefixed tools; `measure` reopened actual 2×3×4 mm STEP | Existing FastMCP HTTP app served by standard uvicorn factory on a private loopback port. Read-back passed; creation response remains unqualified as described below. |

### AgentCAD creation response remains a provider defect

The nested Windows stdio startup exceeded its deadline. The existing provider's
standard SDK HTTP transport worked without adding an adapter or workaround to
Wright. A first copied project was correctly rejected because its manifest bound
the original project directory. A fresh project initialized through the existing
AgentCAD CLI then committed real STEP/native metadata successfully.

That creation call nevertheless returned JSON `status=error`, with exit code zero:
AgentCAD 0.6.0's MCP implementation feeds Click's combined progress/JSON output to
its JSON formatter. Native metadata records success and deliverable validation;
the raw MCP response records failure. Neither is rewritten or promoted into a
successful creation receipt. A separate **read-only** gateway measurement of those
exact STEP bytes succeeded. The [upstream MCP source](https://github.com/jdilla1277/agentcad/blob/main/src/agentcad/mcp/server.py)
also shows the combined-output formatter; a mutable upstream page is context,
not qualification of a new provider revision.

All exact owned CAD HTTP process IDs were subsequently checked exited. Failed
attempt roots are retained. No native creation was retried after the committed
STEP was observed. Complete engineering examples must expose the creation warning
and reconcile exact outputs, or use a separately qualified provider revision;
they must not mask the response or blindly recreate geometry.

T043 remains pending overall qualification and selected creation-binding checks.
These small backend probes do not execute either original engineering assignment,
promote the public catalog, establish human acceptance, or authorize physical work.

## Fresh clean OASiS selected installation — 3 October 2026

Attempt003 starts from neutral Linux/amd64 Wright image
`512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
Preflight confirms selected OASiS/skfem/gmsh/pyvista/Blender packages and native
CAD hosts absent. Only free selected prerequisites and pinned OASiS revision
`7c184d5b7ca5cda6086f3912d1c7923c58307780`, MCP 1.28.1 and scikit-fem 12.0.2
are freshly installed with new selected Python/cache directories; the base image
is unchanged. Attempt002's unprivileged apt failure remains. Fresh attempt003
uses root for prerequisites, then restores default-user selected-cache ownership.

Official initialization/listing succeeds with seventeen tools; their input
schemas exactly match the production gateway projection. One actual
`run_simulation(solver=skfem, critic_approved=false)` call through current
`api.gateway_stdio` solves a 1 W, 50 x 30 x 2 mm conduction case and emits nonempty
CSV/VTU plus balance/refinement records. The provider explicitly reports
`trustworthy_result=false` without independent critic review. Listing other tools
does not qualify their backends.

The selected backend runs with network disabled and one isolated workspace mount.
The production gateway uses the current Windows source environment; no clean-base
in-container API gateway is claimed. Both successful containers and the failed
installer are revalidated stopped by exact labels/IDs. Publication repeats no
solver or installation. The first publisher passed a string to a mapping-only
redactor and stopped; the fresh publisher uses existing text/mapping redactors
and passes an actual credential-value scan.

[Scope/provenance/cleanup](../../../artifacts/process-interfaces/083/20261003-oasis-fresh-clean-qualification-002/checked-scope.json)
and [qualification record](../../../artifacts/process-interfaces/083/20261003-oasis-fresh-clean-qualification-002/README.md)
retain launch/configuration, schemas, installation logs, actual response/outputs,
source hashes and first failures. Databases, contexts and traces are excluded.
T043 remains open for other selected Blender/slicer/AgentCAD fresh install/host
and creation-binding obligations. No public catalog/setup metadata is promoted.

## Fresh clean AgentCAD — creation defect reproduced, readback verified

AgentCAD 0.6.0/build123d 0.10.0/NumPy 2.5.2/MCP 1.28.1 now have a fresh
selected Linux/amd64 install from the neutral Wright image, with no preinstalled
AgentCAD/build123d/OCP. Official stdio lists eleven tools; direct schemas match
both production-gateway projections. No Windows bootstrap was used.

One gateway run call creates a valid 2 x 3 x 4 mm native STEP version but returns
provider JSON status=error with progress mixed into CLI JSON. Strict creation
qualification fails, reproducing the Windows defect on Linux. Exact completion
is observed and creation is never retried. A separate read-only measure call
succeeds on the same STEP bytes: dimensions 2/3/4 mm, volume 24 mm3, valid
deliverable. Error, native success and readback remain separate evidence.

Both exact owned containers are revalidated stopped; backend network is none
with one private mount. Gateways use the current Windows source environment.
[Partial scope](../../../artifacts/process-interfaces/083/20261003-agentcad-fresh-clean-partial/checked-scope.json)
retains installation, initialization, schemas, responses, native files and hashes.
The [provider follow-up](../../../docs/mcp-catalog/followups/agentcad-0-6-creation-response-format.md)
records the unresolved boundary. T043 stays open. No formatter workaround,
creation retry, public promotion or engineering acceptance is claimed.
