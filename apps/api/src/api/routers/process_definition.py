"""Authenticated read-only route for one immutable process definition."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse
from tool_registry.process_definition import (
    ProcessDefinitionErrorCode,
    ProcessDefinitionReadError,
    ProcessDefinitionReader,
)

from api.schemas.process_definition import (
    ProcessDefinitionEnvelopeResponse,
    ProcessDefinitionErrorCode as ApiProcessDefinitionErrorCode,
    ProcessDefinitionErrorResponse,
)


router = APIRouter()


def require_engineer_or_admin(request: Request) -> None:
    settings = request.app.state.security_settings
    if not settings.enforced:
        return
    if getattr(request.state, "principal_role", None) not in {"engineer", "admin"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )


def get_process_definition_reader(request: Request) -> ProcessDefinitionReader:
    configured = getattr(request.app.state, "process_definition_reader", None)
    if configured is not None:
        return configured
    from api.composition import process_definition_reader

    return process_definition_reader()


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", "no-active-span"))


def _error_response(
    request: Request,
    error: ProcessDefinitionReadError,
) -> JSONResponse:
    status_by_code = {
        ProcessDefinitionErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        ProcessDefinitionErrorCode.IDENTITY_MISMATCH: status.HTTP_409_CONFLICT,
        ProcessDefinitionErrorCode.INVALID: status.HTTP_422_UNPROCESSABLE_CONTENT,
        ProcessDefinitionErrorCode.UNSUPPORTED_VERSION: (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        ),
        ProcessDefinitionErrorCode.READ_FAILED: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    recovery_by_code = {
        ProcessDefinitionErrorCode.UNAVAILABLE: "enable_or_reinstall",
        ProcessDefinitionErrorCode.IDENTITY_MISMATCH: "reinstall_exact_artifact",
        ProcessDefinitionErrorCode.INVALID: "replace_validated_definition",
        ProcessDefinitionErrorCode.UNSUPPORTED_VERSION: "install_compatible_wright",
        ProcessDefinitionErrorCode.READ_FAILED: "inspect_local_data_root",
    }
    supported_versions = (
        error.supported_schema_versions
        if error.code is ProcessDefinitionErrorCode.UNSUPPORTED_VERSION
        else None
    )
    payload = ProcessDefinitionErrorResponse(
        error_code=ApiProcessDefinitionErrorCode(error.code.value),
        message="Process definition is not available from validated local evidence.",
        recovery_class=recovery_by_code[error.code],
        trace_id=_trace_id(request),
        supported_schema_versions=supported_versions,
    )
    return JSONResponse(
        status_code=status_by_code[error.code],
        content=payload.model_dump(mode="json", exclude_none=True),
        headers={"Cache-Control": "no-store", "X-Trace-Id": _trace_id(request)},
    )


@router.get(
    "/{process_id}",
    response_model=ProcessDefinitionEnvelopeResponse,
    dependencies=[Depends(require_engineer_or_admin)],
    responses={
        304: {"description": "Exact ETag match"},
        403: {"description": "Engineer or administrator role required"},
        404: {"model": ProcessDefinitionErrorResponse},
        409: {"model": ProcessDefinitionErrorResponse},
        422: {"model": ProcessDefinitionErrorResponse},
        503: {"model": ProcessDefinitionErrorResponse},
    },
)
def read_process_definition(
    process_id: str,
    request: Request,
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
    reader: ProcessDefinitionReader = Depends(get_process_definition_reader),
) -> Response:
    try:
        document = reader.read(process_id)
    except ProcessDefinitionReadError as error:
        return _error_response(request, error)
    etag = f'"{document.etag}"'
    headers = {
        "Cache-Control": "no-cache, private",
        "ETag": etag,
        "X-Trace-Id": _trace_id(request),
    }
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)
    return Response(
        content=document.canonical_bytes,
        status_code=status.HTTP_200_OK,
        media_type="application/json",
        headers=headers,
    )


__all__ = ["get_process_definition_reader", "router"]
