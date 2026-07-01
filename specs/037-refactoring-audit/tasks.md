# Tasks: Architecture Refactoring Audit Implementation

**Input**: Design documents from `/specs/037-refactoring-audit/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are required for every touched contract because this is a production-near architecture refactor.

**Organization**: Tasks are grouped by user story to enable independent implementation and review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish implementation guardrails and reusable fixtures before touching runtime behavior

- [ ] T001 Add a phase checklist to `specs/037-refactoring-audit/risk-review.md`
- [ ] T002 [P] Add API import-boundary test helper notes to `apps/api/tests/conftest.py`
- [ ] T003 [P] Add smoke-test fixture plan comments to `tests/e2e/README.md`
- [ ] T004 [P] Document opt-in clean-container validation command shape in `docs/mcp-catalog/mcp-server-testing-process.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared error/result patterns that later service and registry work can use

**CRITICAL**: No user story implementation should proceed without these compatibility guardrails.

- [x] T005 [P] Add unsupported-runtime domain error tests in `packages/agent_adapters/tests/test_agent_registry.py`
- [ ] T006 [P] Add MCP service result/error mapping tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T007 [P] Add shared catalog fixture entries in `packages/tool_registry/tests/fixtures/catalog_normalization.yaml`
- [ ] T008 [P] Add validation evidence fixture data in `packages/tool_registry/tests/fixtures/validation_evidence.json`

**Checkpoint**: Foundational fixtures and expected error surfaces are ready for implementation.

---

## Phase 3: User Story 1 - Select Agent Runtimes Without Hermes Coupling (Priority: P1) MVP

**Goal**: Add an agent-neutral runtime registry/factory and stop API boot from importing Hermes directly while preserving Hermes as default.

**Independent Test**: Default startup selects Hermes through the registry, explicit Hermes works, invalid agents are rejected, and health response fields remain unchanged.

### Tests for User Story 1

- [x] T009 [P] [US1] Add registry default and explicit Hermes tests in `packages/agent_adapters/tests/test_agent_registry.py`
- [x] T010 [P] [US1] Add invalid runtime selection tests in `packages/agent_adapters/tests/test_agent_registry.py`
- [x] T011 [P] [US1] Add API boot import-boundary test in `apps/api/tests/test_agent_runtime_boot.py`
- [x] T012 [P] [US1] Add active agent selection API tests in `apps/api/tests/test_agent_health.py`
- [x] T013 [P] [US1] Update setup API invalid-agent tests in `apps/api/tests/test_setup_api.py`

### Implementation for User Story 1

- [x] T014 [US1] Implement provider metadata and runtime errors in `packages/agent_adapters/src/agent_adapters/registry.py`
- [x] T015 [US1] Implement Hermes provider factory using existing Hermes config resolution in `packages/agent_adapters/src/agent_adapters/registry.py`
- [x] T016 [US1] Export registry types and factory helpers from `packages/agent_adapters/src/agent_adapters/__init__.py`
- [x] T017 [US1] Remove direct `HermesAdapter` boot wiring from `apps/api/src/api/main.py`
- [x] T018 [US1] Move Hermes API settings compatibility behind registry-backed helpers in `apps/api/src/api/config.py`
- [x] T019 [US1] Use registry validation for active agent GET/POST behavior in `apps/api/src/api/routers/agent.py`
- [x] T020 [US1] Replace hardcoded supported-agent list with registry metadata in `apps/api/src/api/routers/setup.py`
- [ ] T021 [US1] Update API test fixtures to inject registry-created or fake engines in `apps/api/tests/conftest.py`
- [x] T022 [US1] Run targeted US1 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: Hermes still works as default, API boot is agent-neutral, and no public health response shape changed.

---

## Phase 4: User Story 2 - Share A Wright Gateway Contract Across Agents (Priority: P2)

**Goal**: Define Wright gateway contracts and keep Hermes compatibility while preparing an OpenClaw seam without implementing a full OpenClaw engine.

**Independent Test**: Fake and Hermes gateway profiles exercise the same contract, and future-runtime stubs do not require Hermes paths.

### Tests for User Story 2

