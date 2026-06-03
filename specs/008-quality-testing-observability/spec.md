# Feature Specification: Quality, Testing & Observability Refactor

**Feature Branch**: `008-quality-testing-observability`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "Review project against constitution.md and identify compliance gaps. Refactor for clean code, clear interfaces, extensive Playwright tests covering all user stories/use cases, complete API tests, and improved logging/telemetry with future Log Viewer support. Ensure all failures are captured."

## Constitution Compliance Audit

Before defining the feature, here is a systematic audit of current compliance against each constitution section:

| § | Area | Status | Finding |
|---|------|--------|---------|
| 1 | FastAPI, zero business logic in routes | ⚠️ Partial | `workspace.py` router (965 lines) contains direct SQL queries in `activate_workspace_endpoint` (lines 888-900) and inline `sync_workspace_tools_to_hermes` (lines 644-743). Business logic must route to `core/` packages. |
| 2 | Agent Abstraction (Adapter Pattern) | ✅ Pass | `BaseAgentEngine` with `HermesAdapter` implementation. `save_context`/`load_context` abstract methods present. |
| 3 | Zero-server databases (SQLite + LanceDB) | ✅ Pass | All data in SQLite WAL mode. |
| 4 | Local Authentication (OAuth2PasswordBearer) | ⚠️ Missing | No authentication middleware exists anywhere. All API endpoints are unauthenticated. CORS is `allow_origins=["*"]`. |
| 5 | Template Method for tools | ✅ Pass | `BaseTool` pattern in tool_registry. |
| 6 | Tier 1 Component Tests | ❌ Fail | **Zero** Vitest/Storybook component tests exist. No `apps/web/tests/` with component-level specs. |
| 6 | Tier 2 UI Integration (Playwright) | ⚠️ Partial | Only 5 spec files (249 + 219 + 24 + 45 + 10 = ~100 assertions). Many user journeys untested: File Vault, error states, loading states, workspace panel interactions, git operations UI, tool toggle UI. |
| 6 | Tier 3 System E2E | ❌ Fail | `tests/e2e/` directory contains only `.gitkeep`. Zero system E2E tests against live backend. |
| 6 | Test IDs (`data-testid`) | ⚠️ Partial | 23 components have `data-testid` attributes, but coverage is inconsistent. Several interactive elements (buttons, inputs, links, toggles) in DashboardPage, ToolRegistryPage, and FileVaultPage lack test IDs. **Every** interactive element MUST have a unique, descriptive `data-testid`. |
| 7 | Structured JSON Logging (`structlog`) | ❌ Fail | `workspace.py` router uses `import logging` (stdlib). Only `agent.py` and `mcp.py` use `structlog`. Constitution forbids traditional text logs. |
| 7 | OpenTelemetry Tracing + Jaeger | ⚠️ Partial | Only `agent.py` router creates trace spans. `workspace.py` (35+ endpoints, largest router) has **zero** OTel instrumentation. No traces for database reads/writes, tool execution, or file operations. Span naming is ad-hoc with no semantic convention. |
| 7 | Agent Traceability (trace_id propagation) | ⚠️ Partial | `trace_id` generated and bound in agent router but not propagated to `workspace.py`, `mcp.py`, or `core/workspace.py`. No correlation between frontend and backend spans. |
| 7 | Mandatory Spans | ❌ Fail | Missing spans for: LLM inference timing, tool execution success/failure, database reads/writes to SQLite, file vault operations. No span hierarchy or parent-child relationships defined. |
| 7 | UI Transparency (decision matrices) | ⚠️ Partial | Frontend has `telemetry.ts` with span tracking and `logger.ts` with structured JSON output, but logs only go to `console.*`. No persistence, no collection endpoint, no viewer. |
| 8 | Phase Isolation + Branch Discipline | ✅ Pass | Using speckit workflow with feature branches. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Developer Debugs a Failing Workspace Operation (Priority: P1)

A developer encounters an error when creating or activating a workspace. They need structured, traceable logs with full context (trace_id, request params, error details) to diagnose the root cause without guesswork.

**Why this priority**: Logging/traceability is the foundation for all debugging. Without it, every other feature is harder to diagnose and maintain.

**Independent Test**: Can be tested by triggering workspace operations, then verifying structured JSON log entries contain trace_id, operation context, and error details.

**Acceptance Scenarios**:

