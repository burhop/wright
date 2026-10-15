"""Narrow native-editor save; Wright's source owner retains validation and CAS.

Local next-slice code, not enabled in the installed 0.2.0 plugin. No execution,
model selection, generic proxy or retry. UI tool visibility grants no authority.
"""

from typing import Annotated, Any, Literal

import httpx
from mcp.types import ToolAnnotations
from pydantic import Field, StrictStr

from core.process_validation import Contract, Digest, Identifier, canonical_digest
from core.workflow_bundle import BundleInspection, WorkflowBundle


class ExportRequest(Contract):
    workspace_id: Identifier
    session_id: Identifier
    path: Annotated[StrictStr, Field(max_length=256)]
    expected_storage_digest: Digest
    mode: Literal["source", "bundle"] = "source"
    selected_reference_paths: tuple[StrictStr, ...] = Field(default=(), max_length=64)
    selected_ui_ids: tuple[Identifier, ...] = Field(default=(), max_length=16)


class ExportResponse(Contract):
    bundle: WorkflowBundle
    bundle_digest: Digest


class InspectRequest(Contract):
    workspace_id: Identifier
    session_id: Identifier
    bundle: WorkflowBundle
    destination_path: Annotated[StrictStr, Field(max_length=256)]


class ImportRequest(InspectRequest):
    expected_bundle_digest: Digest


class WrightRequestRejected(ValueError):
    """HTTP rejection with a status, preserving existing ValueError behavior."""

    def __init__(self, status_code, message, *, reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


def register_native_source_tools(mcp, client):
    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_import_inspect(request: InspectRequest) -> dict[str, Any]:
        """Inspect a definition for this exact destination; never import or run it."""
        await client.scope(request.workspace_id, request.session_id)
        result = await client.call(
            "POST",
            "/api/workspace/workflow-bundles/inspect",
            json=request.model_dump(mode="json", exclude={"workspace_id"}),
        )
        report = BundleInspection.model_validate(result)
        if report.bundle_digest != canonical_digest(request.bundle):
            raise ValueError("Wright returned inspection for a different bundle")
        return report.model_dump(mode="json")

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_import(request: ImportRequest) -> dict[str, Any]:
        """Import an inspected definition through Wright's write-once owner."""
        dispatched = False
        try:
            if canonical_digest(request.bundle) != request.expected_bundle_digest:
                raise ValueError("Bundle changed after inspection")
            await client.scope(request.workspace_id, request.session_id)
            dispatched = True
            result = await client.call(
                "POST",
                "/api/workspace/workflow-bundles/import",
                json=request.model_dump(mode="json", exclude={"workspace_id"}),
            )
            source = result["source"]
            report = BundleInspection.model_validate(result["inspection"])
            if (
                source["workspace_id"] != request.workspace_id
                or source["path"] != request.destination_path
                or source["source"] != request.bundle.source
                or source["storage_digest"] != request.bundle.source_digest
                or source["metadata_authority"] != "wright_host"
                or report.bundle_digest != request.expected_bundle_digest
            ):
                raise ValueError("Import reply differs from the requested definition")
        except (httpx.HTTPError, ValueError, PermissionError, KeyError, TypeError):
            return {
                "ok": False,
                "error": {
                    "code": "OUTCOME_UNKNOWN" if dispatched else "IMPORT_REJECTED",
                    "outcome_known": not dispatched,
                    "message": (
                        "Wright did not confirm this import. Inspect the destination and import manifest before another action; some files may already exist."
                        if dispatched
                        else "Wright rejected this import before submission. Recheck its workspace and inspected bundle."
                    ),
                },
            }
        return {"ok": True, "document": result}

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        structured_output=True,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_export(request: ExportRequest) -> dict[str, Any]:
        """Read an exact definition-only export; this does not save a host file."""
        try:
            await client.scope(request.workspace_id, request.session_id)
            result = await client.call(
                "POST",
                "/api/workspace/workflow-bundles/export",
                json=request.model_dump(mode="json", exclude={"workspace_id"}),
            )
            exported = ExportResponse.model_validate(result)
            if (
                canonical_digest(exported.bundle) != exported.bundle_digest
                or exported.bundle.source_digest != request.expected_storage_digest
                or exported.bundle.mode != request.mode
            ):
                raise ValueError("Export bytes differ from their recorded digest")
        except (httpx.HTTPError, WrightRequestRejected, ValueError, PermissionError):
            return {
                "ok": False,
                "error": {
                    "code": "EXPORT_UNAVAILABLE",
                    "outcome_known": True,
                    "message": "Wright could not validate this export. Reopen the saved workflow and check its dependencies. No download is confirmed.",
                },
            }
        return {"ok": True, **exported.model_dump(mode="json")}

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=False,
        ),
        structured_output=True,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_save(
        workspace_id: str,
        session_id: str,
        path: str,
        source: str,
        expected_storage_revision: int,
        expected_storage_digest: str,
        semantic_change_validated: bool,
        layout: dict | None = None,
        expected_layout_revision: int | None = None,
    ) -> dict[str, Any]:
        """Save an exact workflow using Wright's existing source/layout compare-and-swap checks."""
        if layout is not None and expected_layout_revision is None:
            raise ValueError("Saving layout requires its expected revision")
        payload = {
            "session_id": session_id,
            "path": path,
            "source": source,
            "expected_storage_revision": expected_storage_revision,
            "expected_storage_digest": expected_storage_digest,
            "semantic_change_validated": semantic_change_validated,
        }
        if layout is not None:
            payload.update(
                layout=layout, expected_layout_revision=expected_layout_revision
            )
        try:
            await client.scope(workspace_id, session_id)
            document = await client.call(
                "PUT", "/api/workspace/workflow-sources", json=payload
            )
        except (httpx.HTTPStatusError, WrightRequestRejected) as failure:
            status = (
                failure.response.status_code
                if isinstance(failure, httpx.HTTPStatusError)
                else failure.status_code
            )
            code = (
                "WORKFLOW_SOURCE_CONFLICT"
                if status == 409
                else "PERMISSION_DENIED"
                if status in (401, 403)
                else "SOURCE_UNAVAILABLE"
            )
            return {
                "ok": False,
                "error": {
                    "code": code,
                    "outcome_known": status in (400, 401, 403, 404, 409, 422),
                    "message": "Wright rejected this save. Your local draft is unchanged."
                    if status < 500
                    else "Wright did not confirm the save. Read the accepted source before taking another action.",
                },
            }
        return {"ok": True, "document": document}
