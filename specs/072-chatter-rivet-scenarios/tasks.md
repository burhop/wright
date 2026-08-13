# Tasks: Chatter and Model-Enabled Rivet Scenarios

**Input**: Design documents from `/specs/072-chatter-rivet-scenarios/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the specification. Contract and failure tests precede implementation within each story; generated fixtures remain the normal-gate proof and the real qualification test is explicit/ignored.

**Organization**: Tasks are grouped by user story so package trust, typed inference, Rivet composition, recovery, and extension/reproduction can be reviewed independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes independent files after declared prerequisites
- **[Story]**: Maps to the five user stories in spec.md
- Every task names its primary file or directory

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Fix the Loop 072 artifact baseline and reusable public contract resources.

- [x] T001 Validate all Loop 072 JSON Schemas with Draft 2020-12 and remove every placeholder from `specs/072-chatter-rivet-scenarios/`
- [x] T002 [P] Copy the reviewed Chatter candidate, result, serving metadata, and parity schemas into `packages/model_registry/src/model_registry/schemas/`
- [x] T003 [P] Add package-resource and spec-resource equality coverage for the four Chatter schemas in `packages/model_registry/tests/test_contract_resources.py`
- [x] T004 [P] Add ignored Chatter qualification/output patterns and payload suffixes to `.gitignore`
- [x] T005 Record the Loop 072 start, branch strategy, Gate D boundary, and deferred final dev merge gate in `docs/engineering-capability-program-progress.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish strict format contracts, provider evidence, generated fixtures, and duplicate-safe extension points used by every story.

**Critical**: No user-story implementation begins until the format/evidence foundation is fail-closed.

- [x] T006 Add immutable Chatter source, feature, preprocessing, classifier, decision, resource, candidate, result, and parity models in `packages/model_registry/src/model_registry/chatter_contracts.py`
- [x] T007 [P] Add valid/invalid Chatter contract fixtures in `packages/model_registry/tests/fixtures/chatter/`
- [x] T008 [P] Add schema and semantic contract tests for feature order, units, bounds, digests, thresholds, and evidence in `packages/model_registry/tests/test_chatter_contracts.py`
- [x] T009 Add provider-neutral MCP/model evidence models and canonical digest rules to `packages/core/src/core/rivet_mcp.py`
- [x] T010 [P] Add Run Manifest v2 provider-evidence contract tests and legacy v1 read tests in `packages/core/tests/test_rivet_mcp_contracts.py`
- [x] T011 Add `capability-binding-v2.schema.json` and `run-manifest-v2.schema.json` for the closed provider union while preserving the Loop 069 version-1 resources byte-for-byte in `packages/workspace_service/src/workspace_service/_rivet/contracts/`
- [x] T012 [P] Add provider-evidence schema/version/resource tests in `packages/workspace_service/tests/test_rivet_run_evidence.py`
- [x] T013 Extend gateway tool provenance with a validated provider-evidence projection in `packages/tool_registry/src/tool_registry/gateway_models.py`
- [x] T014 [P] Add MCP and engineering-model provider projection/collision tests in `packages/tool_registry/tests/test_gateway_service.py`
- [x] T015 Add duplicate-safe public Chatter format/runtime extension registrations in `packages/model_registry/src/model_registry/extensions.py`
- [x] T016 [P] Add Chatter extension duplicate/unsupported/version tests in `packages/model_registry/tests/test_extensions.py`
- [x] T017 Add deterministic tiny binary-forest metadata/NPZ/package/vector generators in `packages/model_registry/src/model_registry/generated.py`
- [x] T018 [P] Add generated forest determinism, digest, and no-repository-write tests in `packages/model_registry/tests/test_chatter_generated.py`
- [x] T019 Register generated Chatter fixture artifacts with existing test factories in `packages/model_registry/tests/fixture_factory.py`
- [x] T020 Run the foundational core/model/gateway contract tests and record any contract corrections in `specs/072-chatter-rivet-scenarios/plan.md`

**Checkpoint**: Chatter data and provider evidence have strict versioned contracts; generated fixtures can exercise them without a private payload.

---