1. **Given** a workspace creation request, **When** the request is processed, **Then** all backend log entries are structured JSON with `trace_id`, `component`, `operation`, `duration_ms`, and relevant request parameters.
2. **Given** any API endpoint failure, **When** an exception is raised, **Then** the error is logged with full stack trace, trace_id, request context, and a unique error reference ID.
3. **Given** the workspace router processes a request, **When** the request completes, **Then** an OpenTelemetry span covers the full request lifecycle including database calls.
4. **Given** a frontend user action triggers an API call, **When** the call fails, **Then** the frontend logger captures the error with trace_id, action name, and HTTP status code, and persists it to local storage for later retrieval.

---

### User Story 2 — Developer Runs Comprehensive API Tests Before Deploying (Priority: P1)

A developer wants to run a complete pytest suite that covers all API endpoints — including happy paths, validation errors, edge cases, and failure scenarios — to catch regressions before they reach production.

**Why this priority**: API tests are the fastest safety net. The current test suite covers only workspace CRUD and git operations but misses agent endpoints, MCP endpoints, context endpoints, error paths, and input validation.

**Independent Test**: Can be tested by running `pytest apps/api/tests/` and verifying all tests pass with >90% endpoint coverage.

**Acceptance Scenarios**:

1. **Given** the API test suite, **When** `pytest` runs, **Then** every public API endpoint has at least one happy-path test and one error-path test.
2. **Given** a workspace creation request with invalid data (empty name, non-existent path), **When** submitted, **Then** the API returns 400 with a descriptive error and the test asserts the response body.
3. **Given** agent session endpoints (`POST /sessions/new`, `GET /sessions`, `DELETE /sessions/{id}`, `POST /chat/start`, `GET /chat/stream`), **When** tests run, **Then** each endpoint is covered with success and failure scenarios.
4. **Given** MCP endpoints (`GET /servers`, `POST /register`, `PUT /toggle/{id}`, `DELETE /{id}`), **When** tests run, **Then** each endpoint is covered with success and failure scenarios.
5. **Given** workspace context endpoints (`POST /by-id/{id}/context/save`, `GET /by-id/{id}/context/load`), **When** tests run, **Then** save/load roundtrip is verified, and 404 for non-existent workspace is tested.

---

### User Story 3 — QA Engineer Validates All UI User Journeys with Playwright (Priority: P1)

A QA engineer runs the Playwright suite and it covers every major user journey in the application — dashboard navigation, workspace creation, workspace interaction (file tree, git, chat), tool registry management, and file vault browsing — with both success and failure scenarios.

**Why this priority**: The current 5 Playwright spec files are insufficient. Multiple bugs have been discovered post-testing that would have been caught by comprehensive UI integration tests.

**Independent Test**: Can be tested by running `npx playwright test` and verifying all test suites pass covering every page and major interaction flow.

**Acceptance Scenarios**:

1. **Given** the Playwright test suite, **When** all tests run, **Then** every page in the application has a dedicated spec file with tests covering its primary user flows.
2. **Given** the Dashboard page, **When** tests run, **Then** the following are tested: workspace list rendering (empty state, populated state), workspace card click navigation, Create Workspace modal (open, fill, auto-path, submit, cancel, validation errors), "View all workspaces" navigation.
3. **Given** the Workspace page, **When** tests run, **Then** the following are tested: workspace loading from URL param, file tree display, file creation/deletion, git status display, git commit flow, session creation, message sending, streaming response rendering, tool/progress display, workspace panel toggle, error states (workspace not found, API failure).
4. **Given** the Tool Registry page, **When** tests run, **Then** the following are tested: tool list rendering, tool card display, register custom tool (form fill + submit), toggle tool active/inactive, remove tool (with confirmation dialog), search/filter tools.
5. **Given** the File Vault page, **When** tests run, **Then** the following are tested: file list rendering, file preview (STL viewer, code viewer), file download.
6. **Given** any page, **When** the backend API returns an error, **Then** the test verifies a user-friendly error state is displayed (not a blank screen or unhandled exception).
7. **Given** any page, **When** the backend API is slow or disconnected, **Then** loading indicators are displayed and timeouts are handled gracefully.
8. **Given** the full Playwright suite, **When** all tests run, **Then** **100% of tests pass**. Any test failure blocks the feature from being marked complete.

---

### User Story 4 — Developer Refactors Workspace Router for Clean Interfaces (Priority: P2)

