# Implementation Plan: Quality, Testing & Observability Refactor

**Branch**: `008-quality-testing-observability` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-quality-testing-observability/spec.md`

## Summary

Bring the Wright project into full compliance with the constitution by: (1) refactoring the 965-line workspace router into clean thin-handler + schema + service layers, (2) replacing all stdlib `logging` with `structlog`, (3) instrumenting every API endpoint and database call with OpenTelemetry spans using a semantic hierarchy, (4) building comprehensive API tests (pytest) for all 3 routers, (5) adding Playwright UI integration tests for every page and user journey, (6) adding Vitest component tests for 6+ critical components, (7) creating frontend log persistence via IndexedDB for a future Log Viewer, and (8) ensuring 100% `data-testid` coverage on every interactive element.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0, React 19 (frontend)

**Primary Dependencies**: FastAPI >=0.115, Pydantic v2, structlog >=24.1, opentelemetry-api/sdk/exporter-otlp >=1.25, React 19, react-router-dom v6, Vitest, Playwright, idb (IndexedDB wrapper)

**Storage**: SQLite with WAL mode (existing tables: `engineering_workspaces`, `mcp_servers`, `mcp_tools`, `agent_contexts`)

**Testing**: pytest (backend API), Vitest (frontend components), Playwright (E2E workspace navigation)

**Target Platform**: Linux local host (offline-first execution)

**Project Type**: Web application (modular monorepo)

**Performance Goals**: No new latency added by tracing/logging (< 5ms overhead per span). IndexedDB log writes must be async and non-blocking.

**Constraints**: Offline-first. No background databases. Single-machine, single-user. All tests must pass at 100%.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Will Fix | Workspace router will be refactored from 965 lines to < 300 lines. All direct SQL in `activate_workspace_endpoint` and `sync_workspace_tools_to_hermes` will move to `core/`. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | Existing boundary structure maintained. New `schemas/` modules added within existing packages. |
| 3 | Offline-First Mandate | ✅ Pass | All changes are local. IndexedDB for frontend logs. No external dependencies. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | No changes to BaseAgentEngine interface. |
| 5 | Zero-server databases | ✅ Pass | SQLite + IndexedDB only. |
| 6 | Local authentication | ⚠️ Out of scope | Authentication is a separate feature. Not addressed in this refactor. |
| 7 | Template Method for tools | ✅ Pass | No changes to tool patterns. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | All new components follow existing CSS token system. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Will Fix | Adding Vitest component tests (Tier 1), comprehensive Playwright tests (Tier 2), and system E2E test (Tier 3). |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Will Fix | All routers will use structlog. All endpoints will have OTel spans with semantic naming. trace_id propagation end-to-end. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Working on `008-quality-testing-observability` branch; plan before implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/008-quality-testing-observability/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model output
├── contracts/           # Phase 1 API contracts
│   └── error-response.md
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
# Backend — API Layer
apps/api/src/api/
├── schemas/
│   ├── workspace.py          # [NEW] All workspace Pydantic models extracted from router
│   ├── common.py             # [NEW] Shared error response schema (ErrorResponse)
│   └── __init__.py           # [NEW]
├── middleware/
│   ├── tracing.py            # [NEW] OTel middleware for automatic span creation + trace_id injection
│   └── __init__.py           # [NEW]
├── routers/
│   ├── workspace.py          # [MODIFY] Refactor to < 300 lines, thin handlers only
│   ├── agent.py              # [MODIFY] Consistent structured logging, error response schema
│   └── mcp.py                # [MODIFY] Add OTel spans, consistent error response schema
├── services/
│   ├── hermes_sync.py        # [NEW] Extract sync_workspace_tools_to_hermes logic
│   └── __init__.py           # [NEW]
└── main.py                   # [MODIFY] Register OTel middleware, configure structlog

# Backend — Core Package
packages/core/src/core/
├── workspace.py              # [MODIFY] Add traced DB helper functions, extract activate logic
├── tracing.py                # [NEW] Shared OTel tracer factory + traced_db_operation decorator
└── logging.py                # [NEW] Shared structlog configuration (JSON processor, trace_id binding)

# Backend — Tests
apps/api/tests/
├── conftest.py               # [MODIFY] Add OTel test fixtures, shared mock factories
├── test_workspace_api.py     # [MODIFY] Add error-path tests, context endpoint tests
├── test_agent_api.py         # [NEW] Full agent router test coverage
├── test_mcp_api.py           # [MODIFY] Add error-path tests for install/uninstall
├── test_hermes_adapter.py    # (no changes — already has good coverage)
├── test_webmcp.py            # (no changes)
└── test_tracing.py           # [NEW] Verify OTel span creation and trace_id propagation

# Frontend — Services
apps/web/src/services/
├── logger.ts                 # [MODIFY] Add IndexedDB persistence, batch writes, pruning
├── log-store.ts              # [NEW] IndexedDB log store with query API for future Log Viewer
├── telemetry.ts              # [MODIFY] Add api.fetch span wrapper, trace_id propagation via header
├── api-client.ts             # [NEW] Centralized fetch wrapper with auto-tracing + error capture
├── agent-service.ts          # [MODIFY] Use api-client for traced HTTP calls
├── workspace-service.ts      # [MODIFY] Use api-client for traced HTTP calls
├── mcp-service.ts            # [MODIFY] Use api-client for traced HTTP calls
└── health-service.ts         # [MODIFY] Use api-client for traced HTTP calls

# Frontend — Components (data-testid audit + fixes)
apps/web/src/components/
├── pages/
│   ├── DashboardPage.tsx     # [MODIFY] Add data-testid to workspace cards, feature cards, empty state
│   ├── WorkspacePage.tsx     # [MODIFY] Add data-testid to error/loading states
│   ├── ToolRegistryPage.tsx  # [MODIFY] Add data-testid to tool cards, register button, search
│   ├── FileVaultPage.tsx     # [MODIFY] Add data-testid to file list, preview, download
│   └── NotFoundPage.tsx      # (already has data-testid)
├── chat/
│   ├── ChatLayout.tsx        # (already has data-testid)
│   ├── ChatTranscript.tsx    # [MODIFY] Add data-testid to message list container
│   ├── MessageBubble.tsx     # [MODIFY] Add data-testid to individual messages
│   ├── MessageComposer.tsx   # (already has data-testid)
│   ├── SessionsSidebar.tsx   # [MODIFY] Add data-testid to session list items, delete button
│   └── WorkspacePanel.tsx    # [MODIFY] Add data-testid to tab buttons, file tree nodes
├── common/
│   ├── CreateWorkspaceModal.tsx # (already has data-testid)
│   ├── FileTree.tsx          # [MODIFY] Add data-testid to tree nodes
│   └── ToolCard.tsx          # [MODIFY] Add data-testid to toggle, remove, install buttons
├── tools/
│   └── AddToolModal.tsx      # [MODIFY] Add data-testid to form inputs, submit button
└── layout/
    ├── AppShell.tsx           # (already has data-testid)
    ├── Sidebar.tsx            # [MODIFY] Add data-testid to nav items
    └── Header.tsx             # (already has data-testid)

# Frontend — Component Tests (Tier 1 — NEW)
apps/web/src/test/
├── setup.ts                  # [NEW] Vitest setup with DOM matchers
├── components/
│   ├── CreateWorkspaceModal.test.tsx  # [NEW]
│   ├── ChatLayout.test.tsx           # [NEW]
│   ├── SessionsSidebar.test.tsx      # [NEW]
│   ├── MessageComposer.test.tsx      # [NEW]
│   ├── FileTree.test.tsx             # [NEW]
│   └── ToolCard.test.tsx             # [NEW]
└── services/
    ├── log-store.test.ts             # [NEW]
    └── api-client.test.ts            # [NEW]

# Playwright — UI Integration Tests (Tier 2 — EXPAND)
tests/ui-integration/
├── dashboard.spec.ts         # [MODIFY] Add empty state, view-all, error scenarios
├── agent-chat.spec.ts        # [MODIFY] Add error states, loading states, session delete
├── workspace-panel.spec.ts   # [NEW] File tree, git operations, tool toggle
├── tool-registry.spec.ts     # [NEW] Full CRUD flow with all states
├── file-vault.spec.ts        # [NEW] File listing, preview, download
├── navigation.spec.ts        # (existing — already covers basic nav)
├── error-states.spec.ts      # [NEW] API failure scenarios across all pages
└── mcp-directory.spec.ts     # (existing — good coverage for CRUD)

# System E2E Tests (Tier 3 — NEW)
tests/e2e/
├── workspace-creation.spec.ts  # [NEW] Full stack: create workspace via API, verify in UI
└── smoke.spec.ts               # [NEW] Health check smoke test
```

