# Tasks: Control-Plane Validator and Live Readiness Dashboard

**Input**: Design documents from `/specs/076-control-plane-validator/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and both completed checklists

**Tests**: Required by FR-020 and SC-002–SC-010. Story tests are written first and must fail for the intended missing behavior before implementation.

**Authority gate**: Do not execute any checkbox until an exact human approval authorizes both EPP-F01 implementation and the material contract decisions R-004 through R-008, binds this task file and the remaining planning artifacts by digest, and expands the implementation lease to the exact paths below. Approval does not authorize push, PR, merge, dev integration, external mutation, publication, benchmark execution, or release.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Logically parallel because it uses different files after its dependencies; the singleton mutating lease and sole-writer rule still apply.
- **[Story]**: User story traceability from `spec.md`.
- Every task names its target path and may be checked only with its required evidence.

## Phase 1: Setup and Frozen Compatibility Evidence

**Purpose**: Establish the repo-local package, deterministic fixtures, and failing contract tests without changing public product code or dependencies.

- [ ] T001 Create the thin entrypoint and importable package skeleton in `scripts/validate-engineering-process-program.py` and `scripts/program_control/__init__.py`
- [ ] T002 [P] Freeze the approved revision-1-through-9 compatibility checkpoint, exact identities, and legacy exceptions in `tests/program_control_plane/fixtures/epp-bootstrap-v1-r1-r9.json`
- [ ] T003 [P] Create isolated temporary-Git-repository builders with fixed clocks, paths with spaces, raw-byte mutation, and Git command spies in `tests/program_control_plane/conftest.py` and `tests/program_control_plane/fixture_builder.py`
- [ ] T004 [P] Add planning-contract schema meta-tests and expected implementation-path assertions in `tests/program_control_plane/test_contract_schemas.py`
- [ ] T005 Document the no-new-dependency setup, supported Python/Git prerequisites, and focused invocation in `scripts/README.md`

**Checkpoint**: Package imports, fixture builders, and contract tests exist; no semantic validator behavior is claimed.

---

## Phase 2: Foundational Machine Contracts

**Purpose**: Material schema/policy/evidence migrations and strict shared primitives that block every user story.

**Critical**: This phase may begin only when the exact implementation/material-change approval is current.

- [ ] T006 [P] Add failing v2 program-state and transition domain/event contract tests, including frozen v1 bootstrap acceptance and rejection of new v1 records, in `tests/program_control_plane/test_transition_chain.py`
- [ ] T007 [P] Add failing lease-identity, approval-history, due-date, and safe-reference contract tests in `tests/program_control_plane/test_roadmap_approval_and_lease.py`
- [ ] T008 [P] Add failing catalog/evidence uniqueness, exact-candidate, freshness, and non-passing-classification contract tests in `tests/program_control_plane/test_dashboard_projection.py`
- [ ] T009 Promote the approved lifecycle-policy schema and instantiate the closed legal graphs, event rules, WIP limits, path roles, action rules, approval boundaries, and bootstrap profile in `docs/programs/engineering-process-platform/schemas/lifecycle-policy.schema.json` and `docs/programs/engineering-process-platform/lifecycle-policy.json`
- [ ] T010 Update the state-machine prose to match the machine policy and explicitly describe state domains, attempt/repair events, source/container history, and the v1 checkpoint in `docs/programs/engineering-process-platform/coordinator-state-machine.md`
- [ ] T011 Promote the approved gate-catalog schema and transcribe all 27 current gates exactly once with evaluator, requiredness, assertions, freshness, and independence policy in `docs/programs/engineering-process-platform/schemas/gate-catalog.schema.json` and `docs/programs/engineering-process-platform/gate-catalog.json`
- [ ] T012 Promote the approved gate-evidence schema and create an honest initial evidence set for the current non-product/non-benchmark candidate without passing unsupported gates in `docs/programs/engineering-process-platform/schemas/gate-evidence.schema.json` and `docs/programs/engineering-process-platform/gate-evidence.json`
- [ ] T013 Migrate program-state and transition-evidence schemas to v2 feature-state, domain/event, source/container, complete-manifest, and `FeatureLeaseV2` fields in `docs/programs/engineering-process-platform/schemas/program-state.schema.json` and `docs/programs/engineering-process-platform/schemas/transition-evidence.schema.json`
- [ ] T014 Add append-only approval revocation/supersession/material-change semantics and structured due/review dates in `docs/programs/engineering-process-platform/schemas/approval.schema.json`, `docs/programs/engineering-process-platform/schemas/decision-register.schema.json`, and `docs/programs/engineering-process-platform/schemas/risk-register.schema.json`
- [ ] T015 Append the approved material-change record and explicit v1-to-v2 migration transition without rewriting revisions 1–9 in `docs/programs/engineering-process-platform/evidence/approvals/`, `docs/programs/engineering-process-platform/evidence/transitions/`, and `docs/programs/engineering-process-platform/program-state.json`
- [ ] T016 Promote the validation-report schema and migrate the dashboard schema to source `S`, inferred container `C`, exact candidate `R`, release approval, input-manifest digest, evidence classifications, and candidate status in `docs/programs/engineering-process-platform/schemas/validation-report.schema.json` and `docs/programs/engineering-process-platform/schemas/dashboard.schema.json`
- [ ] T017 Implement duplicate-key rejection, UTF-8 JSON loading, explicit compatibility tables, Draft 2020-12 validation, canonical state hashing, and stable schema findings in `scripts/program_control/json_contracts.py`
- [ ] T018 Implement safe repository-root/path normalization and read-only Git object access with argument arrays and checkout-representation separation in `scripts/program_control/git_subject.py`
- [ ] T019 Run the focused foundational contract tests and record exact commands/results in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-foundation.json`

