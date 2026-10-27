"""Opt-in native file presentation; Wright's existing owners resolve all scope.

Paths come from the authenticated backend or documented host metadata. Opaque
resource URIs are never parsed, and local byte checks never grant workflow tools.
"""

import hashlib
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from native_file_contracts import FileInput, ProbeObservation, WorkspaceDocument


def verify_local_file(document: dict) -> None:
    """Qualify execution-host byte identity, never a guessed remote path mapping."""
    try:
        path = Path(document["absolute_path"])
        if (
            not path.is_absolute()
            or path.resolve(strict=True) != path
            or not path.is_file()
            or path.stat().st_size > 16 * 1024 * 1024
        ):
            raise ValueError()
        with path.open("rb") as stream:
            content = stream.read(16 * 1024 * 1024 + 1)
        if (
            len(content) != document["bytes"]
            or hashlib.sha256(content).hexdigest() != document["sha256"]
        ):
            raise ValueError()
    except (OSError, ValueError, TypeError, KeyError):
        raise ValueError(
            "Native file opening requires the same execution-host filesystem and current bytes. "
            "This path is unavailable or changed; no remote mapping was attempted."
        ) from None


def register_native_workspace_file_tools(
    mcp, client, *, resource_uri: str, working_view_enabled: bool
):
    read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )

    @mcp.tool(
        title="Prepare workspace file tab",
        annotations=read,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workspace_file_describe(
        request: WorkspaceDocument,
    ) -> dict[str, Any]:
        """Read an exact file descriptor and qualify the backend/host filesystem. No file is opened or executed."""
        document = await client.call(
            "POST",
            "/api/desktop/native-files/describe",
            json=request.model_dump(exclude_none=True),
        )
        if document.get("supported"):
            verify_local_file(document)
        return document

    @mcp.tool(
        title="Wright workflow file",
        annotations=read,
        meta={
            "ui": {"resourceUri": resource_uri, "visibility": ["app"]},
            "openai/ui": {"entrypoints": [{"type": "file", "extensions": [".wflow"]}]},
        },
    )
    async def wright_workflow_file(file: FileInput) -> dict[str, Any]:
        """Render the native shell; filename and opaque URI do not establish scope."""
        return {
            "view": "native-workflow-file",
            "file": file.model_dump(),
            "native_workspace_files_enabled": True,
        }

    @mcp.tool(
        title="Resolve workspace workflow file",
        annotations=read,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_file_context(
        request: ProbeObservation, ctx: Context
    ) -> dict[str, Any]:
        """Resolve only documented host metadata, preserving explicit continuation scope."""
        meta = ctx.request_context.meta
        values = meta.model_dump() if hasattr(meta, "model_dump") else meta
        resource = values.get("openai/resource") if isinstance(values, dict) else None
        path = resource.get("path") if isinstance(resource, dict) else None
        if not isinstance(path, str) or not 0 < len(path) <= 4096:
            raise ValueError("Host file path is missing")
        document = await client.call(
            "POST",
            "/api/desktop/native-files/context",
            json={
                "absolute_path": path,
                **(
                    {"resume": request.resume.model_dump(exclude_none=True)}
                    if request.resume
                    else {}
                ),
            },
        )
        if not document.get("supported") or document.get("viewer") != "workflow":
            raise ValueError("No qualified workflow file binding is available")
        verify_local_file(document)
        workspace = await client.scope(document["workspace_id"], document["session_id"])
        source = await client.call(
            "GET",
            "/api/workspace/workflow-sources",
            params={"session_id": document["session_id"], "path": document["path"]},
        )
        if (
            source.get("workspace_id") != document["workspace_id"]
            or source.get("path") != document["path"]
            or source.get("storage_digest") != document["sha256"]
        ):
            raise ValueError(
                "Accepted source changed while opening the file; explicitly reopen it"
            )
        return {
            "native_workspace_files_enabled": True,
            "workspace": workspace,
            "document": source,
            "working_view_enabled": working_view_enabled,
            "native_file": {
                **document,
                "kind": "workflow",
                "label": document["filename"],
                "source_sha256": document["sha256"],
                "instance_id": request.instance_id,
            },
            "evidence_boundary": "Backend scope/source and local bytes verified at this read; native rendering is unverified.",
        }