**Structure Decision**: Follows the existing modular monorepo layout. Key structural additions:
- `apps/api/src/api/schemas/` — Extract Pydantic models from routers (reduces router line counts)
- `apps/api/src/api/middleware/` — OTel tracing middleware (auto-creates spans for every request)
- `apps/api/src/api/services/` — Business logic extracted from routers (Hermes sync, etc.)
- `packages/core/src/core/tracing.py` — Shared OTel utilities accessible to all packages
- `apps/web/src/services/log-store.ts` — IndexedDB persistence layer for frontend logs
- `apps/web/src/services/api-client.ts` — Centralized fetch wrapper for auto-tracing

## Complexity Tracking

No constitution violations requiring justification.

---

## Proposed Changes (by Component)

### Component 1: Backend Observability Infrastructure

#### [NEW] [tracing.py](file:///home/burhop/repos/wright/packages/core/src/core/tracing.py)

Shared OpenTelemetry tracer factory and instrumentation utilities used by all backend packages.

- `get_tracer(component: str) -> Tracer` — Returns a named tracer from the `wright.api` service
- `@traced(span_name: str)` — Decorator that wraps any function in an OTel span with automatic error recording
- `traced_db(span_name: str, db_path: str, query: str, params: tuple)` — Context manager that creates a `db.sqlite.query` or `db.sqlite.execute` child span with parameterized statement attribute
- All spans follow the semantic hierarchy from the spec: `workspace.create`, `workspace.files.list`, `agent.chat.start`, `mcp.server.register`, `db.sqlite.query`, etc.