## Phase 3: User Story 1 - Qualify the exact Chatter model for local use (Priority: P1) — MVP

**Goal**: Provide an inspectable private source record, safe numeric forest adapter, explicit trusted local conversion/export, non-redistributable offline import, and exact readiness evidence without unsafe deserialization.

**Independent Test**: Generate or locally qualify an exact package, inspect its identities/terms, import it, verify artifacts, pass mandatory vectors, and prove Joblib/pickle/source/changed evidence cannot become ready.

### Tests for User Story 1

- [x] T021 [P] [US1] Add source-record catalog tests for private/offline/non-installable state and blockers in `packages/model_registry/tests/test_catalog.py`
- [x] T022 [P] [US1] Add forest loader rejection tests for object arrays, extra members, dtype/shape/topology/index/finiteness/resource violations in `packages/model_registry/tests/test_chatter_security.py`
- [x] T023 [P] [US1] Add generated package inspect/import/verify/test/ready lifecycle tests in `packages/model_registry/tests/test_install_lifecycle.py`
- [x] T024 [P] [US1] Add non-redistributable export and reference-safe removal tests in `packages/model_registry/tests/test_offline_export.py`
- [x] T025 [P] [US1] Add qualification command identity/failure/cleanup tests with tiny local data in `tests/security/test_chatter_qualification.py`

### Implementation for User Story 1

- [x] T026 [US1] Implement bounded metadata and NPZ loading with `allow_pickle=False` in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T027 [US1] Implement forest topology, reachability, class-fraction, feature-index, and resource validation in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T028 [US1] Implement exact preprocessing and binary Random Forest evaluation primitives in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T029 [US1] Add `wright-chatter-forest-numpy` descriptor/session registration to `packages/model_registry/src/model_registry/runtime.py`
- [x] T030 [US1] Extend model policy allowlists for the exact Chatter format while preserving pickle/source/native-code rejection in `packages/model_registry/src/model_registry/policy.py`
- [x] T031 [US1] Add the private Chatter source candidate with immutable source/data/recipe facts and local-qualification blockers to `packages/model_registry/src/model_registry/catalog/catalog.yaml`
- [x] T032 [US1] Extend catalog views to present source/data/recipe/terms and local conversion recovery without a fabricated package digest in `packages/model_registry/src/model_registry/catalog.py`
- [x] T033 [US1] Add trusted qualification argument parsing, explicit acknowledgement, path confinement, clean-source/dataset/reference-evidence digest preflight, and no-network defaults in `scripts/qualification/qualify-chatter-model.py`
- [x] T034 [US1] Implement the exact feature-095 37-feature, grouped 80/20 seed-42, 96/24 zero-overlap Data Vault recipe and deterministic local retraining behind the explicit qualification boundary in `scripts/qualification/qualify-chatter-model.py`
- [x] T035 [US1] Implement preprocessing/class/tree extraction and numeric serving export in `scripts/qualification/qualify-chatter-model.py`
- [x] T036 [US1] Implement frozen-population and mandatory-boundary source-versus-serving parity evaluation in `scripts/qualification/qualify-chatter-model.py`
- [x] T037 [US1] Implement the acyclic metadata/forest/internal-use notice → parity evidence → final non-redistributable package manifest/vector/archive digest chain in `scripts/qualification/qualify-chatter-model.py`
- [x] T038 [US1] Ensure qualification uses a caller-owned output transaction and removes partial serving/archive state on failure in `scripts/qualification/qualify-chatter-model.py`
- [x] T039 [US1] Extend offline import semantic validation to require and bind Chatter parity evidence in `packages/model_registry/src/model_registry/offline_source.py`
- [x] T040 [US1] Persist package source/conversion/parity identities with installations and evidence in `packages/data_vault/src/data_vault/model_repository.py`
- [x] T041 [US1] Expose installed private-package source, terms, conversion, parity, runtime, resource, vector, and blocker facts in `packages/workspace_service/src/workspace_service/engineering_model_service.py`
- [x] T042 [US1] Keep export prohibited for private/offline or non-redistributable Chatter artifacts in `packages/workspace_service/src/workspace_service/engineering_model_service.py`
- [x] T043 [US1] Add thin API schema projections for the new trust/evidence facts in `apps/api/src/api/schemas/engineering_models.py`
- [x] T044 [US1] Add model-library UI sections for source/data/recipe/conversion/parity/internal terms and explicit qualification recovery in `apps/web/src/components/pages/EngineeringModelLibraryPage.tsx`
- [x] T045 [P] [US1] Add model-library component states for absent conversion, incompatible adapter, parity failure, and ready private package in `apps/web/tests/EngineeringModelLibraryPage.spec.tsx`
- [x] T046 [P] [US1] Add private package and conversion documentation in `docs/models/chatter-local-model.md`
- [x] T047 [US1] Add the explicit ignored real qualification test covering convert, import, verify, install, mandatory test, enable, typed inference, export prohibition, disable, uninstall, and reference-safe purge in `tests/external/test_chatter_local_qualification.py`; exercise Rivet scenario/report evidence with the generated package in T069/T090
- [x] T048 [US1] Run generated package lifecycle tests and, when exact local inputs are available, the real qualification probe defined in `tests/external/test_chatter_local_qualification.py` without tracking output (generated proof passed; private-input probe skipped transparently because reviewed inputs were unavailable)

