# Tasks: UI Navigation and Dashboard Redesign

**Input**: Design documents from `/specs/022-ui-navigation-redesign/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **API (backend)**: `apps/api/src/api/`
- **Web App (frontend)**: `apps/web/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema updates and initialization

- [x] T001 Add `workspace_prompt` and `git_large_file_threshold` columns to migrations in `apps/api/src/api/database/migrate.py`
- [x] T002 Execute startup database migration by running uvicorn dev server and verifying migrate.py completes successfully
- [x] T003 [P] Create Pydantic schemas for Logs and Settings response/request in `apps/api/src/api/schemas/workspace.py`, `apps/api/src/api/schemas/logs.py`, and `apps/api/src/api/schemas/settings.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Logging rotation configuration and REST routers setup

- [x] T004 Add file-based rotating logger destination to structlog config in `packages/core/src/core/logging.py`
- [x] T005 Create log line parser utility with workspace and level filters in `packages/core/src/core/workspace.py`
- [x] T006 Implement logs router endpoints for fetching system logs in `apps/api/src/api/routers/logs.py`
- [x] T007 Implement global settings router endpoints for fetching and saving configs in `apps/api/src/api/routers/settings.py`
- [x] T008 Register the new logs and settings routers in the main application lifespan/app object in `apps/api/src/api/main.py`

---

## Phase 3: User Story 1 - Modernized & Condensed Dashboard Layout (Priority: P1) 🎯 MVP

**Goal**: Modernize the landing dashboard with a condensed four-box grid layout.

**Independent Test**: Navigate to the dashboard `/`, verify the high-density grid is displayed without scrolling, and confirm news links open in a new tab.

### Implementation for User Story 1
- [x] T009 [P] [US1] Create CSS classes and grid styling layout in `apps/web/src/components/pages/DashboardPage.tsx`
- [x] T010 [US1] Implement the half-width Engineering Workspaces box with recent and search capabilities in `apps/web/src/components/pages/DashboardPage.tsx`
- [x] T011 [US1] Implement the Agent Status box rendering Hermes connection, active task queue, and socket connection state in `apps/web/src/components/pages/DashboardPage.tsx`
- [x] T012 [US1] Implement the News & Resources box with external blog/substack links targeting blank tabs in `apps/web/src/components/pages/DashboardPage.tsx`
- [x] T013 [US1] Implement the System Activity & Telemetry box displaying database stats in `apps/web/src/components/pages/DashboardPage.tsx`

---

## Phase 4: User Story 2 - Global Sidebar Re-organization & Application Logs (Priority: P1)

**Goal**: Update main sidebar navigation and add Logs and Settings routes and pages.

**Independent Test**: Confirm sidebar navigation works correctly and the `/logs` route opens the log list with filter dropdowns.

### Implementation for User Story 2
- [x] T014 [US2] Update sidebar item list and icons in `apps/web/src/components/layout/Sidebar.tsx`
- [x] T015 [US2] Map router routes for `/logs` and `/settings` in `apps/web/src/App.tsx`
- [x] T016 [US2] Create new Logs page featuring workspace dropdown, level dropdown, and keyword filter elements in `apps/web/src/components/pages/LogsPage.tsx`
- [x] T017 [US2] Create new Global Settings page for LLM configuration, themes, and API key management in `apps/web/src/components/pages/SettingsPage.tsx`

---

## Phase 5: User Story 4 - Workspace Inner Activity Sidebar (Priority: P1)

**Goal**: Redesign the workspace panel activity buttons and sidebar switching.

**Independent Test**: Navigate to a workspace session, switch sidebar tabs via activity buttons, and verify the main editor area remains untouched.

### Implementation for User Story 4
- [x] T018 [P] [US4] Add custom SVGs for Back, Docs, Settings, and MCP tools in `apps/web/src/components/common/Icons.tsx`
- [x] T019 [US4] Implement the vertical button list containing Back, Explorer, MCP Tool, Git, Workspace Settings, and Docs/Tutorials in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T020 [US4] Add hover tooltips to all buttons in the workspace sidebar row in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T021 [US4] Implement activity click toggle logic so selecting sidebar buttons updates sidebar views without reloading editor views in `apps/web/src/components/chat/WorkspacePanel.tsx`

---

## Phase 6: User Story 3 - Debugging Logs with Hermes (Priority: P2)

**Goal**: Allow right-click log debugging using a side drawer with Hermes chat.

**Independent Test**: Select a range of log lines, right-click, select Send to Hermes, and verify the chat drawer slides open populated with the log lines.

### Implementation for User Story 3
- [x] T022 [US3] Add right-click cursor highlight tracking and context menu in `apps/web/src/components/pages/LogsPage.tsx`
- [x] T023 [US3] Implement sliding drawer container panel on the right side of `apps/web/src/components/pages/LogsPage.tsx`
- [x] T024 [US3] Connect selected text to a new Hermes chat session composer inside the sliding drawer in `apps/web/src/components/pages/LogsPage.tsx`

---

## Phase 7: User Story 5 - Workspace settings & Prompt Context (Priority: P2)

**Goal**: Configure and persist workspace settings and workspace-specific prompts.

**Independent Test**: Update the workspace prompt, save it, and verify the prompt is loaded during agent sessions.

### Implementation for User Story 5
- [x] T025 [US5] Implement prompt input text area and git threshold parameters in the Settings sidebar tab in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T026 [US5] Update configuration update/retrieval handlers in the API router `apps/api/src/api/routers/workspace.py`
- [x] T027 [US5] Read custom workspace prompts and inject them into system prompts in the Hermes sync manager `apps/api/src/api/services/hermes_sync.py`

---

## Phase 8: User Story 6 - Compact MCP Tool Selector (Priority: P2)

**Goal**: Display active MCP tools compactly inside the workspace sidebar.

**Independent Test**: Click MCP Tools in the activity bar, and verify at least 5 tools are displayed compactly.

### Implementation for User Story 6
- [x] T028 [P] [US6] Design compact list styling to show MCP tools compactly in the workspace sidebar in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T029 [US6] Retrieve active/available workspace MCP tools and render them in the sidebar in `apps/web/src/components/chat/WorkspacePanel.tsx`

---

## Phase 9: User Story 7 - Advanced Git Panel with Large File Detection (Priority: P2)

**Goal**: Provide branching/merge/pull controls and highlight oversized files in the Git panel.

**Independent Test**: Place an oversized file in the workspace, open the Git panel, and verify the warning badge appears.

### Implementation for User Story 7
- [x] T030 [US7] Implement branch creation dialog, merge, and pull operations in the Git panel in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T031 [US7] Add file size warning check to Git status payload generation in `apps/api/src/api/routers/workspace.py`
- [x] T032 [US7] Render warning badge for oversized files in the Git list in `apps/web/src/components/chat/WorkspacePanel.tsx`

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Testing, verification, and visual polish

- [x] T033 Run visual verification of dashboard density and tooltip alignments across standard viewports
- [x] T034 Add Playwright integration tests for new routes and layouts in `tests/ui-integration/navigation-redesign.spec.ts`
- [x] T035 Complete documentation updates and verify all new elements possess correct `data-testid` attributes

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Core migrations. No dependencies.
- **Foundational (Phase 2)**: Database migrations must run before endpoints register.
- **User Stories (Phase 3+)**: Depend on Setup and Foundational completions.
- **Polish (Final Phase)**: Runs after all user stories are implemented.

### Parallel Opportunities
- T003 (Schemas) can be written in parallel with T001 (Database migrations).
- T009 (Dashboard layout) can be written in parallel with backend endpoints.
- Workspace buttons icons (T018) can be added in parallel with layout work.
- MCP Tools display styling (T028) can run in parallel with workspace panel logic.
