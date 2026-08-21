# Research: Windows MCP Qualification

## Decision 1: Treat the seven-entry allowlist as execution authority

**Decision**: Executable actions are permitted only for the seven exact catalog
IDs in the feature specification. The check occurs before recipe resolution,
source fetch, package download, process creation, remote connection, Wright
registration, or gateway calls. Read-only catalog/source research uses a
separate interface and cannot transition into execution.

**Rationale**: Similar vendor/product names are not proof of publisher identity.
A pre-execution allowlist is auditable and prevents an optimistic catalog entry
or operator typo from broadening authority.

**Alternatives considered**: Vendor-prefix matching and catalog risk filters
were rejected because community or squatted packages can share those strings.

## Decision 2: Use declarative operations instead of shell recipes

**Decision**: Recipes select reviewed operation types such as pinned Git source,
pinned npm package, built-in local endpoint, remote Streamable HTTP endpoint,
stdio launch, protocol probe, Wright onboarding, gateway probe, residue snapshot,
and cleanup. Each operation has typed arguments and bounds. No recipe carries an
arbitrary command line as authority.

**Rationale**: The current validation plan joins catalog commands into strings,
which cannot safely express Windows quoting, allowed destinations, installed
files, cleanup, or side-effect policy.

**Alternatives considered**: Sanitizing arbitrary shell strings was rejected;
quoting and indirect executables make a meaningful allowlist unreliable.

## Decision 3: Preserve eight independent stage results

**Decision**: Store source, Windows install/registration, MCP startup, protocol,
safe backend probe, Wright onboarding, Wright gateway, and cleanup separately.
Use only the seven result values defined by the specification and attach a
stable reason/recovery to every non-pass.

**Rationale**: A package can install while its proprietary host is absent; a
remote endpoint may have no local install; a protocol pass does not prove a
backend; and gateway failure does not erase direct MCP evidence.

**Alternatives considered**: Reusing the current single `passed/failed/blocked`
status was rejected because it produces the confusing compatibility labels the
user identified.

## Decision 4: Bind currency to source, package, schema, machine, and credentials

**Decision**: Evidence records immutable source/package identities and digests,
tool-schema digest, a redacted machine observation digest, and a boolean-only
credential-binding digest. A mismatch or maximum-age expiry makes the projected
claim stale without deleting history.

**Rationale**: Wright already applies comparable staleness bindings to local MCP
protocol evidence; Windows install claims need the same protection plus package
and residue bindings.

**Alternatives considered**: Date-only staleness was rejected because a package
or schema can change immediately after a run.

## Decision 5: Use an injected Windows executor with process-tree ownership

**Decision**: The native executor receives reviewed structured operations,
creates Wright-owned temporary/package roots, starts processes without a shell,
captures bounded streams, uses per-stage timeouts, inventories child processes,
and performs graceful shutdown followed by `psutil` process-tree termination.
Residue snapshots compare only declared roots and explicitly named local Wright
registrations; the harness never scans or modifies broad user/system state.

**Rationale**: Native Windows evidence cannot be inferred from Linux Docker, and
cleanup requires ownership of the actual process tree and isolated paths.

**Alternatives considered**: Docker-on-Windows was rejected as Windows evidence;
global npm/Python installs and administrator-owned sandboxes violate the goal.

## Decision 6: Keep normal gates offline and real qualification opt-in

**Decision**: Tests use fake source/package/transport/onboarding/gateway ports and
tiny local process fixtures. The native runner requires an explicit CLI action,
Windows target, allowlist confirmation, evidence root, and approved safety
decision. It never runs as part of `pytest` or the merge gate.

**Rationale**: Deterministic development gates must not fetch or execute third-
party MCPs and must remain usable air-gapped.

**Alternatives considered**: Weekly live install tests were rejected for this
loop; scheduled source-current metadata checks may be added later without live
execution.

## Decision 7: Project a concise signed summary, not raw evidence

**Decision**: Each catalog entry may carry a bounded Windows qualification
summary with date, current/stale state, evidence path/digest, and eight engineer-
facing group results: source, package/registration, startup, protocol,
host/backend, Wright setup, gateway, and cleanup. The UI shows this compact grid and expands recovery context;
raw process material is never served.

