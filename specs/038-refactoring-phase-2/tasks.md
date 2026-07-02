# Tasks: Wright Architecture Refactoring Phase 2

**Input**: Design documents from `/specs/038-refactoring-phase-2/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are required because this phase changes architecture and safety boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and review.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish Spec Kit and boundary guardrails before implementation

- [x] T001 Create Phase 2 Spec Kit artifacts in `specs/038-refactoring-phase-2/`
- [x] T002 Update active Spec Kit context references in `AGENTS.md` and `.specify/feature.json`
- [x] T003 [P] Add package import-boundary tests in `tests/test_import_boundaries.py`
- [x] T004 [P] Add `packages/workspace_service` workspace metadata in `pyproject.toml`, `uv.lock`, and `packages/workspace_service/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared telemetry, redaction, and context contract primitives

- [x] T005 [P] Add telemetry constants and redaction helpers in `packages/core/src/core/telemetry.py` and `packages/core/src/core/redaction.py`
- [x] T006 [P] Add telemetry/redaction tests in `packages/core/tests/test_telemetry.py` and `packages/core/tests/test_redaction.py`
- [x] T007 [P] Add agent context materializer contracts in `packages/agent_adapters/src/agent_adapters/context.py`
- [x] T008 [P] Add context materializer tests in `packages/agent_adapters/tests/test_context_materialization.py`

**Checkpoint**: Shared contracts and helpers are ready for route/service work.

---

## Phase 3: User Story 1 - Activate Workspaces Through A Service Boundary (Priority: P1) MVP

**Goal**: Add `workspace_service` and delegate priority workspace lifecycle paths through it.

**Independent Test**: Workspace create, activate, config update, tool toggle, and file run preserve API response shapes while package tests cover service behavior.

### Tests for User Story 1

- [x] T009 [P] [US1] Add workspace service unit tests in `packages/workspace_service/tests/test_workspace_service.py`
- [x] T010 [P] [US1] Add fake non-Hermes activation test in `packages/workspace_service/tests/test_non_hermes_activation.py`
- [x] T011 [P] [US1] Update workspace API compatibility tests in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement workspace service models/errors in `packages/workspace_service/src/workspace_service/models.py`
- [x] T013 [US1] Implement workspace service facade in `packages/workspace_service/src/workspace_service/service.py`
- [x] T014 [US1] Export package API in `packages/workspace_service/src/workspace_service/__init__.py`
- [x] T015 [US1] Refactor priority workspace route internals in `apps/api/src/api/routers/workspace.py`
- [x] T016 [US1] Remove route-local Hermes context writes from touched workspace paths in `apps/api/src/api/routers/workspace.py`

**Checkpoint**: Workspace lifecycle has a package facade and fake non-Hermes activation does not write Hermes files.

---

## Phase 4: User Story 2 - Materialize Agent Context Without Hermes As The Generic Model (Priority: P2)

**Goal**: Move provider-specific context writing behind agent adapter materializers.

**Independent Test**: Hermes materializer writes `.hermes.md`; OpenClaw/fake materializer writes no Hermes files.

### Tests for User Story 2

- [x] T017 [P] [US2] Add Hermes materializer compatibility tests in `packages/agent_adapters/tests/test_context_materialization.py`
- [x] T018 [P] [US2] Add OpenClaw no-Hermes materializer tests in `packages/agent_adapters/tests/test_openclaw_gateway_stub.py`

### Implementation for User Story 2

- [x] T019 [US2] Implement Hermes context materializer in `packages/agent_adapters/src/agent_adapters/hermes_gateway.py`
- [x] T020 [US2] Implement OpenClaw stub context materializer in `packages/agent_adapters/src/agent_adapters/openclaw.py`
- [x] T021 [US2] Export materializer contracts and helpers from `packages/agent_adapters/src/agent_adapters/__init__.py`
- [x] T022 [US2] Use materializers from `workspace_service` context refresh logic in `packages/workspace_service/src/workspace_service/service.py`

**Checkpoint**: Generic workspace service calls agent adapter materializers, not Hermes helpers.

---

