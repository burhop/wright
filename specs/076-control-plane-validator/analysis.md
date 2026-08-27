# Specification Analysis Report: EPP-F01 V5 Approval Subject

**Analysis method**: `speckit-analyze` non-destructive consistency, ambiguity, coverage and constitution review after the one-claim TR-0027 input-origin amendment

**Subject**: planning-only candidate to be frozen in `TR-0034`; implementation remains blocked before T024

**Result**: **PASS after repair** — zero active critical, high or medium findings; all 26 functional requirements and 12 success criteria have task coverage

## Inputs and authority

- Feature artifacts: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, both checklists and every contract.
- Program artifacts: revisions/transitions through 35/TR-0034, both closed correction profiles/schemas, DEC-P0-017/ADR 0017, RISK-019, roadmap, lifecycle, gates/catalog, dashboard contract, compatibility/release and V5 audits.
- Constitution: `.specify/memory/constitution.md` version 3.0.0.
- The existing feature branch/worktree is retained; the optional Spec Kit branch/commit/context hooks were not invoked because this is an amendment to the same bounded feature and explicit-path commits remain coordinator-controlled.
- No implementation, dependency, benchmark, product, external, push/PR/merge, integration, publication, or release action was performed.

## Material findings resolved

| ID | Area | Finding | Disposition |
|---|---|---|---|
| V5-EU-01 | Usability | Missing TR-0034 and stale V4 catch-up/analysis could send a cold coordinator back to T069. | Add TR-0034; update README, analysis and exact V5/T041 actions. |
| V5-EU-02 | Authority | “Bind 69 tasks” was conflated with authority to execute all 69. | V5 binds the unchanged plan but authorizes only T024–T041; `REVIEW_EPP_F01_T041_VALUE_CHECKPOINT` gates T042 onward. |
| V5-ARC-01 | Architecture | A stale V3 action competed with V5 for the same blocked state. | Remove the stale action rule; V5 is the sole action for `PROGRAM_ACTIVE/BLOCKED`. |
| V5-ARC-02 | Architecture | The new schema was absent from the closed gate evidence-class registry and automated promotion task. | Add `TRANSITION_INPUT_CORRECTION` to PROG-01/PROG-05 and extend T024 contract-schema coverage. |
| V5-BQ-01 | Benchmark | Generic non-interference language did not require full empty/non-empty benchmark projection equality. | Add a closed unchanged-field list plus deep equality for `0/100` and non-empty synthetic fixtures in FR-020, plan, T024 and T031. |
| V5-CR-01 | Commercial/release | Audit status and exact approval checkpoint were not yet subject-bound. | Bind the four audit reruns and all material outputs through TR-0034; no readiness or release gate is waived. |

## Coverage

| Requirement group | Coverage | Principal tasks |
|---|---:|---|
| FR-001–FR-009: subject, contracts, Git/history, roadmap, authority and semantic invariants | 9/9 | T002–T029, T069 |
| FR-010–FR-018: four independent areas, release formula, read-only/atomic behavior, findings and privacy | 9/9 | T008, T011–T016, T023–T049 |
| FR-019–FR-024: journey, tests, compatibility, benchmark policy, rollback and empty context | 6/6 | T024, T030–T068 |
| FR-025: exact 37-claim committed-identity correction | 1/1 | T069, T026, T028, T030–T031 |
| FR-026: exact one-claim TR-0027 input-origin correction | 1/1 | T024, T026, T028, T030–T031 |
| SC-001–SC-012 | 12/12 | T023–T069 across story and verification phases |

The task plan remains exactly 69 unique IDs: T001–T023 and T069 are complete; 45 tasks remain. No completed task was redefined. Pending T024/T026/T030/T031 absorb the exact one-claim behavior and automated closure without creating a 70th task.

## Consistency conclusions

- TR-0027 and the planning approval remain byte-immutable. The correction binds exact TR-0027 `/inputs/3`, both Git blobs/raw hashes, declared source, unique container/tree, source absence and unchanged two-path manifest.
- The new profile is independent of the approved 37-claim profile. Neither can correct the other, accept a range/wildcard, suppress original findings, create authority, or alter lifecycle/readiness/benchmark/candidate/freshness/release results.
- `TRANSITION_INPUT_CORRECTION` is a distinct closed class/schema/role required by PROG-01 and PROG-05. Unsupported readers fail closed.
- Full correction-off/on equality is required for both honest `0/100` and non-empty benchmark fixtures, including coverage, qualification, oracle/artifact, holdout, attempts/tiers, deficits, freshness, colors, candidate, approval and release eligibility.
- State revision 35 is `BLOCKED`, has no mutating lease, and exposes only exact V5 approval. V5 can authorize T024–T041 only; the T041 demonstration triggers a new human review before T042.
- EPP-F01B and every external/integration/release action remain separately gated.

## Validation evidence and limitations

- 128 JSON documents parse; 32 schemas pass Draft 2020-12 meta-validation.
- The two transition-input schema copies are byte-identical and the one-claim profile validates.
- Independent Git checks reproduced source absence, unique container introduction, transition/approval blobs and raw hashes.
- The existing focused contract module produced 17 passes. Its active-lease assertion intentionally cannot pass in the legal blocked/no-lease planning state, and the first run's local basetemp path was unavailable. T024 already owns the pending closed schema-matrix update; no implementation test was changed during this planning checkpoint.
- The current validator is expected to fail closed on the new unsupported profile until V5-approved T024/T026 implementation. This is compatibility behavior, not approval authority.

## Constitution and next action

The amendment preserves phase isolation, branch/worktree discipline, explicit human gating, offline/read-only planning, test-first implementation, compatibility, rollback, privacy, bounded repair and independent verification. No constitution exception is requested.

Freeze the exact planning artifacts in TR-0034 and stop for separate same-subject V5 `material_change` and `feature_implementation` approvals accepting DEC-P0-017. Do not execute T024 or later work until that gate passes. After approval, stop again immediately after the T041 value demonstration at `REVIEW_EPP_F01_T041_VALUE_CHECKPOINT`.
