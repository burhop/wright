# Tasks: Migrate to Hermes Native API

**Input**: Design documents from `/specs/025-migrate-hermes-native-api/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test update tasks are included only for the existing test files that must be updated for the new API contract.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `apps/api/src/api/`, `packages/agent_adapters/src/agent_adapters/`, `packages/core/src/core/`
- **Frontend**: `apps/web/src/services/`
- **Infrastructure**: `docker/`, `scripts/`
- **Tests**: `apps/api/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration changes and profile setup that all other phases depend on

- [ ] T001 Rename `HERMES_WEBUI_PORT` → `HERMES_API_PORT` and `HERMES_WEBUI_BASE_URL` → `HERMES_API_BASE_URL`, add `HERMES_API_KEY` constant in `apps/api/src/api/config.py`
- [ ] T002 Update imports from `HERMES_WEBUI_BASE_URL` to `HERMES_API_BASE_URL` and pass `HERMES_API_KEY` to `HermesAdapter()` in `apps/api/src/api/main.py`
- [ ] T003 [P] Rewrite `setup-wright-profile.sh`: configure wright profile `.env` for the native API server (`API_SERVER_ENABLED=true`, `API_SERVER_KEY`, `API_SERVER_PORT=8642`), replace `ctl.sh start 8788` with `hermes -p wright gateway start`, and update health check URL to port 8642 in `scripts/setup-wright-profile.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Redesign the `BaseAgentEngine` interface to align with the OpenAI-compatible streaming model. MUST be complete before any adapter or router work can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Replace `start_chat()` and `stream_response()` abstract methods with unified `stream_chat(request) → AsyncIterator[AgentStreamEvent]` in `packages/agent_adapters/src/agent_adapters/base.py`
- [ ] T005 Remove `AgentChatStartResponse` dataclass from `packages/agent_adapters/src/agent_adapters/base.py`
- [ ] T006 Update `cancel_chat()` signature to remove `stream_id` parameter (keep only `session_id`) in `packages/agent_adapters/src/agent_adapters/base.py`
- [ ] T007 Update `__all__` exports to remove `AgentChatStartResponse` in `packages/agent_adapters/src/agent_adapters/__init__.py`

**Checkpoint**: Foundation ready — the abstract interface is redesigned. Adapter and router work can now begin.

---

## Phase 3: User Story 1 - Seamless Agent Chat After Migration (Priority: P1) 🎯 MVP

**Goal**: Rewrite the HermesAdapter to use the native Hermes API and update the router + frontend to use the unified streaming endpoint. Users can send messages and receive streamed responses exactly as before.

**Independent Test**: Start the Wright app with the native API backend. Open a workspace, send a message, and verify a complete streamed response appears in the transcript.

### Implementation for User Story 1

- [ ] T008 [US1] Rewrite `__init__()` to accept `base_url` and `api_key`, replace `hermes_profile=wright` cookie with `Authorization: Bearer` header in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T009 [US1] Rewrite `check_health()` to target new base URL with Bearer auth in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T010 [US1] Rewrite `create_session()` from `POST /api/session/new` to `POST /api/sessions` with Bearer auth in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T011 [P] [US1] Rewrite `list_sessions()` from `GET /api/sessions?all_profiles=0` to `GET /api/sessions` with Bearer auth in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T012 [P] [US1] Rewrite `delete_session()` from `POST /api/session/delete` to `DELETE /api/sessions/{id}` with Bearer auth in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T013 [US1] Implement unified `stream_chat()` method: `POST /v1/chat/completions` via `httpx` + `aconnect_sse` with `stream: true`. Includes a `_build_messages(request)` helper that constructs the OpenAI `messages` array from `AgentChatRequest` (fetches session history via `get_chat_history()` if needed, appends the new user message). Maps `delta.content` → `token`, `delta.tool_calls` → `tool`, `hermes.tool.progress` → `progress`, `[DONE]` → `stream_end` in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T014 [US1] Rewrite `get_chat_history()` from `GET /api/session?session_id=X&messages=1` to `GET /api/sessions/{id}/messages` in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T015 [US1] Implement `cancel_chat(session_id)` to abort active HTTP connection in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T016 [US1] Remove `start_chat()` and `stream_response()` methods from `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T017 [US1] Merge `POST /chat/start` + `GET /chat/stream` into single `POST /chat` endpoint using `engine.stream_chat()` in `apps/api/src/api/routers/agent.py`
- [ ] T018 [US1] Remove `ChatStartResponse` schema and update `ChatStartRequest` → `ChatRequest` in `apps/api/src/api/routers/agent.py`
- [ ] T019 [US1] Update `POST /chat/cancel` to accept only `session_id` (remove `stream_id` query param) in `apps/api/src/api/routers/agent.py`
- [ ] T020 [US1] Replace Hermes-specific error messages with agent-agnostic messages in `apps/api/src/api/routers/agent.py`
- [ ] T021 [US1] Replace `EventSource` + `stream_id` two-step flow with single `fetch("/api/agent/chat", { method: "POST" })` + `ReadableStream` SSE parsing in `apps/web/src/services/agent-service.ts`
- [ ] T022 [US1] Implement SSE line parser for `response.body` ReadableStream (parse `event:` and `data:` lines) in `apps/web/src/services/agent-service.ts`
- [ ] T023 [US1] Update `cancelStream()` to call `POST /api/agent/chat/cancel` with only `session_id` in `apps/web/src/services/agent-service.ts`
- [ ] T024 [US1] Replace Hermes-specific error messages with agent-agnostic messages in `apps/web/src/services/agent-service.ts`
- [ ] T025 [US1] Implement graceful error handling when the gateway is up but the LLM inference server is offline — map 502/503 from `/v1/chat/completions` to a user-facing "LLM model unavailable" error event in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T026 [US1] Update `HermesAdapter` instantiation to `HermesAdapter(base_url, api_key)` and test health check manually

