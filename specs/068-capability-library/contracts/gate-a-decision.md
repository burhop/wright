# Gate A Decision: Catalog Trust and UX

**Status**: Approved by advance program authorization
**Date**: 2026-08-12
**Scope**: Evidence taxonomy, update/rollback, Install Plan, and top-level UI information architecture.

## Evidence

- Wright's catalog already contains 69 rich engineering records, explicit platform data, aliases, source records, validation results, bundle selectors, and clean-container evidence.
- The official MCP Registry supports aggregator ingestion but is not sufficient as an offline engineering evidence store.
- TUF establishes signed versioned expiring metadata as the appropriate response to repository tampering, rollback, and freeze threats.
- Claude and VS Code both require users to review local/project MCP configuration because local MCP commands can run arbitrary code.
- The current Wright page mixes discovery, install/connect, credentials, validation, and reporting, and missing reports use browser prompts.
- Onshape published a vendor-authoritative Labs FeatureScript MCP endpoint on 2026-08-11, but using it requires an account and App Store subscription that Wright cannot accept autonomously.

## Decision

1. **Evidence taxonomy**: adopt nine explicit classes from official production through excluded/stale. Do not infer official status. Preserve legacy fields and map conservatively.
2. **Update trust**: use a pinned Ed25519 public key, canonical signed envelopes, SHA-256 payload binding, sequence and expiry enforcement, schema/identity/evidence validation, and an administrator preview. No signature bypass exists.
3. **Activation/rollback**: persist immutable snapshots and active/previous pointers in SQLite; reconcile catalog-owned metadata and swap pointers in one transaction; always retain the bundled recovery snapshot.
4. **Install Plan**: require an immutable digest-bound plan based on exact capability revision and current-machine observation before any local package, remote endpoint, host bridge, or advanced local command effect.
5. **UI**: rename the global page Capability Library and separate Discover -> Understand -> Add -> Review plan -> Validate -> Use in workspace. Invocation approval remains outside this loop.
6. **Onshape**: list Onshape Labs FeatureScript MCP as official preview with subscription-required and not-live-validated limitations. Do not contact it or claim exact authentication/tool evidence.

## Alternatives

| Alternative | Benefit | Why not selected now |
|-------------|---------|----------------------|
| Full TUF repository/client | Mature multi-role delegation and root rotation | Disproportionate publisher/runtime complexity for one Wright-owned alpha channel; versioned envelope can migrate later |
| TLS plus hash | Minimal code | Does not authenticate stored/side-loaded artifacts or prevent signed-source impersonation |
| Direct official Registry UI | Broad current discovery | Not offline, not engineering-curated, and upstream availability/schema becomes a core dependency |
| Catalog command executes on click | Fast onboarding | Gives data-update content implicit execution authority and skips exact effects review |
| Keep expanding Tool Cards | Small UI change | Cannot clearly scale to evidence, compatibility, update history, and seven-step onboarding |
| Replace community Onshape entries | Simpler search | Incorrectly collapses distinct implementations and evidence classes |

## Risks and controls

| Risk | Control |
|------|---------|
| Signing key compromise | Offline publisher custody, short expiry, human diff, no update-triggered execution, software-shipped emergency root change |
| Custom format misses TUF edge cases | Strict versioned schema and canonical bytes; bounded single channel; migrate verifier without changing catalog payload |
| Snapshot/user-state partial commit | One SQLite activation/reconciliation transaction |
| Secret leakage through imports | Request-lifetime raw text only; safe normalized projection; adversarial scan tests; existing secret endpoint |
| Preflight becomes execution | Allowlisted read-only detectors; no command from imported/catalog data is run until approved apply |
| UI wording implies authority | Separate verbs/states; workspace enablement explanation; no invocation control on Library page |
| Onshape evidence overstated | Official-preview badge, source link, subscription prerequisite, explicit no-live-validation state |

## Rollback

- Product data rollback selects the named previous verified snapshot transactionally.
- Corrupt/unavailable state falls back read-only to the packaged recovery snapshot and raises a diagnostic.
- Additive migration and legacy endpoints allow the feature merge to be reverted without deleting existing server/custom/secret/workspace state.
- Gate decision can move to full TUF later by adding verifier/envelope version 2; capability identities and payload remain stable.

## Authorization rationale

The program goal explicitly authorizes Gates A-D to proceed with the safest reversible choice supported by the program plan, primary-source research, and current architecture. This choice is fail-closed, additive, does not accept licenses or spend money, and does not widen machine authority. No human interruption is required under that authorization.
