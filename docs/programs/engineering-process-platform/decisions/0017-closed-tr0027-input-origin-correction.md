# ADR 0017: Use one closed TR-0027 input-origin correction

**Status:** proposed; exact V5 approval required  
**Decision ID:** `DEC-P0-017`

## Context

TR-0027 `/inputs/3` names `APR-EPP-F01-REPAIR-PLANNING-001.json` as an input at source commit `c3012733d358dbbeb4821a2fbf5449d6d1b12c47`. Git proves the approval is absent there and that both the approval and TR-0027 were first added by container commit `88481d57f1258f59f303f507eafc4e352569bc11`.

The immutable record is factually wrong about origin, but rewriting it would destroy the append-only evidence chain. A generic exception would be worse: it could allow newly created authority to masquerade as a source input.

## Proposed decision

Preserve both historical blobs and admit exactly one correction profile: `COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001`. It binds the exact transition, `/inputs/3`, approval, source, container/tree, raw digests and Git blobs. The validator must prove source absence, unique container introduction, exact container blob and the unchanged two-path manifest.

The original finding remains visible. Only its historical input-origin disposition may become resolved. The profile cannot change transition/output manifests, approval content or authority, lifecycle state, readiness, gates, benchmark counts, candidate/freshness, delivery, or release eligibility. Unsupported readers fail closed.

## Consequences

T024/T026/T030/T031 incorporate the proof without adding a task or changing T069. DEC-P0-017, PROG-01 and PROG-05 remain blocked until exact V5 `material_change` and `feature_implementation` approvals bind the frozen profile and independent tests prove `1/1` closure plus non-interference. EPP-F01B, T042–T068 before the T041 value gate, and all external/integration/release actions remain unauthorized.

Rollback removes only correction interpretation; it does not edit history and returns the finding to unresolved.
