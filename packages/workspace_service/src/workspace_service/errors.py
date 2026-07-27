"""Typed application failures independent of HTTP and concrete adapters."""

from __future__ import annotations

from typing import Any

from core.errors import ErrorCode, ErrorDetail, WrightError


class WorkspaceServiceError(WrightError):
    code = "workspace.error"

    def __init__(
        self,
        message: str,
        *,
        error_code: ErrorCode = ErrorCode.INTERNAL,
        operation: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            ErrorDetail(error_code, message, operation=operation, context=context or {})
        )


class WorkspaceNotFoundError(WorkspaceServiceError):
    code = "workspace.not_found"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=ErrorCode.NOT_FOUND, **kwargs)


class WorkspaceConflictError(WorkspaceServiceError):
    code = "workspace.conflict"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=ErrorCode.CONFLICT, **kwargs)


class WorkspaceInvalidRequestError(WorkspaceServiceError):
    code = "workspace.invalid_request"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=ErrorCode.INVALID_INPUT, **kwargs)


class WorkspaceExecutionError(WorkspaceServiceError):
    code = "workspace.execution_failed"


class WorkspaceTimeoutError(WorkspaceServiceError):
    code = "workspace.timeout"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=ErrorCode.TIMEOUT, **kwargs)


class WorkspaceCancelledError(WorkspaceServiceError):
    code = "workspace.cancelled"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, error_code=ErrorCode.CANCELLED, **kwargs)
