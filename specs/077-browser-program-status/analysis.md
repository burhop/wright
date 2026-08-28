# Spec Kit Analysis: Browser Program Status

**Analyzed**: 2026-08-28

**Artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `checklists/`, `tasks.md`, constitution v3.0.0

## Result

**PRIMARY PASS after bounded repair attempt 2 for `EPP-F01B-REVIEW-CONTRACT-001` — exact-commit independent re-verification pending.**

- Functional requirements: 39
- Requirements mapped to implementation/test tasks: 39/39
- Dependency-ordered tasks: 48, sequential and unique
- Requirements-quality checks: 36/36 passed
- Unresolved clarification markers: 0
- Constitution violations: 0
- Hidden or unresolved P0 questions: 0

## Coverage map

| Requirement group | Requirements | Primary task coverage | Result |
| --- | --- | --- | --- |
| Authority, identity, atomicity | FR-001–FR-003, FR-020–FR-024 | T005–T012, T035–T044 | Covered |
| Four readiness areas and release rule | FR-004–FR-008 | T013–T020 | Covered |
| Product, benchmark, commercial, program health | FR-009–FR-012, FR-034 | T013–T020, T021–T025 | Covered |
| Work, blockers, evidence, corrections | FR-013–FR-018 | Exact EPP-F01 dashboard, typed governance supplement, and T026–T034 | Covered |
| Sensitive-data and offline boundaries | FR-025–FR-026 | T005, T012–T013, T041 | Covered |
| Accessibility and dedicated page | FR-027–FR-030 | T014–T020, T027, T042–T043 | Covered |
| Exact-time histories and honest task scope | FR-031–FR-035, FR-039 | T021–T025, T040 | Covered |
| Proposed catalog vs qualified benchmark | FR-036 | T015, T030–T034 | Covered |
| Integration and development lanes | FR-037–FR-038 | T030–T034 | Covered |

## Findings resolved during initial analysis

1. **Identity-change blind spot**: the initial data model described `bundle_id` as a projection-only digest, which could miss a changed committed source with identical values. It now binds canonical `source + projection`, excluding only non-semantic publisher observation time.
2. **Allowlist/schema mismatch**: the initial nested contract admitted open-ended objects despite the sensitive-field allowlist. Gate outcomes, histories, lanes, checkpoints, findings, corrections, freshness, release, work, and benchmark detail are now closed or explicitly bounded; safe paths reject traversal/backslashes.
3. **Non-executable packaging task**: the fallback packaging task lacked exact paths. T040 now names the packaged resource, wheel-content/native-lifecycle tests, and documentation target.

## Independent-review repair disposition

Both independent audits failed the pre-repair commit `62af844bdabfe01831ea1096b5d2f7691b0512ec`, and both rejected repair-attempt-1 commit `b1406344bbd67e0c4239b7ddffaf82b3003de61d` for remaining facets of the same stable cause. Repair attempt 2 addresses those exact facets:

- The exact EPP-F01 dashboard is embedded unchanged for the fields it actually contracts; a closed non-authoritative governance supplement covers lifecycle/lease/delivery/correction/finding/risk/decision/verification data sourced from separate committed evidence.
- Raw committed snapshot bytes and canonical parsed dashboard-object bytes have separate recomputed digests.
- The FastAPI route now delegates through `tool_registry` as constitution §1 literally requires.
- Histories have fixed machine-readable semantics, causal transition/parent order, source classes, explicit omissions, and deterministic latest-change records.
- Standard committed-HEAD publisher and package-install triggers are explicit; the publisher default is two seconds and the five-second ETag loop has a ten-second end-to-end acceptance test. Mutable publisher heartbeat has complete service/API/client/UI/end-to-end coverage and cannot change bundle identity.
- Actions, distinct closed lanes, exact safe lease projection, catalog maturity, evidence navigation, safe roots, URL bounds, installed/fallback precedence, Windows/Linux/macOS atomic replacement, closed-version compatibility, RBAC, test IDs, and native lifecycle behavior are contractually/testably bounded.
- Runtime and browser decoders reject incoherent action authority, ambiguous evidence resolution, bad catalog sums, duplicate lane branches, observation/series source mismatches, and completed tasks above total.
- Scripted solo-maintainer comprehension replaces unsupported population percentages.

This is repair attempt 2 of 2 for `EPP-F01B-REVIEW-CONTRACT-001`. The same two reviewers must re-verify the repaired exact commit before the final PASS/freeze claim. Any further material failure for this stable cause exhausts the repair limit and requires a stop.

## Consistency conclusions

- The five stories remain independently demonstrable after the shared identity/read foundation.
- Proposed customer stories cannot enter the governed qualification numerator.
- Feature-local task completion cannot be presented as whole-program completion.
- Historical points require exact commits and trustworthy timestamps; omitted data remains disclosed.
- Runtime has no source-checkout, Git, network, benchmark, product-execution, or mutation dependency.
- Implementation, dependency, benchmark, push/PR/merge, publication, and release authority remain absent.

## Remaining review gate

The engineering-usability and architecture/test reviewers must re-verify repair attempt 2. No additional repair remains for this stable cause. After both pass, rerun consistency checks, preserve the audit record, and freeze the exact commit/tree/program-tree/digest subject; stop at human approval before T001.