**Checkpoint**: At this point, the core chat flow should be fully functional end-to-end: send message → streamed response with tool indicators.

---

## Phase 4: User Story 2 - Dynamic MCP Tool Management (Priority: P1)

**Goal**: Eliminate the process-restart cycle for MCP tool changes. When a user toggles a tool in workspace settings, the change takes effect via the existing `gateway.py` JSONRPC notification path — no `fuser -k` or `ctl.sh` restart needed.

**Independent Test**: Open a workspace, start a chat session, enable an MCP tool in settings, and verify the tool is available to the agent within 5 seconds without any service interruption.

### Implementation for User Story 2

- [ ] T027 [US2] Remove `restart_hermes_background()` function entirely from `apps/api/src/api/services/hermes_sync.py`
- [ ] T028 [US2] Simplify `sync_mcp_server_to_hermes()` — remove restart fallback, keep config write + `notify_gateway_tool_change()` in `apps/api/src/api/services/hermes_sync.py`
- [ ] T029 [US2] Simplify `sync_workspace_tools_to_hermes()` — remove restart fallback, keep config + gitignore + hermes.md write + `notify_gateway_tool_change()` in `apps/api/src/api/services/hermes_sync.py`
- [ ] T030 [US2] Remove lines 161-202 (`fuser -k`, `ctl.sh stop/start`, health-check polling loop) from `_sync_to_hermes()` in `packages/core/src/core/agent_sync.py`
- [ ] T031 [US2] Verify `_write_static_hermes_config()` writes the `wrightgateway` MCP server entry correctly (one-time static config) in `apps/api/src/api/services/hermes_sync.py`

**Checkpoint**: MCP tool toggle should work without any process restarts. The gateway auto-reloads tools via JSONRPC notifications from `gateway.py`.

---

## Phase 5: User Story 3 - Workspace Session Isolation & History (Priority: P2)

**Goal**: Verify that all existing workspace session behavior (create, restore, isolate, history) continues to work with the new native API session endpoints.

**Independent Test**: Create a workspace, chat, leave, return, and verify the session is restored with full message history. Verify sessions from workspace A are not visible in workspace B.

### Implementation for User Story 3

- [ ] T032 [US3] Verify `create_session()` correctly maps the `POST /api/sessions` response fields (session_id, title, created_at, updated_at) for workspace binding in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T033 [US3] Verify `list_sessions()` returns workspace metadata so `agent.py` router can filter by workspace_id in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T034 [US3] Verify `get_chat_history()` returns complete message history including tool call messages from `GET /api/sessions/{id}/messages` in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [ ] T035 [US3] Test loading a pre-migration session_id created under hermes-webui — if the native API returns 404, document that a clean session start is expected behavior and update quickstart.md accordingly

**Checkpoint**: Workspace session isolation should work identically to before — sessions scoped per workspace, last session restored on re-entry.

---

## Phase 6: User Story 4 - System Health Visibility (Priority: P3)

**Goal**: The status bar accurately reflects the native API backend connectivity state.

**Independent Test**: Start the app with the native API running (expect green). Stop the gateway (expect red within 15 seconds).

### Implementation for User Story 4

- [ ] T036 [US4] Verify `check_health()` correctly targets the native API health endpoint at port 8642 with Bearer auth in `packages/agent_adapters/src/agent_adapters/hermes.py`

**Checkpoint**: Health indicators should accurately reflect native API connectivity.

---

## Phase 7: User Story 5 - Simplified Container Deployment (Priority: P3)

**Goal**: The Docker container runs the official Hermes gateway instead of hermes-webui. The image is smaller and has fewer dependencies.

**Independent Test**: Build the Docker image, run the container, verify via `supervisorctl status` that `wright-api` and `hermes-gateway` are both running.

### Implementation for User Story 5

- [ ] T037 [US5] Remove hermes-webui git clone, venv creation, and requirements.txt installation block (lines 87-97) from `docker/Dockerfile`
- [ ] T038 [US5] Add wright profile `.env` configuration (`API_SERVER_ENABLED=true`, `API_SERVER_KEY`, `API_SERVER_PORT=8642`) to the Docker build stage in `docker/Dockerfile`
- [ ] T039 [US5] Replace `[program:hermes-webui]` with `[program:hermes-gateway]` running `hermes -p wright gateway` in `docker/supervisord.conf`
- [ ] T040 [P] [US5] Verify `scripts/setup-wright-profile.sh` changes from T003 are consistent with Docker build steps (same env vars, same port, same gateway command)

