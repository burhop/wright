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

    async def delete_backup(self, workspace_dir: str, backup_id: str) -> None:
        await self._executor.run(
            "workspace.files.backup.delete",
            lambda: self._files_factory(workspace_dir).delete_backup(backup_id),
            timeout_seconds=self._timeout,
        )
