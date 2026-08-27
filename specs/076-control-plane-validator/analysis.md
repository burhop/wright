# Specification Analysis Report: EPP-F01 V7 Repair-Evidence Amendment

**Analysis method**: `speckit-analyze` non-destructive consistency, ambiguity, coverage, and constitution review after the closed two-claim repair-evidence amendment

**Subject**: planning-only candidate; implementation remains blocked before T070–T072 and any T066 retry

**Result**: **PASS after planning repair and independent review** — complete requirement-to-task coverage, no constitution conflict, and all bounded audit findings dispositioned; only exact Git subject freeze and human approval remain

## Inputs and authority

- Feature artifacts: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, both checklists, and all contracts.
- Program artifacts: current state/history through revision 47/TR-0046, prior approvals and corrections, the proposed repair-evidence correction/schema, DEC-P0-018, RISK-020, roadmap, lifecycle policy, README, and approval boundary.
- Constitution: `.specify/memory/constitution.md` version 3.0.0.
- Authority is planning and re-analysis only. No validator implementation, product code, dependency, benchmark, EPP-F01B implementation, external change, push/PR/merge/integration, publication, or release is permitted.

## Material findings and dispositions

| ID | Severity | Finding | Planning disposition |
|---|---|---|---|
| V7-ARC-01 | High | No exact entity constrained the two defects, so a repair could become a generic historical-evidence waiver. | Add one closed schema/profile with exactly two ordered claims, exact Git identities, explicit forbidden targets, and `accept_new_records=false`. |
| V7-TEST-01 | High | The existing plan had no complete negative matrix for omissions, additions, substitutions, pointer/origin/digest drift, current targets, or missing authority. | Add FR-027/SC-013 and test-first T070 covering every enumerated fail-closed class. |
| V7-DEP-01 | High | The roadmap/tasks did not place correction work before a T066 retry. | Add approval-gated T070–T072 and make a T066 retry depend on a passing replacement freeze. |
| V7-GOV-01 | High | No dedicated P0 decision/risk bounded repair-evidence disposition. | Add DEC-P0-018/ADR 0018 and RISK-020; block EPP-F01 and PROG-01/PROG-05. |
| V7-STATE-01 | High | Current control-plane prose implied active implementation although exact validation is blocked. | Add revision 47/TR-0046: no lease, `BLOCKED`, and sole next action exact V7 human approval. |

## Coverage

| Requirement group | Coverage | Principal tasks |
|---|---:|---|
| FR-001–FR-026 | Preserved | T001–T069 |
| FR-027: exact two-claim repair-evidence correction | 1/1 | T070–T072 |
| SC-001–SC-012 | Preserved | Existing story and verification tasks |
| SC-013: exact claims/occurrences, digest provenance, and projection equality | 1/1 | T070, T072 |

The task plan contains 72 unique append-only identifiers. No completed task is redefined. T070 establishes the failing contract matrix, T071 owns the smallest implementation surface, and T072 owns non-interference/regression/re-freeze evidence. All three remain unchecked and unauthorized.

## Consistency conclusions

- The profile names exactly two claims: one covering two exact historical cause-ID pointers and one covering one exact TR-0044 digest pointer.
- Every immutable target is bound to path, raw SHA-256, Git blob, introducing commit/tree, pointer, recorded value, and authoritative value; state targets also bind canonical state digest.
- Original bytes and findings remain visible. The profile cannot mutate current state, create a record, reactivate a lease, validate the failed candidate, or affect lifecycle, authority, readiness, benchmark, candidate, delivery, or release results.
- DEC-P0-018 and exact same-subject V7 `material_change` plus `feature_implementation` approvals are prerequisites to T070–T072 and a later T066 retry.
- EPP-F01B stays dependency-ordered after EPP-F01 and remains implementation-blocked.

## Constitution and next action

The amendment preserves exact committed evidence, append-only correction semantics, test-first delivery, independent verification, bounded repair, explicit human authority, offline/local operation, compatibility, and rollback. No constitution exception is requested.

Freeze the exact commit/tree/program tree and TR-0046 artifact digests, then stop for separate same-subject V7 `material_change` and `feature_implementation` approval. Do not execute T070–T072 or retry T066.
