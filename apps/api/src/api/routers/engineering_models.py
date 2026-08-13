"""Thin authenticated HTTP routes for the Engineering Models library."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from tool_registry.model_library_port import (
    EngineeringModelApplicationPort,
    EngineeringModelPortError,
)

from api.schemas.engineering_models import (
    EngineeringModelListResponse,
    EngineeringModelResponse,
)

router = APIRouter()


def require_engineer_or_admin(request: Request) -> None:
    settings = request.app.state.security_settings
    if not settings.enforced:
        return
    if getattr(request.state, "principal_role", None) not in {"engineer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )


def get_engineering_model_application(
    request: Request,
) -> EngineeringModelApplicationPort:
    application = getattr(request.app.state, "engineering_model_application", None)
    if application is not None:
        return application
    from api.composition import engineering_model_application

    return engineering_model_application()


def _port_error(error: EngineeringModelPortError) -> HTTPException:
    status_code = 404 if error.category == "model_not_found" else 400
    return HTTPException(
        status_code=status_code,
        detail={
            "category": error.category,
            "message": str(error),
            "recovery": error.recovery,
        },
    )


@router.get(
    "/catalog",
    response_model=EngineeringModelListResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def list_engineering_models(
    search: str | None = Query(default=None, max_length=200),
    task: str | None = Query(default=None, max_length=96),
    source_kind: str | None = Query(default=None, max_length=32),
    readiness: list[str] = Query(default=[]),
    platform: str | None = Query(default=None, max_length=32),
    architecture: str | None = Query(default=None, max_length=32),
    accelerator: str | None = Query(default=None, max_length=32),
    evidence_state: str | None = Query(default=None, max_length=32),
    maximum_bytes: int | None = Query(default=None, ge=0),
    cursor: str | None = Query(default=None, max_length=4096),
    limit: int = Query(default=50, ge=1, le=100),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.list_catalog(
            search=search,
            task=task,
            source_kind=source_kind,
            readiness=tuple(readiness),
            platform=platform,
            architecture=architecture,
            accelerator=accelerator,
            evidence_state=evidence_state,
            maximum_bytes=maximum_bytes,
            cursor=cursor,
            limit=limit,
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/catalog/{model_id}",
    response_model=EngineeringModelResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def get_engineering_model(
    model_id: str,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.get_catalog_model(model_id)
    except EngineeringModelPortError as error:
        raise _port_error(error) from error
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail={
                "category": "model_not_found",
                "message": "Engineering model is not present in this snapshot.",
                "recovery": "Choose a model from the active offline catalog snapshot.",
            },
        ) from error


__all__ = ["get_engineering_model_application", "router"]
