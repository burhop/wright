"""Reserved presentation transport over the existing native process handlers.

The isolated origin supplies a host-bound HTTP-only cookie. Request selectors
are compared with server-derived scope; they never mint process/run authority.
"""

import json
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from api.composition import surface_application
from api.routers.workspace import get_workspace_service
from api.schemas import process_interfaces as schemas
from api.surface_route_authority import SurfaceRouteAuthority
from workspace_service.process_interfaces.errors import ProcessInterfaceError

router = APIRouter(prefix="/__wright/process")
_SOURCE = {"session_id", "path", "expected_storage_digest"}
_ID = r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,159}"


def get_process_surface_grants():
    return surface_application().grant_service


def _denied():
    return ProcessInterfaceError(
        "SCOPE_DENIED",
        "This request exceeds its process presentation.",
        "Reopen the exact process and run in its Wright workspace.",
    )


def _json_body(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Repeated JSON field")
            value[key] = item
        return value

    def constant(_value):
        raise ValueError("Nonfinite JSON value")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except RecursionError:
        raise ValueError("JSON depth exceeds its supported bound") from None


async def _bounded_body(request, maximum):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > maximum:
            raise HTTPException(status_code=413, detail="PROCESS_REQUEST_TOO_LARGE")
        body.extend(chunk)
    # The upload parser reuses the already bounded bytes rather than rereading
    # an unbounded stream. No generated code controls parser limits.
    request._body = bytes(body)
    return request._body


def _query(request, permitted):
    pairs = list(request.query_params.multi_items())
    values = dict(pairs)
    if len(values) != len(pairs) or set(values) - permitted:
        raise _denied()
    for value in values.values():
        if len(value) > 2048:
            raise _denied()
    if any(len(values.get(key, "")) > 256 for key in ("page", "cursor")):
        raise _denied()
    return values


def _source_matches(context, value):
    process = context.binding.process
    if (value.session_id, value.path, value.expected_storage_digest) != (
        context.session_id,
        process.source_path,
        process.source_digest,
    ):
        raise _denied()


async def _dispatch(path, request, response, service, route, context):
    from api.routers import process_interfaces as native

    application = service.process_interfaces
    binding = context.binding
    request.state.process_presentation = context
    if path == "loaded" and request.method == "POST":
        _query(request, set())
        raw = await _bounded_body(request, 1024)
        if (
            request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            != "application/json"
        ):
            raise HTTPException(status_code=415, detail="PROCESS_JSON_REQUIRED")
        if _json_body(raw) != {
            "schema_version": "wright.process-presentation-loaded/1"
        }:
            raise _denied()
        if not binding.read_only:
            raise _denied()
        from workspace_service.process_interfaces.artifacts import (
            ProcessUIPreviewObservation,
        )

        _, _, report, _, _ = application.ui_revisions.preview_bundle(
            context.scope, binding.process, context.job_id
        )
        application.ui_revisions.observe_preview(
            context.scope,
            binding.process,
            context.job_id,
            ProcessUIPreviewObservation(
                presentation_id=route.presentation_id,
                ui_id=binding.ui_id,
                revision_id=binding.revision_id,
                bundle_digest=report.bundle_digest,
            ),
        )
        return {"preview_observed": True}
    if path == "context" and request.method == "GET":
        _query(request, set())
        return {
            "schema_version": "wright.process-presentation/1",
            "process": binding.process,
            "session_id": context.session_id,
            "ui_id": binding.ui_id,
            "revision_id": binding.revision_id,
            "run_id": binding.run_id,
            "read_only": binding.read_only,
            "capabilities": sorted(context.scope.capabilities),
            "presentation_id": route.presentation_id,
            "generation": route.generation,
        }
    if request.method == "GET":
        values = _query(
            request, _SOURCE | {"run_id", "input_snapshot_id", "page", "cursor"}
        )
        source = schemas.ProcessSourceRequest.model_validate(
            {key: values.get(key) for key in _SOURCE}
        )
        _source_matches(context, source)
        args = source.model_dump()
        common = {"request": request, "service": service, **args}
        if path == "interaction":
            if "cursor" in values:
                raise _denied()
            run_id = values.get("run_id")
            context.scope.require_run(run_id)
            return await native.interaction_snapshot(
                **common,
                response=response,
                run_id=run_id,
                input_snapshot_id=values.get("input_snapshot_id"),
                page=values.get("page"),
            )
        matched = re.fullmatch(f"runs/({_ID})(/events)?", path)
        if not matched or set(values) & {"run_id", "input_snapshot_id"}:
            raise _denied()
        run_id, events = matched.groups()
        context.scope.require_run(run_id)
        if events:
            if "page" in values:
                raise _denied()
            return await native.follow_process_run(
                **common, run_id=run_id, cursor=values.get("cursor")
            )
        if "cursor" in values:
            raise _denied()
        return await native.attach_process_run(
            **common, response=response, run_id=run_id, page=values.get("page")
        )
    if path == "inputs/upload":
        _query(request, set())
        if binding.run_id is not None:
            raise _denied()
        await _bounded_body(request, application.limits.maximum_upload_bytes + 65536)
        form = await request.form(max_files=1, max_fields=4, max_part_size=65536)
        keys = [key for key, _ in form.multi_items()]
        if sorted(keys) != sorted((*_SOURCE, "input_id", "file")) or not isinstance(
            form.get("file"), UploadFile
        ):
            await form.close()
            raise _denied()
        try:
            source = schemas.ProcessSourceRequest.model_validate(
                {key: form[key] for key in _SOURCE}
            )
            _source_matches(context, source)
            return await native.upload_process_input(
                request=request,
                response=response,
                service=service,
                **source.model_dump(),
                input_id=form["input_id"],
                file=form["file"],
            )
        finally:
            await form.close()
    definitions = {
        "inputs": (schemas.SetProcessInputsRequest, native.set_process_inputs),
        "readiness": (schemas.ProcessReadinessRequest, native.process_readiness),
        "runs": (schemas.ProcessRunRequest, native.start_process_run),
        "representations/read": (
            schemas.ProcessRepresentationRequest,
            native.read_process_representation,
        ),
        "navigation": (
            schemas.ProcessNavigationRequest,
            native.resolve_process_navigation,
        ),
    }
    extra = {}
    match = re.fullmatch(f"runs/({_ID})/cancel", path)
    if match:
        context.scope.require_run(match[1])
        extra["run_id"] = match[1]
        definition = (schemas.ProcessCancelRequest, native.cancel_process_run)
    else:
        match = re.fullmatch(f"interactions/({_ID})/(response|decision)", path)
        if match:
            extra["checkpoint_id"] = match[1]
            definition = (
                (schemas.ProcessInputResponseRequest, native.respond_to_process_input)
                if match[2] == "response"
                else (
                    schemas.ProcessReviewDecisionRequest,
                    native.decide_process_review,
                )
            )
        else:
            match = re.fullmatch(f"actions/({_ID})", path)
            if match:
                extra["action_id"] = match[1]
                definition = (
                    schemas.ProcessActionRequest,
                    native.request_process_action,
                )
            else:
                definition = definitions.get(path)
    if definition is None:
        raise _denied()
    if binding.run_id is not None and path in {"inputs", "readiness", "runs"}:
        raise _denied()
    _query(request, set())
    raw = await _bounded_body(request, 1_200_000)
    if (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        raise HTTPException(status_code=415, detail="PROCESS_JSON_REQUIRED")
    body = definition[0].model_validate(_json_body(raw))
    _source_matches(context, body)
    if path == "runs":
        from workspace_service.process_interfaces.surface_bridge import (
            ProcessSurfaceBridge,
        )

        ProcessSurfaceBridge.retain_start(application, context, body)
    if path == "representations/read":
        context.scope.require_run(body.run_id)
        return await definition[1](body=body, request=request, service=service)
    if path == "navigation":
        # A saved app need not repeat the run already fixed by this presentation.
        # Native navigation still requires an explicit run; only this authorized
        # bridge may supply it. An explicit foreign run never gets replaced.
        target = body.target
        if target.run_id is None and binding.run_id is not None:
            target = target.model_copy(update={"run_id": binding.run_id})
            body = body.model_copy(update={"target": target})
        context.scope.require_run(target.run_id)
    return await definition[1](
        body=body, request=request, response=response, service=service, **extra
    )


def _operation(path, method):
    if method == "GET":
        return "process.read"
    if path in {"inputs", "inputs/upload"}:
        return "process.inputs"
    if path == "readiness":
        return "process.read"
    if path == "loaded":
        return "process.read"
    if path == "runs":
        return "process.start"
    if path == "navigation":
        return "process.navigate"
    if path == "representations/read":
        return "process.results"
    if re.fullmatch(f"runs/{_ID}/cancel", path):
        return "process.cancel"
    if re.fullmatch(f"interactions/{_ID}/response", path):
        return "process.respond"
    if re.fullmatch(f"interactions/{_ID}/decision", path):
        return "process.review"
    if re.fullmatch(f"actions/{_ID}", path):
        return "process.action"
    raise _denied()


@router.api_route("/{operation_path:path}", methods=["GET", "POST"])
async def process_operation(
    operation_path: str,
    request: Request,
    service=Depends(get_workspace_service),
    grants=Depends(get_process_surface_grants),
):
    from api.routers import process_interfaces as native
    from api.routers.surface_preview import _authorize_application_route, _route_error
    from api.surface_route_authority import SurfaceRouteAuthorizationError

    try:
        route = _authorize_application_route(request)
        # GET may omit Origin; every POST, including read-only JSON operations,
        # requires the exact presentation origin. No CORS expansion is provided.
        origins = request.headers.getlist("origin")
        if (origins and origins != [route.presentation_origin]) or (
            request.method == "POST" and origins != [route.presentation_origin]
        ):
            raise _denied()
        operation = _operation(operation_path, request.method)
        context = SurfaceRouteAuthority.authorize_process(
            route,
            application=service.process_interfaces,
            grants=grants,
            operation=operation,
        )
        response = Response(headers={"Cache-Control": "no-store"})
        result = await _dispatch(
            operation_path, request, response, service, route, context
        )
        if isinstance(result, StreamingResponse):
            original = result.body_iterator
            from workspace_service.process_interfaces.surface_bridge import (
                ProcessSurfaceBridge,
            )

            bridge = ProcessSurfaceBridge(service.process_interfaces, grants)

            async def authorized_chunks():
                try:
                    async for chunk in original:
                        try:
                            bridge.revalidate(route, context, operation)
                        except ProcessInterfaceError as error:
                            if result.media_type == "text/event-stream":
                                yield (
                                    "event: reconciliation\ndata: "
                                    + json.dumps(error.reason.model_dump(mode="json"))
                                    + "\n\n"
                                )
                            return
                        yield chunk
                finally:
                    close = getattr(original, "aclose", None)
                    if close:
                        await close()

            result.body_iterator = authorized_chunks()
            return result
        return JSONResponse(
            jsonable_encoder(result),
            status_code=202
            if operation in {"process.start", "process.respond", "process.action"}
            else 200,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
    except SurfaceRouteAuthorizationError as error:
        raise _route_error(error) from error
    except ProcessInterfaceError as error:
        raise native._transport_error(error) from error
    except (ValidationError, ValueError):
        # Do not echo malformed source, uploaded bytes or raw validation input.
        raise HTTPException(status_code=422, detail="PROCESS_REQUEST_INVALID") from None
