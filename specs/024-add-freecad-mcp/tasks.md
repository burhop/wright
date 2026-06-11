# Tasks: FreeCAD MCP Server Integration

**Input**: Design documents from `/specs/024-add-freecad-mcp/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Install FreeCAD stable via snap on host (GB10) command line
- [x] T002 Verify FreeCAD snap installation version on host using /snap/bin/freecad.cmd

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Update docker/Dockerfile to install and extract FreeCAD aarch64 AppImage
- [x] T004 Run docker-compose build agent command to verify thick Docker base image build

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Enable FreeCAD MCP Server in Tool Registry (Priority: P1) 🎯 MVP

**Goal**: Register FreeCAD MCP server in database and make it installable in Tool Registry UI.

**Independent Test**: Navigate to `/tool-registry`, click "Install" on the FreeCAD card, and verify it registers tools in `mcp_tools`.

### Implementation for User Story 1

- [x] T005 [P] [US1] Seed FreeCAD Engineering catalog entry in apps/api/src/api/database/migrate.py
- [x] T006 [US1] Run database migrations in apps/api/src/api/database/migrate.py to update schema and seed state.db
- [x] T007 [US1] Toggle install on FreeCAD card in apps/web/src/components/pages/ToolRegistryPage.tsx and verify tools are populated in mcp_tools table

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Headless FreeCAD Execution in Workspace Sessions (Priority: P2)

**Goal**: Allow agent workspace sessions to run FreeCAD tools headlessly and output results to the active workspace.

**Independent Test**: Run `step_to_stl` tool in a mock workspace session and verify output file is written to the active workspace.

### Implementation for User Story 2

- [x] T008 [US2] Verify headless CAD operations via freecadcmd execution in apps/api/src/api/routers/workspace.py
- [x] T009 [US2] Ensure all FreeCAD output mesh files are written directly into workspace path in apps/api/src/api/routers/workspace.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T010 [P] Document setup and verification steps in specs/024-add-freecad-mcp/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Seed catalog entry:
Task: "Seed FreeCAD Engineering catalog entry in apps/api/src/api/database/migrate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Each story adds value without breaking previous stories
