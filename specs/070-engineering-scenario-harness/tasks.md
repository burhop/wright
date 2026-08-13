# Tasks: Rivet Engineering Scenario Harness

**Input**: Design documents from `specs/070-engineering-scenario-harness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. Tests are written before the corresponding implementation and include unit, contract, integration, API, component, journey, and optional clean-container evidence.

**Organization**: Tasks are grouped by independently testable user story. Loop 070 uses focused gates; the authoritative dev merge gate is deferred until all program loops finish on `codex/rivet-engineering-program`.

## Phase 1: Setup and public contracts

- [ ] T001 Copy the finalized manifest, artifact-envelope, and assertion-result schemas into package-owned public resources under `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/contracts/`.
- [ ] T002 [P] Add package resource inclusion and contract-discovery coverage in `packages/workspace_service/tests/test_engineering_scenario_contracts.py`.
- [ ] T003 [P] Add schema-valid and schema-invalid fixtures for versions, bounds, forbidden extra fields, artifact content/vault exclusivity, and non-pass assertion messages in `packages/workspace_service/tests/fixtures/engineering_scenarios/`.
- [ ] T004 Add focused schema contract tests that fail before implementation in `packages/workspace_service/tests/test_engineering_scenario_contracts.py`.
- [ ] T005 Validate all public JSON contracts and canonical examples with `jsonschema` using the repository's supported draft.

---

## Phase 2: Foundational domain model, units, catalog, and persistence

**Purpose**: Shared infrastructure required by every scenario story.

- [ ] T006 Write failing unit tests for scenario/catalog/artifact/assertion value validation, canonical digests, bounds, and redaction in `packages/core/tests/test_engineering_scenarios.py`.
- [ ] T007 [P] Write failing dimensional-unit tests for length/area/volume/mass/time/temperature/angle/force/pressure/velocity/power/energy/dimensionless conversion and incompatibility in `packages/core/tests/test_engineering_scenario_units.py`.
- [ ] T008 Implement versioned scenario, resource, environment, artifact, producer, assertion, report, and stable reason-code models in `packages/core/src/core/engineering_scenarios.py`.
- [ ] T009 Implement the bounded SI unit registry and explicit absolute-temperature/delta-temperature conversion rules in `packages/core/src/core/engineering_scenarios.py`.
- [ ] T010 Export the new public core values from `packages/core/src/core/__init__.py` and keep imports acyclic.
- [ ] T011 Write failing catalog loader tests for canonical digest, unique IDs, supported versions, resource confinement, Tier 1 environment rules, minimum MCP count, plugin references, artifact references, provenance, and forbidden connection material in `packages/workspace_service/tests/test_engineering_scenario_catalog.py`.
- [ ] T012 Implement package-owned catalog/resource loading and cross-field validation in `packages/workspace_service/src/workspace_service/engineering_scenario_catalog.py`.
- [ ] T013 Add catalog index and Wright-generated fixture provenance notice under `packages/workspace_service/src/workspace_service/engineering_scenario_catalog/`.
- [ ] T014 Write migration/repository tests for exact identity, terminal immutability, idempotent finalize, ordered assertions, restart read, and bounded JSON in `packages/data_vault/tests/test_engineering_scenario_repository.py`.
- [ ] T015 Add additive migration 15 for `engineering_scenario_runs` and `engineering_scenario_assertions` in `packages/data_vault/src/data_vault/migrations.py`.
- [ ] T016 Implement `EngineeringScenarioRepository` in `packages/data_vault/src/data_vault/engineering_scenario_repository.py` and export it from `packages/data_vault/src/data_vault/__init__.py`.
- [ ] T017 Add composition wiring for catalog/repository/service lifetime in `packages/workspace_service/src/workspace_service/composition.py` and `apps/api/src/api/composition.py` without widening other clients' authority.

**Checkpoint**: Public contracts, core values, unit policy, catalog validation, and durable report storage work independently.

---

## Phase 3: User Story 1 - Run curated multi-domain scenarios (Priority: P1) MVP

**Goal**: Three deterministic, multi-MCP scenarios produce engineering-valid outcomes through the Wright gateway.

**Independent Test**: Each scenario runs against two or more independent fake MCP processes, yields normalized artifacts and passing assertions, and cleans up without external dependencies.

### Tests first

- [ ] T018 [P] [US1] Write failing artifact-normalization tests for structured inline content, authorized vault references, digests, producers, lineage, units, coordinates, bounds, redaction, paths, URIs, and executable markup in `packages/workspace_service/tests/test_engineering_scenario_artifacts.py`.
- [ ] T019 [P] [US1] Write failing generic assertion tests for presence, exact, membership, range, relational, absolute/relative tolerance, finite values, unit conversion, and upstream correlation in `packages/workspace_service/tests/test_engineering_scenario_assertions.py`.
- [ ] T020 [P] [US1] Write failing domain assertion tests for mesh/geometry, ECAD board, FEA, CFD, data tree, 3MF/slicer, and static CAM rules in `packages/workspace_service/tests/test_engineering_scenario_assertions.py`.
- [ ] T021 [P] [US1] Write failing manifest tests for the structural bracket, electronics enclosure cooling, and parametric manufacturing resources in `packages/workspace_service/tests/test_engineering_scenario_examples.py`.
- [ ] T022 [US1] Create a deterministic multi-profile stdio MCP fixture server with initialize/list/call/progress/cancel/fault behavior in `packages/workspace_service/tests/fixtures/engineering_mcp_server.py`.
- [ ] T023 [US1] Write a failing gateway integration test proving namespace-qualified calls to at least two independent fixture MCP processes per scenario in `packages/workspace_service/tests/test_engineering_scenario_gateway.py`.
- [ ] T024 [US1] Write a failing end-to-end Rivet test for the three exact scenario graphs, reviews, bindings, child calls, artifacts, and cleanup in `tests/e2e/test_rivet_engineering_scenarios.py`.

### Implementation

- [ ] T025 [US1] Implement bounded artifact normalization and validation in `packages/workspace_service/src/workspace_service/engineering_scenario_artifacts.py`.
- [ ] T026 [US1] Implement the assertion registry, generic numeric/unit/correlation rules, and stable results in `packages/workspace_service/src/workspace_service/engineering_scenario_assertions.py`.
- [ ] T027 [US1] Implement geometry and mass-property assertion plugins using bounded structured summaries.
- [ ] T028 [US1] Implement ECAD board/enclosure assertion plugins using the documented KiCad-derived summary contract.
- [ ] T029 [US1] Implement FEA/CFD completion-versus-convergence, finite-result, bounds/residual, and input-correlation plugins.
- [ ] T030 [US1] Implement Grasshopper-style data-tree topology and typed-item assertion plugins.
- [ ] T031 [US1] Implement 3MF package/build/mesh/unit and bounded slicer-summary assertion plugins without invoking a slicer.
- [ ] T032 [US1] Implement declared-dialect static CAM/G-code lint that rejects physical actuation and unsafe/ambiguous modal state.
- [ ] T033 [P] [US1] Add Wright-generated structural CAD, mass-property, and FEA fixture records with deterministic digests and provenance.
- [ ] T034 [P] [US1] Add Wright-generated ECAD board, CAD enclosure, CFD thermal, and Python margin fixture records with deterministic digests and provenance.
- [ ] T035 [P] [US1] Add Wright-generated parametric data-tree, geometry, 3MF/slicer summary, and static CAM fixture records with deterministic digests and provenance.
- [ ] T036 [P] [US1] Add the structural bracket scenario manifest and static Rivet project under the package catalog.
- [ ] T037 [P] [US1] Add the electronics enclosure cooling scenario manifest and static Rivet project under the package catalog.
- [ ] T038 [P] [US1] Add the parametric manufacturing scenario manifest and static Rivet project under the package catalog.
- [ ] T039 [US1] Implement scenario preflight, reviewed-workflow start context, terminal artifact evaluation, and cleanup state in `packages/workspace_service/src/workspace_service/engineering_scenario_service.py`.
- [ ] T040 [US1] Link scenario report creation/finalization to existing workflow run/evidence identities without storing run authority or raw artifacts.

**Checkpoint**: All three Tier 1 scenarios are independently runnable and deterministic through the gateway.

---

## Phase 4: User Story 2 - Diagnose engineering failures precisely (Priority: P1)

**Goal**: Every injected failure identifies the exact node, capability, artifact, invariant, expected/observed value, units, category, and recovery.

**Independent Test**: Deterministic fault profiles cover missing capability, unit mismatch, invalid artifact, non-convergence, numerical bound, policy denial, unsafe CAM, cancellation, and residue.

- [ ] T041 [P] [US2] Write failing service tests for each stable preflight/policy/transport/tool/artifact/assertion/cancellation/cleanup failure category in `packages/workspace_service/tests/test_engineering_scenario_failures.py`.
- [ ] T042 [P] [US2] Write failing security tests for oversized, secret-like, script-bearing, traversal, unrestricted-URI, unknown-schema, NaN, and infinity child outputs.
- [ ] T043 [US2] Implement bounded diagnostic attribution and recovery projection in `engineering_scenario_service.py` and the assertion/artifact modules.
- [ ] T044 [US2] Ensure failed/blocked/cancelled reports finalize idempotently and late results cannot publish artifacts or pass assertions.
- [ ] T045 [US2] Add structured trace fields connecting scenario/run/node/capability/call/artifact/assertion while excluding secret and raw path values.

**Checkpoint**: Tool success and engineering validity are distinct, and failures are actionable.

---

## Phase 5: User Story 3 - Inspect and compare reproducible evidence (Priority: P2)

**Goal**: Reports survive restart, export safely, and compare every material identity.

**Independent Test**: Reload a passing and failing run, export both, and compare an intentional fixture/tolerance change.

- [ ] T046 [P] [US3] Write failing report/restart/export/compare tests in `packages/workspace_service/tests/test_engineering_scenario_reports.py`.
- [ ] T047 [US3] Implement report read/export and material identity comparison in `engineering_scenario_service.py`.
- [ ] T048 [US3] Add rebuild-on-restart only when all durable material identities match; otherwise report an explicit reproducibility difference.
- [ ] T049 [US3] Add API schema tests for bounded summaries, preflight, start, report, export, compare, and cancel in `apps/api/tests/test_engineering_scenario_api.py`.
- [ ] T050 [US3] Add typed request/response projections to `apps/api/src/api/schemas/workspace.py`.
- [ ] T051 [US3] Add thin authenticated routes from `contracts/engineering-scenario-api.md` to `apps/api/src/api/routers/workspace.py`.
- [ ] T052 [US3] Verify route/service errors map to stable HTTP status and reason codes without child configuration or secrets.

**Checkpoint**: Durable evidence is inspectable and portable without exposing authority or artifacts.

---

## Phase 6: User Story 4 - Extend the harness safely (Priority: P2)

**Goal**: A maintainer can add a manifest/fixture/assertion using public contracts without editing the runner.

**Independent Test**: Register a test-only assertion/scenario, validate/run it, and reject invalid, unsafe, or unlicensed variants.

- [ ] T053 [P] [US4] Write registry extension and invalid plugin/version tests in `packages/workspace_service/tests/test_engineering_scenario_extensions.py`.
- [ ] T054 [US4] Expose documented normalizer/assertion registry interfaces with duplicate/version conflict protection.
- [ ] T055 [US4] Add catalog-validation commands/tests that verify every packaged manifest, workflow node, artifact, assertion, fixture digest, and provenance record.
- [ ] T056 [US4] Document scenario authoring, fixture generation, plugin rules, tier classification, and review checklist in `docs/rivet/engineering-scenarios.md`.

**Checkpoint**: The scenario suite can grow without a bespoke execution path.

---

## Phase 7: User Story 5 - Selected clean-container integrations (Priority: P3)

**Goal**: Eligible real public MCPs can be probed explicitly without contaminating normal tests or the host.

**Independent Test**: One credential-free public MCP initializes/lists tools through a disposable container and records gateway/cleanup evidence; unavailable requirements classify as blocked.

- [ ] T057 [P] [US5] Write environment-guard tests for platform, network, credentials, proprietary app, GPU, hardware, large download, license prompt, catalog state, and host mutation.
- [ ] T058 [US5] Implement Tier 1/2/3 environment classification and fail-closed preflight in `engineering_scenario_service.py`.
- [ ] T059 [US5] Add a selected Tier 2 clean-container scenario adapter that references only confirmed eligible catalog IDs and records catalog/platform/package/discovery/gateway/cleanup digests.
- [ ] T060 [US5] Add explicit opt-in validation recipes for NVIDIA Elements and official Ansys PyFluent, preserving their current partial status until gateway proxy validation passes.
- [ ] T061 [US5] Record bounded pass/partial/blocked/fail evidence without checking downloaded source, build output, or `.local-run/` into Git.

**Checkpoint**: Real-package evidence is useful but never a normal gate dependency.

---

## Phase 8: Rivet UI and human journeys

- [ ] T062 Write failing service-client tests for scenario list/detail/preflight/start/report/export/compare/cancel in `apps/web/src/services/workspace-service.spec.ts`.
- [ ] T063 Add typed scenario client contracts and methods in `apps/web/src/services/workspace-service.ts`.
- [ ] T064 [P] Write failing component tests for domain/tier/resource/safety/readiness cards and blocked preflight in `RivetScenarioLibrary.spec.tsx`.
- [ ] T065 [P] Write failing component tests for node/capability/artifact/assertion/recovery/report states in `RivetScenarioReport.spec.tsx`.
- [ ] T066 Implement `RivetScenarioLibrary.tsx` using existing design tokens, focus behavior, text statuses, and stable test IDs.
- [ ] T067 Implement `RivetScenarioReport.tsx` with bounded values, units, provenance, cleanup/residue, export, and recovery.
- [ ] T068 Integrate scenarios into `RivetWorkflowsPanel.tsx` without changing ordinary workflow cards/history.
- [ ] T069 Add mocked Playwright journeys for pass, blocked, fail, cancel/residue, narrow width, keyboard, and 200% zoom in `tests/ui-integration/rivet-engineering-scenarios.spec.ts`.
- [ ] T070 Add automated accessibility assertions and verify no serious/critical findings.

---

## Phase 9: Polish, focused validation, and handoff

- [ ] T071 [P] Update `docs/engineering-capability-program-progress.md` with Loop 070 architecture, scenario coverage, focused evidence, and next Loop 071.
- [ ] T072 [P] Add performance tests for catalog listing, manifest validation, report loading, cancellation delivery, and cleanup deadlines.
- [ ] T073 Run affected Python lint/format/type/static checks and fix failures.
- [ ] T074 Run core, data-vault, workspace-service, API, runner, and package-resource focused tests for Loop 070.
- [ ] T075 Run affected web lint/type/Vitest and Loop 070 Playwright journeys.
- [ ] T076 Run schema validation, catalog validation, security/redaction tests, and `git diff --check`.
- [ ] T077 Perform Spec Kit cross-artifact analysis, remediate every critical/high finding, and rerun until clean.
- [ ] T078 Mark completed tasks and use the Spec Kit implementation commit hook for the Loop 070 evidence state.
- [ ] T079 Defer the authoritative `scripts/check-dev-merge.sh`, no-ff merge to `dev`, and push until Loop 073 program closeout; keep Loop 070 focused evidence reproducible on the integration branch.

## Dependencies and execution order

- Phase 1 precedes Phase 2; Phase 2 blocks all stories.
- US1 establishes scenario execution and artifacts; US2 hardens failure meaning; US3 adds durable API evidence; US4 formalizes extension; US5 is optional higher-tier evidence.
- UI begins after US3 API contracts are stable. Focused validation follows all desired stories.
- Tests marked in each story are written and observed failing before implementation.
- `[P]` tasks touch independent files/resources and may be parallelized by a future team, but this unattended goal executes them sequentially on one shared integration branch.

## Implementation strategy

Deliver the deterministic three-scenario MVP first. Add precise failure attribution and durable evidence next, then extension and UI. Keep Tier 2 isolated and optional. Do not run the expensive authoritative merge gate until Loops 070-073 are all complete; focused gates catch local regressions at each loop boundary.
