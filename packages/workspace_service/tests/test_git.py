from __future__ import annotations

import subprocess

import pytest

from workspace_service.executor import BoundedExecutor
from workspace_service.adapters import LocalProcessRunner, LocalWorkspaceGit
from data_vault import WorkspaceRepository, upgrade_database
from core.secrets import default_secret_provider
from workspace_service.adapters.runtime import WorkspaceManager
from workspace_service.use_cases.git import WorkspaceGitUseCases


def _git(workspace, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=workspace, check=True, capture_output=True, text=True
    )


@pytest.mark.asyncio
async def test_git_use_cases_status_commit_history_branch_and_diff(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    WorkspaceManager(str(workspace))
    _git(workspace, "config", "user.email", "test@example.com")
    _git(workspace, "config", "user.name", "Test")
    (workspace / "part.txt").write_text("v1", encoding="utf-8")
    executor = BoundedExecutor(max_workers=2)
    db_path = str(tmp_path / "state.db")
    upgrade_database(db_path)
    repository = WorkspaceRepository(db_path, secrets=default_secret_provider())
    process = LocalProcessRunner()
    use_cases = WorkspaceGitUseCases(
        executor,
        repository,
        lambda path: LocalWorkspaceGit(path, process=process, timeout_seconds=30),
    )

    status = await use_cases.status(str(workspace))
    part = next(
        change for change in status["changes"] if change["path"].endswith("part.txt")
    )
    assert part["file_size"] == 2
    commit = await use_cases.commit(str(workspace), "initial")
    assert commit["commit_hash"]
    assert (await use_cases.history(str(workspace)))[0]["message"] == "initial"
    message = await use_cases.branch(str(workspace), "feature/test", create=True)
    assert "branch" in message.lower() or message
    (workspace / "part.txt").write_text("v2", encoding="utf-8")
    assert await use_cases.diff(str(workspace), "part.txt")
    await executor.close()


@pytest.mark.asyncio
async def test_git_use_cases_reject_option_like_branch(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    WorkspaceManager(str(workspace))
    executor = BoundedExecutor(max_workers=1)
    db_path = str(tmp_path / "state.db")
    upgrade_database(db_path)
    repository = WorkspaceRepository(db_path, secrets=default_secret_provider())
    process = LocalProcessRunner()
    use_cases = WorkspaceGitUseCases(
        executor,
        repository,
        lambda path: LocalWorkspaceGit(path, process=process, timeout_seconds=30),
    )
    with pytest.raises(ValueError, match="Invalid branch"):
        await use_cases.branch(str(workspace), "--upload-pack=evil", create=False)
    await executor.close()
