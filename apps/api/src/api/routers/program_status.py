"""Authenticated read-only routes for immutable engineering program status."""

from __future__ import annotations

import json
from collections.abc import Mapping

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse
from tool_registry.program_status import (
    ProgramStatusErrorCode,
    ProgramStatusReadError,
    ProgramStatusReader,
)

from api.schemas.program_status import (
    ProgramStatusErrorCode as ApiProgramStatusErrorCode,
    ProgramStatusErrorResponse,
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


def get_program_status_reader(request: Request) -> ProgramStatusReader:
    configured = getattr(request.app.state, "program_status_reader", None)
    if configured is not None:
        return configured
    from api.composition import program_status_reader

    return program_status_reader()


def _trace_id(request: Request) -> str:
    return str(getattr(request.state, "trace_id", "no-active-span"))


def _error_response(request: Request, error: ProgramStatusReadError) -> JSONResponse:
    status_by_code = {
        ProgramStatusErrorCode.UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        ProgramStatusErrorCode.IDENTITY_MISMATCH: status.HTTP_409_CONFLICT,
        ProgramStatusErrorCode.INVALID: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ProgramStatusErrorCode.READ_FAILED: status.HTTP_503_SERVICE_UNAVAILABLE,
        ProgramStatusErrorCode.PUBLISHER_UNAVAILABLE: status.HTTP_404_NOT_FOUND,
        ProgramStatusErrorCode.PUBLISHER_INVALID: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ProgramStatusErrorCode.PUBLISHER_READ_FAILED: status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    payload = ProgramStatusErrorResponse(
        error_code=ApiProgramStatusErrorCode(error.code.value),
        message="Program status is not available from validated local evidence.",
        recovery_class=error.recovery_class,
        trace_id=_trace_id(request),
    )
    return JSONResponse(
        status_code=status_by_code[error.code],
        content=payload.model_dump(mode="json"),
        headers={"Cache-Control": "no-store", "X-Trace-Id": _trace_id(request)},
    )


@router.get("", dependencies=[Depends(require_engineer_or_admin)])
def read_program_status(
    request: Request,
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
    reader: ProgramStatusReader = Depends(get_program_status_reader),
) -> Response:
    try:
        document = reader.read_bundle()
    except ProgramStatusReadError as error:
        return _error_response(request, error)
    etag = f'"{document.bundle_id}"'
    headers = {
        "Cache-Control": "no-cache, private",
        "ETag": etag,
        "X-Program-Status-Observed-At": document.generated_at,
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


@router.get("/publisher", dependencies=[Depends(require_engineer_or_admin)])
def read_program_status_publisher(
    request: Request,
    reader: ProgramStatusReader = Depends(get_program_status_reader),
) -> Response:
    try:
        publisher = reader.read_publisher()
    except ProgramStatusReadError as error:
        return _error_response(request, error)
    content: Mapping[str, object] = publisher.as_dict()
    return Response(
        content=json.dumps(content, separators=(",", ":"), sort_keys=True),
        status_code=status.HTTP_200_OK,
        media_type="application/json",
        headers={"Cache-Control": "no-store", "X-Trace-Id": _trace_id(request)},
    )


__all__ = ["get_program_status_reader", "router"]
