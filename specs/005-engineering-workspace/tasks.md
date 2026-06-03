# Tasks: Engineering Workspace

**Input**: Design documents from `/specs/005-engineering-workspace/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Core Package**: `packages/core/src/core/`
- **Agent Adapters**: `packages/agent_adapters/src/agent_adapters/`
- **API backend**: `apps/api/src/api/`
- **Web frontend**: `apps/web/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migrations and basic directory configurations

- [x] T001 Add database schema definition for `engineering_workspaces` table in `apps/api/src/api/database/migrate.py`
- [x] T002 Run database migrations to initialize the workspace tables in `apps/api/src/api/database/migrate.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core workspace management class and session link infrastructure

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Implement local directory resolution and Git repository initialization (`git init`) inside `WorkspaceManager` constructor in `packages/core/src/core/workspace.py`
- [x] T004 Implement workspace metadata SQL CRUD access helpers in `packages/core/src/core/workspace.py`
- [x] T005 [P] Setup base routing structure and session validation dependencies in `apps/api/src/api/routers/workspace.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Local Workspace Explorer (Priority: P1) 🎯 MVP

**Goal**: Enable workspace folder tree navigation, file CRUD actions, output files routing, and 3D preview of STL files.

**Independent Test**: Create file/folder from the UI Explorer sidebar, verify changes persist on disk, trigger an agent run and check output files end up in the workspace while temp files go to `/tmp`.

### Tests for User Story 1

- [x] T006 [P] [US1] Write backend integration tests for file creation, folder creation, renaming, and deletion in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 1

- [x] T007 [P] [US1] Implement folder creation, file creation, safe deletion, and move/rename filesystem logic in `packages/core/src/core/workspace.py`
- [x] T008 [US1] Expose CRUD endpoints (POST/DELETE/PUT `/api/workspace/files`) in `apps/api/src/api/routers/workspace.py`
- [x] T009 [P] [US1] Add CRUD REST API client methods in `apps/web/src/services/workspace-service.ts`
- [x] T010 [US1] Update `FileTree.tsx` to render folder hierarchy, context menus, and CRUD dialog overlays in `apps/web/src/components/common/FileTree.tsx`
- [x] T011 [US1] Create the FILES explorer pane layouts and integrate interactive CRUD handlers in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T012 [P] [US1] Configure agent subprocess executors to route final STL/CAD outputs to the session workspace folder in `packages/agent_adapters/src/agent_adapters/hermes.py`

**Checkpoint**: At this point, User Story 1 (MVP) is fully functional and testable.

---

## Phase 4: User Story 2 - Workspace Version Control & Git History (Priority: P2)

**Goal**: Display status badges, unified code diff previews, and revert changes or perform local commits with history timeline.

**Independent Test**: Modify a file in the workspace, confirm it shows as `M` in the explorer sidebar, view diff, and perform a local commit verifying that it clears status and appears in the history timeline.

### Tests for User Story 2

- [x] T013 [P] [US2] Write unit and integration tests for git status, diff, revert, and commit endpoints in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 2

- [x] T014 [US2] Implement git status parsing (porcelain format), git diff file generation, git revert, and git commit CLI wrappers in `packages/core/src/core/workspace.py`
- [x] T015 [US2] Expose endpoints `/api/workspace/git/status`, `/api/workspace/git/diff`, `/api/workspace/git/revert`, and `/api/workspace/git/commit` in `apps/api/src/api/routers/workspace.py`
- [x] T016 [P] [US2] Add Version Control REST API client methods in `apps/web/src/services/workspace-service.ts`
- [x] T017 [US2] Build `DiffViewer.tsx` component to display additions and deletions with custom theme colors in `apps/web/src/components/common/DiffViewer.tsx`
- [x] T018 [US2] Update `FileTree.tsx` to read tree node `git_status` properties and render badges (U, M) in `apps/web/src/components/common/FileTree.tsx`
- [x] T019 [US2] Add the Version Control pane interface, unstaged/staged files list, commit form, and commit history lists in `apps/web/src/components/chat/WorkspacePanel.tsx`

**Checkpoint**: At this point, User Story 1 and 2 work together seamlessly.

---

## Phase 5: User Story 3 - Remote Git Syncing & Options (Priority: P2)

**Goal**: Sync the local repository with remote servers using HTTPS tokens and display Push/Pull action triggers.

**Independent Test**: Add remote configurations and tokens in the Options page, perform a local commit, push to GitHub, and verify success; pull changes from a remote and handle conflicts gracefully.

### Tests for User Story 3

- [x] T020 [P] [US3] Write unit and contract tests for options config updates, push, and pull routes in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 3

- [x] T021 [US3] Implement git push and git pull subprocess wrappers with HTTPS auth token integration in `packages/core/src/core/workspace.py`
- [x] T022 [US3] Expose REST endpoints `/api/workspace/config` and `/api/workspace/git/push` / `/api/workspace/git/pull` in `apps/api/src/api/routers/workspace.py`
- [x] T023 [P] [US3] Add options config and remote sync client methods in `apps/web/src/services/workspace-service.ts`
- [x] T024 [US3] Build the Options pane UI displaying connection forms and action buttons in `apps/web/src/components/chat/WorkspacePanel.tsx`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Performance optimizations, large file safety, and documentation

- [x] T025 [P] Implement auto-generation of `.gitignore` (ignoring `.log`, `.tmp` files) on workspace initialization in `packages/core/src/core/workspace.py`
- [x] T026 Implement concurrent file locks to prevent file renames or deletions during active agent write processes in `packages/core/src/core/workspace.py`
- [x] T027 [P] Update developer docs and verify quickstart manuals in `specs/005-engineering-workspace/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Sequential delivery (P1 → P2 → P3) is recommended to build MVP first
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 tree node structure
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US2 commits list

---

## Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001, T002)
- Models and Services within each user story can proceed in parallel (e.g., T009 and T007)
- Different stories (US1, US2, US3) can be worked on in parallel by separate developers once Phase 2 (Foundation) is complete.

---

## Parallel Example: User Story 1

```bash
# Launch backend implementation and UI tree adjustments together:
Task: "Implement folder creation, file creation, safe deletion, and move/rename filesystem logic in packages/core/src/core/workspace.py"
Task: "Update FileTree.tsx to render folder hierarchy, context menus, and CRUD dialog overlays in apps/web/src/components/common/FileTree.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test local CRUD, file trees, and output routing.
5. Deploy MVP to user.

### Incremental Delivery

1. Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test status indicators, diffs, and local commits
4. Add User Story 3 → Integrate HTTPS remote git repository syncing
5. Each story builds on top of the local explorer without breaking existing layout options.
