# Tasks: Hermes & LLM Integration

**Input**: Design documents from `specs/002-hermes-llm-integration/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — the spec requires Vitest component tests (Tier 1), Playwright integration tests (Tier 2), and E2E smoke tests (Tier 3) per constitution §6.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project dependencies and new file scaffolding

- [x] T001 Add `httpx>=0.28` to `apps/api/pyproject.toml` dependencies and run `uv sync`
- [x] T002 [P] Create `scripts/` directory at repo root for profile management scripts
- [x] T003 [P] Create `apps/api/src/api/routers/` directory and add empty `__init__.py`
- [x] T004 [P] Create `apps/api/src/api/config.py` with Hermes profile configuration constants (HERMES_WEBUI_BASE_URL, HERMES_WEBUI_PORT, LLM_HEALTH_URL)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Implement `BaseAgentEngine` abstract base class in `packages/agent_adapters/src/agent_adapters/base.py` with methods: `check_health`, `create_session`, `list_sessions`, `delete_session`, `start_chat`, `stream_response` per contracts/api-contracts.md
- [x] T006 Implement `AgentStreamEvent`, `AgentChatRequest`, `AgentChatStartResponse`, `AgentSessionInfo` dataclasses in `packages/agent_adapters/src/agent_adapters/base.py`
- [x] T007 Update `packages/agent_adapters/src/agent_adapters/__init__.py` to re-export `BaseAgentEngine` and all dataclasses
- [x] T008 [P] Add `httpx>=0.28` to `packages/agent_adapters/pyproject.toml` dependencies

**Checkpoint**: Foundation ready — `BaseAgentEngine` ABC is importable and defines the full adapter interface

---

## Phase 3: User Story 2 — Dedicated Wright Hermes Profile (Priority: P2)

**Goal**: Create an isolated "wright" Hermes profile that shares the LLM config but has independent sessions/skills

**Independent Test**: Run `hermes profile list` and verify "wright" appears with its own HERMES_HOME. Run the setup script twice to confirm idempotency.

> **Note**: This is implemented before US1 because the profile must exist before the chat proxy can function.

### Implementation for User Story 2

- [x] T009 [US2] Create `scripts/setup-wright-profile.sh` — idempotent script that runs `hermes profile create wright --clone` if profile doesn't exist, and starts the wright WebUI on port 8788 via `HERMES_HOME=~/.hermes/profiles/wright ~/hermes-webui/ctl.sh start --port 8788`
- [x] T010 [US2] Make `scripts/setup-wright-profile.sh` executable and test manually: run it, verify `hermes profile list` shows "wright", verify `curl http://127.0.0.1:8788/api/health` returns OK
- [x] T011 [US2] Add `wright:setup-profile` task to `.vscode/tasks.json` that runs `bash scripts/setup-wright-profile.sh`

**Checkpoint**: Wright Hermes profile exists and its WebUI is accessible on port 8788

---

## Phase 4: User Story 3 — Backend Proxy to Hermes API (Priority: P2)

**Goal**: Wright FastAPI backend exposes proxy endpoints that forward chat requests to the Hermes WebUI API

**Independent Test**: Call `curl -X POST http://127.0.0.1:8000/api/agent/sessions/new` and verify it returns a session. Call the chat start endpoint with a message and verify a stream_id is returned.

### Implementation for User Story 3

