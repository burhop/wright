# Engineering Scenario Harness Quality Checklist

**Purpose**: Verify that Loop 070 requirements are safe, complete, diagnosable, reproducible, and usable before task generation
**Created**: 2026-08-13
**Feature**: [spec.md](../spec.md)

## Scenario coverage and independence

- [x] CHK001 Requirements demand three independently runnable Tier 1 scenarios rather than one monolithic demo.
- [x] CHK002 Each Tier 1 scenario requires two or more independently registered MCP servers through Wright.
- [x] CHK003 The three scenarios collectively cover CAD, ECAD, FEA, CFD, Python, CAM, Grasshopper, additive, and slicing.
- [x] CHK004 Acceptance criteria distinguish engineering-valid output from successful process/tool completion.
- [x] CHK005 Scenario metadata includes purpose, domains, tier, resources, duration, dependencies, safety, artifacts, and assertions.

## Artifact and numerical integrity

- [x] CHK006 Every artifact has an explicit versioned type/schema and bounded content or authorized vault reference.
- [x] CHK007 Artifact lineage identifies producer node/call/capability and upstream digests.
- [x] CHK008 Dimensional values require declared units and compatible SI normalization rather than inferred defaults.
- [x] CHK009 Coordinate-system requirements are explicit where geometry handoff makes them material.
- [x] CHK010 Floating-point exact/range/relational/absolute/relative tolerance semantics are specified.
- [x] CHK011 NaN, infinity, absent units, incompatible dimensions, and unsupported schemas fail closed.
- [x] CHK012 Geometry requirements cover non-empty/finite/bounds/degeneracy/manifoldness and mass-property relationships.
- [x] CHK013 ECAD requirements cover header/schema, dimensions, thickness, layers/nets, envelopes, clearances, and handoff frames.
- [x] CHK014 FEA/CFD requirements cover convergence, completeness, physical bounds, residual/conservation, and input correlation.
- [x] CHK015 Grasshopper-style requirements preserve data-tree branch topology, not only flattened values.
- [x] CHK016 3MF/additive requirements cover package relationships, units, meshes/build items, and bounded slicing summaries.
- [x] CHK017 CAM requirements are static-only and prohibit physical actuation and unsafe/ambiguous machine control.

## Gateway, authority, and failure behavior

- [x] CHK018 Requirements explicitly reuse Loop 069 bindings, review, authority, policy, approvals, progress, cancellation, audit, and evidence.
- [x] CHK019 Manifests cannot carry child URLs, commands, credentials, environments, lifecycle configuration, or host paths.
- [x] CHK020 Missing, ambiguous, disabled, stale, denied, or cross-workspace capabilities block before child invocation.
- [x] CHK021 Failure reports name the scenario, node, namespaced capability, artifact, invariant, expected/observed value, units, and reason code.
- [x] CHK022 Transport, policy, MCP/tool, artifact-contract, engineering-assertion, cancellation, and cleanup failures remain distinct.
- [x] CHK023 Cancellation blocks later calls and late result publication and records truthful cleanup/residue.
- [x] CHK024 Secret-like, oversized, executable-markup, traversal, and unrestricted-URI child outputs are rejected or redacted.

## Determinism, tiers, and provenance

- [x] CHK025 Tier 1 forbids credentials, network, paid/proprietary apps, GPU, hardware, large downloads, prompts, and global mutation.
- [x] CHK026 Deterministic seed/revision rules identify allowed variable fields and preserve stable assertion/artifact digests.
- [x] CHK027 Fake integrations are independent MCP processes through the real gateway, not only in-process mocks.
- [x] CHK028 Scenario/fixture license, source, redistribution, and modification requirements are explicit.
- [x] CHK029 Tier 2 uses the documented disposable clean-container process and is excluded from normal gates.
- [x] CHK030 Confirmed MCP, hosted/API-wrapper candidate, and watchlist/no-public-MCP states remain distinct.
- [x] CHK031 Environment guards run before install/start and cannot silently mutate the host or accept licenses.
- [x] CHK032 Reproducibility comparison enumerates every material identity before claiming equivalence.

## Usability, recovery, and compatibility

- [x] CHK033 Scenario library/preflight/report UI fits the existing Rivet workflow panel.
- [x] CHK034 UI requirements provide plain-language domains, tier/resources, safety, participating capabilities, artifacts, status, and recovery.
- [x] CHK035 Keyboard, narrow-width, zoom, focus, and non-color status requirements are measurable.
- [x] CHK036 Existing non-scenario Rivet workflows and other gateway clients retain current behavior and authority.
- [x] CHK037 Reports survive restart and exports omit secrets, bearer authority, raw paths, and proprietary payloads.
- [x] CHK038 Performance limits cover catalog listing, validation, report loading, cancellation, and cleanup.
- [x] CHK039 Schema, event, artifact-preview, and terminal-output bounds are explicit.
- [x] CHK040 Rollback disables scenario surfaces without removing ordinary workflow or MCP capabilities.

## Notes

- All items pass. No critical ambiguity remains for task generation or implementation.