#### [NEW] [logging.py](file:///home/burhop/repos/wright/packages/core/src/core/logging.py)

Shared structlog configuration used by all backend packages.

- `configure_logging()` — One-time structlog configuration with JSON renderer, trace_id processor, timestamp, log level
- `get_logger(name: str)` — Returns a bound structlog logger with the component name
- Automatically binds `trace_id` from the active OTel span context to every log entry

#### [NEW] [tracing.py](file:///home/burhop/repos/wright/apps/api/src/api/middleware/tracing.py)

FastAPI middleware that automatically creates a root span for every HTTP request.

- Extracts `X-Trace-Id` header from incoming requests (propagated from frontend)
- Creates a root span named by the route pattern (e.g., `workspace.files.list`)
- Sets span attributes: `http.method`, `http.url`, `http.status_code`, `http.route`
- On error, records exception and sets span status to ERROR
- Injects `trace_id` into the request state for downstream handlers

---

### Component 2: Workspace Router Refactor

#### [NEW] [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/schemas/workspace.py)

Extract all 25+ Pydantic models from the workspace router into a dedicated schema module:
- `WorkspaceNodeResponse`, `FileCreateRequest`, `FileMoveRequest`, `FileMoveResponse`
- `GitStatusItem`, `GitStatusResponse`, `GitDiffResponse`, `GitRevertRequest`, `GitRevertResponse`
- `GitCommitRequest`, `GitCommitResponse`, `GitCommitInfo`, `GitHistoryResponse`
- `WorkspaceTreeResponse`, `FileContentSaveRequest`, `FileContentSaveResponse`
- `WorkspaceToolsGetResponse`, `WorkspaceToolToggleRequest`, `WorkspaceToolToggleResponse`
- `WorkspaceListEntry`, `WorkspaceListResponse`, `WorkspaceCreateRequest`
- `WorkspaceActivateRequest`, `WorkspaceActivateResponse`
- `WorkspaceConfigRequest`, `WorkspaceConfigResponse`, `WorkspaceConfigGetResponse`
- `GitPushPullRequest`, `GitPushPullResponse`, `ContextSaveRequest`
- `DefaultWorkspaceDirResponse`

