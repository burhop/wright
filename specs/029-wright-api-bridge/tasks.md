# Tasks: Wright API Bridge Client

**Input**: Design documents from `/specs/029-wright-api-bridge/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests are explicitly requested using httpx mocking.

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

- [x] T001 Create `hermes-plugin-wright/bridge.py` file with basic imports
- [x] T002 Create initial unit test file at `hermes-plugin-wright/tests/test_bridge.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Export constants `WRIGHT_API_BASE` and `WRIGHT_UI_URL` in `hermes-plugin-wright/bridge.py`
- [x] T004 Install or verify `respx` mock testing package in the python environment

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Verify API Health Status (Priority: P1) 🎯 MVP

**Goal**: Implement async health check with timeout and error mapping

**Independent Test**: Mock the HTTP response for `/api/health` and verify returned dictionary structure.

### Implementation for User Story 1

- [x] T005 [US1] Implement `check_api_health()` using httpx with 30s timeout and ConnectError/Timeout error mapping in `hermes-plugin-wright/bridge.py`
- [x] T006 [P] [US1] Write health check unit tests utilizing mock HTTP requests in `hermes-plugin-wright/tests/test_bridge.py`

**Checkpoint**: At this point, User Story 1 is functional.

---

## Phase 4: User Story 2 - Register a Tool Registry Catalog Entry (Priority: P1)

**Goal**: Implement list, register, workspace, and credential status endpoints

**Independent Test**: Mock HTTP endpoints for `/api/mcp/servers`, `/api/workspace/list`, and `/api/mcp/servers/{id}/credentials`.

### Implementation for User Story 2

- [x] T007 [US2] Implement `register_mcp_server()`, `get_mcp_servers()`, `get_workspaces()`, and `get_credential_status()` in `hermes-plugin-wright/bridge.py`
- [x] T008 [P] [US2] Write unit tests with HTTP mock responses for tools registration, listings, workspaces, and credentials status checks in `hermes-plugin-wright/tests/test_bridge.py`

**Checkpoint**: At this point, User Stories 1 and 2 are functional.

---

## Phase 5: User Story 3 - Repository Path Auto-Detection (Priority: P2)

**Goal**: Parse config.yaml files to extract repository path

**Independent Test**: Test path extraction using temporary mock config files.

### Implementation for User Story 3

- [x] T009 [US3] Implement `detect_repo_dir()` to read config files and locate `--project` in `hermes-plugin-wright/bridge.py`
- [x] T010 [P] [US3] Write unit tests for repository detection using file mock systems in `hermes-plugin-wright/tests/test_bridge.py`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification and documentation polish

- [x] T011 [P] Update Hatchling targets mapping in `hermes-plugin-wright/pyproject.toml` to include `bridge.py` and `tests/test_bridge.py`
- [x] T012 [P] Update package documentation in `hermes-plugin-wright/README.md`
- [x] T013 Run unit tests and quickstart validation

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
Task: "Create hermes-plugin-wright/bridge.py file with basic imports"
Task: "Create initial unit test file at hermes-plugin-wright/tests/test_bridge.py"
```
