"""
Standardized error response schema for all Wright API error responses.

Per contracts/error-response.md: All 4xx/5xx responses MUST conform to this schema.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized API error response payload.

    Every error response includes a trace_id for end-to-end correlation
    between frontend and backend.
    """

    error_code: str
    message: str
    trace_id: str
    details: dict | None = None


# Error code constants for consistent usage across routers
class ErrorCodes:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    WORKSPACE_NOT_FOUND = "WORKSPACE_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SERVER_NOT_FOUND = "SERVER_NOT_FOUND"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    DUPLICATE_ENTITY = "DUPLICATE_ENTITY"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    MCP_ENGINE_ERROR = "MCP_ENGINE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    GIT_ERROR = "GIT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
