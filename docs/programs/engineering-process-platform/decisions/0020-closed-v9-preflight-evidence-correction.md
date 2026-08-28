# DEC-P0-020 — Closed EPP-F01 V9 preflight-evidence correction

**Status:** Proposed; pending exact V9 approval.

## Decision

Permit a validator to disposition exactly the two immutable findings enumerated by `COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001` after fresh same-subject `material_change` and `feature_implementation` approval:

1. externally validate the exact committed schema-less `EPP-F01-V8-discovery.json` blob against the exact-value `v8-discovery-evidence.schema.json` contract; and
2. recognize only TR-0051's exact 35-path changed set where the transition self path is recorded last instead of at canonical sorted index 9.

Both claims require exact paths, blobs, raw SHA-256 values, introducing commit/tree/program tree, strict ancestry, and Git-object recomputation. The discovery's missing `/$schema` finding and the manifest-order finding remain visible with this correction reference; neither historical file is edited.

## Guardrails

This decision is not schema inference and not a general unordered-manifest rule. Any other schema-less artifact, schema family, identity, path, pointer, manifest count/set/order defect, duplicate, missing or extra path, wildcard, range, present/future record, generic waiver, or correction-of-correction fails closed. This planning subject replaces the stale V8 approval action with the V9 approval action; after freeze, correction-off/on verification preserves those exact V9 lifecycle-policy bytes and the roadmap-policy result. Authority, leases, tasks outside T077–T080, four readiness areas, benchmark progress, gates, candidate, delivery, dashboard bytes, and release eligibility are unchanged.

Planning and re-analysis do not implement this decision. The possible V9 lease is T077–T080 only. T073–T076, the roadmap-policy repair, T066–T068, EPP-F01B implementation, dependencies, benchmark work, external changes, push/PR/merge/dev integration, publication, and release remain unauthorized. After T080, the coordinator remains blocked until a later explicit reactivation.

## Consequences

- Old validators fail closed.
- Original evidence remains byte-identical and auditable.
- V9 success cannot be cited as V8 completion or product, benchmark, commercial, or release readiness.
- The unfinished T073 working copy remains in reversible local stash object `bf05abcc37236d030fbcd08830a9d065703b9a46` (base `9f30322859e8039863b47cdcb0e4c8f29354c9dc`; one file, 286 insertions) outside the approval subject. It is incomplete and non-authoritative; a fresh clone need not possess it, and its absence never authorizes recreation or application.
