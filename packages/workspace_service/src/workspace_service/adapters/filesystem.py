from __future__ import annotations

from pathlib import Path
from typing import Any

from workspace_service.workspace_path import WorkspacePath

from .runtime import WorkspaceManager


class LocalWorkspaceFiles:
    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self.manager = WorkspaceManager(workspace_dir)

    def tree(self) -> dict[str, Any]:
        return self.manager.get_workspace_tree()

    def read(
        self, relative_path: str, backup_id: str | None = None
    ) -> tuple[Path, bytes]:
        if backup_id:
            absolute = WorkspacePath(self.workspace_dir).backup(
                backup_id, must_exist=True
            )
            return absolute, absolute.read_bytes()
        absolute = Path(self.manager.sanitize_path(relative_path))
        if not absolute.is_file():
            raise FileNotFoundError(relative_path)
        return absolute, self.manager.read_file_content(relative_path)

    def create(self, path: str, node_type: str) -> dict[str, Any]:
        return self.manager.create_file_node(path, node_type)

    def delete(self, path: str) -> None:
        self.manager.delete_file_node(path)

    def move(self, source: str, destination: str) -> None:
        self.manager.move_file_node(source, destination)

    def write(self, path: str, content: bytes) -> None:
        self.manager.write_file_content(path, content)

    def backup(self, path: str, content: bytes) -> str:
        return self.manager.write_backup(path, content)

    def delete_backup(self, backup_id: str) -> None:
        self.manager.delete_backup(backup_id)
