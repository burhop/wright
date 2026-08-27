# Tasks: Control-Plane Validator and Governed Readiness Snapshot

**Input**: Design documents from `/specs/076-control-plane-validator/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and both completed checklists

**Tests**: Required by FR-020 and SC-002–SC-013. Story tests are written first and must fail for the intended missing behavior before implementation.

**Authority gate**: Do not execute T024 or any later checkbox until an exact V5 approval bundle contains separate approved `material_change` and `feature_implementation` records bound to the same newly frozen subject; binds the unchanged 69-task plan, every planning contract, and both exact closed correction profiles by digest; accepts R-004 through R-008, R-014 through R-017 / `DEC-P0-013` through `DEC-P0-017`; and reactivates a lease authorizing execution only from T024 through T041. V4 remains historical authority for completed T069 but is stale for further implementation. After the T041 demonstration, the sole action is `REVIEW_EPP_F01_T041_VALUE_CHECKPOINT`; T042–T068 require a new explicit human instruction and authority checkpoint. V5 does not authorize EPP-F01B, push, PR, merge, dev integration, external mutation, publication, benchmark execution, or release.

**Current V7 repair gate**: The prior approvals are historical authority for completed work only. Do not execute T070, T071, T072, retry T066, or perform any later mutation until two new approved records—`APR-EPP-F01-MC-007.json` and `APR-EPP-F01-IMPL-007.json`—bind the same frozen commit/tree/program tree and exact artifact-digest manifest, accept DEC-P0-018 and `COR-EPP-F01-REPAIR-EVIDENCE-001`, and reactivate a lease limited to T070–T072 plus the subsequent T066 retry. Planning and read-only analysis do not satisfy this gate. Product work, EPP-F01B implementation, dependencies, benchmarks, external changes, push/PR/merge/dev integration, publication, and release remain excluded.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Logically parallel because it uses different files after its dependencies; the singleton mutating lease and sole-writer rule still apply.
- **[Story]**: User story traceability from `spec.md`.
- Every task names its target path and may be checked only with its required evidence.

## Phase 1: Setup and Frozen Compatibility Evidence

**Purpose**: Establish the repo-local package, deterministic fixtures, and failing contract tests without changing public product code or dependencies.

- [x] T001 Create the thin entrypoint and importable package skeleton in `scripts/validate-engineering-process-program.py` and `scripts/program_control/__init__.py`
- [x] T002 [P] Freeze exactly two ordered closed compatibility profiles—the unchanged revision-1-through-9 bootstrap and contiguous revision-10-through-19 / `TR-0009`–`TR-0018` bridge—with unique archive/transition paths, exact raw state and historical-transition blob digests, terminal `TR-0018` `checkpoint_commit_blob` identity, canonical edges, runtime-resolved approval-subject checkpoint rule, no-future-v1 rule, and sole v2 successor in `tests/program_control_plane/fixtures/epp-bootstrap-v1-r1-r9.json` and `tests/program_control_plane/fixtures/epp-bridge-v1-r10-r19.json`
- [x] T003 [P] Create isolated temporary-Git-repository builders with fixed clocks, paths with spaces, raw-byte mutation, and Git command spies in `tests/program_control_plane/conftest.py` and `tests/program_control_plane/fixture_builder.py`
- [x] T004 [P] Add planning-contract schema meta-tests and expected implementation-path assertions in `tests/program_control_plane/test_contract_schemas.py`
- [x] T005 Document the no-new-dependency setup, supported Python/Git prerequisites, and focused invocation in `scripts/README.md`

**Checkpoint**: Package imports, fixture builders, and contract tests exist; no semantic validator behavior is claimed.

---

## Phase 2: Foundational Machine Contracts

**Purpose**: Material schema/policy/evidence migrations and strict shared primitives that block every user story.

**Critical**: This phase may begin only when the exact implementation/material-change approval is current.

- [x] T006 [P] Add failing v2 program-state and transition domain/event contract tests, including exact acceptance of the two ordered/contiguous/unique byte-bound v1 profiles, immutable-null checkpoint plus runtime approval-subject resolution, terminal `TR-0018` blob lookup at that subject without a profile/transition hash cycle, and rejection of duplicate/third/gapped profiles, any other null/raw rule, revision 20/any later v1 record, changed transition bytes, mutable endpoint paths, and a second migration successor, in `tests/program_control_plane/test_transition_chain.py`
- [x] T007 [P] Add failing lease-identity, approval-history, due-date, and safe-reference contract tests in `tests/program_control_plane/test_roadmap_approval_and_lease.py`
- [x] T008 [P] Add failing catalog/gate/assertion-result uniqueness and exact coverage, evaluator binding, exact-candidate, freshness, closed class-registry and class/schema/role/source-manifest binding, required-class coverage, mislabeled-artifact rejection, evidence completeness, independence, derived aggregate, non-passing-classification, and empty-evidence pass-rejection contract tests in `tests/program_control_plane/test_dashboard_projection.py`
- [x] T009 Promote the approved lifecycle-policy and legacy-profile schemas; instantiate the closed legal graphs, event rules, WIP limits, path roles, action rules, approval boundaries, unchanged r1–r9 profile, and exact byte-bound r10–r19 bridge whose permanently-null checkpoint is resolved at validation time from the new approval record without mutating the profile in `docs/programs/engineering-process-platform/schemas/lifecycle-policy.schema.json`, `docs/programs/engineering-process-platform/schemas/legacy-compatibility-profile.schema.json`, and `docs/programs/engineering-process-platform/lifecycle-policy.json`
- [x] T010 Update the state-machine prose to match the machine policy and explicitly describe state domains, attempt/repair events, source/container history, and the v1 checkpoint in `docs/programs/engineering-process-platform/coordinator-state-machine.md`
- [x] T011 Promote the approved gate-catalog schema and transcribe all 34 current gates exactly once with evaluator, requiredness, assertions, freshness, and independence policy in `docs/programs/engineering-process-platform/schemas/gate-catalog.schema.json` and `docs/programs/engineering-process-platform/gate-catalog.json`
- [x] T012 Promote the approved gate-evidence schema and create an honest initial evidence set for the current non-product/non-benchmark candidate without passing unsupported gates in `docs/programs/engineering-process-platform/schemas/gate-evidence.schema.json` and `docs/programs/engineering-process-platform/gate-evidence.json`
- [x] T013 Migrate program-state and transition-evidence schemas to v2 feature-state, domain/event, source/container, complete-manifest, and `FeatureLeaseV2` fields in `docs/programs/engineering-process-platform/schemas/program-state.schema.json` and `docs/programs/engineering-process-platform/schemas/transition-evidence.schema.json`
- [x] T014 Add append-only approval revocation/supersession/material-change semantics and structured due/review dates in `docs/programs/engineering-process-platform/schemas/approval.schema.json`, `docs/programs/engineering-process-platform/schemas/decision-register.schema.json`, and `docs/programs/engineering-process-platform/schemas/risk-register.schema.json`
- [x] T015 Validate and append the replacement same-subject approval-bundle records (`material_change` and `feature_implementation`), resolve the immutable bridge checkpoint to that exact approval subject without editing the profile, and emit the sole v1-to-v2 migration transition without rewriting revisions 1–19 in `docs/programs/engineering-process-platform/evidence/approvals/`, `docs/programs/engineering-process-platform/evidence/transitions/`, and `docs/programs/engineering-process-platform/program-state.json`
- [x] T016 Promote the validation-report, dashboard, and verification-evidence schemas with source `S`, explicit/constrained-inferred container `C`, explicit-only delivery commit `D`, exact candidate `R`, closed bounded source-bundle identity, shared per-gate `fresh`, complete assertion results, candidate-only dashboard bytes, independent-passed descendant delivery envelope, release approval, input-manifest digest, complete gate/benchmark fields, actor separation, original failures/skips, and rollback identity in `docs/programs/engineering-process-platform/schemas/validation-report.schema.json`, `docs/programs/engineering-process-platform/schemas/dashboard.schema.json`, and `docs/programs/engineering-process-platform/schemas/verification-evidence.schema.json`
- [x] T017 Implement duplicate-key rejection, UTF-8 JSON loading, explicit compatibility tables, Draft 2020-12 validation, canonical state hashing, and stable schema findings in `scripts/program_control/json_contracts.py`
- [x] T018 Implement safe repository-root/path normalization and read-only Git object access with argument arrays and checkout-representation separation in `scripts/program_control/git_subject.py`
- [x] T019 Run the focused foundational contract tests and record exact commands/results in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-foundation.json`

