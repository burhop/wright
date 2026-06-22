# Tasks: Wright Slash Commands

**Input**: Design documents from `/specs/030-wright-slash-commands/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests are requested utilizing mock environments and assertion frameworks.

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

- [ ] T001 Initialize `hermes-plugin-wright/commands.py` file with basic shell structures and imports
- [ ] T002 Create unit test skeleton at `hermes-plugin-wright/tests/test_commands.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Implement the command router registering method `register_commands(ctx, catalog)` in `hermes-plugin-wright/commands.py`
- [ ] T004 Wire the entry point loader in `hermes-plugin-wright/__init__.py` to import and call `register_commands`
- [ ] T005 [P] Update `hermes-plugin-wright/pyproject.toml` to list `commands.py` and `tests/test_commands.py` in `force-include`
- [ ] T006 [P] Write a basic test for command router registration in `hermes-plugin-wright/tests/test_commands.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Server Lifecycle Management (Priority: P1) 🎯 MVP

**Goal**: Implement launcher commands `/wright start` and `/wright stop` with process detaching and signaling.

**Independent Test**: Mock subprocess popen and os.kill signals and assert correct process state management.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Write tests for `start` and `stop` subcommands using mock processes, log files, and exit timers in `hermes-plugin-wright/tests/test_commands.py`

### Implementation for User Story 1

- [ ] T008 [US1] Implement `/wright start` command logic (stale frontend build comparison, detached subprocess popen, PID file writing, API polling check) in `hermes-plugin-wright/commands.py`
- [ ] T009 [US1] Implement `/wright stop` command logic (PID reading, SIGTERM signaling, graceful exit verification loop, PID file cleanup) in `hermes-plugin-wright/commands.py`

**Checkpoint**: At this point, User Story 1 is functional.

---

## Phase 4: User Story 2 - Navigation & Diagnostics (Priority: P1)

**Goal**: Implement browser launching `/wright open` and checklist utility `/wright doctor`.

**Independent Test**: Assert browser opens on running stack and check diagnostic permissions check logic.

### Tests for User Story 2

- [ ] T010 [P] [US2] Write tests for `open` and `doctor` subcommands in `hermes-plugin-wright/tests/test_commands.py`

### Implementation for User Story 2

- [ ] T011 [US2] Implement `/wright open` command logic (web browser launch with webbrowser module after health check) in `hermes-plugin-wright/commands.py`
- [ ] T012 [US2] Implement `/wright doctor` diagnostics logic (checking git paths, uvicorn server health, sqlite file existence, secrets file 0600 permissions, active credential variables status) in `hermes-plugin-wright/commands.py`

**Checkpoint**: At this point, User Stories 1 and 2 are functional.

---

## Phase 5: User Story 3 - Catalog Exploration & Search (Priority: P2)

**Goal**: Browse, filter, search and details inspect cataloged engineering tools.

**Independent Test**: Assert markdown layouts and tables are correctly populated on filter and query matches.

### Tests for User Story 3

- [ ] T013 [P] [US3] Write tests for catalog listing, keyword searching, and info detail views in `hermes-plugin-wright/tests/test_commands.py`

### Implementation for User Story 3

- [ ] T014 [US3] Implement `/wright catalog [domain]` and `/wright catalog search <query>` formatting and search dispatch logic in `hermes-plugin-wright/commands.py`
- [ ] T015 [US3] Implement `/wright info <id>` detail presenter logic in `hermes-plugin-wright/commands.py`

**Checkpoint**: User Stories 1, 2, and 3 are functional.

---

## Phase 6: User Story 4 - Tool Installation (Priority: P2)

**Goal**: Support registering cataloged tools in active MCP server instances.

**Independent Test**: Mock post endpoints and check client payload serialization on trigger install.

### Tests for User Story 4

- [ ] T016 [P] [US4] Write tests for the `install` subcommand mock responses in `hermes-plugin-wright/tests/test_commands.py`

### Implementation for User Story 4

- [ ] T017 [US4] Implement `/wright install <id>` command mapping to registration bridge endpoints in `hermes-plugin-wright/commands.py`

**Checkpoint**: User Stories 1 to 4 are functional.

---

## Phase 7: User Story 5 - Integration Status Check (Priority: P2)

**Goal**: Dashboard view showing connectivity and configured tool status mapping.

**Independent Test**: Assert emoji status mappings and active workspace formats are printed accurately.

### Tests for User Story 5

- [ ] T018 [P] [US5] Write tests for the status dashboard check in `hermes-plugin-wright/tests/test_commands.py`

### Implementation for User Story 5

- [ ] T019 [US5] Implement `/wright status` layout with emoji status indicators and connection states in `hermes-plugin-wright/commands.py`

**Checkpoint**: All user stories are independently functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Complete documentation and packaging validation.

- [ ] T020 [P] Update the command reference in `hermes-plugin-wright/README.md`
- [ ] T021 Verify the entire package builds and is loadable by running `verify_plugin.py` and `pytest hermes-plugin-wright`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)
- **User Story 5 (P2)**: Can start after Foundational (Phase 2)

---

## Parallel Example: Setup & US1

```bash
# Setup tasks
Task: "Initialize hermes-plugin-wright/commands.py file with basic shell structures and imports"
Task: "Create unit test skeleton at hermes-plugin-wright/tests/test_commands.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. Complete Phase 4: User Story 2
5. **STOP and VALIDATE**: Test launcher, doctor, and browser control endpoints.