- [x] T012 [US3] Implement `HermesAdapter(BaseAgentEngine)` in `packages/agent_adapters/src/agent_adapters/hermes.py` — uses httpx AsyncClient to proxy all requests to the Hermes WebUI at the configured base URL. Implements: `check_health` (GET /api/health), `create_session` (POST /api/session/new), `list_sessions` (GET /api/sessions), `delete_session`, `start_chat` (POST /api/chat/start), `stream_response` (GET /api/chat/stream SSE consumer)
- [x] T013 [US3] Update `packages/agent_adapters/src/agent_adapters/__init__.py` to re-export `HermesAdapter`
- [x] T014 [US3] Implement agent router in `apps/api/src/api/routers/agent.py` with endpoints: `POST /api/agent/sessions/new`, `GET /api/agent/sessions`, `DELETE /api/agent/sessions/{session_id}`, `POST /api/agent/chat/start`, `GET /api/agent/chat/stream` (SSE StreamingResponse)
- [x] T015 [US3] Update `apps/api/src/api/main.py` to import and mount the agent router with prefix `/api/agent`, instantiate `HermesAdapter` from config, and inject it into the router
- [x] T016 [US3] Replace stub `/api/agent/health` endpoint in `apps/api/src/api/main.py` with real health check that calls `HermesAdapter.check_health()`
- [x] T017 [US3] Replace stub `/api/inference/health` endpoint in `apps/api/src/api/main.py` with real health check that calls the LLM inference server at the URL from `config.py`
- [x] T018 [US3] Add structured JSON logging (structlog) to all agent router handlers in `apps/api/src/api/routers/agent.py` with trace_id propagation
- [x] T019 [US3] Write pytest tests for `HermesAdapter` in `apps/api/tests/test_hermes_adapter.py` — mock httpx responses for session creation, chat start, and SSE streaming

**Checkpoint**: Wright API proxies to Hermes WebUI — `curl` can create sessions and initiate chat

---

## Phase 5: User Story 1 — Live Agent Chat via Wright UI (Priority: P1) 🎯 MVP

**Goal**: User types a message in the Wright Agent Chat page and receives a streamed response from the Hermes agent

**Independent Test**: Start the Wright app, navigate to Agent Chat, create a session, type "Hello", and verify a streamed response appears token-by-token in the transcript

### Implementation for User Story 1

- [x] T020 [US1] Replace `StubAgentService` with `HermesAgentService` in `apps/web/src/services/agent-service.ts` — implements `createSession` (POST /api/agent/sessions/new), `listSessions` (GET /api/agent/sessions), `deleteSession` (DELETE /api/agent/sessions/{id}), `sendMessage` (POST /api/agent/chat/start then EventSource on /api/agent/chat/stream)
- [x] T021 [US1] Update `apps/web/src/services/agent-service.ts` `sendMessage` to consume SSE using native `EventSource` API: parse `token` events → yield `{type: 'token', text}`, parse `tool` events → yield `{type: 'tool', ...}`, parse `stream_end` → yield `{type: 'done', session}`, parse `error` → yield `{type: 'error', message}`
- [x] T022 [US1] Update `apps/web/src/store/sessions.tsx` to call `HermesAgentService.createSession()` instead of local session creation, and `HermesAgentService.listSessions()` for session list hydration
- [x] T023 [US1] Update `apps/web/src/components/chat/ChatTranscript.tsx` to show a streaming indicator (animated dots) while waiting for the first token from the agent
- [x] T024 [US1] Update `apps/web/src/components/chat/MessageComposer.tsx` to disable the send button while a response is actively streaming
- [x] T025 [US1] Handle error states in `apps/web/src/components/chat/ChatLayout.tsx` — display a banner when agent health is "disconnected" with message "Hermes agent is not available. Check that the wright profile WebUI is running."
- [x] T026 [US1] Update Vitest tests in `apps/web/tests/ChatLayout.spec.tsx` to mock the new `HermesAgentService` and verify streaming indicator and error banner rendering
- [x] T027 [US1] Update Playwright test `tests/ui-integration/agent-chat.spec.ts` to verify that the chat page renders correctly with the real service interface (mock the API responses at the network level)

**Checkpoint**: End-to-end chat works — type a message, see a streamed Hermes response

---

## Phase 6: User Story 4 — Health Status Reflects Live Connectivity (Priority: P3)

**Goal**: Status bar shows real-time connectivity state of Hermes agent and LLM inference

**Independent Test**: Start the app with Hermes running → green dots. Stop Hermes → red dot within 15 seconds.

### Implementation for User Story 4