**Checkpoint**: The source is visible but inert until an exact local package passes conversion parity and mandatory tests; unsafe artifacts and exports remain blocked.

---

## Phase 4: User Story 2 - Screen simulated cutting candidates truthfully (Priority: P1)

**Goal**: Evaluate 1-100 fully typed discrete candidates with exact scikit-learn-equivalent semantics and truthful applicability/calibration/evidence output.

**Independent Test**: Send stable, chatter, threshold, out-of-population, malformed, reordered, wrong-unit, duplicate, non-finite, oversized, and cancelled batches through an installed generated package and compare exact ordered results/evidence.

### Tests for User Story 2

- [x] T049 [P] [US2] Add candidate/result public schema equality and valid-instance tests in `packages/model_registry/tests/test_contract_schemas.py`
- [x] T050 [P] [US2] Add stable/chatter/threshold and exact forest-equation tests in `packages/model_registry/tests/test_chatter_runtime.py`
- [x] T051 [P] [US2] Add order/unit/origin/duplicate/non-finite/range/batch/output-limit failure tests in `packages/model_registry/tests/test_chatter_runtime.py`
- [x] T052 [P] [US2] Add generated source-evaluator parity and repeatability tests in `packages/model_registry/tests/test_chatter_generated.py`
- [x] T053 [P] [US2] Add gateway typed inference/evidence/result-bound tests in `packages/model_registry/tests/test_gateway_provider.py`

### Implementation for User Story 2

- [x] T054 [US2] Implement exact feature-order, unit, origin, finite, contract-range, uniqueness, and request-byte validation in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T055 [US2] Implement population applicability and near-threshold classification rules in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T056 [US2] Implement ordered batch scoring, threshold equality, signed margin, warnings, limitations, and eligibility output in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T057 [US2] Bind package/variant/artifact/installation/adapter/runtime/test/task/schema/threshold evidence into runtime output in `packages/model_registry/src/model_registry/chatter_runtime.py`
- [x] T058 [US2] Add progress, deadline, output-byte, cancellation, unload, and shutdown handling for Chatter sessions in `packages/model_registry/src/model_registry/runtime.py`
- [x] T059 [US2] Extend standard-vector predicates for ordered batch outcomes, applicability, warnings, and tolerances in `packages/model_registry/src/model_registry/testing.py`
- [x] T060 [US2] Project full engineering-model provider evidence from enabled Chatter bindings in `packages/model_registry/src/model_registry/gateway_provider.py`
- [x] T061 [US2] Preserve provider-authored structured result and exact output evidence through `packages/tool_registry/src/tool_registry/gateway_service.py`
- [x] T062 [US2] Record bounded input/output/material digests without feature values in `packages/workspace_service/src/workspace_service/engineering_model_service.py`
- [x] T063 [US2] Add candidate inference contract examples and truthful score terminology to `docs/models/chatter-local-model.md`
- [x] T064 [US2] Run focused runtime/vector/gateway tests and the 1/100-candidate cold performance probe in `packages/model_registry/tests/test_performance.py`