#### [NEW] [common.py](file:///home/burhop/repos/wright/apps/api/src/api/schemas/common.py)

Standardized error response schema:
- `ErrorResponse(error_code: str, message: str, trace_id: str, details: dict | None = None)`
- Used by custom exception handlers registered in `main.py`

#### [NEW] [hermes_sync.py](file:///home/burhop/repos/wright/apps/api/src/api/services/hermes_sync.py)

Extract the 100-line `sync_workspace_tools_to_hermes()` function and duplicate in mcp router into this service module:
- `sync_tools_to_hermes_config(session_id: str, db_path: str)` — Main sync function
- `restart_hermes_background()` — Hermes restart utility
- Removes duplicate code from both `workspace.py` and `mcp.py` routers

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py)

**Target: < 300 lines** (currently 965 lines).

Changes:
- Remove all Pydantic model definitions (moved to `schemas/workspace.py`)
- Remove `sync_workspace_tools_to_hermes()` (moved to `services/hermes_sync.py`)
- Remove `_parse_enabled_tools()` and `_serialize_workspace()` helper functions (moved to schemas or core)
- Replace `import logging` with `structlog.get_logger()`
- Add OTel span creation using `@traced` decorator on every endpoint handler
- Extract direct SQL in `activate_workspace_endpoint` into core function `activate_workspace(db_path, session_id)`
- All handlers become thin: parse request → call core function → return response

#### [MODIFY] [agent.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/agent.py)

- Add consistent `ErrorResponse` usage for all error paths
- Ensure `trace_id` is set as response header `X-Trace-Id`

#### [MODIFY] [mcp.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/mcp.py)

- Add `@traced` decorator to all endpoint handlers
- Remove `sync_mcp_server_to_hermes()` inline function (use `services/hermes_sync.py`)
- Add consistent `ErrorResponse` usage

#### [MODIFY] [main.py](file:///home/burhop/repos/wright/apps/api/src/api/main.py)

- Import and register OTel tracing middleware
- Configure structlog globally via `core.logging.configure_logging()`
- Register custom exception handler that returns `ErrorResponse` with `trace_id`
- Replace `print()` calls with structured logger

---

### Component 3: Core Package Updates

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/packages/core/src/core/workspace.py)

- Add `activate_workspace(db_path, session_id, engine)` function — extracted from router
- Add `sync_workspace_runners(db_path, session_id, mcp_engine)` function — extracted from router
- Wrap all SQLite operations with `traced_db` for `db.sqlite.query`/`db.sqlite.execute` spans
- Replace any `print()` calls with structlog

---

### Component 4: Frontend Observability Infrastructure

#### [NEW] [log-store.ts](file:///home/burhop/repos/wright/apps/web/src/services/log-store.ts)

IndexedDB-backed log persistence store:
- Database: `wright-logs`, Object store: `entries`
- `addEntry(entry: LogEntry): Promise<void>` — Async write with batch buffering (flush every 500ms or 50 entries)
- `query(filters: LogFilter): Promise<LogEntry[]>` — Filter by level, component, traceId, time range
- `prune(maxEntries: number): Promise<void>` — Delete oldest entries beyond retention limit
- `getRecentEntries(limit: number): Promise<LogEntry[]>` — For future Log Viewer
- Graceful fallback to console-only if IndexedDB unavailable (incognito mode)

