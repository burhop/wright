# Tasks: Hermes Wright Plugin Skeleton & Registration

**Input**: Design documents from `/specs/027-wright-plugin-skeleton/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Minimal verification script task is added for verification.

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

- [x] T001 Create project directories `hermes-plugin-wright/` and `hermes-plugin-wright/tests/`
- [x] T002 Initialize base `pyproject.toml` at `hermes-plugin-wright/pyproject.toml` with basic metadata
- [x] T003 [P] Create initial `README.md` at `hermes-plugin-wright/README.md` explaining the plugin structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create empty conftest.py configuration at `hermes-plugin-wright/tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Plugin Discovery and Registration (Priority: P1) 🎯 MVP

**Goal**: Expose entry point and log initialization using structlog

**Independent Test**: Execute the loading python script in the environment and verify structlog emits the loading log event.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create the package entry point module file at `hermes-plugin-wright/__init__.py`
- [x] T006 [US1] Implement `register(ctx)` function in `hermes-plugin-wright/__init__.py` logging "Wright plugin loaded" via `structlog`

**Checkpoint**: At this point, User Story 1 is functional and can log loading status.

---

## Phase 4: User Story 2 - Slash Command Namespace Availability (Priority: P1)

**Goal**: Declare the /wright slash command namespace in plugin.yaml

**Independent Test**: Load the plugin yaml manifest and verify it lists "/wright" namespace under commands or capabilities.

### Implementation for User Story 2

- [x] T007 [US2] Create and configure manifest `plugin.yaml` at `hermes-plugin-wright/plugin.yaml` declaring the `/wright` slash command capability

**Checkpoint**: At this point, User Stories 1 and 2 are functional.

---

## Phase 5: User Story 3 - Package Distribution & Installation (Priority: P2)

**Goal**: Define dependencies and entry point registration in pyproject.toml

**Independent Test**: Run `pip install -e ./hermes-plugin-wright` and check entry point availability.

### Implementation for User Story 3

- [x] T008 [US3] Update `pyproject.toml` at `hermes-plugin-wright/pyproject.toml` with dependencies (httpx, pyyaml, pydantic) and the hermes_agent.plugins entry point mapping

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification and documentation polish

- [x] T009 [P] Create a local verification script at `hermes-plugin-wright/verify_plugin.py` to assert package installation and log output
- [x] T010 Run `quickstart.md` validation using the verification script

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2), requires metadata update in pyproject.toml

---

## Parallel Example: Setup & US1

```bash
# Setup tasks
Task: "Create project directories hermes-plugin-wright/ and hermes-plugin-wright/tests/"
Task: "Create initial README.md at hermes-plugin-wright/README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Complete Phase 4: User Story 2
5. Complete Phase 5: User Story 3
6. **STOP and VALIDATE**: Run `verify_plugin.py` script.