**Checkpoint**: Machine contracts validate, history remains append-only, and shared parsers/Git identity primitives are ready. No story is complete yet.

---

## Phase 3: User Story 1 — Validate the Program Before Acting (Priority: P1) — MVP

**Goal**: A maintainer validates one exact committed program subject and receives a fail-closed verdict plus the sole proven next action.

**Independent Test**: A frozen valid temporary Git program and the current committed control plane pass; one raw or semantic mutation per FR-003–FR-009 class fails with the expected stable code and no authorized action. Clean CRLF representation preserves committed identity.

### Tests for User Story 1

- [ ] T020 [P] [US1] Add raw malformed/duplicate-key, missing/extra field, invalid format, unknown-major, and undeclared-minor cases in `tests/program_control_plane/test_json_contracts.py`
- [ ] T021 [P] [US1] Add exact blob/canonical digest, monotonic revision, append-only history, legal domain/event edge, bootstrap-profile, and complete-manifest cases in `tests/program_control_plane/test_transition_chain.py`
- [ ] T022 [P] [US1] Add DAG cycle, dependency, tie ambiguity, status/evidence, blocking decision/risk, approval scope/freshness/revocation, WIP/pointer, and lease identity/action cases in `tests/program_control_plane/test_roadmap_approval_and_lease.py`
- [ ] T023 [P] [US1] Add LF-blob/clean-CRLF, mixed/dirty checkout, detached/missing Git, path-with-spaces, unsafe path/symlink, and no-mutating-Git-command cases in `tests/program_control_plane/test_git_subject.py`
- [ ] T024 [US1] Add valid end-to-end and multi-fault deterministic CLI cases with exact exit classes and no source changes in `tests/program_control_plane/test_cli.py`

### Implementation for User Story 1

