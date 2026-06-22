# Tasks: Docker Integration & Distribution Packaging

**Input**: Design documents from `/specs/031-docker-integration-distribution/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are generated for Docker detection and command start scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- All python plugin package files reside under `/hermes-plugin-wright/`.
- Docker build files reside under `/docker/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize git checklist and branch tracking for the feature branch `031-docker-integration-distribution`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Verify project dependencies (`httpx`, `pyyaml`, `pydantic`, `structlog`) are correctly set in `hermes-plugin-wright/pyproject.toml`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Docker Appliance Execution (Priority: P1) 🎯 MVP

**Goal**: Copy the plugin package and inject it during Docker image build, and implement uvicorn health/start checks inside Docker.

**Independent Test**: Build the Docker container, run `/wright start` inside the container shell, and assert it reports active API status and does not start uvicorn processes.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T003 [P] [US1] Write test cases in `hermes-plugin-wright/tests/test_commands.py` checking `handle_start` behavior when `is_in_docker()` returns True (both healthy API and unhealthy API cases)

### Implementation for User Story 1

- [x] T004 [P] [US1] Implement `is_in_docker()` helper method checking for `/.dockerenv` presence inside `hermes-plugin-wright/commands.py`
- [x] T005 [US1] Modify `handle_start()` inside `hermes-plugin-wright/commands.py` to prevent spawning uvicorn and return a supervisord diagnostic warning if running in Docker and uvicorn is unhealthy
- [x] T006 [US1] Modify `docker/Dockerfile` to copy `hermes-plugin-wright/` to `/opt/hermes-plugins/wright/` and run `uv tool install --with` during image build stage

**Checkpoint**: At this point, User Story 1 is functional inside the Docker appliance image.

---

## Phase 4: User Story 2 - Local Install & Auto-Discovery (Priority: P2)

**Goal**: Configure PEP 517 entry points for automatic plugin discovery.

**Independent Test**: Install package locally and verify that Hermes registers the `/wright` namespace.

### Implementation for User Story 2

- [x] T007 [US2] Ensure `pyproject.toml` contains `wright = "hermes_plugin_wright:register"` under the `[project.entry-points."hermes_agent.plugins"]` section
- [x] T008 [US2] Test plugin discovery locally using `verify_plugin.py` to verify PEP 517 loader succeeds

**Checkpoint**: User Story 2 is functional for standalone/local python environments.

---

## Phase 5: User Story 3 - Context Integration (Priority: P2)

**Goal**: Wire `register(ctx)` to load catalog and register commands without duplicate configuration writes.

**Independent Test**: Verify that loading the plugin registers command routes without duplicate `.hermes.md` config sync actions.

### Implementation for User Story 3

- [x] T009 [US3] Wire `register(ctx)` in `hermes-plugin-wright/__init__.py` to initialize catalog and register slash commands, delegating all instruction/config syncing to the existing `hermes_sync.py`

**Checkpoint**: User Story 3 is completed.

---

## Phase 6: User Story 4 - Onboarding Documentation (Priority: P2)

**Goal**: Add detailed configuration and usage guides to the plugin README.

**Independent Test**: Verify formatting and links in `README.md` render successfully.

### Implementation for User Story 4

- [x] T010 [US4] Update `hermes-plugin-wright/README.md` with instructions for local pip setup, supervisord Docker configurations, command guides, and plan references

**Checkpoint**: User Story 4 is completed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Complete verification, test suites runs, and image build checks.

- [x] T011 Run complete test verification via `pytest hermes-plugin-wright`
- [x] T012 Run container validation to verify `wright` plugin loads successfully inside the appliance container

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
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)

---

## Parallel Example: User Story 1

```bash
# Launch Dockerfile edits and commands logic in parallel:
Task: "Modify docker/Dockerfile to copy and install plugin in image"
Task: "Implement is_in_docker() helper method inside hermes-plugin-wright/commands.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify Docker build and supervisor check behaviors.