**Checkpoint**: Machine contracts validate, history remains append-only, and shared parsers/Git identity primitives are ready. No story is complete yet.

---

## Phase 3: User Story 1 — Validate the Program Before Acting (Priority: P1) — MVP

**Goal**: A maintainer validates one exact committed program subject and receives a fail-closed verdict plus the sole proven next action.

**Independent Test**: A frozen valid temporary Git program and the current committed control plane pass; one raw or semantic mutation per FR-003–FR-009 class fails with the expected stable code and no authorized action. Clean CRLF representation preserves committed identity.

### Tests for User Story 1

- [x] T020 [P] [US1] Add raw malformed/duplicate-key, missing/extra field, invalid format, unknown-major, and undeclared-minor cases in `tests/program_control_plane/test_json_contracts.py`
- [x] T021 [P] [US1] Add exact blob/canonical digest, monotonic revision, append-only history, legal domain/event edge, both closed legacy profiles, bridge approval-subject binding, no-future-v1/single-migration, and complete-manifest cases in `tests/program_control_plane/test_transition_chain.py`
- [x] T022 [P] [US1] Add DAG cycle, dependency, tie ambiguity, status/evidence, blocking decision/risk, approval scope/freshness/revocation, WIP/pointer, and lease identity/action cases in `tests/program_control_plane/test_roadmap_approval_and_lease.py`
- [x] T023 [P] [US1] Add LF-blob/clean-CRLF, mixed/dirty checkout, detached/missing Git, path-with-spaces, unsafe path/symlink, dirty/untracked/ignored validator helpers, runtime-HEAD-versus-explicit-S bundle mismatch, loaded-module path escape, and no-mutating-Git-command cases in `tests/program_control_plane/test_git_subject.py`
- [X] T069 [US1] Add the exact closed `COR-EPP-F01-US1-COMMITTED-IDENTITY-001` contract and tests for its six transition claims, 26 state rows/31 pointers, Git-object and canonical-state identities, strict ancestry, V4 approval binding, `37/37` recomputation, visible finding disposition, readiness non-interference, and rejection of every added, omitted, substituted, wildcard, range, same/future/circular, correction, authority, readiness, gate, benchmark, freshness, candidate, or release target in `tests/program_control_plane/test_transition_chain.py` and `tests/program_control_plane/test_cli.py`
- [x] T024 [US1] Add the transition-input correction schema to the closed Draft-2020-12 and byte-identical promotion matrix in `tests/program_control_plane/test_contract_schemas.py`; add valid end-to-end and multi-fault deterministic CLI cases including optional `--container`, constrained `HEAD` inference, explicit-only `--delivery`, every C/D rejection path, the exact one-claim TR-0027 input-origin positive case and all identity/pointer/origin/authority/target-set negative cases; deep-compare correction-off/on projection for both honest `0/100` and non-empty synthetic benchmark fixtures across the profile's complete unchanged-field list; and prove valid blocked/not-started readiness still exits zero while invalid/ambiguous authority exits four, with no source changes, current-program runtime under 5 seconds, and machine output at most 1 MiB in `tests/program_control_plane/test_cli.py`

