from __future__ import annotations

import subprocess

import pytest

from workspace_service.executor import BoundedExecutor
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.adapters.runtime import WorkspaceManager
from workspace_service.use_cases.files import WorkspaceFileUseCases


def test_workspace_manager_requires_an_existing_root(tmp_path):
    with pytest.raises(FileNotFoundError):
        WorkspaceManager(str(tmp_path / "missing-workspace"))


def test_workspace_manager_allows_file_workspace_when_git_is_unavailable(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    real_run = subprocess.run

    def run_without_git(command, *args, **kwargs):
        if command == ["git", "init"]:
            raise FileNotFoundError("git")
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run_without_git)

    WorkspaceManager(str(workspace))

    assert (workspace / ".gitignore").is_file()
    assert not (workspace / ".git").exists()


@pytest.mark.asyncio
async def test_file_use_cases_preserve_tree_text_binary_and_mutations(tmp_path):
    db_path = str(tmp_path / "unused.db")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    WorkspaceManager(str(workspace))
    executor = BoundedExecutor(max_workers=2)
    use_cases = WorkspaceFileUseCases(db_path, executor, LocalWorkspaceFiles)

    await use_cases.create(str(workspace), "notes.txt", "file")
    await use_cases.write(str(workspace), "notes.txt", "hello")
    result = await use_cases.read(str(workspace), "notes.txt")
    assert result.content == b"hello"
    assert not result.binary
    assert any(
        child["name"] == "notes.txt"
        for child in (await use_cases.tree(str(workspace)))["children"]
    )
    await use_cases.move(str(workspace), "notes.txt", "moved.txt")
    await use_cases.delete(str(workspace), "moved.txt")
    await executor.close()


@pytest.mark.asyncio
async def test_file_use_cases_reject_escape(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    executor = BoundedExecutor(max_workers=1)
    use_cases = WorkspaceFileUseCases(
        str(tmp_path / "unused.db"), executor, LocalWorkspaceFiles
    )
    with pytest.raises(ValueError):
        await use_cases.write(str(workspace), "../outside.txt", "no")
    await executor.close()