- [X] T023 [P] [US2] Add gateway profile contract tests in `packages/agent_adapters/tests/test_wright_gateway_contracts.py`
- [X] T024 [P] [US2] Add Hermes gateway profile compatibility tests in `packages/agent_adapters/tests/test_hermes_gateway_profile.py`
- [X] T025 [P] [US2] Add OpenClaw stub gateway tests in `packages/agent_adapters/tests/test_openclaw_gateway_stub.py`
- [X] T026 [P] [US2] Update Hermes sync API compatibility tests in `apps/api/tests/test_hermes_sync.py`

### Implementation for User Story 2

- [X] T027 [US2] Implement Wright gateway profile contracts in `packages/agent_adapters/src/agent_adapters/gateway.py`
- [X] T028 [US2] Implement Hermes Wright gateway profile adapter in `packages/agent_adapters/src/agent_adapters/hermes_gateway.py`
- [X] T029 [US2] Add OpenClaw gateway stub metadata without an engine factory in `packages/agent_adapters/src/agent_adapters/openclaw.py`
- [X] T030 [US2] Export gateway contracts from `packages/agent_adapters/src/agent_adapters/__init__.py`
- [X] T031 [US2] Create generic gateway sync service wrapper in `apps/api/src/api/services/wright_gateway_sync.py`
- [X] T032 [US2] Preserve `api.services.hermes_sync` compatibility wrappers in `apps/api/src/api/services/hermes_sync.py`
- [X] T033 [US2] Keep workspace context writing compatible while isolating Hermes-specific filenames in `packages/core/src/core/workspace.py`
- [X] T034 [US2] Update gateway route tests for generic Wright gateway terminology in `apps/api/tests/test_gateway_api.py`
- [X] T035 [US2] Run targeted US2 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: Wright gateway is agent-neutral in contracts, Hermes remains compatible, and OpenClaw has only a non-production seam.

---

## Phase 5: User Story 3 - Keep MCP API Routes Thin (Priority: P3)

**Goal**: Extract MCP route business logic into service-layer code while preserving route response shapes.

**Independent Test**: Existing MCP API tests continue to pass and direct service tests cover moved business behavior.

### Tests for User Story 3

- [ ] T036 [P] [US3] Add MCP list/register service tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T037 [P] [US3] Add MCP install/uninstall/activation service tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T038 [P] [US3] Add MCP credential service tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T039 [P] [US3] Add MCP validation/follow-up service tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T040 [P] [US3] Add MCP version check/update service tests in `packages/tool_registry/tests/test_mcp_services.py`
- [ ] T041 [P] [US3] Add route response compatibility assertions in `apps/api/tests/test_mcp_api.py`

### Implementation for User Story 3

- [ ] T042 [US3] Implement MCP catalog/list/register service operations in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T043 [US3] Implement MCP install/uninstall/activation service operations in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T044 [US3] Implement MCP credential service operations in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T045 [US3] Implement MCP validation/follow-up service operations in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T046 [US3] Implement MCP version check/update service operations in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T047 [US3] Add API-side service dependency wiring in `apps/api/src/api/services/mcp_services.py`
- [ ] T048 [US3] Refactor MCP route handlers to delegate to services in `apps/api/src/api/routers/mcp.py`
- [ ] T049 [US3] Keep route response model names unchanged in `apps/api/src/api/routers/mcp.py`
- [ ] T050 [US3] Run targeted US3 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: MCP routes are thin for moved operation groups, service tests cover business logic, and API contracts are unchanged.

---

## Phase 6: User Story 4 - Normalize MCP Catalog Boundaries (Priority: P4)

**Goal**: Start unifying catalog source-of-truth boundaries in `tool_registry` while keeping `hermes-plugin-wright` first-class.

**Independent Test**: Shared normalization preserves representative metadata and Hermes plugin catalog behavior remains compatible.

### Tests for User Story 4

- [ ] T051 [P] [US4] Add shared catalog normalization tests in `packages/tool_registry/tests/test_catalog_normalization.py`
- [ ] T052 [P] [US4] Add API seed normalization parity tests in `apps/api/tests/test_mcp_catalog_seed.py`
- [ ] T053 [P] [US4] Add Hermes plugin parity tests in `hermes-plugin-wright/tests/test_catalog.py`
- [ ] T054 [P] [US4] Add duplicate/invalid catalog normalization tests in `packages/tool_registry/tests/test_catalog_normalization.py`

### Implementation for User Story 4