#### [NEW] [api-client.ts](file:///home/burhop/repos/wright/apps/web/src/services/api-client.ts)

Centralized fetch wrapper with automatic tracing and error capture:
- `apiClient.get(url, options)` / `.post()` / `.put()` / `.delete()` / `.patch()`
- Automatically creates `api.fetch` span as child of active UI span
- Sets `X-Trace-Id` header from active OTel context
- On failure: logs structured error entry with HTTP status, URL, error message, trace_id, duration_ms
- Returns typed responses with proper error handling

#### [MODIFY] [logger.ts](file:///home/burhop/repos/wright/apps/web/src/services/logger.ts)

- Import and use `LogStore` from `log-store.ts`
- On every `log()` call, write to both console AND IndexedDB
- Add `sessionId` field to LogEntry (from active workspace context)
- Add configurable retention limit (default: 10,000 entries)

#### [MODIFY] [telemetry.ts](file:///home/burhop/repos/wright/apps/web/src/services/telemetry.ts)

- Add `startUISpan(name: string, attributes?: Record)` helper for page components
- Integrate `api.fetch` span creation into centralized api-client
- Add `ui.error.boundary` span creation for React error boundaries

#### [MODIFY] All service files ([agent-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/agent-service.ts), [workspace-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/workspace-service.ts), [mcp-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/mcp-service.ts), [health-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/health-service.ts))

- Replace direct `fetch()` calls with `apiClient.*` from api-client.ts
- This automatically instruments all API calls with OTel spans and error logging

---

### Component 5: data-testid Audit & Remediation

All interactive elements across all components MUST have `data-testid` following `{component}-{element}-{qualifier}` convention.

#### [MODIFY] [DashboardPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/DashboardPage.tsx)

Add missing `data-testid`:
- `dashboard-workspace-card-{id}` on each workspace row
- `dashboard-workspace-empty-state` on empty state div
- `dashboard-view-all-btn` on view-all button (currently `id` only)
- `dashboard-create-workspace-btn` (currently `id` only, add `data-testid`)
- `dashboard-tool-registry-card` and `dashboard-file-vault-card` on feature Link cards

#### [MODIFY] [ToolRegistryPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/ToolRegistryPage.tsx)

Add missing `data-testid`:
- `tool-registry-register-btn` on register button
- `tool-registry-search-input` on search/filter input
- `tool-registry-server-card-{id}` on each server card

#### [MODIFY] [FileVaultPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/FileVaultPage.tsx)

Add missing `data-testid`:
- `file-vault-file-list` on file list container
- `file-vault-file-item-{path}` on each file entry
- `file-vault-preview-panel` on preview area
- `file-vault-download-btn` on download button

#### [MODIFY] [SessionsSidebar.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/SessionsSidebar.tsx)

- `sessions-sidebar-item-{id}` on each session list item
- `sessions-sidebar-delete-btn-{id}` on delete button per session

#### [MODIFY] [WorkspacePanel.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/WorkspacePanel.tsx)

- `workspace-panel-tab-{name}` on each tab button (files, git, settings, marketplace)
- `workspace-panel-file-node-{path}` on file tree nodes

#### [MODIFY] [ChatTranscript.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/ChatTranscript.tsx)

- `chat-message-{id}` on each message bubble wrapper

#### [MODIFY] [MessageBubble.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/MessageBubble.tsx)

- `message-bubble-{role}-{id}` on each rendered bubble

#### [MODIFY] [FileTree.tsx](file:///home/burhop/repos/wright/apps/web/src/components/common/FileTree.tsx)

- `file-tree-node-{path}` on each tree node
- `file-tree-expand-btn-{path}` on expand/collapse buttons

