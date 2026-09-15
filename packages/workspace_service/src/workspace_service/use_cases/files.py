from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data_vault import WorkspaceRepository

from ..executor import BoundedExecutor
from ..adapters.filesystem import LocalWorkspaceFiles

BINARY_EXTENSIONS = {
    ".stl",
    ".obj",
    ".step",
    ".stp",
    ".iges",
    ".igs",
    ".3mf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".pdf",
    ".svg",
    ".webp",
}


@dataclass(frozen=True, slots=True)
class FileReadResult:
    path: Path
    content: bytes | None
    binary: bool


class WorkspaceFileUseCases:
    def __init__(
        self,
        db_path: str,
        executor: BoundedExecutor,
        files_factory: Callable[[str], LocalWorkspaceFiles],
        *,
        repository: WorkspaceRepository | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._db_path = db_path
        self._executor = executor
        self._files_factory = files_factory
        self._repository = repository
        self._timeout = timeout_seconds

    async def tree(self, workspace_dir: str) -> dict[str, Any]:
        def work() -> dict[str, Any]:
            tree = self._files_factory(workspace_dir).tree()
            workspace = (
                self._repository.get_by_path(workspace_dir)
                if self._repository is not None
                else None
            )
            if workspace:
                tree["name"] = workspace.get("workspace_name") or os.path.basename(
                    workspace["local_path"]
                )
            return tree

        return await self._executor.run(
            "workspace.files.list", work, timeout_seconds=self._timeout
        )

    async def read(
        self, workspace_dir: str, relative_path: str, backup_id: str | None = None
    ) -> FileReadResult:
        def work() -> FileReadResult:
            absolute, content = self._files_factory(workspace_dir).read(
                relative_path, backup_id
            )
            binary = absolute.suffix.lower() in BINARY_EXTENSIONS
            if not binary:
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError:
                    binary = True
            return FileReadResult(absolute, None if binary else content, binary)

        return await self._executor.run(
            "workspace.files.read", work, timeout_seconds=self._timeout
        )

    async def create(
        self, workspace_dir: str, path: str, node_type: str
    ) -> dict[str, Any]:
        return await self._executor.run(
            "workspace.files.create",
            lambda: self._files_factory(workspace_dir).create(path, node_type),
            timeout_seconds=self._timeout,
        )

    async def delete(self, workspace_dir: str, path: str) -> None:
        await self._executor.run(
            "workspace.files.delete",
            lambda: self._files_factory(workspace_dir).delete(path),
            timeout_seconds=self._timeout,
        )

    async def move(self, workspace_dir: str, source: str, destination: str) -> None:
        await self._executor.run(
            "workspace.files.move",
            lambda: self._files_factory(workspace_dir).move(source, destination),
            timeout_seconds=self._timeout,
        )

    async def write(self, workspace_dir: str, path: str, content: str) -> None:
        await self._executor.run(
            "workspace.files.write",
            lambda: self._files_factory(workspace_dir).write(
                path, content.encode("utf-8")
            ),
            timeout_seconds=self._timeout,
        )

    async def backup(self, workspace_dir: str, path: str, content: str) -> str:
        return await self._executor.run(
            "workspace.files.backup",
            lambda: self._files_factory(workspace_dir).backup(
                path, content.encode("utf-8")
            ),
            timeout_seconds=self._timeout,
        )

    async def write_generated(
        self, workspace_dir: str, path: str, content: str, policy: str
    ) -> str:
        return await self.write_generated_bytes(
            workspace_dir, path, content.encode("utf-8"), policy
        )

    async def write_generated_bytes(
        self, workspace_dir: str, path: str, content: bytes, policy: str
    ) -> str:
        return await self._executor.run(
            "workspace.files.write_generated",
            lambda: self._files_factory(workspace_dir).write_generated(
                path, content, policy
            ),
            timeout_seconds=self._timeout,
        )

    async def read_reference(self, workspace_dir: str, path: str) -> bytes:
        """Bounded bytes for workflow references, including images."""
        from ..workspace_path import WorkspacePath

        def work():
            target = WorkspacePath(workspace_dir).resolve(path, must_exist=True)
            with target.open("rb") as stream:
                content = stream.read(4 * 1024 * 1024 + 1)
            if len(content) > 4 * 1024 * 1024:
                raise ValueError("Choose a reference smaller than 4 MiB.")
            return content

        return await self._executor.run(
            "workspace.files.reference", work, timeout_seconds=self._timeout
        )

    async def hash_reference(self, workspace_dir: str, path: str) -> str:
        """Verify checkpoint bytes without applying the document-loading limit."""
        from ..workspace_file_identity import workspace_file_sha256

        return await self._executor.run(
            "workspace.files.reference_identity",
            lambda: workspace_file_sha256(workspace_dir, path),
            timeout_seconds=self._timeout,
        )

    async def read_capture_file(self, workspace_dir: str, path: str) -> bytes:
        """Read one verified capture artifact with an explicit 20 MiB ceiling."""
        from ..workspace_path import WorkspacePath

        def work():
            target = WorkspacePath(workspace_dir).resolve(path, must_exist=True)
            with target.open("rb") as stream:
                content = stream.read(20 * 1024 * 1024 + 1)
            if len(content) > 20 * 1024 * 1024:
                raise ValueError("Choose a capture artifact no larger than 20 MiB.")
            return content

        return await self._executor.run(
            "workspace.files.capture", work, timeout_seconds=self._timeout
        )

    async def upload_workflow_image(
        self, workspace_dir: str, name: str, content: bytes
    ) -> str:
        from ..workflow_references import image_media_type

        if not content or len(content) > 4 * 1024 * 1024:
            raise ValueError("Choose an image smaller than 4 MiB.")
        if (
            Path(name).name != name
            or any(c in name for c in "/\\:%")
            or name.startswith(".")
        ):
            raise ValueError("Choose an image with a simple filename.")
        image_media_type(name, content)
        return await self._executor.run(
            "workspace.files.upload_image",
            lambda: self._files_factory(workspace_dir).write_generated(
                name, content, "indexed"
            ),
            timeout_seconds=self._timeout,
        )

    async def delete_backup(self, workspace_dir: str, backup_id: str) -> None:
        await self._executor.run(
            "workspace.files.backup.delete",
            lambda: self._files_factory(workspace_dir).delete_backup(backup_id),
            timeout_seconds=self._timeout,
        )
