"""Authenticated, default-off routes for provisional workflow draft authoring."""

from __future__ import annotations

from typing import TypeVar

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from api.config import workflow_composer_enabled
from api.middleware.tracing import normalize_correlation_id
from api.schemas.workflow_drafts import (
    WorkflowDraftCreateRequest,
    WorkflowDraftDiagnosticResponse,
    WorkflowDraftEnvelope,
    WorkflowDraftErrorCode,
    WorkflowDraftErrorResponse,
    WorkflowDraftValidationResponse,
)
from core.workflow_drafts import canonical_json_bytes, canonical_sha256
from workspace_service import (
    WorkflowDraftConflictError,
    WorkflowDraftIdentityMismatchError,
    WorkflowDraftInvalidError,
    WorkflowDraftNotFoundError,
    WorkflowDraftService,
)


router = APIRouter()
_MAX_BODY_BYTES = 1024 * 1024
_Model = TypeVar("_Model", bound=BaseModel)


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


def get_workflow_draft_service(request: Request) -> WorkflowDraftService:
    configured = getattr(request.app.state, "workflow_draft_service", None)
    if configured is not None:
        return configured
    from api.composition import workflow_draft_service

    return workflow_draft_service()


def _enabled(request: Request) -> bool:
    configured = getattr(request.app.state, "workflow_composer_enabled", None)
    return bool(configured) if configured is not None else workflow_composer_enabled()


def _trace_id(request: Request) -> str:
    value = getattr(request.state, "trace_id", None)
    return normalize_correlation_id(value if isinstance(value, str) else None)


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: WorkflowDraftErrorCode,
    message: str,
    recovery_class: str,
    diagnostics: tuple[WorkflowDraftDiagnosticResponse, ...] | None = None,
) -> JSONResponse:
    trace_id = _trace_id(request)
    payload = WorkflowDraftErrorResponse(
        error_code=code,
        message=message,
        recovery_class=recovery_class,
        trace_id=trace_id,
        diagnostics=diagnostics,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json", exclude_none=True),
        headers={"Cache-Control": "no-store", "X-Trace-Id": trace_id},
    )


def _unavailable(request: Request) -> JSONResponse:
    return _error_response(
        request,
        status_code=status.HTTP_404_NOT_FOUND,
        code=WorkflowDraftErrorCode.UNAVAILABLE,
        message="Workflow Composer is not available.",
        recovery_class="enable_feature",
    )


async def _parse_body(
    request: Request, model: type[_Model]
) -> _Model | JSONResponse:
    body = await request.body()
    if len(body) > _MAX_BODY_BYTES:
        return _error_response(
            request,
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            code=WorkflowDraftErrorCode.INVALID,
            message="Workflow draft request exceeds the supported limit.",
            recovery_class="correct_candidate",
        )
    try:
        return model.model_validate_json(body or b"{}")
    except (ValidationError, ValueError):
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=WorkflowDraftErrorCode.INVALID,
            message="Workflow draft request is invalid.",
            recovery_class="correct_candidate",
        )


def _etag(draft: WorkflowDraftEnvelope | BaseModel) -> str:
    return f'"{canonical_sha256(draft)}"'


def _draft_response(
    request: Request, draft: BaseModel, *, status_code: int = status.HTTP_200_OK
) -> Response:
    return Response(
        content=canonical_json_bytes(draft),
        status_code=status_code,
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, private",
            "ETag": _etag(draft),
            "X-Trace-Id": _trace_id(request),
        },
    )