### Implementation for User Story 1

- [x] T025 [US1] Implement normalized validation subject and complete authoritative-input manifest resolution in `scripts/program_control/git_subject.py`
- [x] T026 [US1] Implement schema/reference/raw/canonical digest and append-only transition/history semantic checks, including both independently approval-bound closed correction profiles, exact source-absence/container-introduction proof for TR-0027 `/inputs/3`, visible original-finding disposition, and zero readiness/authority effect, in `scripts/program_control/validation.py`
- [x] T027 [US1] Implement roadmap graph, decision/risk due status, approval freshness/scope, WIP/pointer, lease, and sole-next-action derivation in `scripts/program_control/validation.py`
- [x] T028 [US1] Implement stable finding/report entities including exact nullable pointer, resolution status and nullable correction reference; retain original findings after disposition; and implement deterministic aggregation/sorting and fail-closed precedence in `scripts/program_control/validation.py`
- [x] T029 [US1] Implement `validate` argument parsing including optional `--container`, explicit/constrained-inferred container resolution, optional explicit-only `--delivery` with no descendant search, validator-versus-readiness verdict separation, versioned JSON/text rendering, bounded exits, and top-level exception containment in `scripts/program_control/cli.py` and `scripts/validate-engineering-process-program.py`
- [x] T030 [US1] Document exact validate prerequisites, pass/fail/blocked semantics, evidence inspection, both bounded known-history correction diagnostics, compatibility, and recovery in `docs/programs/engineering-process-platform/README.md` and `scripts/README.md`
- [x] T031 [US1] Run the complete US1 fixture matrix plus current-control-plane validation, prove the TR-0027 correction resolves exactly `1/1` without source mutation and with deep equality of the complete benchmark/readiness/candidate/approval/release projection for both empty and non-empty fixtures, preserve immutable `EPP-F01-US1.json`, and append exact repair evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US1-repair.json`

**Checkpoint**: US1 is independently useful as a read-only validator and the suggested MVP stopping point.

---

## Phase 4: User Story 2 — See Four Truthful Readiness Areas (Priority: P2)

**Goal**: Generate one evidence-linked dashboard whose four readiness areas and release formula are independently derived for one exact candidate.

**Independent Test**: Each area independently passes, blocks, fails, and becomes stale; only that area changes. A 100-terminal-success benchmark fixture never compensates for another area or missing exact release approval.

### Tests for User Story 2

- [x] T032 [P] [US2] Add gate-catalog completeness, one-row-per-gate, denominator/numerator, status precedence, and evidence-link cases in `tests/program_control_plane/test_dashboard_projection.py`
- [x] T033 [P] [US2] Add the four-area independence matrix, honest empty state, catalog assertion-result completeness, all benchmark population/counter equations and deficits, isolated coverage/lifecycle/oracle/artifact/holdout/attempt/tier/freshness negatives including T2-without-T1 and T3-without-T1 rejection, and 100-success/hand-set-pass traps in `tests/program_control_plane/test_dashboard_projection.py`
- [x] T034 [P] [US2] Add source `S`/container `C`/candidate `R`, explicit/inferred container resolution, explicit-only `D` resolution, dashboard-only successor, added/deleted/imported/changed source modules, dirty/untracked/ignored helpers, runtime-HEAD-versus-S and loaded-module-path mismatch, bundle count/byte/import bounds, input-manifest digests, shared per-gate freshness, candidate-only dashboard bytes, independent-passed delivery envelopes, stale-source, and seed/non-evidence cases in `tests/program_control_plane/test_dashboard_provenance.py`
- [x] T035 [P] [US2] Add exact-subject release approval, cross-candidate rejection, and no-manual-green cases in `tests/program_control_plane/test_dashboard_projection.py`

### Implementation for User Story 2

- [x] T036 [US2] Implement gate catalog and complete same-ID assertion-result validation, closed evidence-class registry plus exact class/schema/role/source-manifest binding and required-class coverage, evaluator/evidence/independence/freshness checks, exact-candidate binding, and derived-only aggregate gate status in `scripts/program_control/dashboard.py`
- [x] T037 [US2] Implement independent area derivation and catalog-ordered gate rows with fixed non-passing precedence in `scripts/program_control/dashboard.py`
- [x] T038 [US2] Implement existing benchmark coverage, qualification lifecycle, process/oracle/output, artifact completeness, holdout chain/contamination, attempt-history, tier, freshness, summary-population, and deficit derivation plus the exact four-area-plus-human-approval release formula in `scripts/program_control/dashboard.py`
- [x] T039 [US2] Implement source/input-manifest provenance, closed entrypoint-plus-package source-bundle enumeration/import validation, loaded-module/runtime-HEAD-to-S blob binding with clean-path enforcement, explicit/constrained-inferred container resolution, explicit-only delivery resolution, and independent-passed descendant-delivery currentness validation in `scripts/program_control/dashboard.py`
- [x] T040 [US2] Update the durable dashboard contract and seed/current interpretation so dashboard bytes remain candidate-only while the external report envelope proves committed-current delivery in `docs/programs/engineering-process-platform/status-dashboard-contract.md` and `docs/programs/engineering-process-platform/dashboard.json`
- [x] T041 [US2] Run the complete US2 independence/provenance matrix and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US2.json`

