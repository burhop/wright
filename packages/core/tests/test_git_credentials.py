import subprocess

import pytest

from core.workspace import WorkspaceManager


@pytest.mark.parametrize("operation", ["push_remote", "pull_remote"])
def test_git_credentials_use_askpass_not_url_or_argv(tmp_path, monkeypatch, operation):
    manager = WorkspaceManager(str(tmp_path))
    monkeypatch.setattr(
        manager, "get_git_status", lambda: {"branch_name": "main", "changes": []}
    )
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    token = "provider-token:with/@reserved?characters"
    remote = "https://example.test/owner/repository.git"

    getattr(manager, operation)(remote, "engineer", token)

    command, kwargs = calls[-1]
    assert remote in command
    assert token not in repr(command)
    assert "engineer" not in repr(command)
    assert kwargs["env"]["WRIGHT_GIT_TOKEN"] == token
    assert kwargs["env"]["WRIGHT_GIT_USERNAME"] == "engineer"
    assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_git_error_redacts_token(tmp_path, monkeypatch):
    manager = WorkspaceManager(str(tmp_path))
    monkeypatch.setattr(
        manager, "get_git_status", lambda: {"branch_name": "main", "changes": []}
    )
    token = "provider-token-that-must-not-leak"

    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr=f"denied {token}")

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(RuntimeError) as error:
        manager.push_remote("https://example.test/repo.git", "user", token)
    assert token not in str(error.value)
