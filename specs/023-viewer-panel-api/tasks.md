# Tasks: Pluggable Viewer Panel API

**Input**: Design documents from `/specs/023-viewer-panel-api/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `apps/api/src/api/`, `apps/web/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure folders under `apps/web/src/services/viewer-panel/`
- [x] T002 Configure tsconfig paths and initial exports in `apps/web/src/services/viewer-panel/index.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Define standard interfaces (`FileDescriptor`, `ViewerDocument`, `PanelHost`, `ViewerProvider`) in `apps/web/src/services/viewer-panel/types.ts`
- [x] T004 Create `ViewerRegistry` class with register and resolution algorithms in `apps/web/src/services/viewer-panel/registry.ts`
- [x] T005 Create base React context/hook `useViewerPanel` for managing open tabs/documents in `apps/web/src/store/viewer.tsx`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Custom Viewer Registration & Discovery (Priority: P1) 🎯 MVP

**Goal**: Register custom viewer providers and resolve the best matching choice.

**Independent Test**: Register a mock `.step` viewer and verify matching resolution.

### Implementation for User Story 1

- [x] T006 [P] [US1] Create unit tests for `ViewerRegistry` in `apps/web/src/services/viewer-panel/__tests__/registry.test.ts`
- [x] T007 [US1] Implement matching resolution rules (extension, mimeType, pattern) in `apps/web/src/services/viewer-panel/registry.ts`
- [x] T008 [P] [US1] Create generic Fallback Plain Text Viewer provider in `apps/web/src/services/viewer-panel/providers/text-provider.ts`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently


---

## Phase 4: User Story 2 - Viewer Tab Opening & Lifecycle Management (Priority: P1)

**Goal**: Open selected files in tabs and manage their active/visibility lifecycles.

**Independent Test**: Click a `.step` file and check that a tab is mounted and disposed on close.

### Implementation for User Story 2

- [x] T009 [US2] Implement `PanelHost` React wrapper and message listener manager in `apps/web/src/services/viewer-panel/panel-host.ts`
- [x] T010 [US2] Create center pane `EditorTabs` UI component rendering tab lists and close buttons in `apps/web/src/components/chat/EditorTabs.tsx`
- [x] T011 [US2] Integrate `EditorTabs` and mounting DOM containers inside `apps/web/src/components/chat/WorkspacePanel.tsx`
- [x] T012 [P] [US2] Implement WebGL 3D graphics viewer provider adapter with Three.js scene setup and explicit context disposal in `apps/web/src/services/viewer-panel/providers/threed-provider.ts`
- [x] T013 [P] [US2] Implement Monaco/CodeMirror code editor provider adapter with editor teardown in `apps/web/src/services/viewer-panel/providers/code-provider.ts`
- [x] T014 [P] [US2] Implement PDF.js viewer provider adapter mounting PDF contents in `apps/web/src/services/viewer-panel/providers/pdf-provider.ts`
- [x] T015 [P] [US2] Create Playwright integration tests verifying mounting and tab opening of 3D, code, and PDF viewers in `tests/ui-integration/viewer-panel-lifecycle.spec.ts`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Persistence & Transaction History (Dirty Tracking / Undo-Redo) (Priority: P2)

**Goal**: Support dirty tracking and undo/redo stacks per document.

**Independent Test**: Edit text, verify dirty badge, trigger undo, check save is persisted.

### Implementation for User Story 3

- [x] T016 [US3] Implement document change event dispatchers and global undo/redo stack manager in `apps/web/src/store/viewer.tsx`
- [x] T017 [P] [US3] Add save, revert, and backup methods to `apps/web/src/services/viewer-panel/providers/code-provider.ts` and `threed-provider.ts`
- [x] T018 [US3] Implement backend FastAPI router endpoints for file save and temporary backup in `apps/api/src/api/routers/workspace.py`
- [x] T019 [P] [US3] Add Playwright integration test verifying dirty indicators, undo/redo keystrokes, and save endpoint triggers in `tests/ui-integration/viewer-panel-persistence.spec.ts`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Unresponsive Panel Watchdog & Resource Isolation (Priority: P2)

**Goal**: Heartbeat pings, unresponsive UI detection overlays, and resource isolation.

**Independent Test**: Simulate a hung thread and check that the watchdog overlay appears after 5s.

### Implementation for User Story 4

- [x] T020 [US4] Implement heartbeat watchdog timer inside `PanelHost` in `apps/web/src/services/viewer-panel/panel-host.ts`
- [x] T021 [US4] Design warning reload/close dialog overlay inside `apps/web/src/components/chat/WorkspacePanel.tsx` UI when unresponsive state is triggered
- [x] T022 [P] [US4] Implement isolated `IframeViewer` provider with sandboxed properties and CSP header rules in `apps/web/src/services/viewer-panel/providers/iframe-provider.ts`
- [x] T023 [P] [US4] Add Playwright test checking watchdog heartbeat timeouts and sandbox iframe isolation in `tests/ui-integration/viewer-panel-watchdog.spec.ts`

---

## Phase 7: User Story 5 - Developer Tools & Inspector Overlay (Priority: P3)

**Goal**: Visual diagnostic inspector panel for testing.

**Independent Test**: Click Inspector button and check metadata overlay.

### Implementation for User Story 5

- [x] T024 [US5] Implement DevTools inspector overlay UI panel in `apps/web/src/components/chat/ViewerInspector.tsx`
- [x] T025 [US5] Render inspector button and link triggers inside `apps/web/src/components/chat/WorkspacePanel.tsx` panel shell

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T026 Code cleanup and format checks across all updated components
- [x] T027 Run quickstart.md validation to ensure everything works flawlessly

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all registry and mock providers for User Story 1 together:
Task: "Create unit tests for ViewerRegistry in apps/web/src/services/viewer-panel/__tests__/registry.test.ts"
Task: "Create generic Fallback Plain Text Viewer provider in apps/web/src/services/viewer-panel/providers/text-provider.ts"
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
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently
