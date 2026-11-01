"""Offline next-slice MCP ports over Wright's existing process API.

Opt-in only; not registered by the installed frozen 0.3.0 editor candidate.
Closed request types, no arbitrary URL/method, no model call or executor.
"""

import base64
import hashlib
from typing import Annotated, Any, Literal
from urllib.parse import quote

from mcp.types import ToolAnnotations
from pydantic import Field, AfterValidator, field_validator

from api.schemas.process_interfaces import (
    ProcessActionRequest,
    ProcessCancelRequest,
    ProcessInputResponseRequest,
    ProcessNavigationRequest,
    ProcessReadinessRequest,
    ProcessReviewDecisionRequest,
    ProcessRepresentationRequest,
    ProcessRunRequest,
    ProcessSourceRequest,
    SetProcessInputsRequest,
)
from core.process_validation import Identifier
from native_source_tools import WrightRequestRejected


def uri_segment(value):
    if (
        value in {".", ".."}
        or any(character in value for character in "/\\?#")
        or any(ord(character) < 32 for character in value)
    ):
        raise ValueError("Process identifiers must fit one exact URI segment")
    return value


Segment = Annotated[Identifier, AfterValidator(uri_segment)]


class PanelSnapshot(ProcessSourceRequest):
    workspace_id: Segment
    operation: Literal["snapshot"]
    run_id: Segment | None = None
    input_snapshot_id: Identifier | None = None
    page: str | None = Field(default=None, max_length=256)


class PanelReasoning(ProcessSourceRequest):
    workspace_id: Segment
    operation: Literal["reasoning"]
    run_id: Segment


class PanelRepresentation(ProcessRepresentationRequest):
    workspace_id: Segment
    operation: Literal["representation"]


class PanelNavigation(ProcessNavigationRequest):
    workspace_id: Segment
    operation: Literal["navigation"]


class PanelInputs(SetProcessInputsRequest):
    workspace_id: Segment
    operation: Literal["inputs"]


class PanelUpload(ProcessSourceRequest):
    workspace_id: Segment
    operation: Literal["upload"]
    input_id: Identifier
    filename: str = Field(min_length=1, max_length=160)
    bytes_base64: str = Field(min_length=4, max_length=44_739_244)

    @field_validator("bytes_base64")
    @classmethod
    def bounded_file(cls, value):
        content = base64.b64decode(value, validate=True)
        if not 0 < len(content) <= 33_554_432:
            raise ValueError("Input files must contain at most 32 MiB")
        return value


class PanelReadiness(ProcessReadinessRequest):
    workspace_id: Segment
    operation: Literal["readiness"]


class PanelStart(ProcessRunRequest):
    workspace_id: Segment
    operation: Literal["start"]


class PanelResponse(ProcessInputResponseRequest):
    workspace_id: Segment
    operation: Literal["respond"]
    checkpoint_id: Segment
    # This UI cannot supply test-auto response attribution or review authority.
    auto: Literal[False] = False


class PanelDecision(ProcessReviewDecisionRequest):
    workspace_id: Segment
    operation: Literal["decide"]
    checkpoint_id: Segment


class PanelCancel(ProcessCancelRequest):
    workspace_id: Segment
    operation: Literal["cancel"]
    run_id: Segment


class PanelContinue(ProcessActionRequest):
    workspace_id: Segment
    operation: Literal["continue"]
    action_id: Segment = Field(pattern=r"^continue-.+")


PanelRead = Annotated[
    PanelSnapshot | PanelReasoning | PanelRepresentation | PanelNavigation,
    Field(discriminator="operation"),
]
PanelUpdate = Annotated[
    PanelInputs
    | PanelUpload
    | PanelReadiness
    | PanelStart
    | PanelResponse
    | PanelDecision
    | PanelContinue
    | PanelCancel,
    Field(discriminator="operation"),
]
BASE = "/api/workspace/process-interfaces"


