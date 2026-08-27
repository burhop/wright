# DEC-P0-018 — Closed two-claim repair-evidence correction

- **Status:** Proposed; implementation-blocking
- **Owner:** human program and architecture approver
- **Decision boundary:** before correction implementation, candidate refreeze, T066 retry, dashboard delivery, or integration request

## Question

May EPP-F01 recognize exactly `COR-EPP-F01-REPAIR-EVIDENCE-001` to dispose two immutable planning/repair evidence defects without rewriting their original Git objects or changing any readiness, approval, candidate, benchmark, delivery, or release result?

## Context

Exact validation of local commit `b61b069c6a68688193a60c7f39d9f2b8044027bf` found two closed defects introduced during bounded candidate repair:

1. state revisions 45 and 46 use invalid identifier spelling `CANDIDATE_RUFF_FORMAT_DRIFT` at the same recovery pointer; and
2. TR-0044 records a 63-character SHA-256 for the exact TR-0043 input because one `b` was omitted.

The original commits and blobs are immutable audit evidence. Editing them in place or accepting a generic exception would violate append-only control-plane rules.

## Proposed decision

Accept only the two ordered claims in `COR-EPP-F01-REPAIR-EVIDENCE-001`. The validator must recompute every bound path, pointer, introducing commit/tree, Git blob, raw SHA-256, and canonical state digest; retain the original findings and bytes; reject every addition, omission, substitution, wildcard, range, current-pointer, authority, readiness, benchmark, candidate, delivery, release, or correction target; and prove full projection non-interference. Unsupported readers fail closed.

Implementation requires separate same-subject `material_change` and `feature_implementation` approvals. Planning approval alone does not activate the profile.

## Rejected alternatives

- Rewrite or amend the historical commits or evidence files.
- Broaden either earlier correction profile.
- Add a generic schema/digest waiver or partial-resolution mechanism.
- Continue T066–T068 while exact validation fails.

## Required approval evidence

- Exact two-claim profile and promoted/feature contract schemas.
- Negative matrix for every identity, occurrence-set, pointer, ancestry, authority, forbidden-class, and correction-of-correction mutation.
- Correction-off/on deep equality for all readiness, benchmark, candidate, approval, delivery, and release projections.
- Independent read-only audit and exact frozen artifact manifest.