#### [MODIFY] [ToolCard.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/ToolCard.tsx)

- `tool-card-toggle-{id}` on activation toggle
- `tool-card-install-btn-{id}` on install button
- `tool-card-remove-btn-{id}` on remove button

#### [MODIFY] [AddToolModal.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/AddToolModal.tsx)

- `add-tool-name-input` on name field
- `add-tool-type-select` on type dropdown
- `add-tool-command-input` on command field
- `add-tool-submit-btn` on submit button
- `add-tool-cancel-btn` on cancel button

---

### Component 6: API Tests (pytest)

#### [MODIFY] [conftest.py](file:///home/burhop/repos/wright/apps/api/tests/conftest.py)

- Add shared `mock_agent_engine` fixture factory
- Add `traced_client` fixture that validates OTel span creation
- Add helper to assert ErrorResponse schema in error tests

#### [MODIFY] [test_workspace_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_workspace_api.py)

Add missing tests:
- `test_create_workspace_invalid_name` — empty name returns 400
- `test_create_workspace_invalid_path` — non-absolute path returns 400
- `test_get_workspace_by_id_not_found` — returns 404
- `test_save_agent_context_roundtrip` — save + load returns same data
- `test_load_agent_context_not_found` — returns 404
- `test_activate_workspace_not_found` — session not in DB returns appropriate response
- `test_default_dir_endpoint` — returns expected path
- `test_error_responses_include_trace_id` — all 4xx/5xx responses have trace_id

#### [NEW] [test_agent_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_agent_api.py)

Complete test coverage for agent router:
- `test_create_session_success` — POST /api/agent/sessions/new returns session_id
- `test_create_session_backend_failure` — returns 502 with error detail
- `test_list_sessions_success` — GET /api/agent/sessions returns list
- `test_list_sessions_empty` — returns empty list
- `test_delete_session_success` — DELETE /api/agent/sessions/{id} returns ok
- `test_delete_session_not_found` — returns 404
- `test_start_chat_success` — POST /api/agent/chat/start returns stream_id + trace_id
- `test_start_chat_backend_failure` — returns 502
- `test_chat_stream_sse_events` — GET /api/agent/chat/stream returns SSE events
- `test_get_active_agent` — GET /api/agent/active returns agent name
- `test_set_active_agent` — POST /api/agent/active updates agent
- `test_health_endpoints` — GET /api/health, /api/agent/health, /api/inference/health

#### [MODIFY] [test_mcp_api.py](file:///home/burhop/repos/wright/apps/api/tests/test_mcp_api.py)

Add missing tests:
- `test_toggle_tool_not_found` — returns 404
- `test_delete_server_not_found` — returns 404
- `test_install_server_success` — POST /servers/{id}/install
- `test_uninstall_server_success` — POST /servers/{id}/uninstall
- `test_install_server_not_found` — returns 404

#### [NEW] [test_tracing.py](file:///home/burhop/repos/wright/apps/api/tests/test_tracing.py)

- `test_request_creates_span` — verify OTel span is created for workspace.files.list
- `test_trace_id_in_response_header` — verify X-Trace-Id header present
- `test_error_span_records_exception` — verify exception recorded on 500
- `test_db_operation_creates_child_span` — verify db.sqlite.query is child of request span

---

### Component 7: Playwright Tests (Tier 2)

#### [MODIFY] [dashboard.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/dashboard.spec.ts)

Add:
- `test: should display empty state when no workspaces exist`
- `test: should display workspace list with correct data`
- `test: should show error state when API fails`
- `test: should toggle view-all workspaces`
- `test: should show validation errors in create modal`

#### [MODIFY] [agent-chat.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/agent-chat.spec.ts)

Add:
- `test: should display error state when workspace not found`
- `test: should show loading indicator while workspace loads`
- `test: should handle chat API error gracefully`
- `test: should delete a session`
- `test: should display workspace panel with file tree`

