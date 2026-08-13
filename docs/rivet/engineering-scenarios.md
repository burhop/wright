# Rivet Engineering Scenarios

Engineering scenarios are curated Rivet workflows that coordinate several
workspace-enabled MCP capabilities and then check whether the resulting
engineering evidence is meaningful. A successful tool call is not automatically
an engineering pass.

## What ships in Loop 070

| Scenario | Domains | Deterministic MCP calls | Representative checks |
|----------|---------|-------------------------|-----------------------|
| Structural bracket | CAD, Python, FEA | 3 | Geometry, mass, convergence, stress |
| Electronics enclosure cooling | ECAD, CAD, CFD, Python | 4 | Board/enclosure clearance, convergence, temperature, margin |
| Parametric manufacturing | Grasshopper, CAD, additive, slicing, CAM | 5 | Data-tree topology, geometry, 3MF/build data, slicer summary, static CAM safety |

All three examples are Tier 1. They run offline against separate deterministic
MCP processes through Wright's existing workspace gateway and Rivet run
authority. They require no paid service, credential, proprietary application,
GPU, hardware, or large download. CAM and additive evidence is static; Wright
does not send it to a machine.

## Engineer workflow

1. Open **Rivet Workflows** and find **Engineering scenarios**.
2. Read the domains, tier, resource class, duration, and safety boundary.
3. Select **Check and prepare**. Wright installs the package-owned Rivet project
   into this workspace and resolves the exact namespaced MCP tools.
4. Resolve any blocker. The preflight result names the missing or incompatible
   capability and gives a recovery action.
5. Review the exact prepared workflow and capability bindings in the existing
   Rivet review screen.
6. Select **Run reviewed scenario**. Rivet receives only the short-lived,
   run-bound Wright provider described in [Rivet MCP Workflows](mcp-gateway.md).
7. Inspect the engineering report. It names the producer node and capability,
   expected rule, observed value, units, recovery, artifact digest, and cleanup
   state. Export contains bounded metadata and hashes, not raw paths, reusable
   authority, credentials, or proprietary payloads.

Preflight is not execution authority. A changed workflow, graph, binding,
server revision, schema, validation record, workspace grant, or policy makes the
existing review stale and blocks Start.

## Evidence model

Each child result must contain a versioned artifact envelope. Wright accepts
exactly one bounded inline structured value or authorized vault reference,
recomputes its digest, retains original unit/coordinate declarations, and links
the producer run, node, call, and namespaced capability. Script content,
traversal text, unrestricted file URIs, raw host paths, secrets, oversized
values, unsupported schemas, NaN, and infinity fail closed.

Numeric comparisons normalize explicitly declared compatible units to SI.
Wright never guesses whether a bare value means metres or millimetres, and
absolute temperature is distinct from temperature difference.

Assertion plugins currently cover generic numeric relationships, geometry,
ECAD, FEA/CFD convergence and input correlation, Grasshopper-style data trees,
3MF/additive summaries, slicer summaries, and static CAM lint. Results are
`pass`, `fail`, `skip`, or `error`; every non-pass result has a stable reason and
recovery action.

Scenario reports use additive SQLite migration 15. Terminal reports are
immutable and idempotent. A restart may finish a running report from durable
workflow output only when the recorded scenario revision, manifest digest, and
assertion-set digest still match. Otherwise Wright reports
`scenario_rebuild_identity_mismatch` rather than guessing.

## Adding a deterministic scenario

1. Read the public schemas in
   `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/contracts/`.
2. Add a static Rivet project whose MCP nodes use exact namespace-qualified tool
   names. Do not add server commands, URLs, credentials, environment variables,
   or application lifecycle settings.
3. Add a manifest with stable identity/revision, at least two Tier 1
   capabilities, resources, timeouts, safety, cleanup, artifacts, assertions,
   and provenance.
4. Add small deterministic fixtures. Wright-generated fixtures declare
   `fixture_origin: wright-generated` and a license. Third-party data also needs
   source, license, redistribution, and modification records.
5. Prefer an existing assertion plugin. A new plugin must use a new exact
   name/version, return bounded observations, reject incompatible schemas and
   units, and include negative tests. Duplicate plugin versions are rejected.
6. Add the manifest to `catalog.yaml`, then run the contract, catalog, fixture,
   artifact, assertion, gateway, API, component, and browser tests. Every
   packaged workflow node, artifact, fixture, and assertion reference is
   validated before publication.

Material changes require a manifest revision change. Time and trace values may
be excluded from strict comparison only when declared; engineering inputs,
tolerances, fixtures, implementations, schemas, bindings, artifacts, and
environment classification remain material.

## Tier classification and real MCP probes

- **Tier 1** is deterministic, offline, bounded, and credential-free.
- **Tier 2** is an explicit, disposable clean-container probe of a confirmed
  public MCP. It may require authorized network access, but never mutates the
  developer host or silently accepts a license.
- **Tier 3** is credentialed, proprietary, GPU, hardware, large-asset, or manual
  evidence. It is not a normal gate.

Before any Tier 2 install or startup, Wright checks explicit opt-in, disposable
container use, platform support, catalog confirmation, network/credential/app/
GPU/hardware/large-download requirements, license review, interactive prompts,
and host mutation. API-wrapper candidates, watchlist entries, and entries with
no public MCP are never projected as runnable MCPs.

Loop 070 defines evidence-only adapters for two previously probed catalog
entries:

- `nvidia-elements-mcp`, safe tool `skills_list`. Existing GB10 clean-container
  evidence is partial. The catalog currently records its license as unknown, so
  a new unattended validation remains blocked until the exact package license
  metadata is reviewed. Wright/Hermes gateway evidence is also pending.
- `ansys-fluent-mcp`, safe tool `session_status`. Existing GB10 clean-container
  evidence is partial and returned `connected:false` without Fluent. A
  status-only gateway probe does not authorize solver work. Live Fluent remains
  Tier 3 because it needs a licensed local or remote application.

Use the [MCP Server Testing Process](../mcp-catalog/mcp-server-testing-process.md)
and the reviewed commands in the
[MCP setup recipes](../mcp-catalog/mcp-server-setup-recipes.md). The plan records
catalog, package/install-command, platform, discovery, gateway, result, and
cleanup digests. Missing credentials or applications are classified as blocked;
partial protocol evidence is not promoted to a full pass.

Downloaded source, package caches, container residue, and `.local-run/` remain
untracked. MCP-specific host software never enters Wright's base image.

## Recovery and rollback

- Missing or ambiguous capability: enable and validate one exact workspace MCP,
  rerun preflight, and review the new binding.
- Changed scenario/workflow identity: restore the package-owned workflow or
  prepare a new revision; do not reuse an old review.
- Unit or assertion failure: inspect the named producer, artifact digest,
  declared unit, expected rule, and observed value.
- Cancellation residue: inspect the reported process/container/file residue
  before retrying. A cancelled run never publishes a late success.
- Disable the feature by hiding the scenario endpoints/UI section. Ordinary
  Rivet workflows and Loop 069 MCP execution remain unchanged; migration 15 is
  additive and can remain dormant.

Gate E remains closed: never use a scenario to start motion, heat, extrusion, a
spindle, a robot, a PLC, or other physical equipment.
