from __future__ import annotations

from pathlib import Path
from typing import Any

from .runtime import MergeConflictError, WorkspaceManager
from ..models import ProcessResult
from .process import LocalProcessRunner


class LocalWorkspaceGit:
    def __init__(
        self,
        workspace_dir: str,
        *,
        process: LocalProcessRunner,
        timeout_seconds: float,
    ) -> None:
        self.workspace_dir = workspace_dir
        self.manager = WorkspaceManager(workspace_dir)
        self.process = process
        self.timeout = timeout_seconds

    def status(self) -> dict[str, Any]:
        return self.manager.get_git_status()

    def diff(self, path: str) -> str:
        return self.manager.get_git_diff(path)

    def revert(self, path: str) -> None:
        self.manager.revert_file(path)

    def commit(self, message: str) -> dict[str, Any]:
        return self.manager.commit_changes(message)

    def history(self) -> list[dict[str, Any]]:
        return self.manager.get_git_history()

    def push(self, remote: str, username: str | None, token: str | None) -> None:
        self.manager.push_remote(remote, username, token)

    def pull(self, remote: str, username: str | None, token: str | None) -> None:
        self.manager.pull_remote(remote, username, token)

    def validate_branch(self, branch: str) -> str:
        cleaned = branch.strip()
        if not cleaned or cleaned.startswith("-"):
            raise ValueError("Invalid branch name")
        result = self.process.run(
            ["git", "check-ref-format", "--branch", cleaned],
            cwd=Path(self.workspace_dir),
            timeout_seconds=min(self.timeout, 10),
        )
        if result.exit_code != 0:
            raise ValueError("Invalid branch name")
        return cleaned

    def branch(self, branch: str, *, create: bool) -> ProcessResult:
        cleaned = self.validate_branch(branch)
        argv = ["git", "checkout"]
        argv.extend(["-b", cleaned] if create else ["--", cleaned])
        return self.process.run(
            argv,
            cwd=Path(self.workspace_dir),
            timeout_seconds=self.timeout,
            check=True,
        )

    def merge(self, branch: str) -> ProcessResult:
        cleaned = self.validate_branch(branch)
        return self.process.run(
            ["git", "merge", "--", cleaned],
            cwd=Path(self.workspace_dir),
            timeout_seconds=self.timeout,
            check=True,
        )


__all__ = ["LocalWorkspaceGit", "MergeConflictError"]
