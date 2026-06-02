# Tasks: MCP & Tool Registry

**Input**: Design documents from `specs/003-mcp-tool-registry/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — the spec requires Vitest component tests (Tier 1), Playwright integration tests (Tier 2), and E2E adapter tests per constitution §6.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and package structure setup

- [ ] T001 Scaffold `packages/tool_registry/` package containing `pyproject.toml` workspace setup and empty src modules
- [ ] T002 Update root `pyproject.toml` to list `packages/tool_registry` workspace member and run `uv sync`
- [ ] T003 Configure database schema initialization scripts to create `mcp_servers` and `mcp_tools` tables in `apps/api/src/api/database/migrate.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core MCP runners and SQLite schemas

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `McpServer` and `McpTool` Pydantic models in `packages/tool_registry/src/tool_registry/models.py`
- [ ] T005 Implement SQLite queries for inserting, deleting, and updating tool registry records in `packages/tool_registry/src/tool_registry/db.py`
- [ ] T006 Implement base subprocess execution class `BaseRunner` in `packages/tool_registry/src/tool_registry/runners/base.py`
- [ ] T007 Implement subprocess spawn and stdio stdin/stdout reader in `packages/tool_registry/src/tool_registry/runners/stdio.py`
- [ ] T008 Implement HTTP SSE connection client in `packages/tool_registry/src/tool_registry/runners/sse.py`
- [ ] T009 Implement `McpEngine` coordinating active server processes and discovering JSON schemas in `packages/tool_registry/src/tool_registry/manager.py`

**Checkpoint**: Foundation ready — MCP runners are fully capable of spawning processes and discovering schemas

---

## Phase 3: User Story 1 — Visual Tool Registry Directory (Priority: P1) 🎯 MVP

**Goal**: User browses, searches, and enables MCP tools in a visual directory grid

**Independent Test**: Navigate to the Tool Registry page, search for a tool card, click Activate, and verify it shows active status.

### Implementation for User Story 1

- [ ] T010 Write pytest backend unit tests verifying stdio subprocess launch and schema parsing in `packages/tool_registry/tests/test_registry.py`
- [ ] T011 Implement REST endpoint handlers for GET/PATCH servers and tools in `apps/api/src/api/routers/mcp.py`
- [ ] T012 Mount `/api/mcp` router in `apps/api/src/api/main.py`
- [ ] T013 Create MCP API handler service in `apps/web/src/services/mcp-service.ts`
- [ ] T014 Implement tools React context state store in `apps/web/src/store/tools.tsx`
- [ ] T015 Implement `ToolCard.tsx` displaying title, category, description, and status toggle in `apps/web/src/components/tools/ToolCard.tsx`
- [ ] T016 Replace placeholder `ToolRegistryPage.tsx` with searchable category layout in `apps/web/src/pages/ToolRegistryPage.tsx`
- [ ] T017 Write Vitest component tests verifying search and toggle actions in `apps/web/tests/ToolRegistry.spec.tsx`

**Checkpoint**: User Story 1 works independently — users can activate/deactivate default MCP tools

---

## Phase 4: User Story 2 — Register Custom MCP Servers & CLIs (Priority: P2)

**Goal**: Form panel allowing users to register new custom local CLI wrappers or HTTP SSE endpoints

**Independent Test**: Click "Add Custom Tool", select stdio, provide a CLI script, click Save, and verify the tool is immediately added to the store.

### Implementation for User Story 2

- [ ] T018 Implement `POST /api/mcp/servers` and `DELETE /api/mcp/servers/{server_id}` endpoints in `apps/api/src/api/routers/mcp.py`
- [ ] T019 Create the custom tool modal popup component `AddToolModal.tsx` in `apps/web/src/components/tools/AddToolModal.tsx`
- [ ] T020 Wire the save form handler in `AddToolModal.tsx` to `mcp-service.ts` and update listings upon successful registration
- [ ] T021 Write Vitest inputs validation unit tests in `apps/web/tests/AddToolModal.spec.tsx`
- [ ] T022 Write Playwright integration test verifying registry save flow in `tests/ui-integration/mcp-directory.spec.ts`

**Checkpoint**: User Story 2 works independently — custom local tools can be registered and spawned on the fly

---

## Phase 5: User Story 3 — Rich UI Renderers for Tool Progress (MCP-UI) (Priority: P2)

**Goal**: Render animating progress meters or stats cards in transcript during long tool runs

**Independent Test**: Invoke mesh tool in chat and verify it renders a progress bar.

### Implementation for User Story 3

- [ ] T023 Update backend tool execution routers to yield structured progress events via chat SSE stream in `apps/api/src/api/routers/agent.py`
- [ ] T024 Update `ChatTranscript.tsx` in `apps/web/src/components/chat/ChatTranscript.tsx` to dynamically render custom visual component cards for tool status updates
- [ ] T025 Update E2E Playwright tests to assert progress components render cleanly in `tests/ui-integration/agent-chat.spec.ts`

**Checkpoint**: Visual progress indicators display live status updates during execution

---

## Phase 6: User Story 4 — WebMCP Browser Context Sharing (Priority: P3)

**Goal**: Allow agent to query browser viewport selection state via client-side WebMCP event listeners

**Independent Test**: Agent queries user viewport selections and receives exact 3D selection GUIDs.

### Implementation for User Story 4

- [ ] T026 Create client-side WebMCP socket receiver in `apps/web/src/services/webmcp-service.ts`
- [ ] T027 Wire viewport selection listeners to register tool calls in workspace viewer component files

**Checkpoint**: Agent can query and correlate active viewport components

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, tracing, and code cleanup

- [ ] T028 Update developer setup instructions in `specs/003-mcp-tool-registry/quickstart.md`
- [ ] T029 Enable structured structlog and OpenTelemetry spans for tool process execution paths
- [ ] T030 Run all unit, component, and Playwright integration tests and verify they pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (UI list must exist to append new tools)
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2)
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2)
- **Polish (Phase 7)**: Depends on all user stories being complete