#### [NEW] [workspace-panel.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/workspace-panel.spec.ts)

- `test: should display file tree from workspace files API`
- `test: should create a new file via file tree`
- `test: should display git status`
- `test: should commit changes through git panel`
- `test: should toggle workspace tools`
- `test: should switch between panel tabs (files, git, settings)`

#### [NEW] [tool-registry.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/tool-registry.spec.ts)

- `test: should list all registered tools`
- `test: should register a custom tool via modal`
- `test: should toggle tool activation`
- `test: should install a tool`
- `test: should uninstall a tool`
- `test: should delete a tool with confirmation`
- `test: should show error when registration fails`

#### [NEW] [file-vault.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/file-vault.spec.ts)

- `test: should list vault files`
- `test: should preview an STL file`
- `test: should preview a code file`
- `test: should display empty vault state`

#### [NEW] [error-states.spec.ts](file:///home/burhop/repos/wright/tests/ui-integration/error-states.spec.ts)

- `test: should show error when workspace API returns 500`
- `test: should show error when workspace not found (404)`
- `test: should show loading indicators during API calls`
- `test: should handle network timeout gracefully`

---

### Component 8: Vitest Component Tests (Tier 1)

#### [NEW] [setup.ts](file:///home/burhop/repos/wright/apps/web/src/test/setup.ts)

Vitest test setup with `@testing-library/react`, `@testing-library/jest-dom` matchers, and mock providers.

#### [NEW] Component test files (6 components)

Each test file covers 3 states: default render, loading state, error state + user interaction.

- `CreateWorkspaceModal.test.tsx` — modal open/close, form validation, submit success, submit error
- `ChatLayout.test.tsx` — renders three-panel layout, sidebar toggle
- `SessionsSidebar.test.tsx` — empty list, populated list, create session click, delete session click
- `MessageComposer.test.tsx` — empty input disabled, type + send, keyboard shortcut
- `FileTree.test.tsx` — render tree, expand/collapse, click file, empty tree
- `ToolCard.test.tsx` — render card data, toggle activation, install click, remove click

---

### Component 9: System E2E Tests (Tier 3)

#### [NEW] [workspace-creation.spec.ts](file:///home/burhop/repos/wright/tests/e2e/workspace-creation.spec.ts)

Full-stack test against live API:
- POST /api/workspace/create → verify workspace created in SQLite
- Navigate to /workspace/{id} → verify page renders with file tree
- Requires API server running (uses `webServer` in playwright config)

#### [NEW] [smoke.spec.ts](file:///home/burhop/repos/wright/tests/e2e/smoke.spec.ts)

Health check smoke test:
- GET /api/health → 200, state: connected
- GET / → dashboard page renders
- Navigate to each section → no crashes

---

## Verification Plan

### Automated Tests

All tests MUST pass at 100%. Any failure blocks completion.

1. **Backend API tests**: `cd apps/api && PYTHONPATH=src uv run pytest tests/ -v --tb=short`
   - Expected: All tests pass, covering every public endpoint
2. **Frontend component tests**: `cd apps/web && npx vitest run`
   - Expected: All 6+ component test files pass
3. **Playwright UI integration**: `npx playwright test tests/ui-integration/`
   - Expected: All spec files pass covering all pages
4. **Playwright E2E**: `npx playwright test tests/e2e/`
   - Expected: Workspace creation and smoke tests pass against live stack
5. **Lint check**: Verify zero `import logging` in any router file
6. **Line count**: `wc -l apps/api/src/api/routers/workspace.py` → under 300

### Manual Verification

1. Open Jaeger UI at `http://localhost:16686` — verify traces appear with semantic span names
2. Open browser DevTools console — verify structured JSON log entries
3. Check IndexedDB in DevTools → Application → IndexedDB → `wright-logs` → entries exist
4. Trigger an API error (e.g., navigate to `/workspace/invalid-id`) — verify error response contains `trace_id`