def register_native_process_tools(mcp, client, *, resource_uri=None, native_workspace_files=False):
    async def invoke(request, *, changes=False):
        owner_called = False
        try:
            await client.scope(request.workspace_id, request.session_id)
            body = request.model_dump(
                mode="json", exclude={"workspace_id", "operation"}, exclude_none=True
            )
            operation = request.operation
            if operation == "representation":
                if request.preview is not None:
                    return {
                        "ok": False,
                        "http_status": 415,
                        "reason": {
                            "code": "CAPABILITY_UNAVAILABLE",
                            "message": "This native view has not qualified derived file previews.",
                            "correction": "Use the recorded raw text file or Wright's existing working view.",
                        },
                    }
                owner_called = True
                async with client.http.stream(
                    "POST", BASE + "/representations/read", json=body
                ) as response:
                    if not response.is_success:
                        raise WrightRequestRejected(
                            response.status_code,
                            "Representation owner rejected the read",
                        )
                    media = response.headers.get("content-type", "").split(";", 1)[0]
                    size = response.headers.get("content-length", "")
                    if (
                        media
                        not in {
                            "text/plain",
                            "text/markdown",
                            "text/csv",
                            "application/json",
                            "image/png",
                            "image/jpeg",
                        }
                        or not size.isdecimal()
                        or int(size) > 1048576
                    ):
                        return {
                            "ok": False,
                            "http_status": 415,
                            "reason": {
                                "code": "CAPABILITY_UNAVAILABLE",
                                "message": "This native view supports text, PNG and JPEG files up to 1 MiB.",
                                "correction": "Open this representation in Wright's existing working view.",
                            },
                        }
                    if (
                        response.headers.get("x-wright-artifact-sha256")
                        != request.reference.sha256
                        or response.headers.get("x-content-type-options") != "nosniff"
                    ):
                        raise WrightRequestRejected(
                            409, "Representation identity was not confirmed"
                        )
                    parts = bytearray()
                    async for chunk in response.aiter_bytes():
                        parts.extend(chunk)
                        if len(parts) > 1048576 or len(parts) > int(size):
                            raise WrightRequestRejected(
                                409, "Representation size differs"
                            )
                    if (
                        len(parts) != int(size)
                        or hashlib.sha256(parts).hexdigest() != request.reference.sha256
                    ):
                        raise WrightRequestRejected(409, "Representation hash differs")
                    document = {
                        "bytes_base64": base64.b64encode(parts).decode("ascii"),
                        "sha256": request.reference.sha256,
                        "media_type": media,
                        "size_bytes": len(parts),
                    }
            elif operation == "navigation":
                owner_called = True
                document = await client.call("POST", BASE + "/navigation", json=body)
            elif operation == "upload":
                content = base64.b64decode(body.pop("bytes_base64"), validate=True)
                filename = body.pop("filename")
                owner_called = True
                document = await client.call(
                    "POST",
                    BASE + "/inputs/upload",
                    data=body,
                    files={"file": (filename, content, "application/octet-stream")},
                )
            elif operation in ("snapshot", "reasoning"):
                run = body.pop("run_id", None)
                path = BASE + (
                    "/runs/" + quote(run, safe="") if run else "/interaction"
                )
                owner_called = True
                document = await client.call("GET", path, params=body)
                if operation == "reasoning":
                    # Verify the exact run/source through its owner before reading handoffs.
                    rows = await client.call(
                        "GET",
                        "/api/desktop/reasoning",
                        params={
                            "workspace_id": request.workspace_id,
                            "session_id": request.session_id,
                        },
                    )
                    document = [
                        row
                        for row in rows
                        if row.get("request", {}).get("run_id") == request.run_id
                    ]
            else:
                if operation == "continue":
                    path = BASE + "/actions/" + quote(body.pop("action_id"), safe="")
                elif operation in ("respond", "decide", "cancel"):
                    subject = quote(
                        body.pop(
                            "checkpoint_id"
                            if operation in ("respond", "decide")
                            else "run_id"
                        ),
                        safe="",
                    )
                    path = BASE + (
                        "/interactions/"
                        + subject
                        + ("/decision" if operation == "decide" else "/response")
                        if operation in ("respond", "decide")
                        else "/runs/" + subject + "/cancel"
                    )
                else:
                    path = (
                        BASE
                        + {
                            "inputs": "/inputs",
                            "readiness": "/readiness",
                            "start": "/runs",
                        }[operation]
                    )
                owner_called = True
                document = await client.call("POST", path, json=body)
            return {"ok": True, "document": document}
        except WrightRequestRejected as failure:
            # The start owner reports capability failures before reserving a run.
            # A validated public reason distinguishes that rejection from a lost
            # acknowledgement. Other writes retain conservative reconciliation.
            start_rejected = (
                request.operation == "start"
                and failure.reason is not None
                and failure.reason.code == "CAPABILITY_UNAVAILABLE"
            )
            uncertain = (
                changes
                and owner_called
                and failure.status_code >= 500
                and not start_rejected
            )
            if not uncertain and failure.reason is not None:
                return {
                    "ok": False,
                    "http_status": failure.status_code,
                    "reason": failure.reason.model_dump(mode="json", exclude_none=True),
                }
            code = (
                "OUTCOME_UNKNOWN"
                if uncertain
                else "SCOPE_DENIED"
                if failure.status_code in (401, 403)
                else "SUBJECT_STALE"
                if failure.status_code == 409
                else "CAPABILITY_UNAVAILABLE"
            )
            return {
                "ok": False,
                "http_status": failure.status_code,
                "reason": {
                    "code": code,
                    "message": "Wright did not confirm this operation."
                    if uncertain
                    else "Wright rejected this process operation.",
                    "correction": "Reconcile the same saved request and run; no retry was sent."
                    if uncertain
                    else "Keep your draft and inspect the exact process or connection before proceeding.",
                },
            }

    @mcp.tool(
        structured_output=True,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_process_ui_read(request: PanelRead) -> dict[str, Any]:
        """Read one exact process/run snapshot or its queued desktop handoff. No effects."""
        return await invoke(request)

    @mcp.tool(
        structured_output=True,
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_process_ui_update(request: PanelUpdate) -> dict[str, Any]:
        """Submit a user-requested process operation to Wright's existing authority and recovery owners."""
        return await invoke(request, changes=True)

    if resource_uri:

        @mcp.tool(
            title="Open Wright run and results",
            structured_output=True,
            annotations=ToolAnnotations(
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,
                openWorldHint=False,
            ),
            meta={
                "ui": {"resourceUri": resource_uri, "visibility": ["model", "app"]},
                "openai/ui": {"entrypoints": [{"type": "thread"}]},
            },
        )
        async def wright_process_view(request: PanelSnapshot) -> dict[str, Any]:
            """Open an exact accepted process or durable run. Read only; never starts or resumes work."""
            result = await invoke(request)
            if not result["ok"]:
                return result
            workspace = await client.scope(request.workspace_id, request.session_id)
            return {
                "workspace": workspace,
                "snapshot": result["document"],
                "working_view_enabled": True,
                **({"native_workspace_files_enabled": True} if native_workspace_files else {}),
            }