A developer opens the workspace router and finds it well-organized with clear separation: each endpoint handler is thin (dispatches to core), all models are in a separate schema file, and the file is under 300 lines.

**Why this priority**: The 965-line workspace router violates the constitution's "zero business logic in routes" mandate and is difficult to maintain. Clean interfaces make future development faster and bugs easier to spot.

**Independent Test**: Can be tested by verifying the workspace router file is under 300 lines, all business logic is in `core/workspace.py`, and all Pydantic models are in a separate schemas file.

**Acceptance Scenarios**:

1. **Given** the workspace router, **When** a developer opens it, **Then** it contains only endpoint handler functions with no business logic — all operations dispatch to functions in `core/workspace.py`.
2. **Given** the workspace router, **When** a developer reviews it, **Then** all Pydantic request/response models are in a separate `schemas/workspace.py` file, imported by the router.
3. **Given** the `activate_workspace_endpoint`, **When** reviewed, **Then** it contains zero direct SQL queries — all database operations are delegated to core functions.
4. **Given** `sync_workspace_tools_to_hermes` (currently a 100-line function embedded in the router), **When** reviewed, **Then** it has been moved to a service module with clean interfaces.

---

### User Story 5 — Developer Integrates Frontend Log Persistence for Future Log Viewer (Priority: P2)

A developer wants frontend logs to be persisted locally (IndexedDB) so that a future Log Viewer page can display them. Currently, logs only go to `console.*` and are lost when the browser refreshes.

**Why this priority**: Constitution §7 requires UI transparency and agent traceability. A persistent log store is the prerequisite for the planned Log Viewer feature. Capturing all failures now means no debugging data is lost.

**Independent Test**: Can be tested by triggering UI actions, then querying the local log store to verify entries exist with proper structure and trace correlation.

**Acceptance Scenarios**:

1. **Given** the frontend logger, **When** any log entry is created, **Then** it is persisted to IndexedDB in addition to being written to console.
2. **Given** the log store, **When** queried, **Then** each entry contains: `timestamp`, `level`, `message`, `component`, `traceId`, `metadata`, and `sessionId`.
3. **Given** an API call failure, **When** the error is logged, **Then** the log entry includes: HTTP status, endpoint URL, error message, trace_id, and request duration.
4. **Given** the log store grows beyond a configurable retention limit (default: 10,000 entries), **When** new entries are added, **Then** the oldest entries are automatically pruned.
5. **Given** a future Log Viewer component, **When** it queries the log store, **Then** it can filter by level, component, traceId, and time range.

---

### User Story 6 — CI Pipeline Runs Full Test Suite with Confidence (Priority: P3)

A CI pipeline runs the full test suite (pytest API tests, Vitest component tests, Playwright E2E) and reports clear pass/fail status with coverage metrics.

**Why this priority**: Automated testing in CI prevents regressions from reaching production. Currently there is no component test infrastructure.

**Independent Test**: Can be tested by running all three test tiers locally and verifying they complete with meaningful coverage output.

**Acceptance Scenarios**:

1. **Given** the test pyramid, **When** a developer runs the full suite, **Then** Tier 1 (component), Tier 2 (UI integration), and Tier 3 (E2E) all execute without failures.
2. **Given** the Vitest component test suite, **When** tests run, **Then** critical interactive components (CreateWorkspaceModal, ChatLayout, SessionsSidebar, MessageComposer, FileTree, ToolCard) each have tests covering default, loading, error, and interactive states.
3. **Given** the Playwright config, **When** tests run, **Then** HTML reporter generates a test report with screenshots on failure.

---

### Edge Cases

