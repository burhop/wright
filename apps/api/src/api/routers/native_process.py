"""Bounded native HTTP transport. Authoring rules live in the shared service."""

from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from core.canonical_json import strict_json_loads
from core.logging import get_logger
from core.native_process import NativeProcessError
from data_vault.native_process_repository import NativeRepositoryError
from workspace_service.native_process_service import (
    NativeProcessService,
    NativeServiceError,
)

from api.middleware.tracing import normalize_correlation_id
from api.schemas.native_process import (
    CheckNativeProcess,
    CreateNativeProcess,
    SaveNativeProcess,
)

logger = get_logger(__name__)
M = TypeVar("M", bound=BaseModel)
Session = Annotated[str, Query(min_length=1, max_length=200)]


def trace_id(request: Request) -> str:
    value = getattr(request.state, "trace_id", None)
    return normalize_correlation_id(value if isinstance(value, str) else None)


class NativeRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request: Request):
            findings = []
            recovery = "Correct the request and retry."
            try:
                response = await original(request)
                response.headers["Cache-Control"] = "no-store"
                response.headers["X-Trace-Id"] = trace_id(request)
                return response
            except NativeProcessError as error:
                code, message, status = (
                    "NATIVE_INVALID",
                    "Definition does not match the native language.",
                    422,
                )
                findings = [f.as_dict() for f in error.findings]
            except (NativeServiceError, NativeRepositoryError) as error:
                code, message = error.code, str(error)
                recovery = getattr(
                    error,
                    "recovery",
                    "Reopen the current process; use a fresh request identity for changed content.",
                )
                findings = [f.as_dict() for f in getattr(error, "findings", ())]
                status = {
                    "NATIVE_NOT_FOUND": 404,
                    "NATIVE_DENIED": 403,
                    "NATIVE_CONFLICT": 409,
                    "NATIVE_REQUEST_REUSED": 409,
                    "NATIVE_NOT_READY": 422,
                    "NATIVE_BINDING_CHANGED": 409,
                    "NATIVE_RUNTIME_BUSY": 503,
                    "NATIVE_LIMIT": 413,
                }.get(code, 400)
            except (RequestValidationError, ValidationError):
                code, message, status = (
                    "NATIVE_INVALID",
                    "Request fields are missing or invalid.",
                    400,
                )
            except HTTPException as error:
                code = "NATIVE_DENIED" if error.status_code == 403 else "NATIVE_INVALID"
                message, status = (
                    "Request is not permitted."
                    if error.status_code == 403
                    else "Request is invalid.",
                    error.status_code,
                )
            except Exception as error:
                code, message, status = (
                    "NATIVE_INTERNAL",
                    "Native process operation could not be completed.",
                    500,
                )
                recovery = "Retry or inspect local support diagnostics using the trace identity."
                logger.error(
                    "native_request_failed",
                    error_type=type(error).__name__,
                    trace_id=trace_id(request),
                )
            return JSONResponse(
                status_code=status,
                content={
                    "code": code,
                    "message": message,
                    "recovery": recovery,
                    "trace_id": trace_id(request),
                    "findings": findings,
                },
                headers={"Cache-Control": "no-store", "X-Trace-Id": trace_id(request)},
            )

        return handle


def require_engineer(request: Request) -> None:
    if request.app.state.security_settings.enforced and getattr(
        request.state, "principal_role", None
    ) not in {"engineer", "admin"}:
        raise HTTPException(403)


def get_service(request: Request) -> NativeProcessService:
    configured = getattr(request.app.state, "native_process_service", None)
    if configured is not None:
        return configured
    from api.composition import native_process_service

    return native_process_service()


async def body(request: Request, model: type[M]) -> M:
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1100 * 1024:
            raise NativeServiceError(
                "NATIVE_LIMIT",
                "Request exceeds the native size limit.",
                "Use a smaller definition.",
            )
    try:
        value = strict_json_loads(bytes(raw), max_bytes=1100 * 1024)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise NativeServiceError(
            "NATIVE_INVALID",
            "Request is not strict bounded UTF-8 JSON.",
            "Use the published JSON language profile.",
        ) from error
    return model.model_validate(value)


router = APIRouter(route_class=NativeRoute, dependencies=[Depends(require_engineer)])
Service = Annotated[NativeProcessService, Depends(get_service)]


@router.get("/contract")
def contract(session_id: Session, service: Service):
    return service.contract(session_id)


@router.get("/examples")
def examples(service: Service):
    return service.examples()


@router.get("")
def documents(
    session_id: Session,
    service: Service,
    limit: int = Query(25, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
):
    return service.list_documents(session_id, limit=limit, cursor=cursor)


@router.post("", status_code=201)
async def create(request: Request, session_id: Session, service: Service):
    payload = await body(request, CreateNativeProcess)
    return await run_in_threadpool(
        service.save_document,
        session_id,
        payload.definition,
        payload.presentation,
        request_id=payload.request_id,
        expected_token=None,
        trace_id=trace_id(request),
    )


@router.post("/check")
async def check(request: Request, session_id: Session, service: Service):
    payload = await body(request, CheckNativeProcess)
    return await run_in_threadpool(
        service.check,
        session_id,
        payload.definition,
        {key: value.model_dump() for key, value in payload.bindings.items()},
    )


@router.get("/{process_id}")
def read(process_id: str, session_id: Session, service: Service):
    return service.get_document(session_id, process_id)


@router.put("/{process_id}")
async def save(
    process_id: str, request: Request, session_id: Session, service: Service
):
    payload = await body(request, SaveNativeProcess)
    return await run_in_threadpool(
        service.save_document,
        session_id,
        payload.definition,
        payload.presentation,
        process_id=process_id,
        request_id=payload.request_id,
        expected_token=payload.expected_token,
        trace_id=trace_id(request),
    )
