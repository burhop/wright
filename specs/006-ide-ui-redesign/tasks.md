# Tasks: IDE UI Redesign

**Input**: Design documents from `/specs/006-ide-ui-redesign/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included to verify functional requirements, including pytest integrations and component tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend API: `apps/api/`
- Core Package: `packages/core/`
- Web Frontend: `apps/web/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure verification

- [x] T001 Verify active development environment by launching backend server in `apps/api` and web frontend in `apps/web`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema migrations and workspace class methods that MUST be completed before any user story UI implementation begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Modify `apps/api/src/api/database/migrate.py` to add `enabled_tools` column to `engineering_workspaces` table schema
- [x] T003 Implement `enabled_tools` getter and updater logic in `packages/core/src/core/workspace.py`
- [x] T004 Implement file content write-back helper method in `packages/core/src/core/workspace.py`

**Checkpoint**: Foundation ready - database schemas and core helpers ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Multi-Panel Activity Bar Layout (Priority: P1) 🎯 MVP

**Goal**: Implement the VS Code-like tripartite console layout including Activity Bar, Left Sidebar, central Tabbed View, and Right Agent Sidebar.

**Independent Test**: Drag sidebar borders to resize, collapse/expand panels, and verify that the layout adjusts dynamically using Vitest and local browser checks.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create layout visibility states and navigation types in `apps/web/src/store/types.ts`
- [x] T006 [US1] Restructure main tripartite CSS grid layout and style definitions in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T007 [US1] Implement Activity Bar panel select click handlers and collapse logic in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T008 [P] [US1] Implement collapsible Right Agent Console drawer controls and collapse triggers in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T009 [US1] Write Vitest component assertions for panel toggle states in `apps/web/src/components/chat/WorkspacePanel.test.tsx`

**Checkpoint**: At this point, the outer IDE layout structure and collapse states should be fully functional and testable.

---

## Phase 4: User Story 2 - Extensible File Tab Viewers (Priority: P1)

**Goal**: Support list of open file tabs in the central area, dispatching specialized view components for STL, images, and text/code with auto-save.

**Independent Test**: Double-click files in tree, verify separate tab renders, and edit code tab to assert auto-save PUT request persists to disk.

### Implementation for User Story 2

- [x] T010 [P] [US2] Implement PUT `/api/workspace/files/content` API endpoint in `apps/api/src/api/routers/workspace.py`
- [x] T011 [US2] Implement frontend file content saving method `saveFileContent` in `apps/web/src/services/workspace-service.ts`
- [x] T012 [P] [US2] Create tab header list view with tab close actions in `apps/web/src/components/common/EditorTabs.tsx`
- [x] T013 [P] [US2] Create visual image previewer tab component in `apps/web/src/components/common/ImagePreviewer.tsx`
- [x] T014 [US2] Create editable text/code editor with syntax highlighting and auto-save on blur in `apps/web/src/components/common/FileEditor.tsx`
- [x] T015 [US2] Wire editor tabs dispatcher logic to render specific viewer tabs in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T016 [US2] Write backend integration tests for PUT content endpoint in `apps/api/tests/test_workspace_api.py`

**Checkpoint**: Central editor tabs dispatcher is functional. Open files render in tabs, and text edits are saved to disk.

---

## Phase 5: User Story 3 - Workspace-Specific Tools Marketplace (Priority: P2)

**Goal**: Toggle workspace-specific MCP tools/servers in Left Sidebar marketplace drawer and persist settings in SQLite.

**Independent Test**: Enable/disable tools in the Tools sidebar, and verify update persists to database.

### Implementation for User Story 3

- [x] T017 [P] [US3] Implement GET `/api/workspace/tools` and POST `/api/workspace/tools/toggle` in `apps/api/src/api/routers/workspace.py`
- [x] T018 [US3] Implement workspace tools API methods `getWorkspaceTools` and `toggleWorkspaceTool` in `apps/web/src/services/workspace-service.ts`
- [x] T019 [P] [US3] Create MCP server/tool toggle card components in `apps/web/src/components/common/ToolsMarketplace.tsx`
- [x] T020 [US3] Mount and integrate ToolsMarketplace view inside Left Sidebar drawer in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T021 [US3] Write unit/integration tests asserting GET and POST tools toggle endpoints in `apps/api/tests/test_workspace_api.py`

**Checkpoint**: All user stories complete. Tool configurations are session-specific and persist in SQLite.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T022 Document workspace storage schemas and configuration details in `specs/006-ide-ui-redesign/quickstart.md`
- [x] T023 Ensure all interactive UI elements have distinct `data-testid` attributes
- [x] T024 Perform smoke verification testing for tab switching responsiveness and panel toggle times