- What happens when the SQLite database file is locked or corrupted during a workspace operation? — All database operations should catch and log SQLite-specific errors with structured diagnostics.
- How does the system handle concurrent workspace activations from multiple browser tabs? — SQLite WAL mode handles concurrency; the API should log and handle lock contention gracefully.
- What happens when frontend log storage (IndexedDB) is full or unavailable (incognito mode)? — Logger should fall back to console-only with a warning, never blocking the user.
- What happens when OpenTelemetry/Jaeger is unavailable? — Tracing should degrade gracefully; spans should still be created in-process for structured logging but export failures should not crash the application.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All backend routers MUST use `structlog` for structured JSON logging. Traditional `import logging` usage MUST be eliminated.
- **FR-002**: All API endpoints MUST generate and propagate a `trace_id` through the full request lifecycle (route handler → core function → database operation).
- **FR-003**: The workspace router MUST be refactored to contain zero business logic — all operations MUST delegate to `core/workspace.py` or dedicated service modules.
- **FR-004**: All Pydantic request/response models MUST be extracted from router files into dedicated schema modules.
- **FR-005**: Every public API endpoint MUST have at least one happy-path and one error-path pytest test. **All tests MUST pass at 100%.**
- **FR-006**: Every page in the frontend MUST have a Playwright spec file testing its primary user flows. **All tests MUST pass at 100%.**
- **FR-007**: Every interactive UI element (buttons, inputs, links, toggles, modals, dropdowns, cards) MUST have a unique `data-testid` attribute following the naming convention `{component}-{element}-{qualifier}` (e.g., `dashboard-create-workspace-btn`, `workspace-file-tree-node`, `tool-registry-register-btn`). A `data-testid` audit checklist MUST be maintained to verify 100% coverage.
- **FR-008**: The frontend logger MUST persist log entries to IndexedDB in addition to console output.
- **FR-009**: The frontend logger MUST capture all API call failures with HTTP status, endpoint URL, error message, trace_id, and request duration.
- **FR-010**: OpenTelemetry spans MUST follow the semantic hierarchy defined in the "OpenTelemetry Span Organization" section below. Every API endpoint, database operation, and external call MUST have a corresponding span.
- **FR-011**: Critical interactive components (CreateWorkspaceModal, ChatLayout, SessionsSidebar, MessageComposer, FileTree, ToolCard) MUST have Vitest component tests covering default, loading, and error states. **All tests MUST pass at 100%.**
- **FR-012**: The `tests/e2e/` directory MUST contain at least one system E2E test that verifies the live FastAPI backend + frontend integration. **All tests MUST pass at 100%.**
- **FR-013**: All API error responses MUST use a consistent error response schema with `error_code`, `message`, `trace_id`, and optional `details` fields.
- **FR-014**: The frontend log store MUST support querying by level, component, traceId, and time range to enable a future Log Viewer.
- **FR-015**: Log retention MUST be configurable with automatic pruning of entries beyond the limit (default: 10,000 frontend entries).

### Key Entities

- **LogEntry**: A structured log record with timestamp, level, message, component, traceId, sessionId, and metadata. Stored in IndexedDB on the frontend and emitted as structured JSON on the backend.
- **TraceContext**: Correlation context containing traceId, spanId, operation name, start time, duration, and status. Links frontend actions to backend operations.
- **ErrorResponse**: Standardized API error payload with error_code, message, trace_id, and details. Used across all API error responses for consistency.

## OpenTelemetry Span Organization *(mandatory)*

All spans MUST follow a semantic hierarchical naming convention to enable clear trace visualization in Jaeger. The organization separates concerns by domain and operation type.

### Backend Service: `wright.api`

| Domain | Span Name | Parent | Attributes |
|--------|-----------|--------|------------|
| **Workspace** | `workspace.create` | request root | `workspace.name`, `workspace.path` |
| | `workspace.activate` | request root | `workspace.id`, `session.id` |
| | `workspace.list` | request root | `workspace.count` |
| | `workspace.get` | request root | `workspace.id` |
| **Files** | `workspace.files.list` | request root | `workspace.path` |
| | `workspace.files.read` | request root | `file.path`, `file.size` |
| | `workspace.files.write` | request root | `file.path`, `content.length` |
| | `workspace.files.create` | request root | `file.path`, `file.type` |
| | `workspace.files.delete` | request root | `file.path` |
| | `workspace.files.move` | request root | `file.source`, `file.destination` |
| **Git** | `workspace.git.status` | request root | `git.branch`, `git.is_clean` |
| | `workspace.git.commit` | request root | `git.message`, `git.hash` |
| | `workspace.git.diff` | request root | `file.path` |
| | `workspace.git.revert` | request root | `file.path` |
| | `workspace.git.push` | request root | `git.remote_url` |
| | `workspace.git.pull` | request root | `git.remote_url`, `git.conflict` |
| **Agent** | `agent.session.create` | request root | `session.id`, `workspace.path` |
| | `agent.session.list` | request root | `session.count` |
| | `agent.session.delete` | request root | `session.id` |
| | `agent.chat.start` | request root | `session.id`, `message.length` |
| | `agent.chat.stream` | request root | `stream.id`, `token.count` |
| **MCP** | `mcp.server.register` | request root | `server.name`, `server.type` |
| | `mcp.server.list` | request root | `server.count` |
| | `mcp.server.toggle` | request root | `server.id`, `server.active` |
| | `mcp.server.delete` | request root | `server.id` |
| | `mcp.server.start` | request root | `server.id`, `server.pid` |
| | `mcp.server.stop` | request root | `server.id` |
| **Database** | `db.sqlite.query` | parent operation | `db.statement` (parameterized), `db.rows_affected` |
| | `db.sqlite.execute` | parent operation | `db.statement` (parameterized), `db.rows_affected` |