- [x] T028 [US4] Update `apps/web/src/services/health-service.ts` to make real HTTP fetch calls to `/api/agent/health` and `/api/inference/health` instead of returning mock "connected" state
- [x] T029 [US4] Update `apps/web/tests/StatusBar.spec.tsx` to test both connected and disconnected states with mocked fetch responses
- [x] T030 [US4] Add `data-testid="health-error-hermes"` to the status bar Hermes indicator in `apps/web/src/components/layout/StatusBar.tsx` for Playwright targeting

**Checkpoint**: Status bar accurately reflects real backend connectivity

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and quality gates

- [x] T031 [P] Update `specs/002-hermes-llm-integration/quickstart.md` with any setup steps discovered during implementation
- [x] T032 [P] Update `.vscode/tasks.json` to add `wright:setup-profile` pre-launch task so the profile is created before the app starts
- [x] T033 Run all Vitest component tests (`npm run test --prefix apps/web`) and verify all pass
- [x] T034 Run all Playwright integration tests (`npx playwright test`) and verify all pass
- [x] T035 Run pytest backend tests (`uv run pytest`) and verify all pass
- [x] T036 Manual end-to-end verification: start Wright app, create session, send "Hello, what can you do?", verify streamed response appears
- [x] T037 [P] Update `apps/web/src/services/logger.ts` to log agent chat events (session create, message send, stream start/end/error) with structured JSON
- [x] T038 Code cleanup: remove any remaining stub/mock code from agent-service.ts and health-service.ts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 2 / Profile (Phase 3)**: Depends on Foundational — creates the Hermes profile
- **User Story 3 / Backend Proxy (Phase 4)**: Depends on Foundational + Phase 3 (profile must exist for proxy)
- **User Story 1 / Frontend Chat (Phase 5)**: Depends on Phase 4 (backend endpoints must exist)
- **User Story 4 / Health Status (Phase 6)**: Depends on Phase 4 (real health endpoints must exist)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 2 (Profile)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (Backend)**: Depends on US2 (profile must exist for the WebUI to connect to)
- **User Story 1 (Frontend Chat)**: Depends on US3 (backend API must be available)
- **User Story 4 (Health)**: Depends on US3 (real health endpoints required) — can run in parallel with US1

### Within Each User Story

- Models/dataclasses before services
- Services before endpoints/routers
- Backend before frontend (for integration)
- Core implementation before tests
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004 can all run in parallel (different files, no dependencies)
- T005 and T008 can run in parallel (different packages)
- T028, T029, T030 (US4) can start as soon as Phase 4 completes — in parallel with US1 work
- T031, T032, T037 can all run in parallel during Polish phase

---

## Parallel Example: Phase 4 (User Story 3)

```bash
# After T012 (HermesAdapter) completes, these can run in parallel:
Task T014: "Implement agent router in apps/api/src/api/routers/agent.py"
Task T018: "Add structured JSON logging to agent router handlers"

# T016 and T017 (health endpoints) can run in parallel with each other:
Task T016: "Replace stub /api/agent/health with real check"
Task T017: "Replace stub /api/inference/health with real check"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (BaseAgentEngine ABC)
3. Complete Phase 3: Create Wright Hermes profile
4. Complete Phase 4: Backend proxy to Hermes API
5. Complete Phase 5: Frontend chat integration
6. **STOP and VALIDATE**: Send a message → receive a streamed response
7. Demo to user

### Incremental Delivery

1. Setup + Foundational → BaseAgentEngine ABC ready
2. Add Profile (US2) → Wright profile exists, WebUI accessible
3. Add Backend Proxy (US3) → API endpoints working, `curl` test passes
4. Add Frontend Chat (US1) → **Full MVP — end-to-end chat works** 🎯
5. Add Health Status (US4) → Status bar shows real connectivity
6. Polish → Tests green, documentation updated, code cleaned

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- US2 and US3 are both Priority P2 in the spec but are sequenced here because the profile (US2) must exist before the proxy (US3) can connect
- The frontend (US1) is Priority P1 in the spec but depends on the backend (US3), so it's implemented after the backend is ready
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
