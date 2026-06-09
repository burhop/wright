# Tasks: Chat Composer Commands

**Input**: Design documents from `/specs/020-chat-composer-commands/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Path Conventions

- **Web app**: `apps/api/src/`, `apps/web/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize `.vault` local directory checking utilities if needed (or dynamically handled in the router)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure and API clients that MUST be complete before ANY user story can be implemented

- [x] T002 Implement `POST /api/vault/upload` and `GET /api/vault/files/{file_id}` in `apps/api/src/api/routers/vault.py`
- [x] T003 Include `vault_router` in `apps/api/src/api/main.py`
- [x] T004 Implement `GET /api/agent/commands` in `apps/api/src/api/routers/agent.py`
- [x] T005 Add `uploadFile` and `getCommands` to `apps/web/src/services/agent-service.ts`

**Checkpoint**: Foundation ready - API routes and client service methods are available for the UI components.

---

## Phase 3: User Story 1 - Add Context via Action Menu (Priority: P1) 🎯 MVP

**Goal**: Users need a visual entry point to add context, media, or run agent commands via a "+" button next to the chat input.

**Independent Test**: Click "+" button and verify a popup menu appears with options.

### Implementation for User Story 1

- [x] T006 [US1] Create a "+" action button inside `apps/web/src/components/chat/MessageComposer.tsx` adjacent to the input field.
- [x] T007 [US1] Create floating context menu component triggered by the "+" button to display static actions like "Add Context" and "Media".

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Keyboard-Driven Auto-Complete (Priority: P1)

**Goal**: Typing `@` or `/` in the input should trigger a dynamic autocomplete popup.

**Independent Test**: Type `/` and verify the correct command menu appears.

### Implementation for User Story 2

- [x] T008 [P] [US2] Create `CommandMenu` component in `apps/web/src/components/chat/CommandMenu.tsx` to render command autocomplete lists.
- [x] T009 [US2] Fetch commands via `agentService.getCommands` on component mount/session load inside `apps/web/src/components/chat/WorkspacePanel.tsx` or `MessageComposer.tsx`.
- [x] T010 [US2] Integrate `CommandMenu` into `MessageComposer.tsx` by tracking cursor position and `/` or `@` keystrokes.
- [x] T011 [US2] Implement keyboard navigation (Up/Down/Enter) within `CommandMenu.tsx` and replacement logic into the composer input.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Paste and Drag-and-Drop Media (Priority: P2)

**Goal**: Users need to add image context by dragging images or pasting them from the clipboard.

**Independent Test**: Paste or drop an image into the composer and verify it uploads and attaches.

### Implementation for User Story 3

- [x] T012 [P] [US3] Create `AttachmentPill` component to render image previews above the input field.
- [x] T013 [US3] Add `onPaste` event handler to the textarea in `apps/web/src/components/chat/MessageComposer.tsx` to process image clipboard data, calling `uploadFile`.
- [x] T014 [US3] Add `onDrop` and `onDragOver` event handlers to the dropzone area in `MessageComposer.tsx`.
- [x] T015 [US3] Modify `onSend` callback in `MessageComposer.tsx` and `WorkspacePanel.tsx` to include `attachments` file IDs alongside the text message payload.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T016 Check frontend styling consistency using CSS variables.
- [x] T017 Verify edge cases for unsupported file types with user-friendly error alerts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: BLOCKS all user stories.
- **User Stories (Phase 3-5)**: Depend on Foundational phase completion. Can proceed sequentially.

### User Story Dependencies

- **User Story 1 & 2 (P1)**: Can be implemented concurrently.
- **User Story 3 (P2)**: Requires the file vault APIs from Phase 2.

### Parallel Opportunities

- T002, T004 can be executed in parallel by different developers.
- T008 can be built as a pure UI component while the backend for US2 is being finalized.
- T012 can be built independently of the drag-and-drop event handlers.