- [ ] T025 [US1] Implement normalized validation subject and complete authoritative-input manifest resolution in `scripts/program_control/git_subject.py`
- [ ] T026 [US1] Implement schema/reference/raw/canonical digest and append-only transition/history semantic checks in `scripts/program_control/validation.py`
- [ ] T027 [US1] Implement roadmap graph, decision/risk due status, approval freshness/scope, WIP/pointer, lease, and sole-next-action derivation in `scripts/program_control/validation.py`
- [ ] T028 [US1] Implement stable finding/report entities, deterministic aggregation/sorting, and fail-closed precedence in `scripts/program_control/validation.py`
- [ ] T029 [US1] Implement `validate` argument parsing, versioned JSON/text rendering, bounded exits, and top-level exception containment in `scripts/program_control/cli.py` and `scripts/validate-engineering-process-program.py`
- [ ] T030 [US1] Document exact validate prerequisites, pass/fail/blocked semantics, evidence inspection, and recovery in `docs/programs/engineering-process-platform/README.md` and `scripts/README.md`
- [ ] T031 [US1] Run the complete US1 fixture matrix plus current-control-plane validation and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US1.json`

**Checkpoint**: US1 is independently useful as a read-only validator and the suggested MVP stopping point.

---

## Phase 4: User Story 2 — See Four Truthful Readiness Areas (Priority: P2)

**Goal**: Generate one evidence-linked dashboard whose four readiness areas and release formula are independently derived for one exact candidate.

**Independent Test**: Each area independently passes, blocks, fails, and becomes stale; only that area changes. A 100-terminal-success benchmark fixture never compensates for another area or missing exact release approval.

### Tests for User Story 2

- [ ] T032 [P] [US2] Add gate-catalog completeness, one-row-per-gate, denominator/numerator, status precedence, and evidence-link cases in `tests/program_control_plane/test_dashboard_projection.py`
- [ ] T033 [P] [US2] Add the four-area independence matrix, honest empty state, all benchmark counters/deficits, and 100-success traps in `tests/program_control_plane/test_dashboard_projection.py`
- [ ] T034 [P] [US2] Add source `S`/container `C`/candidate `R`, dashboard-only successor, generator/input-manifest digest, stale-source, and seed/non-evidence cases in `tests/program_control_plane/test_dashboard_provenance.py`
- [ ] T035 [P] [US2] Add exact-subject release approval, cross-candidate rejection, and no-manual-green cases in `tests/program_control_plane/test_dashboard_projection.py`

### Implementation for User Story 2

- [ ] T036 [US2] Implement gate catalog/evidence validation, freshness evaluation, and exact-candidate binding in `scripts/program_control/dashboard.py`
- [ ] T037 [US2] Implement independent area derivation and catalog-ordered gate rows with fixed non-passing precedence in `scripts/program_control/dashboard.py`
- [ ] T038 [US2] Implement benchmark summary/deficit derivation and the exact four-area-plus-human-approval release formula in `scripts/program_control/dashboard.py`
- [ ] T039 [US2] Implement source/input-manifest/generator provenance and source/container currentness validation in `scripts/program_control/dashboard.py`
- [ ] T040 [US2] Update the durable dashboard contract and seed/current interpretation to match the approved v2 provenance model in `docs/programs/engineering-process-platform/status-dashboard-contract.md` and `docs/programs/engineering-process-platform/dashboard.json`
- [ ] T041 [US2] Run the complete US2 independence/provenance matrix and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US2.json`

**Checkpoint**: US2 generates a truthful candidate projection but does not grant release or integration authority.

---

## Phase 5: User Story 3 — Diagnose and Recover Safely (Priority: P3)

**Goal**: Deterministic bounded diagnostics and transactional dashboard generation preserve the last valid snapshot and prevent sensitive output.

**Independent Test**: Multi-fault fixtures report all safely discoverable findings in stable order; injected validation/write/flush/`fsync`/replace failures leave prior bytes unchanged and no residue; runtime-built sensitive canaries appear nowhere in output.

### Tests for User Story 3

- [ ] T042 [P] [US3] Add multi-fault collection, stable ordering, exit precedence, bounded recovery, and unknown-exception containment cases in `tests/program_control_plane/test_cli.py`
- [ ] T043 [P] [US3] Add runtime-built credential/token/prompt/log/payload/endpoint/authority/command and Windows/UNC/POSIX absolute-path canaries across JSON/text/stdout/stderr in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [ ] T044 [P] [US3] Add successful atomic replacement plus candidate-validation, write, flush, `fsync`, reread, replace, and interruption failure injection in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [ ] T045 [P] [US3] Add before/after source-identity and allowed-target-only mutation assertions for valid and invalid runs in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`

### Implementation for User Story 3

- [ ] T046 [US3] Implement metadata allowlisting, bounded reason/recovery catalogs, relative-path rendering, and redacted internal failures in `scripts/program_control/cli.py`
- [ ] T047 [US3] Implement same-directory UTF-8/LF temporary writing, flush, file-`fsync`, reread validation, atomic replace, and cleanup in `scripts/program_control/dashboard.py`
- [ ] T048 [US3] Implement `generate-dashboard` delivery envelopes and preserve-prior behavior without mutating a stale snapshot in `scripts/program_control/cli.py`
- [ ] T049 [US3] Run the complete US3 failure/redaction/immutability matrix and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US3.json`