- [ ] T055 [US4] Implement shared catalog schema models in `packages/tool_registry/src/tool_registry/catalog_models.py`
- [ ] T056 [US4] Implement catalog normalization loader in `packages/tool_registry/src/tool_registry/catalog_loader.py`
- [ ] T057 [US4] Reuse shared installability sorting/default platform support in `packages/tool_registry/src/tool_registry/mcp_catalog.py`
- [ ] T058 [US4] Add API seed conversion helper in `apps/api/src/api/database/migrate.py`
- [ ] T059 [US4] Add Hermes plugin shared-model adapter without deleting plugin APIs in `hermes-plugin-wright/catalog.py`
- [ ] T060 [US4] Add shared dependency to Hermes plugin package metadata in `hermes-plugin-wright/pyproject.toml`
- [ ] T061 [US4] Run targeted US4 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: Shared normalization exists and parity is proven for representative entries without deleting or demoting the Hermes plugin.

---

## Phase 7: User Story 5 - Plan Clean-Container MCP Validation Evidence (Priority: P5)

**Goal**: Add the first validation harness seam with validation plans/evidence while keeping metadata classification as preflight and Docker/network opt-in.

**Independent Test**: Fast tests generate plans and run lightweight mock MCP probes without Docker or network.

### Tests for User Story 5

- [ ] T062 [P] [US5] Add validation plan generation tests in `packages/tool_registry/tests/test_mcp_validation_plan.py`
- [ ] T063 [P] [US5] Add validation evidence serialization/redaction tests in `packages/tool_registry/tests/test_mcp_validation_evidence.py`
- [ ] T064 [P] [US5] Add lightweight mock MCP probe tests in `packages/tool_registry/tests/test_mcp_validation_runner.py`
- [ ] T065 [P] [US5] Add API validation compatibility tests in `apps/api/tests/test_mcp_api.py`

### Implementation for User Story 5

- [ ] T066 [US5] Implement `ValidationPlan` and probe step models in `packages/tool_registry/src/tool_registry/validation_plan.py`
- [ ] T067 [US5] Implement `ValidationEvidence` and redaction helpers in `packages/tool_registry/src/tool_registry/validation_evidence.py`
- [ ] T068 [US5] Implement lightweight local validation runner seam in `packages/tool_registry/src/tool_registry/validation_runner.py`
- [ ] T069 [US5] Preserve metadata classification as preflight in `packages/tool_registry/src/tool_registry/mcp_validation.py`
- [ ] T070 [US5] Wire validation plan/evidence through MCP validation service in `packages/tool_registry/src/tool_registry/services.py`
- [ ] T071 [US5] Document Docker/network validation opt-in details in `docs/mcp-catalog/mcp-server-testing-process.md`
- [ ] T072 [US5] Run targeted US5 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: Fast validation tests are offline-safe, and clean-container execution is a documented opt-in seam.

---

## Phase 8: User Story 6 - Add Constitution-Required System Smoke Coverage (Priority: P6)

**Goal**: Add minimal E2E/system smoke coverage for API health, default agent behavior, MCP listing, and Wright gateway happy path.

**Independent Test**: Smoke tests run locally with mocks/fakes and no live agent, Docker, network, credentials, or proprietary software.

### Tests for User Story 6

- [ ] T073 [P] [US6] Add API health smoke test in `tests/e2e/test_api_health_smoke.py`
- [ ] T074 [P] [US6] Add agent registry default smoke test in `tests/e2e/test_agent_registry_smoke.py`
- [ ] T075 [P] [US6] Add MCP listing smoke test in `tests/e2e/test_mcp_listing_smoke.py`
- [ ] T076 [P] [US6] Add Wright gateway happy-path smoke test in `tests/e2e/test_wright_gateway_smoke.py`

### Implementation for User Story 6

- [ ] T077 [US6] Add reusable offline API smoke fixtures in `tests/e2e/conftest.py`
- [ ] T078 [US6] Update smoke test documentation in `tests/e2e/README.md`
- [ ] T079 [US6] Ensure smoke fixtures use temporary SQLite state in `tests/e2e/conftest.py`
- [ ] T080 [US6] Run targeted US6 tests documented in `specs/037-refactoring-audit/quickstart.md`

**Checkpoint**: Constitution-required smoke coverage exists and stays offline-safe by default.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final compatibility verification, documentation, and staged commits