### Frontend Service: `wright.frontend`

| Domain | Span Name | Parent | Attributes |
|--------|-----------|--------|------------|
| **Navigation** | `ui.page.navigate` | — | `page.name`, `page.url` |
| **Workspace** | `ui.workspace.create` | — | `workspace.name` |
| | `ui.workspace.open` | — | `workspace.id` |
| | `ui.workspace.activate` | — | `workspace.id`, `session.id` |
| **Chat** | `ui.chat.send` | — | `session.id`, `message.length` |
| | `ui.chat.stream` | `ui.chat.send` | `token.count`, `duration_ms` |
| | `ui.chat.tool_execution` | `ui.chat.stream` | `tool.name`, `tool.progress` |
| **Files** | `ui.file.open` | — | `file.path`, `file.type` |
| | `ui.file.save` | — | `file.path` |
| **API Calls** | `api.fetch` | parent UI span | `http.method`, `http.url`, `http.status_code`, `duration_ms` |
| **Errors** | `ui.error.boundary` | — | `error.message`, `error.component`, `error.stack` |

### Span Rules

1. **Every API request** MUST create a root span named by its domain + operation (e.g., `workspace.create`).
2. **Database calls** MUST be child spans of the operation that triggered them (e.g., `db.sqlite.query` is a child of `workspace.create`).
3. **Frontend API calls** (`api.fetch`) MUST be child spans of the UI action that triggered them and MUST propagate `trace_id` to the backend via the `X-Trace-Id` HTTP header.
4. **Error spans** MUST set `status = ERROR` and record the exception with `span.record_exception()`.
5. **All spans** MUST include `trace_id` in their attributes for correlation with structured logs.
6. **Long-running operations** (chat streaming, git push/pull) MUST record intermediate events as span events, not separate spans.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All backend log output is valid structured JSON with trace_id correlation — zero traditional text log lines remain.
- **SC-002**: API test suite covers 100% of public endpoints with at least one happy-path and one error-path test each. **All tests pass at 100%.**
- **SC-003**: Playwright test suite covers all 5 application pages with tests for every primary user flow and acceptance scenario defined in this spec. **All tests pass at 100%.**
- **SC-004**: The workspace router file is under 300 lines after refactoring, with all business logic in core/service modules.
- **SC-005**: Frontend log entries persist across page refreshes and are queryable by level, component, and time range.
- **SC-006**: Every API error response includes a trace_id, enabling end-to-end request tracing from frontend to backend.
- **SC-007**: Interactive component test suite (Vitest) covers at least 6 critical components with state tests. **All tests pass at 100%.**
- **SC-008**: At least one system E2E test verifies the complete stack (frontend → API → SQLite) for the core workspace creation flow. **All tests pass at 100%.**
- **SC-009**: Every interactive UI element has a unique `data-testid` attribute following the `{component}-{element}-{qualifier}` naming convention. A `data-testid` audit confirms 100% coverage.
- **SC-010**: OpenTelemetry spans follow the semantic hierarchy defined above, with parent-child relationships correctly linking API requests to database operations and frontend actions to API calls.

## Assumptions

- The existing SQLite WAL-mode database schema does not require migration for this feature (logging/testing changes are application-layer).
- Vitest is the appropriate component testing framework given the existing Vite build setup.
- IndexedDB is available in the target browser environment (Chromium-based browsers for the local desktop appliance).
- OpenTelemetry SDK dependencies are already installed (`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp` in `apps/api/pyproject.toml`).
- The Log Viewer UI component itself is out of scope for this feature — only the log persistence and query infrastructure is included.
- Authentication (Constitution §4) is a separate feature and out of scope for this refactor.
