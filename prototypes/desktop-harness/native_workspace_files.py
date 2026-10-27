"""Read-only native-file presentation over existing Wright owners.

No file URI interpretation, workspace activation, source creation or execution.
The experimental backend explicitly opts in; the installed runtime is unchanged.
"""

import hashlib
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from workspace_service.workspace_path import WorkspacePath
from workspace_service.workflow_sources import WorkflowSourceStorageError


class WorkspaceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workspace_id: str = Field(min_length=1, max_length=100)
    session_id: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=4096)
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class HostDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    absolute_path: str = Field(min_length=1, max_length=4096)
    resume: WorkspaceDocument | None = None


def visible_document_path(workspace_dir: str, path: str) -> Path:
    """Same visible-file restriction used by the desktop download surface."""
    parts = path.replace("\\", "/").split("/")
    if (
        len(path) > 4096
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
        or any(
            not part or part.startswith(".") or part == "freecad_mcp_work"
            for part in parts
        )
    ):
        raise ValueError("File is outside the visible file surface")
    return WorkspacePath(workspace_dir).resolve(path, must_exist=True)


class NativeWorkspaceFiles:
    def __init__(self, backend):
        self.backend = backend

    def workspace(self, workspace_id, session_id):
        try:
            return self.backend.workspace(workspace_id, session_id)
        except (OSError, ValueError):
            raise HTTPException(403, "Native workspace scope is unavailable") from None

    async def describe(self, request: WorkspaceDocument) -> dict:
        self.backend.require_connection()
        row = self.workspace(request.workspace_id, request.session_id)
        try:
            target = visible_document_path(row["local_path"], request.path)
            if not target.is_file():
                raise ValueError("A regular file is required")
            content = await self.backend.service.files.read_bytes(
                row["local_path"], request.path, maximum_bytes=16 * 1024 * 1024
            )
        except (OSError, ValueError):
            raise HTTPException(
                422, "Choose a visible workspace file up to 16 MiB"
            ) from None
        except RuntimeError:
            raise HTTPException(503, "Workspace file reading is unavailable") from None
        digest = hashlib.sha256(content).hexdigest()
        if request.expected_sha256 and request.expected_sha256 != digest:
            raise HTTPException(
                409, "The file changed; explicitly reopen its current revision"
            )
        result = {
            "schema_version": "wright.native-workspace-file/1",
            "workspace_id": request.workspace_id,
            "session_id": request.session_id,
            "path": target.relative_to(Path(row["local_path"]).resolve()).as_posix(),
            "filename": target.name,
            "sha256": digest,
            "bytes": len(content),
        }
        if target.suffix.lower() == ".wflow":
            try:
                document = await self.backend.service.workflow_sources.read(
                    row["local_path"], result["path"]
                )
            except (WorkflowSourceStorageError, OSError, ValueError):
                raise HTTPException(
                    409, "This file is not an available accepted workflow"
                ) from None
            if document.path != result["path"] or document.storage_digest != digest:
                raise HTTPException(
                    409, "Accepted source differs from the current file; reopen it"
                )
            result.update(
                viewer="workflow", definition_revision=document.definition_revision
            )
        elif (
            target.suffix.lower() == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n")
        ) or (
            target.suffix.lower() in {".jpg", ".jpeg"}
            and content.startswith(b"\xff\xd8\xff")
        ):
            result["viewer"] = "image"
        else:
            # No renderer is advertised merely because a file has an extension.
            return {
                **result,
                "supported": False,
                "reason": "No qualified native viewer for this format yet",
            }
        return {**result, "supported": True, "absolute_path": str(target)}

    async def resolve(self, request: HostDocument) -> dict:
        self.backend.require_connection()
        absolute = Path(request.absolute_path)
        if not absolute.is_absolute():
            raise HTTPException(403, "Native file scope is unavailable")
        if request.resume is not None:
            result = await self.describe(request.resume)
            if not result.get("supported") or Path(result["absolute_path"]) != absolute:
                raise HTTPException(
                    403, "Native file differs from the remembered workspace scope"
                )
            return result
        matches = []
        for row in self.backend.service.lifecycle.list_all():
            root = Path(row["local_path"])
            # Lexical scope is checked before probing the supplied host path.
            if not absolute.is_relative_to(root):
                continue
            sessions = [
                item
                for item in self.backend.service.repository.list_sessions(
                    row["workspace_id"]
                )
                if item["agent_id"] == "openai-desktop-harness"
            ]
            if len(sessions) != 1:
                raise HTTPException(
                    409, "An explicit saved desktop session is required for this file"
                )
            scope = WorkspaceDocument(
                workspace_id=row["workspace_id"],
                session_id=sessions[0]["session_id"],
                path=absolute.relative_to(root).as_posix(),
            )
            # Existing workspace authorization rejects outside roots/other platforms.
            self.workspace(scope.workspace_id, scope.session_id)
            matches.append(scope)
        if len(matches) != 1:
            raise HTTPException(403, "Native file scope is unavailable or ambiguous")
        result = await self.describe(matches[0])
        if not result.get("supported") or Path(result["absolute_path"]) != absolute:
            raise HTTPException(403, "Native file identity is unavailable")
        return result


def register_native_workspace_files(router, backend):
    owner = NativeWorkspaceFiles(backend)

    @router.post("/native-files/describe")
    async def describe_native_file(request: WorkspaceDocument):
        return await owner.describe(request)

    @router.post("/native-files/context")
    async def resolve_native_file(request: HostDocument):
        return await owner.resolve(request)