- [ ] T081 [P] Update final boundary summary in `specs/037-refactoring-audit/risk-review.md`
- [ ] T082 [P] Update architecture follow-up notes in `docs/architecture/refactoring-audit-2026-07-01.md`
- [ ] T083 Run full targeted pytest set from `specs/037-refactoring-audit/quickstart.md`
- [ ] T084 Run frontend/Playwright checks from `specs/037-refactoring-audit/quickstart.md` if frontend files changed
- [ ] T085 Review `AGENTS.md` and `.specify/feature.json` for correct feature references
- [ ] T086 Commit each completed implementation phase with clear commit messages from `specs/037-refactoring-audit/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks user story phases.
- **US1 Agent Runtime Registry (Phase 3)**: Must complete before US2 and US6.
- **US2 Wright Gateway Contracts (Phase 4)**: Depends on US1 registry metadata.
- **US3 MCP Service Extraction (Phase 5)**: Can begin after Foundational, but should merge after US1 to avoid API boot conflicts.
- **US4 Catalog Normalization (Phase 6)**: Can begin after Foundational and before or after US3, but shared service tests should be reconciled.
- **US5 Validation Harness Seam (Phase 7)**: Depends on US3 service extraction for API wiring and can reuse US4 catalog models where available.
- **US6 Smoke Coverage (Phase 8)**: Depends on US1 and should include US3/US5 fakes when available.
- **Polish (Phase 9)**: Depends on selected story phases.

### User Story Dependencies

- **US1 (P1)**: First implementation slice and MVP.
- **US2 (P2)**: Builds on US1 provider metadata and gateway profile hooks.
- **US3 (P3)**: Independent service extraction, but coordinate with US1 API fixture changes.
- **US4 (P4)**: Independent from runtime registry; coordinate with US3 if services consume catalog normalization.
- **US5 (P5)**: Depends on validation service seams from US3 and can reuse catalog normalization from US4.
- **US6 (P6)**: Depends on US1 and benefits from US3 gateway/service seams.

### Within Each User Story

- Tests are written first and should fail before implementation.
- Package-level contracts before API wiring.
- Services before routes.
- Compatibility wrappers before deleting old call paths.
- Story complete before moving to the next phase commit.

### Parallel Opportunities

- Setup and foundational fixture tasks marked [P] can run in parallel.
- Test files for each user story marked [P] can be drafted in parallel.
- US3 service operation groups can be implemented independently after shared service scaffolding exists.
- US4 catalog normalization and US6 smoke fixtures can proceed in parallel after US1 if file conflicts are managed.

---

## Parallel Example: User Story 1

```bash
Task: "Add registry default and explicit Hermes tests in packages/agent_adapters/tests/test_agent_registry.py"
Task: "Add API boot import-boundary test in apps/api/tests/test_agent_runtime_boot.py"
Task: "Add active agent selection API tests in apps/api/tests/test_agent_health.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "Add MCP install/uninstall/activation service tests in packages/tool_registry/tests/test_mcp_services.py"
Task: "Add MCP credential service tests in packages/tool_registry/tests/test_mcp_services.py"
Task: "Add MCP validation/follow-up service tests in packages/tool_registry/tests/test_mcp_services.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational tasks.
2. Complete US1 tests.
3. Implement registry/factory and API boot changes.
4. Run targeted US1 pytest checks.
5. Commit US1 as a small coherent phase.

### Incremental Delivery

1. US1 creates the runtime registry and removes API boot Hermes coupling.
2. US2 adds gateway contracts while preserving Hermes.
3. US3 moves MCP business logic into services without API response changes.
4. US4 adds catalog normalization and parity checks.
5. US5 adds validation plan/evidence seams with Docker/network opt-in.
6. US6 adds smoke coverage required by the constitution.

### Review Discipline

- Commit after each completed phase or tightly related task group.
- Stop if a phase requires a breaking API contract change.
- Stop if a phase would require MCP-specific host software in the base image.
- Keep default tests offline-safe.

## Notes

- Do not delete `hermes-plugin-wright`.
- Do not tune abstractions specifically to Hermes.
- Do not make package-manager install/update flows require extra approval gates.
- Do not add network-dependent tests to the default fast suite.
- Preserve existing API response shapes unless explicitly approved.
