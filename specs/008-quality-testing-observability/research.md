# Research: Quality, Testing & Observability Refactor

**Date**: 2026-06-03

## Decision 1: Frontend Log Persistence Strategy

**Decision**: Use IndexedDB via the `idb` library for frontend log persistence.

**Rationale**: IndexedDB is the only browser-native persistence API that supports structured queries (by index), async operations, and large storage quotas (typically 50% of disk). It's available in all Chromium-based browsers which is the target platform.

**Alternatives considered**:
- **localStorage**: Rejected — 5MB limit, synchronous API would block UI thread, no query capability
- **sessionStorage**: Rejected — cleared on tab close, not persistent
- **Backend log endpoint**: Rejected — violates offline-first mandate; adds network dependency
- **Service Worker with Cache API**: Rejected — overly complex for structured log queries

**Implementation Note**: Use the `idb` library (4KB gzipped, zero dependencies) for a Promise-based wrapper around IndexedDB. Already compatible with Vite bundler.

## Decision 2: OpenTelemetry Backend Instrumentation Approach

**Decision**: Use a FastAPI middleware + `@traced` decorator pattern rather than auto-instrumentation.

**Rationale**: The `opentelemetry-instrumentation-fastapi` auto-instrumentor creates spans with generic names like `GET /api/workspace/{workspace_id}/files`. Our spec requires semantic domain names like `workspace.files.list`. Manual instrumentation via a thin middleware + decorator gives full control over span naming, attribute selection, and parent-child relationships.

**Alternatives considered**:
- **Auto-instrumentation (`opentelemetry-instrumentation-fastapi`)**: Rejected — generates generic span names, no control over attributes, creates noise for health endpoints
- **Manual span creation in every handler**: Rejected — too verbose, violates DRY
- **Decorator-only (no middleware)**: Rejected — middleware handles common concerns (trace_id extraction, response header injection) that decorators can't easily share

**Implementation Note**: The middleware creates the root span and extracts/generates trace_id. The `@traced` decorator on individual handlers adds domain-specific attributes. Database operations use the `traced_db` context manager for child spans.

## Decision 3: Frontend-to-Backend Trace Correlation

**Decision**: Propagate `trace_id` via the `X-Trace-Id` HTTP header on all API requests from the frontend.

**Rationale**: W3C `traceparent` header requires full OTel context propagation which is heavier than needed for a single-user local app. A simple custom header is lightweight, easy to implement, and provides the key correlation value.

**Alternatives considered**:
- **W3C Trace Context (`traceparent` header)**: Rejected for now — overkill for single-user local app; can be added later when distributed tracing across services is needed
- **Query parameter**: Rejected — clutters URLs, not idiomatic for trace correlation
- **No correlation**: Rejected — violates constitution §7 agent traceability mandate

## Decision 4: Vitest Configuration for React Components

**Decision**: Use Vitest with `@testing-library/react` and `jsdom` environment.

**Rationale**: Vitest is the natural test runner for Vite projects (zero config needed). `@testing-library/react` encourages testing user interactions rather than implementation details, which aligns with the constitution's focus on user journeys.

**Alternatives considered**:
- **Jest**: Rejected — requires additional configuration for ESM modules and Vite compatibility; Vitest is drop-in compatible with the existing Vite setup
- **Storybook play functions**: Considered for Tier 1 per constitution §6, but Vitest is faster for CI and doesn't require a running Storybook server

**Implementation Note**: Add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, and `@testing-library/user-event` as dev dependencies.

## Decision 5: Error Response Standardization

**Decision**: Implement a global `ErrorResponse` Pydantic model and register FastAPI exception handlers that ensure all errors return this schema.

**Rationale**: Currently, error responses are ad-hoc — some include `detail` (FastAPI default), others are custom strings. A standardized schema with `error_code`, `message`, `trace_id`, and optional `details` makes frontend error handling consistent and enables the future Log Viewer to correlate errors.

**Schema**:
```python
class ErrorResponse(BaseModel):
    error_code: str     # e.g., "WORKSPACE_NOT_FOUND", "VALIDATION_ERROR"
    message: str        # Human-readable error description
    trace_id: str       # OTel trace ID for correlation
    details: dict | None = None  # Optional structured error context
```

## Decision 6: Workspace Router Refactoring Strategy

**Decision**: Extract in three passes: (1) Pydantic models → `schemas/workspace.py`, (2) business logic → `core/workspace.py` + `services/hermes_sync.py`, (3) add tracing + structlog.

**Rationale**: Doing all three at once risks introducing bugs. The three-pass approach lets us verify each step independently:
- After pass 1: existing API tests still pass (models just moved, imported differently)
- After pass 2: existing API tests still pass (handlers now delegate to core)
- After pass 3: new tracing tests verify spans are created correctly

## Decision 7: IndexedDB Log Retention Strategy

**Decision**: FIFO eviction with a configurable max entry count (default: 10,000). Pruning runs on a debounced timer, not on every write.

**Rationale**: Time-based retention (e.g., "keep 7 days") is harder to manage because log volume varies dramatically. Entry-count-based FIFO is simpler, predictable in storage usage, and easy to implement with IndexedDB cursor operations.

**Implementation Note**: Prune check runs every 100 writes. When triggered, delete the oldest entries beyond the limit in a single transaction.
