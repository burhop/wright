# Tasks: Engineering MCP Catalog

**Input**: Design documents from `/specs/034-engineering-mcp-catalog/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. The constitution and feature request require broad test coverage across registry data, API behavior, UI cards, and container validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm active sprint context and prepare directories used by the implementation

- [X] T001 Verify active branch `034-engineering-mcp-catalog` and active feature pointer `.specify/feature.json`
- [X] T002 [P] Create follow-up output directory `docs/mcp-catalog/followups/`
- [X] T003 [P] Confirm existing ignore files cover generated caches and test artifacts in `.gitignore` and `.dockerignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schema, metadata, and persistence changes that all user stories depend on

- [X] T004 [P] Add catalog metadata models and defaults in `packages/tool_registry/src/tool_registry/models.py`
- [X] T005 Update SQLite migrations and serialization for new MCP metadata fields in `packages/tool_registry/src/tool_registry/db.py`
- [X] T006 [P] Extend Hermes plugin catalog schemas with verification, platform, installability, risk, and validation metadata in `hermes-plugin-wright/schemas.py`
- [X] T007 Update Hermes catalog loader sorting/search helpers in `hermes-plugin-wright/catalog.py`
- [X] T008 Update API seed catalog metadata enrichment and database migration columns in `apps/api/src/api/database/migrate.py`
- [X] T009 [P] Add shared catalog classification helpers in `packages/tool_registry/src/tool_registry/mcp_catalog.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Browse Statused Engineering MCPs (Priority: P1) MVP

**Goal**: Users can browse catalog entries ordered by tested, might-work, blocked, and non-working tiers with explicit evidence and safety metadata.

**Independent Test**: Load Python catalog/API data and the web registry page; verify known entries show correct verification state, platform support, risk, and readiness ordering.

### Tests for User Story 1

- [X] T010 [P] [US1] Add Python model/database metadata tests in `packages/tool_registry/tests/test_registry.py`
- [X] T011 [P] [US1] Add Hermes catalog ordering/search tests in `hermes-plugin-wright/tests/test_catalog.py`
- [X] T012 [P] [US1] Add API extended metadata response tests in `apps/api/tests/test_mcp_api.py`
- [X] T013 [P] [US1] Add Tool Registry card metadata and ordering tests in `apps/web/tests/ToolRegistry.spec.tsx`

### Implementation for User Story 1

- [X] T014 [US1] Seed corrected engineering MCP metadata and installability tiers in `apps/api/src/api/database/migrate.py`
- [X] T015 [US1] Update TypeScript MCP service types in `apps/web/src/services/mcp-service.ts`
- [X] T016 [US1] Update tool store sorting-compatible state handling in `apps/web/src/store/tools.tsx`
- [X] T017 [US1] Update registry page counts, filters, search, and readiness sorting in `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [X] T018 [US1] Update current UI cards to display verification, tier, platform, dependency, credential, risk, and blocked reason metadata in `apps/web/src/components/tools/ToolCard.tsx`

**Checkpoint**: User Story 1 is fully browsable and testable independently

---

## Phase 4: User Story 2 - Validate Installability in One Local Linux Environment (Priority: P1)

**Goal**: Validation classifies entries as passed, dependency-missing, blocked, failed, skipped, or not-tested without requiring unavailable CAD software, credentials, GUI apps, hardware, or licenses.

**Independent Test**: Run validation unit/API tests and Docker smoke tests; verify host-dependent entries produce expected dependency diagnostics.

### Tests for User Story 2

