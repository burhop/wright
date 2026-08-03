# Research: Rivet Compatibility Spike

**Branch**: `055-rivet-compatibility-spike`

**Date**: 2026-08-03

## Decision: Select a Source Commit, Not a Floating Package Line

**Decision**: The spike selects a candidate by immutable upstream commit plus the exact resolved application, core, Node, and executor dependency graph. It records the source archive hash, lockfile hash, package tarball integrity values, build command, generated asset manifest, and output checksums.

**Rationale**: Rivet's application, core, and Node packages have independently evolving versions. A semver range, `main`, or `latest` cannot prove that an editor build and Node executor are mutually compatible or remain reproducible.

**Alternatives considered**:

- Pin only npm packages: rejected because it omits the editable UI build and patch context.
- Vendor a release binary: rejected because it does not expose the host-adapter seam or reproducible browser/Docker build path.
- Track upstream main: rejected because a later upstream change could silently alter the evidence result.

## Decision: Start With the Official Node Integration API

**Decision**: The runner probe uses the upstream Node integration surface, centered on `runGraphInFile`, external functions, abort signal, process events, and remote debugger APIs.

**Rationale**: This is the narrowest documented host-runner path and allows Wright to supervise a separate process instead of coupling execution to the browser editor.

**Alternatives considered**:

- Browser executor: inspect only; it is unsuitable as a production decision because of visible-editor and CORS lifecycle constraints.
- In-process JavaScript from Python: rejected because it would create an unsupported compatibility layer and reduce process isolation.
- Unmanaged CLI process: rejected because it cannot establish typed events, cancellation, or a governed host bridge.

## Decision: Prove Per-Instance Host Provider Injection

**Decision**: The editor probe must establish a per-instance injection mechanism for IO, dataset, native API, and debugger configuration. The proof must open two fixture instances with distinct mock workspace identities and demonstrate that state/capabilities do not cross.

**Rationale**: Wright needs one retained editor per active workspace. A process-global mutable provider, global browser store, or shared project directory would violate workspace separation before the production persistence slice can defend it.

**Alternatives considered**:

- Use upstream browser storage: rejected; it is not workspace-owned.
- Use a single global adapter and switch it on focus: rejected; inactive editors can retain callbacks and stale authority.
- Directly mount Wright workspace files: rejected; it bypasses mediated path and permission enforcement.

## Decision: External Calls Are the First Governed-Bridge Candidate

**Decision**: The fixture uses an external call that invokes a mock Wright operation. It records function discovery, argument/value representation, error propagation, cancellation interaction, and remote-debugger visibility. A Wright-owned plugin is evaluated only if this seam cannot express necessary safe UX or typed behavior.

**Rationale**: External calls are host-provided and keep the graph's requested operation separate from actual Wright authority. This aligns with the planned `GatewayService` boundary.

**Alternatives considered**:

- Direct Rivet MCP configuration: rejected as a candidate because it would create a second tool-authority path.
- Arbitrary third-party plugin: rejected because supply-chain and code authority would be unbounded.
- Build a plugin first: deferred until the external-call evidence proves it necessary.

## Decision: Offline Must Be Observed, Not Assumed

**Decision**: The fixture runs behind a network-denial proxy/firewall or an equivalent deterministic request interceptor after all declared build inputs are present. The report captures every attempted outbound authority and classifies it as declared build input, blocked defect, or supported packaged asset.

**Rationale**: Lockfiles do not detect CDN fonts, telemetry, dynamic plugin import, source-map, package metadata, or browser fetches.

**Alternatives considered**:

- Review source only: rejected because indirect dependencies and generated assets can still fetch at runtime.
- Allow first-run download: rejected by Wright's offline-first requirement.

## Decision: Keep the Spike Non-Production

**Decision**: All downloaded/upstream/generated artifacts, scripts, fixtures, and patches remain below `integrations/rivet/spike/` and are excluded from production package ownership. The spike does not update application dependency manifests, routes, schemas, Dockerfiles, installers, or UI navigation.

**Rationale**: The evidence may produce a no-go result. Isolation makes rollback a deletion of experimental assets rather than a data migration or feature removal.

## Candidate Selection Criteria

The experiment chooses its primary candidate only when it has:

1. A public immutable upstream revision or release source that can be archived and hashed.
2. A compatible published `@ironclad/rivet-core` and `@ironclad/rivet-node` resolution with a supported Node version.
3. A reproducible editor build that can serve at a non-root path without Tauri-only startup requirements.
4. A feasible per-instance provider injection strategy, with any patch small enough to review and maintain.
5. A Node fixture path supporting run, bounded events, cancellation attempt, and external call.
6. A license/security inventory with an actionable disposition for all shipped dependencies.
7. A credible no-runtime-download/offline path.

The fallback candidate is investigated only if the primary candidate fails a mandatory criterion. The spike cannot silently select a less secure workaround merely to obtain a green demo.

## Decision Outcomes

| Outcome | Meaning | Next action |
|---|---|---|
| Go | All mandatory criteria have repeatable evidence; limitations are enforceable by later slice contracts. | Start `rivet-workspace-persistence`; pass exact constraints to runner/editor slices. |
| Conditional-go | A bounded non-production gap has a named owner, deadline, and safe default that does not weaken mandatory boundaries. | Amend the umbrella plan if scope/sequence changes, then start only unaffected slices. |
| No-go | A mandatory workspace, governance, offline, licensing, or packaging criterion cannot be met. | Stop before production implementation and present the smallest viable alternative/amendment. |

## Sources

- Rivet repository and license: <https://github.com/Ironclad/rivet>
- Host runner integration: <https://rivet.ironcladapp.com/docs/api-reference/getting-started-integration>
- External Call: <https://rivet.ironcladapp.com/docs/node-reference/external-call>
- Remote debugging: <https://rivet.ironcladapp.com/docs/user-guide/remote-debugging>
- Dataset provider: <https://rivet.ironcladapp.com/docs/node-reference/load-dataset>
- Plugin authoring constraints: <https://rivet.ironcladapp.com/docs/user-guide/plugins/creating-plugins>

These sources establish candidate seams. Only recorded spike evidence establishes a supported Wright compatibility baseline.
