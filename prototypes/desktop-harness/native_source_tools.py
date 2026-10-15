"""Narrow native-editor save; Wright's source owner retains validation and CAS.

Local next-slice code, not enabled in the installed 0.2.0 plugin. No execution,
model selection, generic proxy or retry. UI tool visibility grants no authority.
"""

from typing import Any

import httpx
from mcp.types import ToolAnnotations


class WrightRequestRejected(ValueError):
    """HTTP rejection with a status, preserving existing ValueError behavior."""

    def __init__(self, status_code, message, *, reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


def register_native_source_tools(mcp, client):
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