- [X] T019 [P] [US2] Add validation classification tests in `packages/tool_registry/tests/test_mcp_validation.py`
- [X] T020 [P] [US2] Add install blocking/dependency-limited API tests in `apps/api/tests/test_mcp_api.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement validation classification service in `packages/tool_registry/src/tool_registry/mcp_validation.py`
- [X] T022 [US2] Add validation response models and endpoints in `apps/api/src/api/routers/mcp.py`
- [X] T023 [US2] Guard install endpoint against blocked and non-working entries in `apps/api/src/api/routers/mcp.py`
- [X] T024 [US2] Document container validation command expectations in `specs/034-engineering-mcp-catalog/quickstart.md`

**Checkpoint**: User Story 2 validation can run without paid host software

---

## Phase 5: User Story 3 - Track Follow-Up Work for Broken MCPs (Priority: P2)

**Goal**: Non-working validation results create or link durable follow-up records ready for GitHub triage.

**Independent Test**: Mark a sample entry failed and verify a redacted follow-up markdown file is generated and linked without duplicates.

### Tests for User Story 3

- [X] T025 [P] [US3] Add follow-up generation and deduplication tests in `packages/tool_registry/tests/test_mcp_followups.py`
- [X] T026 [P] [US3] Add UI follow-up link rendering test in `apps/web/tests/ToolRegistry.spec.tsx`

### Implementation for User Story 3

- [X] T027 [US3] Implement follow-up record writer in `packages/tool_registry/src/tool_registry/mcp_followups.py`
- [X] T028 [US3] Connect failed validation results to follow-up records in `apps/api/src/api/routers/mcp.py`
- [X] T029 [US3] Render follow-up links for non-working entries in `apps/web/src/components/tools/ToolCard.tsx`

**Checkpoint**: Broken entries have actionable follow-up records

---

## Phase 6: User Story 4 - Report Missing or Newly Found MCPs (Priority: P3)

**Goal**: Users can submit missing MCP candidates as pending seed entries without granting verified status.

**Independent Test**: Submit a missing MCP candidate and verify it appears as user-reported/pending with install blocked.

### Tests for User Story 4

- [X] T030 [P] [US4] Add missing MCP report model/API tests in `apps/api/tests/test_mcp_api.py`
- [X] T031 [P] [US4] Add report missing MCP UI test in `apps/web/tests/ToolRegistry.spec.tsx`

### Implementation for User Story 4

- [X] T032 [US4] Add missing MCP report request handling in `apps/api/src/api/routers/mcp.py`
- [X] T033 [US4] Add frontend service method for missing MCP reports in `apps/web/src/services/mcp-service.ts`
- [X] T034 [US4] Add report missing MCP workflow entry point in `apps/web/src/components/pages/ToolRegistryPage.tsx`

**Checkpoint**: Missing candidates can be added as blocked/pending seeds

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate everything together and update docs/tasks

- [X] T035 [P] Update docs in `docs/mcp-catalog/tools-list.md` to describe readiness tiers and follow-up records
- [X] T036 Run Python validation `uv run pytest hermes-plugin-wright/tests packages/tool_registry/tests apps/api/tests`
- [X] T037 Run frontend validation `npm run test --workspace=apps/web` and `npm run build --workspace=apps/web`
- [X] T038 Run or document Docker validation from `specs/034-engineering-mcp-catalog/quickstart.md`
- [X] T039 Mark all completed tasks in `specs/034-engineering-mcp-catalog/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Story 1 (P1)**: Depends on Foundational
- **User Story 2 (P1)**: Depends on Foundational; can proceed after metadata fields exist
- **User Story 3 (P2)**: Depends on User Story 2 validation statuses
- **User Story 4 (P3)**: Depends on Foundational metadata fields
- **Polish**: Depends on all implemented stories

### Parallel Opportunities

- T002 and T003 can run in parallel.
- T004, T006, and T009 can run in parallel before persistence wiring.
- T010-T013 can run in parallel after foundational schema is known.
- T019 and T020 can run in parallel.
- T025 and T026 can run in parallel.
- T030 and T031 can run in parallel.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1 so users can browse the statused catalog.
3. Validate the UI and API ordering before adding validation/follow-up workflows.

### Incremental Delivery

1. Add statused catalog metadata and UI.
2. Add local Ubuntu-friendly validation classification.
3. Add follow-up records for non-working entries.
4. Add missing-MCP report workflow.
