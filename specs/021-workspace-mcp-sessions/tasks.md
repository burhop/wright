# Tasks: Workspace MCP & Session Isolation

**Input**: Design documents from `/specs/021-workspace-mcp-sessions/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic validation of the workspace state

- [x] T001 Verify database connection and dev environment run correctly (no new files)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model updates that must be complete before any user story can be implemented

- [x] T002 Update Pydantic schemas in apps/api/src/api/schemas/workspace.py to make `local_path` optional and support `enabled_tools` serialization

---

## Phase 3: User Story 1 - Create Named Workspace & Auto-Start Chatting (Priority: P1)

**Goal**: Support human-readable sanitized directory folders under the workspace parent folder and automatically spin up a chat session on workspace creation.

**Independent Test**: Create a workspace from the dashboard UI and verify it immediately redirects to the active chat screen and created the matching directory under `~/workspace/`.

### Implementation for User Story 1

- [x] T003 [P] [US1] Implement display name sanitization helper function in packages/core/src/core/workspace.py
- [x] T004 [US1] Update `create_workspace_endpoint` in apps/api/src/api/routers/workspace.py to sanitize workspace name, raise HTTP 400 if duplicate folder or DB record exists, create directory, run WorkspaceManager, create session, and save
- [x] T005 [P] [US1] Update workspace creation modal form in apps/web/src/components/common/CreateWorkspaceModal.tsx to only request name and hide/auto-generate path based on the new API contract

---

## Phase 4: User Story 2 - Toggle MCP Tools Inside Active Workspace Session (Priority: P1)

**Goal**: Allow users to enable or disable installed MCP servers as tools for all sessions within the active workspace.

**Independent Test**: Enable an installed tool in the sidebar's tools tab, and verify the agent's system prompt or tool checklist is updated dynamically in subsequent chats.

### Implementation for User Story 2

- [x] T006 [US2] Update `/tools/toggle` route handler in apps/api/src/api/routers/workspace.py to write to SQLite and reload active agent tool schemas
- [x] T007 [P] [US2] Update frontend Marketplace rendering in apps/web/src/components/chat/WorkspacePanel.tsx to bind tool state to the workspace

---

## Phase 5: User Story 3 - Existing Workspace Last-Session Restore & Session List (Priority: P2)

**Goal**: Automatically restore the last active session when returning to a workspace and display only sessions that belong to the active workspace.

**Independent Test**: Verify returning to a workspace loads the correct active session, and that only sessions matching this workspace path are selectable in the switcher list.

### Implementation for User Story 3

- [ ] T008 [US3] Add `workspace_id` filtering query parameter to `GET /api/agent/sessions` in apps/api/src/api/routers/agent.py to filter sessions from agent backend by workspace path
- [ ] T009 [US3] Update `/api/workspace/activate` in apps/api/src/api/routers/workspace.py to check session existence, fall back to other workspace sessions, or create a new session
- [ ] T010 [P] [US3] Implement `POST /api/workspace/by-id/{workspace_id}/session` in apps/api/src/api/routers/workspace.py to update the `session_id` pointer in SQLite
- [ ] T011 [P] [US3] Update `listSessions` service layer method in apps/web/src/services/agent-service.ts and state hydration in apps/web/src/store/sessions.tsx to pass `workspaceId`
- [ ] T012 [US3] Update session list rendering and switcher interaction in apps/web/src/components/chat/WorkspacePanel.tsx to list workspace sessions and invoke the update pointer endpoint on switch

---

## Phase 6: User Story 4 - Workspace Context Propagation to LLM Agents (Priority: P1)

**Goal**: Propagate the absolute workspace path to the LLM agent adapter so it can work with files in the workspace directory.

**Independent Test**: Prompt the agent to list files or save a design, and confirm it reads/writes from the correct folder.

### Implementation for User Story 4

- [ ] T013 [US4] Verify packages/agent_adapters/src/agent_adapters/hermes.py maps workspace context to the agent backend correctly during session creation
- [ ] T014 [US4] Ensure chat start routes in apps/api/src/api/routers/agent.py properly pass workspace parameters to the adapter

---

## Phase 7: User Story 5 - Automated Clean Up of Test Workspaces (Priority: P2)

**Goal**: Clean out all previous test workspaces and records.

**Independent Test**: Run the cleanup script and verify the SQLite database and `~/workspace/` directory are empty.

### Implementation for User Story 5

- [ ] T015 [US5] Create python cleanup script scripts/cleanup-workspaces.py to truncate tables `engineering_workspaces`, `agent_contexts`, and `chat_messages` and empty directories under `~/workspace/`
- [ ] T016 [P] [US5] Configure executable permissions or add package runner target for scripts/cleanup-workspaces.py in package.json

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, testing, and final documentation

- [ ] T017 [P] Execute backend integration tests using pytest to verify workspace API routes
- [ ] T018 [P] Run Playwright UI integration tests to verify frontend pages and session list integrity
- [ ] T019 [P] Update documentation and quickstart instructions in README.md

---

## Dependencies & Execution Order

### Phase Dependencies
1. **Setup (Phase 1)**: Can start immediately.
2. **Foundational (Phase 2)**: Depends on Setup completion.
3. **User Stories (Phases 3–7)**: Depend on Foundational phase completion.
   - User Story 1 (P1) is the MVP and must be completed first.
   - User Stories 2 (P1), 3 (P2), 4 (P1), and 5 (P2) can proceed in parallel once the core workspace model and creation flow (User Story 1) are complete.
4. **Polish (Phase 8)**: Depends on all user stories being implemented.

### Parallel Opportunities
- T003 (core logic) and T005 (frontend modal) can be worked on in parallel with T004 (router).
- Tool toggle logic (US2) and session restoration/switcher logic (US3) are independent and can be implemented in parallel.
- The cleanup script (US5) is completely independent and can be implemented in parallel.

---

## Parallel Example: User Story 1
```bash
# Launch workspace creation logic and frontend modal in parallel:
Task: "Update workspace creation modal form in apps/web/src/components/common/CreateWorkspaceModal.tsx"
Task: "Implement display name sanitization helper function in packages/core/src/core/workspace.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)
1. Complete Setup and Foundational.
2. Implement sanitization, folder creation, and auto-session starting (User Story 1).
3. Verify that creating a workspace from the dashboard redirects to the chat workspace page with an active session.

### Incremental Delivery
1. Setup + Foundational + User Story 1 -> Workspace creation MVP.
2. User Story 4 -> Workspace path context propagated to agents.
3. User Story 3 -> Last active session restore and switcher list.
4. User Story 2 -> Tool synchronization in workspace.
5. User Story 5 -> Cleanup tool.
