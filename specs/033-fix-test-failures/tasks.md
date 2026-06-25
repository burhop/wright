# Tasks: Fix Test Validation Failures

**Input**: Design documents from `/specs/033-fix-test-failures/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/validation-commands.md, quickstart.md

**Tests**: This feature is validation-driven. Each user story includes the command that must pass before its tasks are marked complete.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Confirm baseline and prepare validation context.

- [x] T001 Capture failing baseline for `npm run test --workspace=apps/web`
- [x] T002 Capture failing baseline for `npm run build:desktop --workspace=apps/web`
- [x] T003 Capture Python test collection baseline for `uv run pytest`

---

## Phase 2: User Story 1 - Frontend Tests Pass on Windows (Priority: P1)

**Goal**: AppShell renders in restricted test/browser contexts without crashing on storage access.

**Independent Test**: `npm run test --workspace=apps/web`

### Implementation for User Story 1

- [x] T004 [US1] Add safe AppShell storage read/write helpers in apps/web/src/components/layout/AppShell.tsx
- [x] T005 [US1] Preserve existing split-view default behavior in apps/web/src/components/layout/AppShell.tsx
- [x] T006 [US1] Run `npm run test --workspace=apps/web` and verify all Vitest tests pass

---

## Phase 3: User Story 2 - Desktop Build Works Cross-Platform (Priority: P1)

**Goal**: The desktop build script runs from Windows npm shells and still works cross-platform.

**Independent Test**: `npm run build:desktop --workspace=apps/web`

### Implementation for User Story 2

- [x] T007 [US2] Make the desktop build script shell-independent in apps/web/package.json
- [x] T008 [US2] Update dependency metadata if the script requires a portable env helper in apps/web/package.json and package-lock.json
- [x] T009 [US2] Run `npm run build --workspace=apps/web` and verify the standard build still passes
- [x] T010 [US2] Run `npm run build:desktop --workspace=apps/web` and verify the desktop build passes

---

## Phase 4: User Story 3 - Python Test Command Uses the Project Environment (Priority: P2)

**Goal**: Python tests collect using declared workspace packages and dependencies.

**Independent Test**: `uv run pytest`

### Implementation for User Story 3

- [x] T011 [US3] Run `uv sync --all-packages --all-groups` to synchronize the workspace environment
- [x] T012 [US3] If import failures remain, update Python workspace metadata in pyproject.toml or package pyproject files without hardcoding local paths
- [x] T013 [US3] Run `uv run pytest` and document whether failures are resolved or reduced to actionable test assertions

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and Spec Kit task closure.

- [x] T014 Run `git diff --check`
- [x] T015 Update specs/033-fix-test-failures/tasks.md with actual completion status
- [x] T016 Review `git status --short --branch` for only intentional changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Complete
- **US1 (Phase 2)**: Can start immediately
- **US2 (Phase 3)**: Can start immediately, independent of US1
- **US3 (Phase 4)**: Can start after baseline capture; may require environment synchronization
- **Polish (Phase 5)**: Depends on selected user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent
- **US2 (P1)**: Independent
- **US3 (P2)**: Independent except for shared validation timing

### Parallel Opportunities

- US1 and US2 touch different files and can be implemented independently.
- Python environment validation can run after frontend code edits are in progress, but metadata changes must be reviewed carefully.

---

## Implementation Strategy

### MVP First

1. Complete US1 and US2 to restore frontend test/build confidence.
2. Validate Python environment and only change metadata if synchronization does not resolve collection.
3. Run final checks and update task statuses based on actual command results.

### Stop Point

Per the project constitution, implementation should begin only after human approval of this plan.