**Checkpoint**: US2 generates a truthful candidate projection but does not grant release or integration authority.

---

## Phase 5: User Story 3 — Diagnose and Recover Safely (Priority: P3)

**Goal**: Deterministic bounded diagnostics and transactional dashboard generation preserve the last valid snapshot and prevent sensitive output.

**Independent Test**: Multi-fault fixtures report all safely discoverable findings in stable order; injected validation/write/flush/`fsync`/replace failures leave prior bytes unchanged and no residue; runtime-built sensitive canaries appear nowhere in output.

### Tests for User Story 3

- [x] T042 [P] [US3] Add multi-fault collection, stable ordering, exit precedence, bounded recovery, and unknown-exception containment cases in `tests/program_control_plane/test_cli.py`
- [x] T043 [P] [US3] Add runtime-built credential/token/prompt/log/payload/endpoint/authority/command and Windows/UNC/POSIX absolute-path canaries across JSON/text/stdout/stderr in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [x] T044 [P] [US3] Add successful atomic replacement plus candidate-validation, write, flush, `fsync`, reread, replace, and interruption failure injection in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [x] T045 [P] [US3] Add before/after source-identity and allowed-target-only mutation assertions for valid and invalid runs in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`

### Implementation for User Story 3

- [x] T046 [US3] Implement metadata allowlisting, bounded reason/recovery catalogs, relative-path rendering, and redacted internal failures in `scripts/program_control/cli.py`
- [x] T047 [US3] Implement same-directory UTF-8/LF temporary writing, flush, file-`fsync`, reread validation, atomic replace, and cleanup in `scripts/program_control/dashboard.py`
- [x] T048 [US3] Implement `generate-dashboard` candidate delivery envelopes plus `validate --delivery D` committed-current independent-passed envelopes and preserve-prior behavior without descendant search or stale-snapshot mutation in `scripts/program_control/cli.py`
- [x] T049 [US3] Run the complete US3 failure/redaction/immutability matrix and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US3.json`

