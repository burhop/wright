# Tasks: Workspace Session Model

**Input**: Design documents from `/specs/040-workspace-session-model/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/workspace-session-api.md, quickstart.md

**Tests**: Required for this feature because the bug crosses persistence, API behavior, MCP status, and frontend state.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare migration and test surfaces.

- [X] T001 Review current workspace/session persistence helpers in `packages/core/src/core/workspace.py`
- [X] T002 Review current workspace API/session routes in `apps/api/src/api/routers/workspace.py` and `apps/api/src/api/routers/agent.py`
- [X] T003 Review current frontend workspace/session state flow in `apps/web/src/components/chat/WorkspacePanel.tsx`, `apps/web/src/store/sessions.tsx`, and services

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the storage and service model that all stories depend on.

- [X] T004 Add SQLite migration for `workspace_agent_sessions` in `apps/api/src/api/database/migrate.py`
- [X] T005 Add workspace session association helpers in `packages/core/src/core/workspace.py`
- [X] T006 Update workspace service models in `packages/workspace_service/src/workspace_service/models.py`
- [X] T007 Update workspace service orchestration in `packages/workspace_service/src/workspace_service/service.py`
- [X] T008 [P] Add backend persistence tests for migration and association helpers in `apps/api/tests/test_workspace_api.py`

**Checkpoint**: Storage and service layer can represent one workspace with many sessions.

---

## Phase 3: User Story 1 - Continue Sessions Within A Workspace (Priority: P1) MVP

**Goal**: Users can create, list, and select multiple sessions in one workspace without overwriting workspace identity.

**Independent Test**: Create two sessions for one workspace and verify both remain associated with the workspace after refresh/listing.

### Tests for User Story 1

- [X] T009 [P] [US1] Add API regression tests for workspace-scoped session list/create/select in `apps/api/tests/test_workspace_api.py`
- [X] T010 [P] [US1] Add frontend regression test for workspace-scoped session list in `apps/web/tests/WorkspacePanelSessions.spec.tsx`

### Implementation for User Story 1

- [X] T011 [US1] Add workspace session API schemas in `apps/api/src/api/schemas/workspace.py`
- [X] T012 [US1] Add workspace session endpoints in `apps/api/src/api/routers/workspace.py`
- [X] T013 [US1] Update agent session creation/listing routes to maintain workspace associations in `apps/api/src/api/routers/agent.py`
- [X] T014 [US1] Update frontend workspace and agent services for workspace session APIs in `apps/web/src/services/workspace-service.ts` and `apps/web/src/services/agent-service.ts`
- [X] T015 [US1] Update chat session store to refresh sessions by workspace without relying on localStorage-only ownership in `apps/web/src/store/sessions.tsx`

**Checkpoint**: User Story 1 should be fully functional and independently testable.

---

## Phase 4: User Story 2 - Keep MCP Tools Workspace-Scoped (Priority: P1)

**Goal**: MCP status and enablement are evaluated by workspace identity and inherited by all sessions in that workspace.

**Independent Test**: Configure different MCP tools in two workspaces and verify each workspace reports only its own required tools.

### Tests for User Story 2

- [X] T016 [P] [US2] Add backend tests for workspace-scoped tool list/toggle/status in `apps/api/tests/test_workspace_api.py`
- [X] T017 [P] [US2] Add frontend test that MessageComposer requests MCP status by workspace in `apps/web/tests/WorkspacePanelSessions.spec.tsx`

### Implementation for User Story 2

- [X] T018 [US2] Add workspace-id tool and MCP status endpoints in `apps/api/src/api/routers/workspace.py`
- [X] T019 [US2] Update workspace service tool helpers to accept workspace identity in `packages/workspace_service/src/workspace_service/service.py`
- [X] T020 [US2] Update gateway/activation helpers to resolve active workspace context correctly in `packages/core/src/core/workspace.py` and `apps/api/src/api/routers/gateway.py`
- [X] T021 [US2] Update frontend services and MessageComposer to use workspace MCP status in `apps/web/src/services/workspace-service.ts` and `apps/web/src/components/chat/MessageComposer.tsx`

**Checkpoint**: User Story 2 should be functional without cross-workspace MCP bleed.

---

## Phase 5: User Story 3 - Recover Existing Installations Safely (Priority: P2)

**Goal**: Existing local databases migrate one-session workspace data into workspace session associations safely.

**Independent Test**: Start with legacy workspace rows and verify associations are populated after migration.

### Tests for User Story 3

- [X] T022 [P] [US3] Add migration test for legacy session backfill in `apps/api/tests/test_workspace_api.py`

### Implementation for User Story 3

- [X] T023 [US3] Backfill workspace session associations from legacy workspace rows in `apps/api/src/api/database/migrate.py`
- [X] T024 [US3] Add recovery behavior for missing agent sessions in `packages/workspace_service/src/workspace_service/service.py`

**Checkpoint**: Existing installations retain workspace/session/tool state.

---

## Phase 6: User Story 4 - Preserve Workspace Context During Session Actions (Priority: P2)

**Goal**: Session actions do not reset the middle panel or workspace layout.

**Independent Test**: Open a file/viewer tab, switch sessions, and verify only chat transcript changes.

### Tests for User Story 4

- [X] T025 [P] [US4] Add frontend regression test for no viewer reset on session switch in `apps/web/tests/WorkspacePanelSessions.spec.tsx`

### Implementation for User Story 4

- [X] T026 [US4] Key workspace layout and reset logic by workspace id instead of session id in `apps/web/src/components/chat/WorkspacePanel.tsx`
- [X] T027 [US4] Ensure WorkspacePage does not rewrite workspace state during chat-only session selection in `apps/web/src/components/pages/WorkspacePage.tsx`

**Checkpoint**: Session switching updates chat only.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Validate feature end to end.

- [X] T028 Run backend focused tests for workspace/session/MCP behavior in `apps/api/tests/test_workspace_api.py`
- [X] T029 Run frontend focused tests in `apps/web/tests/WorkspacePanelSessions.spec.tsx`
- [X] T030 Run typecheck/lint checks relevant to changed frontend files
- [X] T031 Run quickstart validation steps from `specs/040-workspace-session-model/quickstart.md` as far as possible locally
- [X] T032 Update task checkboxes in `specs/040-workspace-session-model/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational and is MVP.
- **US2 (Phase 4)**: Depends on Foundational and may proceed after US1 service/API patterns are in place.
- **US3 (Phase 5)**: Depends on Foundational.
- **US4 (Phase 6)**: Depends on US1 frontend session API changes.
- **Polish**: Depends on selected user stories being complete.

### Parallel Opportunities

- T008 can be written while service helper implementation is in progress after schema direction is known.
- T009/T010 can be drafted in parallel.
- T016/T017 can be drafted in parallel.
- T022 and T025 touch different layers and can be prepared independently.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 so workspace sessions are no longer overwritten.
3. Validate backend and frontend session association behavior.
4. Complete US2 because MCP correctness is part of the same user-facing failure.

### Incremental Delivery

1. Storage association and migration.
2. Workspace session APIs and frontend use.
3. Workspace-scoped MCP APIs and frontend use.
4. Legacy recovery and UI reset polish.
5. Focused test validation.
