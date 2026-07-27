from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from data_vault import WorkspaceRepository

from ..adapters.git import LocalWorkspaceGit, MergeConflictError
from ..executor import BoundedExecutor


@dataclass(frozen=True, slots=True)
class GitMergeConflict(Exception):
    files: tuple[str, ...]
    message: str = "Merge conflicts detected"


class WorkspaceGitUseCases:
    def __init__(
        self,
        executor: BoundedExecutor,
        repository: WorkspaceRepository,
        git_factory: Callable[[str], LocalWorkspaceGit],
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._executor = executor
        self._repository = repository
        self._git_factory = git_factory
        self._timeout = timeout_seconds

    async def status(self, workspace_dir: str) -> dict[str, Any]:
        def work() -> dict[str, Any]:
            result = self._git_factory(workspace_dir).status()
            for change in result["changes"]:
                path = os.path.join(workspace_dir, change["path"].lstrip("/\\"))
                try:
                    change["file_size"] = (
                        os.path.getsize(path) if os.path.isfile(path) else None
                    )
                except OSError:
                    change["file_size"] = None
            return result

        return await self._executor.run(
            "workspace.git.status", work, timeout_seconds=self._timeout
        )

    async def diff(self, workspace_dir: str, path: str) -> str:
        return await self._executor.run(
            "workspace.git.diff",
            lambda: self._git_factory(workspace_dir).diff(path),
            timeout_seconds=self._timeout,
        )

    async def revert(self, workspace_dir: str, path: str) -> None:
        await self._executor.run(
            "workspace.git.revert",
            lambda: self._git_factory(workspace_dir).revert(path),
            timeout_seconds=self._timeout,
        )

    async def commit(self, workspace_dir: str, message: str) -> dict[str, Any]:
        return await self._executor.run(
            "workspace.git.commit",
            lambda: self._git_factory(workspace_dir).commit(message),
            timeout_seconds=self._timeout,
        )

    async def history(self, workspace_dir: str) -> list[dict[str, Any]]:
        return await self._executor.run(
            "workspace.git.history",
            lambda: self._git_factory(workspace_dir).history(),
            timeout_seconds=self._timeout,
        )

    def _remote(
        self, workspace_dir: str
    ) -> tuple[LocalWorkspaceGit, dict[str, Any], str]:
        workspace = self._repository.get_by_path(workspace_dir)
        if not workspace:
            raise LookupError("Workspace not found")
        remote = workspace.get("git_remote_url")
        if not remote:
            raise ValueError("Git remote URL not configured")
        return self._git_factory(workspace_dir), workspace, remote

    async def push(self, workspace_dir: str) -> None:
        def work() -> None:
            adapter, workspace, remote = self._remote(workspace_dir)
            adapter.push(
                remote,
                workspace.get("git_username"),
                self._repository.git_token(workspace["workspace_id"]),
            )

        await self._executor.run(
            "workspace.git.push", work, timeout_seconds=self._timeout
        )

    async def pull(self, workspace_dir: str) -> None:
        def work() -> None:
            adapter, workspace, remote = self._remote(workspace_dir)
            try:
                adapter.pull(
                    remote,
                    workspace.get("git_username"),
                    self._repository.git_token(workspace["workspace_id"]),
                )
            except MergeConflictError as error:
                raise GitMergeConflict(tuple(error.conflicted_files)) from error

        await self._executor.run(
            "workspace.git.pull", work, timeout_seconds=self._timeout
        )

    async def branch(self, workspace_dir: str, branch: str, *, create: bool) -> str:
        def work() -> str:
            try:
                result = self._git_factory(workspace_dir).branch(branch, create=create)
            except subprocess.CalledProcessError as error:
                raise ValueError(
                    error.stderr or "Git branch operation failed"
                ) from error
            return result.stdout or result.stderr or "Branch checked out successfully"

        return await self._executor.run(
            "workspace.git.branch", work, timeout_seconds=self._timeout
        )

    async def merge(self, workspace_dir: str, branch: str) -> str:
        def work() -> str:
            try:
                result = self._git_factory(workspace_dir).merge(branch)
            except subprocess.CalledProcessError as error:
                output = (error.stdout or "") + (error.stderr or "")
                if "CONFLICT" in output:
                    raise GitMergeConflict((), output) from error
                raise ValueError(error.stderr or "Git merge failed") from error
            return result.stdout or result.stderr or "Branch merged successfully"

        return await self._executor.run(
            "workspace.git.merge", work, timeout_seconds=self._timeout
        )