**Checkpoint**: Failure behavior is inspectable and recovery is bounded without source mutation or leakage.

---

## Phase 6: User Story 4 — Reproduce the Result in an Empty Context (Priority: P4)

**Goal**: A fresh agent reproduces the verdict and follows exact evidence from committed documentation and output alone.

**Independent Test**: Two fixed-clock runs over one subject produce byte-identical machine output; Windows/POSIX semantic fixtures agree; a reviewer follows every sampled gate/finding reference and determines the same blocker/pass without conversation history.

### Tests for User Story 4

- [ ] T050 [P] [US4] Add fixed-clock, shuffled discovery/insertion order, two-run byte identity, and declared observation-field exclusion cases in `tests/program_control_plane/test_determinism.py`
- [ ] T051 [P] [US4] Add seed, frozen-v1 profile, explicitly supported prior contract, unknown generator, unsupported major/minor, and removed-validator rollback cases in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [ ] T052 [P] [US4] Add repository-relative evidence resolvability and empty-context walkthrough assertions in `tests/program_control_plane/test_evidence_walkthrough.py`

### Implementation for User Story 4

- [ ] T053 [US4] Finalize deterministic semantic JSON and concise human report rendering from one model in `scripts/program_control/cli.py`
- [ ] T054 [US4] Replace planning-language quickstart with exact supported commands, outputs, compatibility table, manual fallback, and rollback journey in `specs/076-control-plane-validator/quickstart.md` and `docs/programs/engineering-process-platform/README.md`
- [ ] T055 [US4] Add operator/developer troubleshooting, limitations, reason-code reference, and support-safe evidence inspection in `scripts/README.md` and `docs/programs/engineering-process-platform/status-dashboard-contract.md`
- [ ] T056 [US4] Run the complete US4 determinism/compatibility/evidence-walkthrough suite and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US4.json`

**Checkpoint**: All four user stories are independently demonstrated locally; no integration or release claim follows.

---

## Phase 7: Cross-Cutting Gates, Rollback, and Verification Handoff

**Purpose**: Integrate the focused suite into Wright's local gates, prove rollback/compatibility, and freeze a candidate for a different verifier.

- [ ] T057 [P] Route `docs/programs/engineering-process-platform/**`, `scripts/program_control/**`, the entrypoint, and `tests/program_control_plane/**` through focused tests in `scripts/check-dev-push.sh`
- [ ] T058 [P] Add `scripts/program_control` and focused tests to Ruff, formatting, MyPy, and early full-gate tranches in `scripts/check-dev-merge.sh` and `.github/workflows/python-quality.yml`
- [ ] T059 [P] Add Windows focused program-control execution without duplicating validator semantics in `.github/workflows/test-windows.yml`
- [ ] T060 Add regression coverage proving docs/control-plane changes cannot bypass validator routing in `tests/release/test_dev_push_process.py`
- [ ] T061 Reconcile user/operator/developer docs, schema index, compatibility/rollback instructions, gate impacts, and unsupported claims in `docs/programs/engineering-process-platform/schemas/README.md`, `docs/programs/engineering-process-platform/gates.md`, `docs/contributing/dev-push-runbook.md`, and `specs/076-control-plane-validator/quickstart.md`
- [ ] T062 Run focused pytest, Ruff, formatting, MyPy, planning-contract schema validation, manual quickstart, source-mutation audit, and the applicable local pre-push gate; record exact commands, environment, skips, failures, and digests in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-author.json`
- [ ] T063 Exercise removal/manual-validation rollback and previous-compatible snapshot reading, then record immutable source and prior-dashboard identities in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-rollback.json`
- [ ] T064 Inspect the full candidate diff for scope, secrets/private payloads, generated/binary artifacts, dependency drift, benchmark/product execution, and unauthorized external/Git changes in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-diff-audit.json`
- [ ] T065 Freeze the exact candidate commit/tree/artifact manifest, author identity, commands, acceptance envelope, remaining limitations, and rollback pointer in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-candidate.json`
- [ ] T066 Stop author mutation and have a different independent-verifier identity rerun the critical deterministic, negative, platform, quickstart, evidence-link, rollback, and original-failure/skip review on the unchanged candidate; persist its verdict in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-independent.json`

**Stop**: Any author change after T065 invalidates T066. A failed/blocked verifier returns to bounded repair with a stable cause; passing verification permits only a request for separate dev-integration approval.

---

## Dependencies and Execution Order

### Phase Dependencies

```text
exact implementation + material-change approval
                    │
                    ▼
     Phase 1 Setup → Phase 2 Foundation
                           │
                           ▼
                    Phase 3 US1 (MVP)
                           │
                           ▼
                    Phase 4 US2
                           │
                           ▼
                    Phase 5 US3
                           │
                           ▼
                    Phase 6 US4
                           │
                           ▼
              Phase 7 Gates and Verification
```

- Phase 1 has no implementation dependency beyond exact approval and lease expansion.
- Phase 2 depends on Phase 1 and blocks all user stories.
- US1 depends on the foundation and is the independently shippable MVP.
- US2 depends on US1's validated source/report model.
- US3 depends on US2's candidate-generation path.
- US4 depends on the complete report/projection behavior from US1–US3.
- Phase 7 depends on all stories. T066 depends on candidate freeze at T065 and a distinct verifier.

### Within-Phase Dependencies

- Tests precede their corresponding implementation tasks and must fail for the intended missing behavior.
- T009–T016 depend on T006–T008; T017–T018 may proceed after their relevant schema expectations are fixed; T019 depends on all foundation work.
- T025–T029 depend on T020–T024; T030–T031 depend on the US1 implementation.
- T036–T040 depend on T032–T035; T041 depends on all US2 work.
- T046–T048 depend on T042–T045; T049 depends on all US3 work.
- T053–T055 depend on T050–T052 and prior stories; T056 depends on all US4 work.
- T060 depends on T057; T062 depends on T057–T061; T063–T064 depend on T062; T065 depends on T062–T064; T066 depends on T065.

### Parallel Opportunities

- T002–T004 use distinct files after T001.
- T006–T008 are separate test modules.
- Within US1, T020–T023 are separate modules; within US2, T034 is separate from T032/T033/T035; within US3, T042–T045 divide CLI, privacy, atomicity, and mutation assertions; within US4, T050–T052 are separate modules.
- T057–T059 target distinct gate/workflow files.
- `[P]` is dependency information, not permission to exceed the singleton writer/lease rule.

---

## Implementation Strategy

### MVP First

1. Obtain exact feature/material-change approval and implementation lease.
2. Complete setup and foundational migrations without rewriting history.
3. Deliver US1 as the read-only local validator.
4. Stop and validate US1 independently before continuing if scope, contract, or repair risk changes.

### Incremental Delivery

1. US1: exact committed-subject validation and next action.
2. US2: four independent readiness projections and non-circular provenance.
3. US3: bounded diagnostics, privacy, and atomic generation.
4. US4: deterministic empty-context reproduction and compatibility.
5. Gate integration, rollback, candidate freeze, independent verification, then separate integration approval.

## Task Summary

- Total tasks: 66
- Setup/foundation: 19
- US1: 12
- US2: 10
- US3: 8
- US4: 7
- Cross-cutting/verification: 10
- Suggested MVP: Phases 1–3 (US1), followed by a deliberate validation checkpoint

## Notes

- No task adds or upgrades a dependency, changes product runtime, creates/executes benchmark cases, contacts external systems, pushes, opens/merges a PR, integrates to `dev`, publishes, or releases.
- Task checkboxes are progress markers, not lifecycle or approval evidence.
- Optional Spec Kit auto-commit hooks remain disabled for this workflow because reviewed allowlist staging is required; no `git add .` may be used.
- Every evidence task records original failures/skips as well as terminal results; reruns cannot erase earlier evidence.