**Checkpoint**: Failure behavior is inspectable and recovery is bounded without source mutation or leakage.

---

## Phase 6: User Story 4 — Reproduce the Result in an Empty Context (Priority: P4)

**Goal**: A fresh agent reproduces the verdict and follows exact evidence from committed documentation and output alone.

**Independent Test**: Two fixed-clock runs over one subject produce byte-identical machine output; Windows/POSIX semantic fixtures agree; a reviewer follows every sampled gate/finding reference and determines the same blocker/pass without conversation history.

### Tests for User Story 4

- [x] T050 [P] [US4] Add fixed-clock, shuffled discovery/insertion order, two-run byte identity, and declared observation-field exclusion cases in `tests/program_control_plane/test_determinism.py`
- [x] T051 [P] [US4] Add seed, both ordered byte-bound v1 profiles, future-v1 and second-migration rejection, explicitly supported prior contract, added/deleted/imported/changed non-entrypoint generator module, dirty/helper and runtime-source bundle boundary violations, unsupported major/minor, and removed-validator rollback cases in `tests/program_control_plane/test_atomicity_redaction_and_compatibility.py`
- [x] T052 [P] [US4] Add repository-relative evidence resolvability, direct README links to the active Spec Kit subject and exact approval manifest, and empty-context walkthrough assertions in `tests/program_control_plane/test_evidence_walkthrough.py`

