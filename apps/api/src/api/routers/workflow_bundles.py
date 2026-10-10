"""Authenticated, session-workspace scoped definition-only workflow transfer."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field, StrictStr

from core.process_validation import Contract, Digest, Identifier
from core.workflow_bundle import WorkflowBundle
from workspace_service import WorkspaceService
from workspace_service.workflow_bundles import WorkflowBundleError
from workspace_service.workflow_sources import WorkflowSourceStorageError
from .workspace import (
    _require_process_validation_role,
    _workflow_source_scope,
    get_workspace_service,
)

router = APIRouter(dependencies=[Depends(_require_process_validation_role)])


class ExportRequest(Contract):
    session_id: Identifier
    path: Annotated[StrictStr, Field(max_length=256)]
    expected_storage_digest: Digest
    mode: Literal["source", "bundle"] = "source"
    selected_reference_paths: tuple[StrictStr, ...] = Field(default=(), max_length=64)
    selected_ui_ids: tuple[Identifier, ...] = Field(default=(), max_length=16)


class InspectRequest(Contract):
    session_id: Identifier
    bundle: WorkflowBundle
    destination_path: Annotated[StrictStr, Field(max_length=256)]


class ImportRequest(InspectRequest):
    expected_bundle_digest: Digest


async def _catalog(request, scope, session_id):
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
    from tool_registry.gateway_models import GatewayError

    gateway = getattr(request.app.state, "gateway_service", None)
    if gateway is None:
        return ()
    runtime = None
    try:
        runtime = WorkflowMcpRuntime(
            gateway, workspace_id=scope.workspace_id, session_id=session_id
        )
        return runtime.available()
    except GatewayError:
        # Source transfer remains available while a provider is offline. Empty
        # catalog is explicitly unqualified in the dependency manifest, never
        # treated as evidence of compatibility or permission to execute.
        return ()
    finally:
        if runtime is not None:
            await runtime.close()


def _error(exc):
    return HTTPException(
        status_code=422,
        detail={
            "code": "workflow_bundle_rejected",
            "message": str(exc)
            if isinstance(exc, WorkflowBundleError)
            else "Workflow transfer could not be validated. Inspect the source, dependencies and selected files.",
        },
    )


@router.post("/export")
async def export(
    body: ExportRequest,
    request: Request,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    scope = _workflow_source_scope(body.session_id, service)
    response.headers["Cache-Control"] = "no-store"
    try:
        return await service.workflow_bundles.export(
            scope.workspace_id,
            scope.workspace_dir,
            body.path,
            body.expected_storage_digest,
            mode=body.mode,
            selected_reference_paths=body.selected_reference_paths,
            selected_ui_ids=body.selected_ui_ids,
            catalog=await _catalog(request, scope, body.session_id),
        )
    except (ValueError, OSError, KeyError, WorkflowSourceStorageError) as exc:
        raise _error(exc) from exc


@router.post("/inspect")
async def inspect(
    body: InspectRequest,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    scope = _workflow_source_scope(body.session_id, service)
    response.headers["Cache-Control"] = "no-store"
    try:
        return await service.workflow_bundles.inspect(
            scope.workspace_dir, body.bundle, body.destination_path
        )
    except (ValueError, OSError, WorkflowSourceStorageError) as exc:
        raise _error(exc) from exc


@router.post("/import")
async def import_bundle(
    body: ImportRequest,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    scope = _workflow_source_scope(body.session_id, service)
    response.headers["Cache-Control"] = "no-store"
    try:
        result = await service.workflow_bundles.apply(
            scope.workspace_dir,
            body.bundle,
            body.destination_path,
            body.expected_bundle_digest,
        )
        result["source"] = {
            **result["source"],
            "workspace_id": scope.workspace_id,
            "metadata_authority": "wright_host",
        }
        return result
    except (ValueError, OSError, WorkflowSourceStorageError) as exc:
        raise _error(exc) from exc
