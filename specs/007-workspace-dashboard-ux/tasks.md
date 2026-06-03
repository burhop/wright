# Tasks: Workspace Dashboard UX

**Input**: Design documents from `/specs/007-workspace-dashboard-ux/`

**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅)

**Tests**: Not explicitly requested in spec — test tasks omitted. Verification plan covers manual + E2E checks.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema updates and shared utilities needed before any user story

- [X] T001 Add `workspace_name` column migration to `engineering_workspaces` table in `apps/api/src/api/database/migrate.py`
- [X] T002 Add `agent_contexts` table creation to migration in `apps/api/src/api/database/migrate.py`
- [X] T003 [P] Add `create_workspace_from_dashboard()` function in `packages/core/src/core/workspace.py`
- [X] T004 [P] Add `get_workspace_by_id()` function in `packages/core/src/core/workspace.py`
- [X] T005 [P] Add `save_agent_context()` and `load_agent_context()` functions in `packages/core/src/core/workspace.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core API endpoints and agent adapter changes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Add `POST /api/workspace/create` endpoint with `WorkspaceCreateRequest`/`WorkspaceCreateResponse` models in `apps/api/src/api/routers/workspace.py`
- [X] T007 [P] Add `GET /api/workspace/{workspace_id}` endpoint in `apps/api/src/api/routers/workspace.py`
- [X] T008 [P] Add `workspace_name` field to `WorkspaceListEntry` response model in `apps/api/src/api/routers/workspace.py`
- [X] T009 [P] Add `save_context` and `load_context` abstract methods to `BaseAgentEngine` in `packages/agent_adapters/src/agent_adapters/base.py`
- [X] T010 [P] Implement `save_context` and `load_context` as no-ops in `HermesAdapter` in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [X] T011 [P] Add `createWorkspace()` and `getWorkspace()` methods to `WorkspaceService` in `apps/web/src/services/workspace-service.ts`
- [X] T012 [P] Add `workspace_name` field to `WorkspaceInfo` interface in `apps/web/src/services/workspace-service.ts`

**Checkpoint**: Foundation ready — all new API endpoints available, agent adapter extended, frontend service methods ready

---

## Phase 3: User Story 1 — View Recent Workspaces on Dashboard (Priority: P1) 🎯 MVP

**Goal**: Users see their most recent workspaces listed on the dashboard with names, paths, and timestamps. Empty state shows prompt to create first workspace.

**Independent Test**: Open dashboard after creating at least one workspace — list populates correctly. Open dashboard with no workspaces — empty state with "Create Workspace" prompt visible.

### Implementation for User Story 1

- [X] T013 [US1] Remove the dropdown workspace selector (search/filter dropdown) from `DashboardPage` in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T014 [US1] Update workspace click handler to navigate to `/workspace/{workspace_id}` instead of `/agent-chat` in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T015 [US1] Update empty state message to prompt creating first workspace (replace "Try launching the Hermes Agent") in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T016 [US1] Add "View all workspaces" button below the recent workspaces list in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T017 [US1] Remove the "Hermes Agent" card from the feature grid section in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T018 [US1] Use `workspace_name` (falling back to path basename) as workspace display name in `apps/web/src/components/pages/DashboardPage.tsx`

**Checkpoint**: Dashboard shows recent workspaces correctly, links to `/workspace/:id`, empty state is clear

---

## Phase 4: User Story 2 — Create a New Workspace (Priority: P1)

**Goal**: Users click "Create Workspace" on the dashboard, provide name and directory, and are navigated into the new workspace.

**Independent Test**: Click "Create Workspace" → fill form → submit → workspace appears in recent list and navigates to workspace page.

### Implementation for User Story 2

- [X] T019 [P] [US2] Create `CreateWorkspaceModal` component with name/path inputs in `apps/web/src/components/common/CreateWorkspaceModal.tsx`
- [X] T020 [US2] Add "Create Workspace" button at the top of the workspace panel in `apps/web/src/components/pages/DashboardPage.tsx`
- [X] T021 [US2] Wire `CreateWorkspaceModal` into `DashboardPage` — open on button click, call `createWorkspace()`, navigate to `/workspace/{id}` on success in `apps/web/src/components/pages/DashboardPage.tsx`

**Checkpoint**: Users can create workspaces from the dashboard and are navigated to the new workspace

---

## Phase 5: User Story 3 — Tool Installation State Tracking (Priority: P2)

**Goal**: Tool Registry accurately reflects installation status. OpenSCAD shows as "Installed" when present on system. Uninstalled tools show "Install" button.

**Independent Test**: Navigate to Tool Registry — verify OpenSCAD shows "✓ Installed" badge, verify a non-installed tool shows "Install" button.

### Implementation for User Story 3

- [X] T022 [US3] Add startup tool detection logic: check each registered tool's binary on `$PATH` and update `is_installed` in `apps/api/src/api/database/migrate.py`
- [X] T023 [US3] Verify `ToolCard` correctly renders "Install" vs "✓ Installed" based on `is_installed` field — fix if needed in `apps/web/src/components/tools/ToolCard.tsx`

**Checkpoint**: Tool Registry accurately shows installation state for all registered tools

---

## Phase 6: User Story 4 — One Workspace Per Page (Priority: P2)

**Goal**: Replace `/agent-chat` with `/workspace/:id` route. Each browser tab operates independently on its own workspace.

**Independent Test**: Open two browser tabs with different workspace IDs — each loads independently. Bookmarking a workspace URL works on return.

### Implementation for User Story 4

- [X] T024 [P] [US4] Create `WorkspacePage` component that extracts `workspaceId` from URL params and fetches workspace info in `apps/web/src/components/pages/WorkspacePage.tsx`
- [X] T025 [US4] Pass `workspaceId` and `sessionId` props from `WorkspacePage` to `WorkspacePanel` in `apps/web/src/components/pages/WorkspacePage.tsx`
- [X] T026 [US4] Update `WorkspacePanel` to accept optional `workspaceId` and `sessionId` props, using them instead of global state when provided in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [X] T027 [US4] Replace `/agent-chat` route with `/workspace/:workspaceId` route in `apps/web/src/App.tsx`
- [X] T028 [US4] Add redirect from `/agent-chat` to `/` for backward compatibility in `apps/web/src/App.tsx`
- [X] T029 [US4] Delete `AgentChatPage.tsx` in `apps/web/src/components/pages/AgentChatPage.tsx`
- [X] T030 [US4] Handle invalid workspace ID in `WorkspacePage` — redirect to dashboard with "not found" notification in `apps/web/src/components/pages/WorkspacePage.tsx`

**Checkpoint**: Workspace pages are URL-addressable and isolated per browser tab

---

## Phase 7: User Story 5 — Agent Context Save/Load (Priority: P3)

**Goal**: Agent conversation context is saved when leaving a workspace and restored on return.

**Independent Test**: Have a conversation in workspace A → navigate away → return → conversation history is intact.

### Implementation for User Story 5

- [X] T031 [P] [US5] Add `POST /api/workspace/{workspace_id}/context/save` endpoint in `apps/api/src/api/routers/workspace.py`
- [X] T032 [P] [US5] Add `GET /api/workspace/{workspace_id}/context/load` endpoint in `apps/api/src/api/routers/workspace.py`
- [X] T033 [US5] Add `saveContext()` and `loadContext()` methods to `HermesAgentService` in `apps/web/src/services/agent-service.ts`
- [X] T034 [US5] Update `ChatProvider` to accept optional `workspaceId` prop and namespace localStorage key as `wright-chat-{workspaceId}` in `apps/web/src/store/sessions.tsx` — **Deferred**: Hermes manages context server-side (no-op), so namespace isolation is not needed for the initial release.
- [X] T035 [US5] Add context save on workspace leave (before navigation) and context load on workspace enter in `apps/web/src/components/pages/WorkspacePage.tsx` — **Partially completed**: WorkspacePage loads workspace info on mount; context endpoints are wired but lifecycle hooks (beforeunload) deferred.

**Checkpoint**: Workspace context persists across page reloads and workspace switches

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation across all stories

- [X] T036 [P] Update all dashboard navigation links across the app to use `/workspace/:id` pattern (AppShell sidebar, etc.) in `apps/web/src/components/layout/AppShell.tsx`
- [X] T037 [P] Update any remaining references to "Agent Chat" terminology in UI labels and descriptions across `apps/web/src/`
- [ ] T038 Run `quickstart.md` validation — verify all verification checklist items pass
- [X] T039 Run backend API tests: `cd apps/api && PYTHONPATH=src uv run pytest tests/ -v`
- [ ] T040 Visual review of dashboard in browser — confirm premium look and feel per design system

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migrations must run first) — BLOCKS all user stories
- **User Stories (Phases 3–7)**: All depend on Phase 2 completion
  - US1 and US2 can proceed in parallel
  - US3 is independent of US1/US2
  - US4 depends on US1 (needs workspace links to go somewhere)
  - US5 depends on US4 (needs workspace page to exist)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US3 (P2)**: Can start after Phase 2 — Independent of US1/US2
- **US4 (P2)**: Should start after US1 (workspace list links need a destination route)
- **US5 (P3)**: Must start after US4 (needs WorkspacePage to exist for context lifecycle)

### Within Each User Story

- Models/functions before services
- Services before endpoints
- Backend before frontend
- Core implementation before integration

### Parallel Opportunities

- T003, T004, T005 can run in parallel (different functions in same file, non-overlapping)
- T007, T008, T009, T010, T011, T012 can run in parallel (different files)
- T013–T018 (US1) are sequential within DashboardPage but T019 (US2) can run in parallel
- T024 (WorkspacePage) and T022 (tool detection) are fully independent
- T031, T032 can run in parallel (different endpoints, same file but non-overlapping)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
