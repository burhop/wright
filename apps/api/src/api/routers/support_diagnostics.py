"""Thin authenticated routes for local support-diagnostic preview and export."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from workspace_service import (
    SupportDiagnosticError,
    SupportDiagnosticService,
    SupportDiagnosticSnapshot,
)


router = APIRouter()


class DiagnosticScopeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(default=None, max_length=128)
    scenario_run_id: str | None = Field(default=None, max_length=128)


class DiagnosticPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=128)
    scope: DiagnosticScopeRequest = Field(default_factory=DiagnosticScopeRequest)


class DiagnosticPreviewResponse(BaseModel):
    snapshot: SupportDiagnosticSnapshot
    snapshot_digest: str
    confirmation_token: str
    expires_at: str
    filename: str


class DiagnosticExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str = Field(min_length=1, max_length=128)
    snapshot_digest: str = Field(min_length=71, max_length=71)
    confirmation_token: str = Field(min_length=1, max_length=512)


def require_engineer_or_admin(request: Request) -> None:
    settings = request.app.state.security_settings
    if not settings.enforced:
        return
    if getattr(request.state, "principal_role", None) not in {"engineer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )


def get_support_diagnostic_application(request: Request) -> SupportDiagnosticService:
    application = getattr(request.app.state, "support_diagnostic_application", None)
    if application is not None:
        return application
    from api.composition import support_diagnostic_application

    return support_diagnostic_application()


def _principal(request: Request) -> str:
    return str(getattr(request.state, "principal_id", "local-user"))


def _diagnostic_error(error: SupportDiagnosticError) -> HTTPException:
    if error.code == "WORKSPACE_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif error.code == "DIAGNOSTIC_PREVIEW_EXPIRED":
        status_code = status.HTTP_410_GONE
    elif error.code == "DIAGNOSTIC_PREVIEW_STALE":
        status_code = status.HTTP_409_CONFLICT
    elif error.code == "DIAGNOSTIC_EXPORT_TOO_LARGE":
        status_code = status.HTTP_413_CONTENT_TOO_LARGE
    elif error.code in {"DIAGNOSTIC_SCOPE_FORBIDDEN", "DIAGNOSTIC_EXPORT_DENIED"}:
        status_code = status.HTTP_403_FORBIDDEN
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": "Support diagnostic request was denied.",
        },
    )


@router.post(
    "/preview",
    response_model=DiagnosticPreviewResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(require_engineer_or_admin)],
)
def preview_support_diagnostic(
    body: DiagnosticPreviewRequest,
    request: Request,
    application: SupportDiagnosticService = Depends(get_support_diagnostic_application),
) -> DiagnosticPreviewResponse:
    try:
        preview = application.preview(
            principal_id=_principal(request),
            workspace_id=body.workspace_id,
            scope=body.scope.model_dump(exclude_none=True),
        )
    except SupportDiagnosticError as error:
        raise _diagnostic_error(error) from error
    return DiagnosticPreviewResponse(
        snapshot=preview.snapshot,
        snapshot_digest=preview.snapshot.snapshot_digest,
        confirmation_token=preview.confirmation_token,
        expires_at=preview.expires_at.isoformat().replace("+00:00", "Z"),
        filename=preview.filename,
    )


@router.post(
    "/export",
    dependencies=[Depends(require_engineer_or_admin)],
    responses={200: {"content": {"application/json": {}}}},
)
def export_support_diagnostic(
    body: DiagnosticExportRequest,
    request: Request,
    application: SupportDiagnosticService = Depends(get_support_diagnostic_application),
) -> Response:
    try:
        export = application.export(
            principal_id=_principal(request),
            workspace_id=body.workspace_id,
            snapshot_digest=body.snapshot_digest,
            confirmation_token=body.confirmation_token,
        )
    except SupportDiagnosticError as error:
        raise _diagnostic_error(error) from error
    headers: dict[str, Any] = {
        "Content-Disposition": f'attachment; filename="{export.filename}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(
        content=export.content, media_type="application/json", headers=headers
    )
