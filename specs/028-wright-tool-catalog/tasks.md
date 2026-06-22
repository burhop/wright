# Tasks: Engineering Tool Catalog

**Input**: Design documents from `/specs/028-wright-tool-catalog/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests are explicitly requested for validation and search.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- All paths are relative to the repository root. The package code resides under `/hermes-plugin-wright/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create `hermes-plugin-wright/schemas.py` file with basic imports
- [x] T002 Create empty `hermes-plugin-wright/catalog.yaml` file
- [x] T003 Create `hermes-plugin-wright/catalog.py` file with basic imports
- [x] T004 [P] Create initial unit test file at `hermes-plugin-wright/tests/test_catalog.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement Pydantic validation models (`EnvVarDefinition`, `DependencySpec`, `CatalogEntry`) in `hermes-plugin-wright/schemas.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Browse Engineering Tools by Domain (Priority: P1) 🎯 MVP

**Goal**: Expose loader initialization and domain filtering

**Independent Test**: Load the catalog yaml and fetch tools matching the "cad" domain.

### Implementation for User Story 1

- [x] T006 [US1] Build catalog database containing ~30 engineering MCP tool entries in `hermes-plugin-wright/catalog.yaml`
- [x] T007 [US1] Implement `CatalogLoader` initialization and `get_by_domain` filtering in `hermes-plugin-wright/catalog.py`
- [x] T008 [P] [US1] Write unit tests for domain taxonomy filtering in `hermes-plugin-wright/tests/test_catalog.py`

**Checkpoint**: At this point, User Story 1 is functional.

---

## Phase 4: User Story 2 - Keyword Search Across Catalog (Priority: P1)

**Goal**: Implement free-text search across tools

**Independent Test**: Execute search keyword matching and verify correct tools are returned.

### Implementation for User Story 2

- [x] T009 [US2] Implement keyword `search` logic in `CatalogLoader` class at `hermes-plugin-wright/catalog.py`
- [x] T010 [P] [US2] Write unit tests for keyword search matching case-insensitively in `hermes-plugin-wright/tests/test_catalog.py`

**Checkpoint**: At this point, User Stories 1 and 2 are functional.

---

## Phase 5: User Story 3 - Database Insertion Validation (Priority: P1)

**Goal**: Validate direct insertability to Wright DB

**Independent Test**: Run validation checks matching schemas to models.

### Implementation for User Story 3

- [x] T011 [US3] Verify and assert alignment of schemas in `hermes-plugin-wright/schemas.py` with `packages/tool_registry/src/tool_registry/models.py`
- [x] T012 [P] [US3] Write schema structure validation unit tests in `hermes-plugin-wright/tests/test_catalog.py`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification and documentation polish

- [x] T013 [P] Update `README.md` at `hermes-plugin-wright/README.md` with loader details
- [x] T014 Run unit tests and quickstart validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2)

---

## Parallel Example: Setup & US1

```bash
# Setup tasks
Task: "Create hermes-plugin-wright/schemas.py file with basic imports"
Task: "Create hermes-plugin-wright/catalog.yaml file"
```