**Checkpoint**: An installed package provides deterministic typed screening without calibration claims, hidden defaults, continuous interpolation, or machine recommendations.

---

## Phase 5: User Story 3 - Run a reviewed chatter-aware CNC workflow in Rivet (Priority: P1)

**Goal**: Compose two independent deterministic fixture MCPs and one exact engineering-model capability in the real Rivet/gateway path and emit a bounded advisory report.

**Independent Test**: Preflight and execute the packaged Tier-1 graph through the real worker/gateway using generated fixtures, correlate three or more candidates/model calls/artifacts, pass invariants, and prove the report contains no executable machine authority.

### Tests for User Story 3

- [x] T065 [P] [US3] Add scenario 1.1 schema/provider-kind/domain/cross-field tests plus byte-stable 1.0 compatibility coverage in `packages/workspace_service/tests/test_engineering_scenario_contracts.py`
- [x] T066 [P] [US3] Add CAD context and simulated CAM candidate artifact normalizer tests in `packages/workspace_service/tests/test_engineering_scenario_artifacts.py`
- [x] T067 [P] [US3] Add chatter advisory assertion and selection-ineligibility tests in `packages/workspace_service/tests/test_engineering_scenario_assertions.py`
- [x] T068 [P] [US3] Add model-capability preflight/staleness/resource tests in `packages/workspace_service/tests/test_engineering_scenario_service.py`
- [x] T069 [P] [US3] Add real Rivet worker plus gateway plus two MCP/model provider system test in `tests/e2e/test_rivet_engineering_models.py`; keep packaged fixture/assertion coverage in `tests/e2e/test_chatter_model_scenario.py`

### Implementation for User Story 3

