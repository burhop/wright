# Error Response Contract

**Date**: 2026-06-03

## Overview

All Wright API error responses (4xx, 5xx) MUST conform to this schema. This replaces the ad-hoc `{"detail": "..."}` responses currently returned by FastAPI default exception handlers.

## Schema

```json
{
  "error_code": "WORKSPACE_NOT_FOUND",
  "message": "Workspace with ID 'abc-123' does not exist.",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "details": {
    "workspace_id": "abc-123"
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error_code` | string | Yes | Machine-readable error identifier, UPPER_SNAKE_CASE |
| `message` | string | Yes | Human-readable description, safe to display to user |
| `trace_id` | string | Yes | OTel trace ID from the active span context |
| `details` | object | null | No | Optional structured context (request params, entity IDs, etc.) |

### Error Codes

| Code | HTTP Status | When |
|------|-------------|------|
| `VALIDATION_ERROR` | 400 | Request body fails Pydantic validation |
| `WORKSPACE_NOT_FOUND` | 404 | Workspace ID not found in database |
| `SESSION_NOT_FOUND` | 404 | Agent session not found |
| `SERVER_NOT_FOUND` | 404 | MCP server not found |
| `TOOL_NOT_FOUND` | 404 | MCP tool not found |
| `FILE_NOT_FOUND` | 404 | File path not found in workspace |
| `DUPLICATE_ENTITY` | 400 | Entity with same name already exists |
| `AGENT_UNAVAILABLE` | 502 | Agent engine (Hermes) is unreachable |
| `MCP_ENGINE_ERROR` | 500 | MCP engine operation failed |
| `DATABASE_ERROR` | 500 | SQLite operation failed |
| `GIT_ERROR` | 500 | Git operation failed |
| `INTERNAL_ERROR` | 500 | Unhandled server error |

### Response Headers

All error responses MUST include:
- `X-Trace-Id: {trace_id}` — same value as in the response body

## Backend Implementation

```python
# apps/api/src/api/schemas/common.py
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    trace_id: str
    details: dict | None = None
```

```python
# Registered in main.py as exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=_status_to_code(exc.status_code),
            message=str(exc.detail),
            trace_id=trace_id,
        ).model_dump(),
        headers={"X-Trace-Id": trace_id},
    )
```

## Frontend Consumption

```typescript
// api-client.ts error handling
interface ApiError {
  error_code: string;
  message: string;
  trace_id: string;
  details?: Record<string, unknown>;
}
```