def _service_error(request: Request, error: Exception) -> JSONResponse:
    if isinstance(error, WorkflowDraftNotFoundError):
        return _error_response(
            request,
            status_code=status.HTTP_404_NOT_FOUND,
            code=WorkflowDraftErrorCode.NOT_FOUND,
            message="Workflow draft not found.",
            recovery_class="reopen_draft",
        )
    if isinstance(error, WorkflowDraftInvalidError):
        diagnostics = tuple(
            WorkflowDraftDiagnosticResponse.from_domain(item)
            for item in error.diagnostics
        )
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=WorkflowDraftErrorCode.INVALID,
            message="Workflow draft candidate is invalid.",
            recovery_class="correct_candidate",
            diagnostics=diagnostics,
        )
    if isinstance(error, WorkflowDraftIdentityMismatchError):
        return _error_response(
            request,
            status_code=status.HTTP_409_CONFLICT,
            code=WorkflowDraftErrorCode.IDENTITY_MISMATCH,
            message="Workflow draft identity does not match the requested resource.",
            recovery_class="reopen_draft",
        )
    if isinstance(error, WorkflowDraftConflictError):
        return _error_response(
            request,
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            code=WorkflowDraftErrorCode.STALE_REVISION,
            message="Workflow draft changed; reopen it before saving again.",
            recovery_class="refresh_and_retry",
        )
    return _error_response(
        request,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code=WorkflowDraftErrorCode.STORAGE_FAILED,
        message="Workflow draft storage is unavailable.",
        recovery_class="retry_or_inspect_local_store",
    )


@router.post("", dependencies=[Depends(require_engineer_or_admin)])
async def create_workflow_draft(
    request: Request,
    service: WorkflowDraftService = Depends(get_workflow_draft_service),
) -> Response:
    if not _enabled(request):
        return _unavailable(request)
    body = await _parse_body(request, WorkflowDraftCreateRequest)
    if isinstance(body, JSONResponse):
        return body
    try:
        draft = service.create(title=body.title, purpose=body.purpose)
    except Exception as error:
        return _service_error(request, error)
    return _draft_response(request, draft, status_code=status.HTTP_201_CREATED)


@router.get("/{draft_id}", dependencies=[Depends(require_engineer_or_admin)])
def read_workflow_draft(
    draft_id: str,
    request: Request,
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
    service: WorkflowDraftService = Depends(get_workflow_draft_service),
) -> Response:
    if not _enabled(request):
        return _unavailable(request)
    try:
        draft = service.read(draft_id)
    except Exception as error:
        return _service_error(request, error)
    etag = _etag(draft)
    if if_none_match == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "Cache-Control": "no-cache, private",
                "ETag": etag,
                "X-Trace-Id": _trace_id(request),
            },
        )
    return _draft_response(request, draft)


@router.post(
    "/{draft_id}/validate", dependencies=[Depends(require_engineer_or_admin)]
)
async def validate_workflow_draft_candidate(
    draft_id: str,
    request: Request,
    service: WorkflowDraftService = Depends(get_workflow_draft_service),
) -> Response:
    if not _enabled(request):
        return _unavailable(request)
    body = await _parse_body(request, WorkflowDraftEnvelope)
    if isinstance(body, JSONResponse):
        return body
    if body.draft_id != draft_id:
        return _service_error(
            request,
            WorkflowDraftIdentityMismatchError("Draft identity mismatch"),
        )
    result = WorkflowDraftValidationResponse.from_domain(service.validate(body))
    return JSONResponse(
        content=result.model_dump(mode="json"),
        headers={"Cache-Control": "no-store", "X-Trace-Id": _trace_id(request)},
    )


@router.put("/{draft_id}", dependencies=[Depends(require_engineer_or_admin)])
async def save_workflow_draft(
    draft_id: str,
    request: Request,
    if_match: str | None = Header(default=None, alias="If-Match"),
    service: WorkflowDraftService = Depends(get_workflow_draft_service),
) -> Response:
    if not _enabled(request):
        return _unavailable(request)
    body = await _parse_body(request, WorkflowDraftEnvelope)
    if isinstance(body, JSONResponse):
        return body
    try:
        current = service.read(draft_id)
        if if_match is None or if_match != _etag(current):
            raise WorkflowDraftConflictError(
                expected_revision=body.revision,
                current_revision=current.revision,
            )
        saved = service.save(
            draft_id,
            body,
            expected_revision=current.revision,
        )
    except Exception as error:
        return _service_error(request, error)
    return _draft_response(request, saved)


__all__ = ["get_workflow_draft_service", "router"]