## Phase 5: User Story 3 - Enforce MCP Safety Policy In The Registry Package (Priority: P3)

**Goal**: Add `tool_registry` policy decisions and enforce them at install/start/call boundaries.

**Independent Test**: Blocked, high-risk approval, missing credential, and approved paths are covered offline.

### Tests for User Story 3

- [x] T023 [P] [US3] Add MCP safety policy tests in `packages/tool_registry/tests/test_mcp_safety.py`
- [x] T024 [P] [US3] Add install/start/call enforcement tests in `packages/tool_registry/tests/test_mcp_services.py` and `packages/tool_registry/tests/test_registry.py`

### Implementation for User Story 3

- [x] T025 [US3] Implement policy models and evaluator in `packages/tool_registry/src/tool_registry/safety.py`
- [x] T026 [US3] Wire install policy into `packages/tool_registry/src/tool_registry/services.py`
- [x] T027 [US3] Wire start/call policy into `packages/tool_registry/src/tool_registry/manager.py`
- [x] T028 [US3] Wire gateway call start/call policy context in `apps/api/src/api/routers/gateway.py`
- [x] T029 [US3] Export safety contracts from `packages/tool_registry/src/tool_registry/__init__.py`

**Checkpoint**: Safety policy is package-owned and enforced beyond UI code.

---

## Phase 6: User Story 4 - Produce Opt-In Validation Evidence (Priority: P4)

**Goal**: Add validation executor/CLI seams and redacted JSON plus Markdown evidence writing.

**Independent Test**: Mock executor and evidence writer pass without Docker or network.

### Tests for User Story 4

- [x] T030 [P] [US4] Add validation writer tests in `packages/tool_registry/tests/test_validation_writer.py`
- [x] T031 [P] [US4] Add validation CLI mock tests in `packages/tool_registry/tests/test_validation_cli.py`

### Implementation for User Story 4

- [x] T032 [US4] Extend validation evidence model in `packages/tool_registry/src/tool_registry/validation_evidence.py`
- [x] T033 [US4] Implement validation executors in `packages/tool_registry/src/tool_registry/validation_executor.py`
- [x] T034 [US4] Implement evidence writer in `packages/tool_registry/src/tool_registry/validation_writer.py`
- [x] T035 [US4] Implement validation CLI in `packages/tool_registry/src/tool_registry/validation_cli.py`
- [x] T036 [US4] Document CLI behavior in `docs/mcp-catalog/mcp-server-testing-process.md`

**Checkpoint**: Validation can write redacted evidence without claiming clean-container success.

---

## Phase 7: User Story 5 - Keep Frontend Contracts In Sync With Backend Schemas (Priority: P5)

**Goal**: Generate checked-in TypeScript domain contracts and add a freshness check.

**Independent Test**: Contract generator check passes offline and frontend tests run.

### Tests for User Story 5

- [x] T037 [P] [US5] Add contract generation check test in `tests/test_frontend_contracts.py`

### Implementation for User Story 5

- [x] T038 [US5] Add frontend contract generator in `scripts/generate-frontend-contracts.py`
- [x] T039 [US5] Generate contracts in `apps/web/src/types/generated/wright-contracts.ts`
- [x] T040 [US5] Update frontend README in `apps/web/README.md`

**Checkpoint**: Generated TypeScript contracts are checked in and freshness-tested.

---

## Phase 8: User Story 6 - Observe Phase 2 Safety Flows Locally (Priority: P6)

**Goal**: Clarify trace/correlation semantics and use shared redaction in touched flows.

**Independent Test**: Log-shape, correlation, redaction, and remote-export-off tests pass.

### Tests for User Story 6

- [x] T041 [P] [US6] Add API trace/correlation tests in `apps/api/tests/test_trace_correlation.py`
- [x] T042 [P] [US6] Add default-off remote telemetry tests in `packages/core/tests/test_telemetry.py`

### Implementation for User Story 6

- [x] T043 [US6] Update logging processor in `packages/core/src/core/logging.py`
- [x] T044 [US6] Update tracing middleware in `apps/api/src/api/middleware/tracing.py`
- [x] T045 [US6] Use redaction helper in validation evidence/follow-up paths in `packages/tool_registry/src/tool_registry/validation_evidence.py` and `packages/tool_registry/src/tool_registry/mcp_followups.py`
- [x] T046 [US6] Replace stdlib logging in touched registry manager path in `packages/tool_registry/src/tool_registry/manager.py`