- [x] T070 [US3] Add `scenario-manifest-1.1.schema.json` with `model` domain, provider kind, model resources, advisory artifacts, and machine-instruction prohibition while preserving the 1.0 schema in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/contracts/`
- [x] T071 [US3] Select the exact 1.0/1.1 schema by declared version and add provider-kind, model-resource, candidate-producer/consumer, and Gate-E cross-field validation in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog_service.py`
- [x] T072 [US3] Add CAD context, candidate batch, model result, and advisory artifact normalizers in `packages/workspace_service/src/workspace_service/engineering_scenario_artifacts.py`
- [x] T073 [US3] Add duplicate-safe `chatter_advisory` assertion plugin for correlation, applicability, invariants, selection, provenance, and forbidden content in `packages/workspace_service/src/workspace_service/engineering_scenario_assertions.py`
- [x] T074 [US3] Add deterministic CAD and simulated CAM fixture MCP tools to `packages/workspace_service/tests/fixtures/rivet_mcp_servers.py`
- [x] T075 [US3] Add the `chatter-candidate-review` manifest in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/scenarios/chatter-candidate-review.yaml`
- [x] T076 [US3] Add the static gateway-only Rivet graph in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/workflows/chatter-candidate-review.rivet-project`
- [x] T077 [US3] Add generated CAD/CAM/model/advisory fixture envelopes in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/fixtures/chatter-candidate-review.json`
- [x] T078 [US3] Register the scenario in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/catalog.yaml`
- [x] T079 [US3] Make scenario preflight provider-neutral and validate model installation/adapter/vector/schema/threshold/resource evidence in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`
- [x] T080 [US3] Preserve exact provider evidence while reviewing static tool selections in `packages/workspace_service/src/workspace_service/rivet_capabilities.py`
- [x] T081 [US3] Write Run Manifest v2 provider evidence for MCP and model bindings in `packages/workspace_service/src/workspace_service/workflow_runner.py`
- [x] T082 [US3] Correlate candidate producer receipt, model call/result, invariant outcomes, and authorized artifacts in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`
- [x] T083 [US3] Build the advisory report with selected-for-review/rejection reasons and fixed safety notices in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`
- [x] T084 [US3] Add provider evidence and advisory fields to scenario API schemas in `apps/api/src/api/schemas/workspace.py`
- [x] T085 [US3] Extend workspace-service TypeScript contracts for provider preflight and advisory reports in `apps/web/src/services/workspace-service.ts`
- [x] T086 [US3] Show MCP/model composition, resource readiness, simulation status, and exact review blockers in `apps/web/src/components/chat/RivetScenarioLibrary.tsx`
- [x] T087 [US3] Show candidate outcomes, uncalibrated scores, threshold margins, applicability, invariants, selected-for-review, provider evidence, and no-machine-authority notices in `apps/web/src/components/chat/RivetScenarioReport.tsx`
- [x] T088 [P] [US3] Add scenario library/report component tests for all Chatter advisory states in `apps/web/src/components/chat/RivetScenarioLibrary.spec.tsx` and `apps/web/src/components/chat/RivetScenarioReport.spec.tsx`
- [x] T089 [P] [US3] Add mocked keyboard/narrow/zoom/accessibility journey in `tests/ui-integration/chatter-rivet-scenario.spec.ts`
- [x] T090 [US3] Run the generated end-to-end scenario in `tests/e2e/test_rivet_engineering_models.py` through the verified real Rivet worker and record deterministic evidence in `docs/rivet/model-enabled-scenarios.md`

**Checkpoint**: Rivet composes independent MCP and local model capabilities through Wright and emits only a human-review advisory report.

---

## Phase 6: User Story 4 - Diagnose cancellation, resources, and drift (Priority: P1)

**Goal**: Fail early and truthfully for resource, readiness, drift, runtime, cancellation, restart, and cleanup problems with stable provider attribution and no late success.

**Independent Test**: Exercise every enumerated failure and cancellation race, restart durable state, and verify exact attribution/recovery plus clean or explicit residue.

### Tests for User Story 4

- [x] T091 [P] [US4] Add insufficient RAM/disk, reservation conflict, load timeout, inference timeout, crash, and output-limit tests in `packages/model_registry/tests/test_runtime_supervisor.py`
- [x] T092 [P] [US4] Add package/adapter/vector/schema/threshold/policy drift tests in `packages/workspace_service/tests/test_rivet_capabilities.py`
- [x] T093 [P] [US4] Add cancellation-before-load/during-inference/late-output/cleanup-residue tests in `packages/workspace_service/tests/test_rivet_mcp_cancellation.py`
- [x] T094 [P] [US4] Add scenario restart and no-false-success tests in `packages/workspace_service/tests/test_engineering_scenario_failures.py`
- [x] T095 [P] [US4] Add bounded diagnostics/redaction tests for model/provider failures in `packages/workspace_service/tests/test_rivet_run_evidence.py`

### Implementation for User Story 4

- [x] T096 [US4] Add stable Chatter contract, artifact, runtime, applicability, resource, cancellation, and cleanup failure categories in `packages/model_registry/src/model_registry/chatter_contracts.py`
- [x] T097 [US4] Enforce atomic model resource reservations and release across verify/load/infer/unload/cancel in `packages/model_registry/src/model_registry/runtime.py`
- [x] T098 [US4] Include provider evidence in binding staleness reasons and recovery actions in `packages/workspace_service/src/workspace_service/rivet_capabilities.py`
- [x] T099 [US4] Revoke run authority before parallel provider cancellation and suppress late output in `packages/workspace_service/src/workspace_service/workflow_runner.py`
- [x] T100 [US4] Record provider cancellation acknowledgement, cleanup, possible residue, and recovery in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T101 [US4] Project required/available resources and provider-specific recovery in scenario preflight/report in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`
- [x] T102 [US4] Reconcile interrupted Chatter model/scenario states without reusable authority or false success in `packages/data_vault/src/data_vault/model_repository.py` and `packages/data_vault/src/data_vault/engineering_scenario_repository.py`
- [x] T103 [US4] Add accessible cancelling/cancelled/residue/stale/resource/crash recovery states in `apps/web/src/components/chat/RivetScenarioReport.tsx`
- [x] T104 [P] [US4] Add component tests for focus, non-color state, retry guidance, and late-success suppression in `apps/web/src/components/chat/RivetScenarioReport.spec.tsx`
- [x] T105 [US4] Run deterministic cancellation/performance/restart tests and document any bounded residue behavior in `docs/rivet/model-enabled-scenarios.md`