### Implementation for User Story 4

- [x] T053 [US4] Finalize deterministic semantic JSON and concise human report rendering from one model in `scripts/program_control/cli.py`
- [x] T054 [US4] Replace planning-language quickstart with exact supported commands, outputs, compatibility table, manual fallback, and rollback journey in `specs/076-control-plane-validator/quickstart.md` and `docs/programs/engineering-process-platform/README.md`
- [x] T055 [US4] Add operator/developer troubleshooting, limitations, reason-code reference, and support-safe evidence inspection in `scripts/README.md` and `docs/programs/engineering-process-platform/status-dashboard-contract.md`
- [x] T056 [US4] Run the complete US4 determinism/compatibility/evidence-walkthrough suite and record exact evidence in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-US4.json`

**Checkpoint**: All four user stories are independently demonstrated locally; no integration or release claim follows.

---

## Phase 7: Cross-Cutting Gates, Rollback, and Verification Handoff

**Purpose**: Integrate the focused suite into Wright's local gates, prove rollback/compatibility, and freeze a candidate for a different verifier.

- [x] T057 [P] Route `docs/programs/engineering-process-platform/**`, `scripts/program_control/**`, the entrypoint, and `tests/program_control_plane/**` through focused tests in `scripts/check-dev-push.sh`
- [x] T058 [P] Add `scripts/program_control` and focused tests to Ruff, formatting, MyPy, and early full-gate tranches in `scripts/check-dev-merge.sh` and `.github/workflows/python-quality.yml`
- [x] T059 [P] Add Windows focused program-control execution without duplicating validator semantics in `.github/workflows/test-windows.yml`
- [x] T060 Add regression coverage proving docs/control-plane changes cannot bypass validator routing in `tests/release/test_dev_push_process.py`
- [x] T061 Reconcile user/operator/developer docs, schema index, compatibility/rollback instructions, gate impacts, and unsupported claims in `docs/programs/engineering-process-platform/schemas/README.md`, `docs/programs/engineering-process-platform/gates.md`, `docs/contributing/dev-push-runbook.md`, and `specs/076-control-plane-validator/quickstart.md`
- [x] T062 Run focused pytest, Ruff, formatting, MyPy, planning-contract schema validation, manual quickstart, source-mutation audit, and the applicable local pre-push gate; record exact commands, environment, skips, failures, and digests in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-author.json`
- [x] T063 Exercise removal/manual-validation rollback and previous-compatible snapshot reading, then record immutable source and prior-dashboard identities in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-rollback.json`
- [x] T064 Inspect the full candidate diff for scope, secrets/private payloads, generated/binary artifacts, dependency drift, benchmark/product execution, and unauthorized external/Git changes in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-diff-audit.json`
- [x] T065 Freeze the exact candidate commit/tree/artifact manifest, author identity, commands, acceptance envelope, remaining limitations, and rollback pointer in `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-candidate.json`
- [x] T070 Add failing exact-profile tests in `tests/program_control_plane/test_transition_chain.py` and `tests/program_control_plane/test_cli.py` for `COR-EPP-F01-REPAIR-EVIDENCE-001`: the positive `2/2` claim and `2/2` occurrence proof plus every omitted, added, substituted, reordered, relocated, wrong-identity, wrong-pointer, wrong-digest, wrong-origin, current-state, wildcard, future, new-record, correction-of-correction, missing-V7-authority, and projection-interference case
- [ ] T071 Implement recognition of only the exact repair-evidence correction in `scripts/program_control/validation.py`, `scripts/program_control/git_subject.py`, and `scripts/program_control/json_contracts.py`; retain immutable source findings, emit bounded diagnostics and recovery, require exact Git-object recomputation and V7 authority, and change no lifecycle, authority, readiness, benchmark, candidate, delivery, or release result
- [ ] T072 Run correction-off/on non-interference for honest `0/100` and non-empty synthetic benchmark inputs, focused validator tests, Ruff/format, full regression, source-mutation audit, and exact-subject verification; record the bounded result and freeze a replacement T066 candidate only if every check passes, otherwise stop under the existing repair limit
- [ ] T066 Stop author mutation and have a different independent-verifier identity rerun the critical deterministic, negative, platform, quickstart, evidence-link, rollback, and original-failure/skip review on unchanged candidate `R`; persist its candidate verdict in source commit `S` via `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-independent.json`
- [ ] T067 Have the coordinator validate source commit `S`, generate exact deterministic `candidate_not_evidence` dashboard bytes without code/source mutation, commit only `docs/programs/engineering-process-platform/dashboard.json` as successor `C`, and prove the first-parent, diff-allowlist, source-bundle, input-manifest, and byte-digest relation
- [ ] T068 Have the independent verifier inspect exact container `C`, dashboard bytes, schema/semantic and per-assertion/per-gate-freshness recomputation, and `S`/`C` relation; then persist a passing `kind=delivery` record in descendant `D` at `docs/programs/engineering-process-platform/evidence/verification/EPP-F01-dashboard-delivery.json`, prove the `C..D` delivery-only diff, and run `validate --source S --container C --delivery D` to show that only the external validation envelope—not dashboard bytes—reports `committed_valid`

**Stop**: Any author code/source change after T065 invalidates T066. A failed/blocked verifier returns to bounded repair with a stable cause. T067 is a declared generated-output delivery by the coordinator; any other change invalidates the verdict. T068 may add only delivery evidence about `C`; new readiness/source evidence makes the snapshot stale. Passing delivery permits only a request for separate dev-integration approval.

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
- Phase 7 depends on all stories. The failed first T066 attempt routes through approval-gated T070–T072; a T066 retry depends on a passing T072 replacement freeze and a distinct verifier. T067 depends on passing T066 and must be a dashboard-only successor; T068 depends on T067 and changes only delivery evidence.

### Within-Phase Dependencies

- Tests precede their corresponding implementation tasks and must fail for the intended missing behavior.
- T009–T016 depend on T006–T008; T017–T018 may proceed after their relevant schema expectations are fixed; T019 depends on all foundation work.
- T069 follows the already-complete T020–T023 tests and MUST complete before T024 or any remaining US1 implementation. T025–T029 depend on T020–T024 and T069; T030–T031 depend on the US1 implementation.
- T036–T040 depend on T032–T035; T041 depends on all US2 work.
- T046–T048 depend on T042–T045; T049 depends on all US3 work.
- T053–T055 depend on T050–T052 and prior stories; T056 depends on all US4 work.
- T060 depends on T057; T062 depends on T057–T061; T063–T064 depend on T062; T065 depends on T062–T064. T070 depends on the frozen two-claim profile and exact V7 approvals; T071 depends on failing T070 tests; T072 depends on T071. The T066 retry depends on passing T072; T067 depends on passing T066; T068 depends on T067.

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

- Total tasks: 72
- Setup/foundation: 19
- US1: 13
- US2: 10
- US3: 8
- US4: 7
- Cross-cutting/verification: 15
- Suggested MVP: Phases 1–3 (US1), followed by a deliberate validation checkpoint

## Notes

- These 72 tasks produce validator, provenance, machine `dashboard.json`, and CLI behavior only. They contain no browser route, frontend adapter, page, component, refresh, or browser-accessibility work; EPP-F01B owns that separate outcome.
- T069–T072 are intentionally numbered append-only while placed at their dependency-ordered execution points. Existing task identities and completed task records are not renumbered or reinterpreted.
- No task adds or upgrades a dependency, changes product runtime, creates/executes benchmark cases, contacts external systems, pushes, opens/merges a PR, integrates to `dev`, publishes, or releases.
- Task checkboxes are progress markers, not lifecycle or approval evidence.
- Optional Spec Kit auto-commit hooks remain disabled for this workflow because reviewed allowlist staging is required; no `git add .` may be used.
- Every evidence task records original failures/skips as well as terminal results; reruns cannot erase earlier evidence.