**Rationale**: Engineers need a clear answer in the MCP Server Library while
full evidence remains an auditable maintainer artifact.

**Alternatives considered**: Showing the raw JSON or the legacy compatibility
badge alone was rejected for usability and information-safety reasons.

## Decision 8: Preliminary canonical-source findings

These are source/safety inputs, not final qualification claims. They must be
rechecked and pinned in per-server evidence immediately before action.

| Server | Canonical primary source finding on 2026-08-13 | Planned boundary |
|---|---|---|
| `brep-mcp` | The active [andymai/brepjs](https://github.com/andymai/brepjs) repository documents the `brepjs-cad` package and `brep-mcp` stdio server. Its `run_program` capability executes authored JavaScript and can export STEP, so it is not a read-only general probe. | Inspect pinned npm/Git manifests and dependencies first; if approved, install locally and use only a deterministic disposable model in an isolated root. |
| `solid-edge-mcp-burhop` | The catalog's canonical [burhop/SolidEdgeMCP](https://github.com/burhop/SolidEdgeMCP) URL returns 404. No publisher-controlled replacement has been established. | Do not clone or execute. Record `obsolete_or_unavailable` unless the exact canonical source reappears during recheck. |
| `aps-mcp-server-nodejs` | Autodesk's [official repository](https://github.com/autodesk-platform-services/aps-mcp-server-nodejs) was archived by its owner on 2026-05-07 and requires APS credentials plus a Secure Service Account private key. | Source-current fails; do not install an archived server merely because old code remains downloadable. Record the archival and credential boundary. |
| `autodesk-product-help-mcp` | [Autodesk Product Help](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html) documents a public no-auth Streamable HTTP endpoint at `https://developer.api.autodesk.com/knowledge/public/v1/mcp` and two read-only documentation tools. | Local install is `not_applicable`; connect, initialize/list tools, call only product listing or bounded help search, then validate Wright registration/gateway. |
| `autodesk-fusion-desktop-mcp` | [Autodesk documentation](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html) says Fusion hosts the local endpoint at `http://127.0.0.1:27182/mcp` only while Fusion is running and the user-enabled preference is on. | No separate package install. Detect the loopback endpoint without starting/configuring Fusion; absence is `partial/host_required`. No mutating tool call. |
| `autodesk-fusion-data-mcp` | [Autodesk's Fusion MCP overview](https://help.autodesk.com/view/fusion360/ENU/?guid=FMCP-OVERVIEW) describes a cloud Streamable HTTP server on Autodesk infrastructure that requires Autodesk account OAuth and no Fusion desktop host. | Local install is `not_applicable`; do not start OAuth. Record the documented endpoint/auth boundary and register only if Wright can do so without beginning credential flow. |
| `onshape-labs-featurescript-mcp` | The [official Onshape Labs page](https://www.onshape.com/en/features/onshape-labs) currently labels FeatureScript MCP “Coming Soon,” while a dated official announcement URL and preview endpoint appear in the catalog. Source state is therefore time-sensitive and potentially inconsistent. | Recheck the exact official announcement/endpoint. Do not authenticate or accept App Store terms; record subscription/OAuth or unavailable boundary. |

## Decision 9: Remote registration is not installation

**Decision**: Remote and built-in-host recipes use `not_applicable` for local
package installation and record the registration/connection result separately.

**Rationale**: Telling users that a public endpoint was “installed on Windows”
is inaccurate and obscures credential and service availability.

**Alternatives considered**: Treating every onboarding record as installation
was rejected because it repeats the UI confusion already reported.

## Decision 10: Archived, missing, and risky sources remain visible

**Decision**: Safety-blocked and obsolete/unavailable results generate complete
source/safety/cleanup evidence and remain visible in the catalog with install
actions disabled. They do not disappear and do not inherit old optimistic notes.

**Rationale**: Users need to understand why a known MCP cannot be recommended,
and maintainers need evidence for later re-evaluation.

**Alternatives considered**: Removing entries or retaining `likely` platform
claims was rejected because both hide the present source truth.