**Checkpoint**: Every model-enabled run ends in one truthful durable state with bounded recovery and no hidden resource ownership.

---

## Phase 7: User Story 5 - Reproduce and extend model-enabled scenarios safely (Priority: P2)

**Goal**: Compare exact material evidence and prove another generated model-enabled scenario can use public contracts without generic runner/gateway/UI model branches.

**Independent Test**: Repeat an unchanged run, change each material identity, and register a second generated model scenario plus invalid/colliding extensions while asserting generic components contain no Chatter identity branches.

### Tests for User Story 5

- [x] T106 [P] [US5] Add material-versus-observation reproduction comparison tests in `packages/workspace_service/tests/test_engineering_scenario_reports.py`
- [x] T107 [P] [US5] Add provider-kind/evidence comparison and legacy v1 behavior tests in `packages/workspace_service/tests/test_rivet_run_evidence.py`
- [x] T108 [P] [US5] Add second generated model-enabled scenario registration and collision tests in `packages/workspace_service/tests/test_engineering_scenario_extensions.py`
- [x] T109 [P] [US5] Add static no-Chatter-branch/no-dynamic-binding tests for generic runner/gateway/scenario/UI files in `tests/compatibility/test_chatter_compatibility.py`

### Implementation for User Story 5

- [x] T110 [US5] Extend run/scenario comparison to include all provider/package/vector/fixture/input/result/policy material identities in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T111 [US5] Keep timing, observed resources, request/trace IDs, timestamps, and host diagnostics in a separate observation projection in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T112 [US5] Expose exact material differences and fresh-review recovery through scenario comparison in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`
- [x] T113 [US5] Add a generated affine model scenario extension fixture using the same provider-neutral contracts in `packages/workspace_service/tests/fixtures/engineering_scenarios/model-enabled-affine.yaml`
- [x] T114 [US5] Document the provider-neutral model scenario extension procedure in `docs/rivet/model-enabled-scenarios.md`
- [x] T115 [US5] Run unchanged/changed comparison and second-model extension tests, then inspect generic files with `tests/compatibility/test_chatter_compatibility.py` for model-ID branches

**Checkpoint**: Reproduction claims are exact and the model-enabled seam is demonstrably reusable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Close requirements review, packaging/security/accessibility evidence, documentation, and the Loop 072 commit without performing the final program merge.

- [x] T116 Mark every satisfied item and record/remediate findings in `specs/072-chatter-rivet-scenarios/checklists/chatter-trust-and-security.md`
- [x] T117 Mark every satisfied item and record/remediate findings in `specs/072-chatter-rivet-scenarios/checklists/scenario-engineering.md`
- [x] T118 Mark every satisfied item and record/remediate findings in `specs/072-chatter-rivet-scenarios/checklists/usability-and-recovery.md`
- [x] T119 [P] Add wheel/sdist/native/Docker/Git scans for private data, Joblib/pickle, NPZ, offline archives, and payload signatures in `tests/packaging/test_chatter_distribution.py`
- [x] T120 [P] Add schema/unit/command/endpoint/credential/path/authority/model-byte security cases in `tests/security/test_chatter_boundaries.py`
- [x] T121 [P] Add cross-platform runtime compatibility and incompatible-host cases in `tests/compatibility/test_chatter_compatibility.py`
- [x] T122 [P] Add packaged model-enabled scenario coverage in `tests/e2e/test_chatter_model_scenario.py` and real worker/gateway system coverage in `tests/e2e/test_rivet_engineering_models.py`
- [x] T123 Complete keyboard, 320 CSS pixel, 200% zoom, focus, non-color, and axe checks in `tests/ui-integration/chatter-rivet-scenario.spec.ts`
- [x] T124 Validate every command and safety assertion in `specs/072-chatter-rivet-scenarios/quickstart.md`
- [x] T125 Run Ruff, formatting, Prettier, focused Python/web tests, real Chromium UI tests, schema/docs/security/compatibility/packaging gates, `git diff --check`, and payload scans
- [x] T126 Run `/speckit-analyze`, remediate every critical/high finding, and rerun until clean against `specs/072-chatter-rivet-scenarios/`
- [x] T127 Update Loop 072 completion, test evidence, real-probe status, rollback, payload hygiene, and deferred final dev gate in `docs/engineering-capability-program-progress.md`
- [x] T128 Mark Loop 072 spec status complete and every completed task in `specs/072-chatter-rivet-scenarios/spec.md` and `specs/072-chatter-rivet-scenarios/tasks.md`
- [x] T129 Verify `.local-run/` and any private dataset, source checkout, qualification environment, Joblib/pickle, serving NPZ, or offline model archive remain ignored/untracked and no Loop 072 private payload is present in the public worktree
- [x] T130 Commit the complete Loop 072 Spec Kit artifacts and implementation on `codex/rivet-engineering-program` without pushing or merging

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks every story.
- **US1 (Phase 3)**: Depends on the strict contracts, generated forest, runtime registration, and provider evidence foundation.
- **US2 (Phase 4)**: Depends on US1's loader/evaluator and generated installable package; it is independently testable through the model capability.
- **US3 (Phase 5)**: Depends on US2 typed inference and foundational provider evidence; CAD/CAM resources/tests can be prepared in parallel.
- **US4 (Phase 6)**: Depends on the executable model/scenario path so all failures are attributable at real boundaries.
- **US5 (Phase 7)**: Depends on provider evidence and complete scenario reports; comparison tests may begin once those contracts exist.
- **Polish (Phase 8)**: Depends on all selected stories. The final `scripts/check-dev-merge.sh`, push, and merge remain deliberately deferred through Loop 073.

### User Story Dependencies

```text
Foundation
  -> US1 Exact local package
      -> US2 Typed screening
          -> US3 Rivet CAD/CAM/model scenario
              -> US4 Resource/cancellation/drift recovery
              -> US5 Reproduction and generic extension
                  -> Loop 072 closeout commit