**Checkpoint**: Docker container should build and run with hermes-gateway instead of hermes-webui.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Test updates, documentation, and cleanup across all components

- [ ] T041 Update `HermesAdapter("http://127.0.0.1:8788")` instantiations to `HermesAdapter("http://127.0.0.1:8642", "test-key")` in `apps/api/tests/test_hermes_adapter.py`
- [ ] T042 Update mocked endpoints to match native API paths (`/api/sessions` instead of `/api/session/new`, etc.) in `apps/api/tests/test_hermes_adapter.py`
- [ ] T043 [P] Add test for `hermes.tool.progress` event parsing in `stream_chat()` in `apps/api/tests/test_hermes_adapter.py`
- [ ] T044 [P] Add test for OpenAI-compatible streaming format parsing in `stream_chat()` in `apps/api/tests/test_hermes_adapter.py`
- [ ] T045 Replace `start_chat()`/`stream_response()` test mocks with `stream_chat()` mocks in `apps/api/tests/test_hermes_adapter.py`
- [ ] T046 Run full pytest suite: `uv run pytest apps/api/tests/ -v`
- [ ] T047 [P] Run frontend tests: `npm test --workspace=apps/web`
- [ ] T048 Run quickstart.md manual verification checklist from `specs/025-migrate-hermes-native-api/quickstart.md` — include verification of slash commands parity with previous hermes-webui behavior
- [ ] T049 [P] Verify agent hot-swap works with redesigned `BaseAgentEngine`: call `set_active_agent_endpoint` to switch adapters and confirm `stream_chat()` dispatches to the correct adapter in `apps/api/src/api/routers/agent.py`
- [ ] T050 [P] Update spec comments/docstrings to reference native API instead of hermes-webui across modified files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — core chat migration
- **User Story 2 (Phase 4)**: Depends on Setup (Phase 1) only — MCP sync is independent of adapter rewrite
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) — verifies session behavior with new API
- **User Story 4 (Phase 6)**: Depends on User Story 1 (Phase 3) — verifies health check with new API
- **User Story 5 (Phase 7)**: Can start after Setup (Phase 1) — Docker/infra is independent
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational → core migration, adapter + router + frontend
- **User Story 2 (P1)**: After Setup → independent MCP sync simplification (can run parallel with US1)
- **User Story 3 (P2)**: After US1 → verification of session behavior with new adapter
- **User Story 4 (P3)**: After US1 → verification of health checks with new adapter
- **User Story 5 (P3)**: After Setup → independent infrastructure work (can run parallel with US1/US2)

### Within Each User Story

- Config changes before adapter code
- Adapter code before router code
- Router code before frontend code
- Core implementation before integration verification
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T003 can run in parallel (different files)
- **Phase 3 (US1)**: T011 and T012 can run in parallel (list_sessions and delete_session are independent)
- **Phase 4 (US2)**: Can run entirely in parallel with Phase 3 (US1) — different files, independent concern
- **Phase 7 (US5)**: T037, T038, T039 can run partially in parallel; T040 is a verification task
- **Phase 8**: T043, T044, T047, T049, T050 can run in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, launch parallel adapter rewrites:
Task: T011 [P] [US1] Rewrite list_sessions() in hermes.py
Task: T012 [P] [US1] Rewrite delete_session() in hermes.py

# After adapter is complete, launch parallel frontend updates:
Task: T021 [US1] Replace EventSource flow in agent-service.ts
Task: T022 [US1] Implement SSE parser in agent-service.ts
```

## Parallel Example: Cross-Story Parallelism

```bash
# After Foundational (Phase 2) completes, US1 and US2 can run in parallel:
# Developer A: User Story 1 (adapter + router + frontend)
Task: T008-T026 [US1] Full chat migration

# Developer B: User Story 2 (MCP sync simplification)  
Task: T027-T031 [US2] Remove restart logic

# Developer C: User Story 5 (Docker/infra)
Task: T037-T040 [US5] Container migration
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T026)
4. **STOP and VALIDATE**: Test end-to-end chat flow — send message → streamed response
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Interface redesigned
2. Add User Story 1 → Test chat independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test MCP toggle independently → No more restarts!
4. Add User Story 3 → Verify session isolation → Deploy/Demo
5. Add User Story 5 → Build Docker image → Deploy/Demo
6. Polish phase → Tests, docs, cleanup

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T007)
2. Once Foundational is done:
   - Developer A: User Story 1 (T008-T026) — core migration
   - Developer B: User Story 2 (T027-T031) — MCP simplification
   - Developer C: User Story 5 (T037-T040) — Docker migration
3. After US1 completes:
   - Developer A: User Story 3 (T032-T035) — session verification
   - Developer A: User Story 4 (T036) — health check verification
4. All developers: Polish phase (T041-T050)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 is the critical path — all other stories verify or complement the core migration
- US2 and US5 can run fully in parallel with US1 since they touch different files
