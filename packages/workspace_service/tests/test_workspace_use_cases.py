from __future__ import annotations

import pytest

from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.use_cases.git import WorkspaceGitUseCases
from workspace_service.models import ProcessResult

from .fakes import RecordingRepository


class RecordingFiles:
    def __init__(self, workspace: str) -> None:
        self.workspace = workspace
        self.values: dict[str, bytes] = {}

    def write(self, path: str, content: bytes) -> None:
        self.values[path] = content


@pytest.mark.asyncio
async def test_file_use_case_accepts_recording_adapter_without_filesystem():
    adapters: dict[str, RecordingFiles] = {}

    def factory(workspace: str) -> RecordingFiles:
        return adapters.setdefault(workspace, RecordingFiles(workspace))

    executor = BoundedExecutor(max_workers=1)
    use_cases = WorkspaceFileUseCases("unused", executor, factory)
    await use_cases.write("workspace-a", "part.txt", "content")
    assert adapters["workspace-a"].values == {"part.txt": b"content"}
    await executor.close()


class RecordingGit:
    def __init__(self, workspace: str) -> None:
        self.workspace = workspace
        self.messages: list[str] = []

    def status(self):
        return {"branch_name": "main", "is_clean": True, "changes": []}

    def commit(self, message: str):
        self.messages.append(message)
        return {"commit_hash": "abc123", "message": message}

    def branch(self, branch: str, *, create: bool):
        return ProcessResult(0, f"branch {branch}", "")


@pytest.mark.asyncio
async def test_git_use_case_accepts_recording_adapter_without_git_executable():
    adapters: dict[str, RecordingGit] = {}

    def factory(workspace: str) -> RecordingGit:
        return adapters.setdefault(workspace, RecordingGit(workspace))

    repository = RecordingRepository()
    executor = BoundedExecutor(max_workers=1)
    use_cases = WorkspaceGitUseCases(executor, repository, factory)
    assert (await use_cases.status("workspace-a"))["is_clean"] is True
    assert (await use_cases.commit("workspace-a", "message"))["commit_hash"] == "abc123"
    assert (
        await use_cases.branch("workspace-a", "feature", create=True)
        == "branch feature"
    )
    assert adapters["workspace-a"].messages == ["message"]
    await executor.close()