```

### Parallel Opportunities

- Schema-resource, payload-ignore, documentation, and independent contract-test tasks marked `[P]` can proceed after their phase prerequisite.
- US1 catalog/UI/docs tests can run alongside runtime/qualification work after contracts are stable.
- US3 scenario resources, artifact/assertion tests, API types, and UI mocks can be authored independently after the 1.1 contract lands.
- US4 runtime, binding-drift, cancellation, restart, and UI failure tests touch independent files.
- US5 comparison, extension, and static architecture tests are independent until their final integration run.

## Parallel Examples

### User Story 1

```text
T021 catalog source-record tests
T022 forest security tests
T023 lifecycle tests
T024 export/removal tests
T025 qualification boundary tests
```

### User Story 3

```text
T065 manifest contracts
T066 artifact normalizers
T067 advisory assertions
T068 preflight
T069 real worker/gateway system path
```

### User Story 4

```text
T091 runtime resources
T092 identity drift
T093 cancellation races
T094 restart/no-false-success
T095 bounded diagnostics
```

## Implementation Strategy

### MVP first

1. Complete Setup and Foundational contracts.
2. Complete US1 using the generated package first.
3. Validate the explicit local qualification path separately; never weaken trust rules if private inputs are unavailable.
4. Complete US2 typed inference before adding scenario composition.

### Incremental delivery

1. Source record + safe adapter + offline package lifecycle.
2. Typed batch screening with truthful result semantics.
3. CAD/CAM/model scenario through the real Wright/Rivet path.
4. Full failure, cancellation, restart, and drift recovery.
5. Reproduction comparison and second generated model extension.
6. Cross-cutting security, accessibility, packaging, analysis, and one coherent Loop 072 commit.

## Notes

- Tests are written before the implementation they constrain.
- `[P]` means file-level independence, not permission to bypass phase prerequisites.
- The private real-model probe may be skipped only when exact local inputs are unavailable; generated proof must never be relabelled as real qualification.
- No task authorizes AWS/cloud/paid use, proprietary application launch, model payload commit, push/merge, `main`, release publication, machine instructions, or physical actuation.