**Checkpoint**: Touched safety flows use local structured telemetry and shared redaction.

---

## Phase 9: Documentation And Verification

**Purpose**: Update architecture/contributor docs and run required checks

- [x] T047 [P] Update architecture documentation in `docs/architecture/refactoring-phase-2-2026-07-01.md`
- [x] T048 [P] Update root README architecture summary in `README.md`
- [x] T049 [P] Update Hermes plugin README to remove stale local file URL and describe shared catalog ownership in `hermes-plugin-wright/README.md`
- [x] T050 Run `uv run pytest packages/agent_adapters packages/tool_registry packages/workspace_service packages/core apps/api/tests`
- [x] T051 Run `npm run test --workspace=apps/web`
- [x] T052 Run `uv run python scripts/generate-frontend-contracts.py --check`
- [x] T053 Run Spec Kit analysis/checklist validation for `specs/038-refactoring-phase-2/`
- [x] T054 Mark completed tasks in `specs/038-refactoring-phase-2/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Blocks workspace, policy, validation, contracts, and telemetry work.
- **US1 Workspace Service (Phase 3)**: Depends on package metadata and materializer contracts.
- **US2 Context Materialization (Phase 4)**: Depends on agent adapter contracts.
- **US3 MCP Safety (Phase 5)**: Can proceed after foundational helpers.
- **US4 Validation Evidence (Phase 6)**: Depends on shared redaction helpers.
- **US5 Frontend Contracts (Phase 7)**: Depends on package/domain models.
- **US6 Observability (Phase 8)**: Depends on telemetry constants/redaction helpers.
- **Docs/Verification (Phase 9)**: Depends on implementation.

### Parallel Opportunities

- T003, T005, T006, T007, T008 can be prepared in parallel.
- Workspace service tests and agent materializer tests touch different packages.
- MCP safety and validation writer tests touch different files after redaction exists.
- Documentation updates can proceed after APIs stabilize.

## Implementation Strategy

1. Add tests and package scaffolding.
2. Implement helpers and package facades.
3. Wire API routes to facades without response changes.
4. Add CLI/contracts/docs.
5. Run targeted verification.
6. Complete follow-up ownership slices and record remaining operator-only caveats.

---

## Phase 10: Deferred Phase 2 Completion Pass

**Purpose**: Finish the explicitly deferred Phase 2 ownership and maintainability items without changing default offline test behavior.

- [x] T055 Move large API migration catalog data into package-owned `packages/tool_registry/src/tool_registry/engineering_catalog.py`
- [x] T056 Add package catalog ownership tests in `packages/tool_registry/tests/test_engineering_catalog.py` and API migration parity tests in `apps/api/tests/test_mcp_catalog_seed.py`
- [x] T057 Add `data_vault` SQLite state-store seam in `packages/data_vault/src/data_vault/state_store.py`
- [x] T058 Use the `data_vault` state-store seam from API migrations and workspace service direct SQL paths
- [x] T059 Strengthen `DockerCleanContainerExecutor` so opt-in Docker validation launches a clean container and records direct MCP stdio probe evidence without claiming gateway success
- [x] T060 Add Docker executor fake-runner tests in `packages/tool_registry/tests/test_validation_executor.py`
- [x] T061 Extract frontend workspace enablement UI from `ToolCard` into `apps/web/src/components/tools/WorkspaceEnablement.tsx`
- [x] T062 Extract frontend workspace activity bar from `WorkspacePanel` into `apps/web/src/components/chat/WorkspaceActivityBar.tsx`
- [x] T063 Update Phase 2 architecture and MCP validation docs for the completion pass

## Remaining Operator-Only Caveat

- Clean-container validation still must be run by an operator against selected catalog entries before any entry is marked fully validated. The Docker executor can now run direct stdio probes, but evidence remains `partial` unless the documented Wright gateway proxy probe is also executed and recorded.

