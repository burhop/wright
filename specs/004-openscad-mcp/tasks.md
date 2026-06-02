# Tasks: OpenSCAD MCP & 3D Visualization

**Input**: Design documents from `/specs/004-openscad-mcp/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Includes test tasks for API and component validation per verification plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Includes exact file paths in descriptions.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration and database setup

- [x] T001 Configure three and @types/three dependencies in `apps/web/package.json`
- [x] T002 Initialize OpenSCAD server seeding in `apps/api/src/api/database/migrate.py`
- [x] T003 [P] Create headless execution wrapper script in `scripts/openscad-headless.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend file access services and environment self-configuration

**⚠️ CRITICAL**: Must be completed before starting any user story implementations

- [x] T004 Implement dynamic wrapper environment configuration in `apps/api/src/api/config.py`
- [x] T005 [P] Implement `WorkspaceManager` core file indexing in `packages/core/src/core/workspace.py`
- [x] T006 [P] Create workspace file listing and serving API router in `apps/api/src/api/routers/workspace.py`
- [x] T007 Mount workspace API routes in backend lifespan/startup in `apps/api/src/api/main.py`
- [x] T008 [P] Implement workspace service HTTP client calls in `apps/web/src/services/workspace-service.ts`

**Checkpoint**: Foundation ready - workspace API is active and frontend client is wired up.

---

## Phase 3: User Story 1 - Register and Execute OpenSCAD MCP Server (Priority: P1) 🎯 MVP

**Goal**: Expose local OpenSCAD compile/render capability via MCP stdio wrapper server to LLM agent

**Independent Test**: Call OpenSCAD MCP tools to generate STL files, verifying they write successfully to the local workspace.

### Tests for User Story 1
- [x] T009 [P] [US1] Create backend unit tests verifying workspace listings and file content reads in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 1
- [x] T010 [US1] Complete directories traversal sanitization in `packages/core/src/core/workspace.py`
- [x] T011 [US1] Complete file stream response endpoint in `apps/api/src/api/routers/workspace.py`
- [x] T012 [US1] Run database migrations and verify OpenSCAD server registration status in backend SQLite database

**Checkpoint**: User Story 1 is fully functional. OpenSCAD MCP is active and the agent can write models to workspace.

---

## Phase 4: User Story 2 - Interactive 3D Model Viewport (Priority: P1)

**Goal**: Load and render workspace STL meshes interactively in the web browser using WebGL

**Independent Test**: Click an STL file in the browser tree and verify it displays inside the 3D preview pane.

### Tests for User Story 2
- [x] T013 [P] [US2] Create Vitest tests ensuring WebGL canvas mounts correctly in `apps/web/tests/ThreeDViewer.spec.tsx`

### Implementation for User Story 2
- [x] T014 [US2] Create 3D mesh rendering component `apps/web/src/components/common/ThreeDViewer.tsx` using Three.js and STLLoader
- [x] T015 [US2] Implement tab selector switching between File Tree and 3D Preview in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T016 [US2] Embed `ThreeDViewer` and download binary data via workspace service in `apps/web/src/components/chat/WorkspacePanel.tsx`

**Checkpoint**: User Story 2 is complete. Interactive 3D STL visualization is working in the workspace sidepanel.

---

## Phase 5: User Story 3 - Real-Time Canvas Auto-Refresh (Priority: P2)

**Goal**: Auto-update the 3D viewer scene dynamically when the agent updates model geometry files

**Independent Test**: Overwrite an STL file on disk and verify the 3D viewport canvas automatically reloads.

### Implementation for User Story 3
- [x] T017 [US3] Implement file modified timestamp polling loop in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T018 [US3] Add cleanup logic to cancel timer when selected file closes or panel unmounts in `apps/web/src/components/chat/WorkspacePanel.tsx`

**Checkpoint**: Live design loop is complete. Workspace mesh refreshes on agent iteration.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Testing, formatting, and optimization

- [x] T019 Run all backend pytest tests in `apps/api/tests/`
- [x] T020 Run all frontend vitest tests in `apps/web/`
- [x] T021 Validate setup instructions in `specs/004-openscad-mcp/quickstart.md`
- [x] T022 Run linters and formatting commands across all modified monorepo files

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup - Blocks User Stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion. US1 and US2 can run in parallel. US3 depends on US2 completion.
- **Polish (Phase 6)**: Runs after all stories are completed.

### Parallel Opportunities
- Setup tasks `T001`, `T002`, `T003` are parallelizable.
- Core helpers `T005` and router `T006` are parallelizable.
- Story tests `T009` and `T013` are parallelizable.

---

## Parallel Example: User Story 1
```bash
# Launch test and implementation tasks in parallel:
Task: "Create backend unit tests verifying workspace listings in apps/api/tests/test_workspace_api.py"
Task: "Complete directories traversal sanitization in packages/core/src/core/workspace.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Setup and Foundational APIs.
2. Activate and test OpenSCAD MCP tools in chat.
3. Validate STL exports write correctly to workspace.

### Incremental Delivery
1. Foundation setup completed.
2. Add STL loading + Three.js rendering (US2).
3. Add automatic reloading check (US3).
