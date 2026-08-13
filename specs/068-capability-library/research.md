# Research: Capability Library and MCP Onboarding

**Date**: 2026-08-12
**Scope**: Discovery, catalog trust, import compatibility, installer isolation, evidence taxonomy, current-machine checks, UI information architecture, and Onshape official evidence.

## Method and evidence rules

- Prefer protocol specifications, vendor documentation, vendor repositories, and established update-security specifications.
- Treat a repository name, vendor logo, directory listing, or community statement as discovery evidence only.
- Record official status only when a vendor-authoritative source supports it.
- Do not equate successful protocol initialization with application-level validation.
- Keep confirmed MCPs, API/wrapper candidates, documentation-only resources, and watchlist/no-public-MCP entries distinct.
- Research does not authorize subscription, license acceptance, credential use, endpoint invocation, or software installation.

## Decision 1: Wright publishes a reviewed aggregate snapshot

**Decision**: Wright ships a complete offline snapshot and optionally consumes upstream sources in a reviewed publisher pipeline. User installations fetch only a Wright-approved signed snapshot. They do not query the official MCP Registry or arbitrary directories on every page load.

**Rationale**:

- The official MCP Registry API supports cursor pagination, search, update-time filtering, latest-version selection, and deleted records, which is suitable for an aggregator ingestion job.
- MCP's registry documentation describes downstream aggregators that retain, enrich, and filter registry data.
- The registry has been preview software and does not provide the offline, durability, engineering evidence, platform, host-software, or local validation guarantees Wright requires.
- A reviewed snapshot allows Wright to merge official registry facts with vendor sources, clean-container evidence, platform compatibility, and explicit exclusions.

**Primary sources**:

- [Official Registry API reference](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md)
- [MCP Registry about](https://modelcontextprotocol.io/registry/about)
- [Registry aggregators](https://modelcontextprotocol.io/registry/registry-aggregators)
- [server.json draft schema](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/draft/server.schema.json)
- [server.json change log](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/CHANGELOG.md)

**Alternatives considered**:

- **Direct end-user Registry queries**: rejected as a core path because it is not offline and would expose users to upstream availability/schema changes without Wright review.
- **Manual code releases only**: rejected because newly released official servers would remain unavailable until a Wright software release.
- **Unreviewed third-party aggregator feed**: rejected because evidence and supply-chain policy would be delegated to an unknown party.

## Decision 2: Signed, expiring, monotonic catalog envelopes

**Decision**: Use a Wright-pinned Ed25519 public verification key and a canonical JSON envelope containing channel, sequence, issued/expiry times, schema version, SHA-256 payload digest, key identifier, and signature. Reject unknown keys, bad signatures, digest mismatches, expired metadata, non-increasing sequences, schema failures, and identity conflicts. Persist candidate, active, and previous snapshots transactionally.

**Rationale**:

- Hash-only verification detects corruption but cannot authenticate who published the new hash.
- TLS authenticates a network connection but does not provide durable offline provenance or protect a copied/replayed artifact after download.
- Ed25519 supplies compact deterministic signatures with standard library support through Wright's existing cryptographic runtime dependency.
- Sequence plus expiry provides rollback and bounded freeze protection. An active/previous transaction provides deterministic local rollback.
- The design deliberately borrows the signed-versioned-expiring metadata and rollback/freeze threat model from The Update Framework while avoiding an unnecessary multi-role repository in the first single-publisher channel.

**Primary sources**:

- [The Update Framework specification](https://github.com/theupdateframework/specification/blob/master/tuf-spec.md)
- [python-tuf reference implementation](https://github.com/theupdateframework/python-tuf)
- [Sigstore bundle format](https://docs.sigstore.dev/about/bundle/)
- [MCP Registry releases with checksums, signatures, and SBOM assets](https://github.com/modelcontextprotocol/registry/releases)

**Alternatives considered**:

- **Full TUF repository now**: strongest delegation and root-rotation story, but rejected for the first single-publisher data channel because it adds multiple roles, repository tooling, metadata expiry operations, and a significant new dependency surface. The envelope fields and tables are versioned so a later TUF client can replace verification without changing capability records.
- **Sigstore-only snapshot**: useful for transparency and keyless CI identity, but requires online or bundled transparency evidence and more publisher infrastructure. It remains a compatible future publisher option.
- **TLS plus SHA-256**: rejected because it does not authenticate a stored or side-loaded update.
- **Embedded private signing key**: prohibited. Only public verification material may ship in Wright.

**Residual risk and mitigation**:

- A compromised Wright signing key can sign a malicious catalog. Mitigate with offline publisher key custody, bounded expiry, audited preview, no catalog-triggered execution, and an emergency trust-root software update.
- The first format does not rotate trust roots inside catalog data. Root change therefore requires an ordinary reviewed Wright release, which is conservative and reversible.

## Decision 3: Data ownership is split, activation is atomic

**Decision**: Store immutable signed snapshot records and the active/previous pointers in SQLite. Reconcile only catalog-owned metadata into the existing MCP registry within the same activation transaction. Keep install state, process state, custom entries, credentials, user disablement, and workspace grants outside snapshot ownership.

**Rationale**:

- SQLite `BEGIN IMMEDIATE` serializes the single local writer while preserving concurrent readers under the existing WAL configuration.
- One transaction prevents a pointer from referring to a snapshot whose metadata projection only partially applied.
- Additive tables preserve existing installations and allow older software to ignore the new feature.
- The package-resource catalog remains a separately validated recovery root.

**Alternatives considered**:

- **Active/previous files only**: simple, but coordinating a file swap with SQLite user-state reconciliation creates a cross-store partial-commit risk.
- **Overwrite the packaged YAML**: impossible for immutable installed packages and unsafe for rollback.
- **Replace `mcp_servers` from each snapshot**: rejected because current rows own user choices and lifecycle state.

## Decision 4: Evidence is a first-class taxonomy

**Decision**: Add an explicit `evidence_class` with these values:

1. `official_production`
2. `official_preview`
3. `verified_community`
4. `community_candidate`
5. `user_reported_source_needed`
6. `api_wrapper_candidate`
7. `documentation_only`
8. `blocked_validation`
9. `excluded_or_stale`

Legacy `verification_state`, `maturity`, `installability_tier`, and `validation_result` remain available and are mapped conservatively when a catalog record has not yet been curated with the new field. A mapping can never promote a record to either official class without a vendor-authoritative source record.

**Rationale**:

- Existing fields mix source authority, protocol existence, validation result, and installability.
- A separate evidence class prevents “has vendor name,” “works as an API,” and “is an official MCP” from collapsing into one badge.
- Retaining legacy fields permits a staged migration of the current 69 records.

**Alternatives considered**:

- **Replace every legacy field immediately**: rejected as a high-risk catalog-wide migration with no user benefit.
- **One verified/unverified boolean**: rejected because it loses the distinctions the engineering program depends on.

## Decision 5: Import is a non-executing normalized preview

**Decision**: Initially support three documented JSON shapes:

- Claude-family project/user shape: top-level `mcpServers`.
- Visual Studio Code shape: top-level `servers` with optional top-level `inputs`.
- Plain single-server object for vendor documentation and the UI's remote/local forms.

Each server normalizes to name, transport, command or URL, literal argument list, non-secret environment metadata, credential requirements, headers-as-credential requirements, source format, warnings, and field-level errors. Import never executes, expands variables, evaluates shell syntax, contacts a URL, or persists pasted secret values.

**Primary sources**:

- [Claude Code MCP configuration and scopes](https://code.claude.com/docs/en/mcp)
- [VS Code MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)
- [VS Code MCP server user documentation](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
- [MCP Authorization specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/index.mdx)
- [MCP Bundle manifest](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md)

**Important compatibility facts**:

- Claude project configuration uses `.mcp.json` with a top-level `mcpServers` object and asks users to approve project-scoped servers.
- VS Code configuration uses a top-level `servers` object, can declare reusable `inputs`, supports local stdio and remote HTTP/SSE, and warns that local MCPs can run arbitrary code.
- Common formats permit environment variables or headers that may contain secrets. Wright must extract requirements and send actual values only through its secret boundary.

**Alternatives considered**:

- **Arbitrary YAML/TOML/shell snippets**: deferred until an authoritative grammar and safe tokenization exist.
- **Reuse a shell parser and execute `--help` during preview**: rejected because preview must have no machine effects.
- **Copy every unknown field through**: rejected because unknown security-relevant semantics would become executable configuration.

## Decision 6: Exact Install Plans precede all effects

**Decision**: Replace ad hoc “install” semantics with an immutable Install Plan derived from a capability revision plus a current-machine observation. The plan enumerates executable/endpoint, literal arguments, package/source pin, dependencies, network and storage effects, credentials, approvals, validation, rollback, and blockers. The approval digest covers all material fields.

**Rationale**:

- Existing validation plans describe probes but not the exact lifecycle or review binding.
- A plan gives the UI and policy layer one stable object for local packages, remote endpoints, and host bridges.
- Rechecking the snapshot and machine-observation digests before apply prevents time-of-check/time-of-use drift.

**Alternatives considered**:

- **One-click catalog command execution**: rejected because catalog data must not become implicit executable authority.
- **Separate unrelated plans per backend**: rejected because users need a consistent review journey and policy needs one digest.

## Decision 7: Installer backends are isolated adapters

**Decision**: Define prepare, apply, validate, rollback, and remove boundaries for:

- `local_package`: a reviewed package-manager/source recipe installed into a Wright-owned isolated location.
- `remote_endpoint`: an HTTP/SSE registration with bounded initialize/discovery and no local software install.
- `host_bridge`: detection of an already installed supported application/add-on, local handshake, and optional read-only probe.
- `local_command`: an advanced explicit command that is registered only after exact preview and approval.

Normal tests use injectable fake adapters. Catalog refresh never invokes an adapter. This feature does not install proprietary host applications.

**Primary sources**:

- [MCP architecture and transports](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP lifecycle specification](https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification)
- Wright clean-container process: `docs/mcp-catalog/mcp-server-testing-process.md`

**Alternatives considered**:

- **Containerize every MCP**: rejected because remote services and desktop bridges do not fit, and host communication needs explicit policy.
- **Install MCP-specific host software into Wright's base image**: prohibited by project policy and would make the base unbounded.

## Decision 8: Compatibility is observed, reasoned, and time-bounded

**Decision**: A read-only observation records OS, architecture, Wright distribution mode, available package managers/runtimes, exact executable resolution and version, container availability, network policy, and requested host application/add-on facts. A policy combines that observation with catalog requirements to yield `compatible`, `incompatible`, `uncertain`, or `blocked`, plus stable reason codes and recovery actions.

**Rationale**:

- Catalog platform labels are evidence about tested environments, not proof about the current machine.
- A timestamp and digest make staleness visible and bind approval to what was actually checked.
- Unknown is not compatible; it remains visible and actionable.

**Alternatives considered**:

- **Static platform badge only**: rejected because it cannot detect missing runtimes or installed host versions.
- **Install dependencies while probing**: rejected because preflight must remain read-only.

## Decision 9: Capability Library information architecture

**Decision**: Retain Wright's global navigation location but rename the page **Capability Library**. Separate the journey into:

1. **Discover**: search, filters, badges, compatibility reason.
2. **Understand**: evidence, source, license, data/credentials, requirements, validation, alternatives.
3. **Add**: catalog, paste config, remote, local, or report missing.
4. **Review plan**: exact effects and blockers.
5. **Validate**: protocol and optional read-only result with evidence.
6. **Use in workspace**: explicit single-workspace enablement.

Catalog update history/preview/rollback is an administrator panel, not mixed into every card. Installation and workspace enablement use different verbs and confirmation screens. Invocation approval is explained but remains in later workflow/run surfaces.

**Rationale**:

- The current page combines discovery, installation, credentials, process state, and reporting in large cards; the current missing-report path uses browser prompts.
- Progressive disclosure lets engineers compare capabilities before dealing with setup mechanics.
- Separate verbs reduce the risk that “installed” or “enabled” is read as permission to run destructive tools.

**Alternatives considered**:

- **Continue expanding each Tool Card**: rejected because dense cards do not scale to evidence, update history, compatibility, and multi-step onboarding.
- **Per-workspace library only**: rejected because discovery and administration are global, while use is workspace-scoped.

## Decision 10: Official Onshape Labs acceptance record

**Decision**: Add a distinct catalog record for **Onshape Labs FeatureScript MCP** with:

- vendor: Onshape/PTC
- evidence class: `official_preview`
- transport: remote Streamable HTTP
- endpoint: `https://fs-mcp.labs.onshape.app/mcp`
- vendor release source: Onshape's “How Onshape Labs FeatureScript MCP Server Enables Text-to-Code-to-CAD” article
- marketplace source: the Onshape App Store listing
- prerequisites: Onshape account, sign-in, and Onshape Labs subscription
- validation: `not_tested`/external follow-up; do not claim OAuth or tool results without authoritative/live evidence
- default enabled: false

**Primary sources**:

- [Onshape: How Onshape Labs FeatureScript MCP Server Enables Text-to-Code-to-CAD](https://www.onshape.com/en/blog/featurescript-mcp-server-enables-text-code-cad)
- [Onshape App Store listing](https://cad.onshape.com/appstore/apps/Onshape%20Labs/6a29aea7c03f8bf659841734)
- [Onshape Labs overview](https://www.onshape.com/en/features/onshape-labs)
- [PTC Onshape Labs announcement](https://www.ptc.com/en/news/2026/onshapelabs)

**Evidence note**: Onshape's article instructs users to sign in, subscribe through the App Store, and connect the published MCP URL from a compatible client. This supports official-preview existence and endpoint facts. It does not authorize Wright to subscribe or establish the exact authentication exchange. The existing community Onshape MCP records remain separate identities.

**Alternatives considered**:

- **Replace community Onshape entries**: rejected because they are distinct implementations and evidence classes.
- **Claim production status**: rejected; the vendor labels the capability as Onshape Labs.
- **Live-validate now**: rejected because subscription/license and credentials are unavailable and explicitly outside autonomous authority.

## Decision 11: Migration and backward compatibility

**Decision**: Add tables and fields; do not delete or repurpose current `mcp_servers` columns or endpoints. Bootstrap the bundled snapshot, derive capability views, and progressively move the UI to the new endpoints. Existing custom rows remain listed even when no active catalog record exists.

**Rationale**:

- Existing users and tests rely on the current server registration and credential endpoints.
- Additive storage permits feature rollback and older-code tolerance.
- A merged projection makes ownership visible and prevents catalog activation from resetting user state.

## Deferred research and follow-ups

- Publisher root rotation, delegated vendor roles, and a full TUF repository are deferred until Wright operates a durable external catalog service.
- Official MCP Registry ingestion automation belongs in the publisher/weekly validation workflow; clients still consume approved Wright snapshots.
- Live Onshape initialization/tool discovery requires the user's subscription/license acceptance and credentials.
- Usability target SC-009 requires a later moderated five-engineer study. Automated tests verify information architecture and accessibility but cannot fabricate human evidence.
- Additional import grammars (Codex TOML, Cursor variants, arbitrary YAML) require authoritative stable examples and separate adversarial-parser coverage.
