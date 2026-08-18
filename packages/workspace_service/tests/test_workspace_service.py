import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest
import workspace_service.service as service_module

from agent_adapters import AgentSessionInfo
from workspace_service import (
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceProtectedPathError,
    WorkspaceService,
    default_workspace_parent_dir,
)
from workspace_service.surfaces.display_tokens import (
    DisplayExecutionTokenService,
    DisplayTokenRejected,
)


class FakeEngine:
    def __init__(self):
        self.sessions: list[AgentSessionInfo] = []

    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        info = AgentSessionInfo(
            session_id=f"session-{len(self.sessions) + 1}",
            title="Fake",
            created_at=1,
            updated_at=1,
            message_count=0,
            workspace=workspace,
        )
        self.sessions.append(info)
        return info

    async def list_sessions(self) -> list[AgentSessionInfo]:
        return list(self.sessions)

    async def get_session_workspace(self, session_id: str) -> str | None:
        for session in self.sessions:
            if session.session_id == session_id:
                return session.workspace
        return None


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "workspace.db"
    conn = sqlite3.connect(path)
    try:
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            workspace_prompt TEXT,
            git_large_file_threshold INTEGER,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_installed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive',
            instructions TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()
    return str(path)


def test_default_workspace_parent_prefers_userprofile():
    assert (
        default_workspace_parent_dir(
            {"USERPROFILE": r"C:\Users\Engineer", "HOME": "/unexpected"}
        )
        == r"C:\Users\Engineer\wright"
    )


def test_default_workspace_parent_honors_explicit_root():
    assert (
        default_workspace_parent_dir(
            {
                "WRIGHT_WORKSPACES_DIR": r"D:\Engineering\Wright",
                "USERPROFILE": r"C:\Users\Engineer",
            }
        )
        == r"D:\Engineering\Wright"
    )


@pytest.mark.asyncio
async def test_create_workspace_uses_facade_and_materializes_hermes_context(
    tmp_path, db_path
):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    workspace_path = str(tmp_path / "phase-two-workspace")

    record = await service.create_workspace(
        "Phase Two Workspace", workspace_path, FakeEngine()
    )

    assert record.workspace_name == "Phase Two Workspace"
    assert record.local_path == workspace_path
    assert os.path.isdir(workspace_path)
    assert os.path.exists(os.path.join(workspace_path, ".hermes.md"))


@pytest.mark.asyncio
async def test_create_workspace_rejects_existing_path(tmp_path, db_path):
    workspace_path = tmp_path / "existing"
    workspace_path.mkdir()
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))

    with pytest.raises(WorkspaceConflictError):
        await service.create_workspace("Existing", str(workspace_path), FakeEngine())


@pytest.mark.asyncio
async def test_create_workspace_rejects_nonmanaged_explicit_path(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))

    with pytest.raises(WorkspaceInvalidRequestError, match="managed path"):
        await service.create_workspace(
            "Managed Workspace", str(tmp_path / "somewhere-else"), FakeEngine()
        )


def test_authorize_session_workspace_accepts_registered_existing_path(
    tmp_path, db_path
):
    managed_root = tmp_path / "managed"
    workspace = tmp_path / "explicit-workspace"
    workspace.mkdir()
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(managed_root))
    service.repository.create(
        "workspace-1", "session-1", str(workspace), workspace_name="Explicit"
    )

    authorized = service.authorize_session_workspace(str(workspace))

    assert authorized.path == str(workspace.resolve())
    assert authorized.workspace_id == "workspace-1"
    assert authorized.created is False


def test_authorize_session_workspace_rejects_registered_application_source(
    tmp_path, db_path
):
    application_root = tmp_path / "wright-application"
    application_root.mkdir()
    service = WorkspaceService(
        db_path,
        parent_dir_provider=lambda: str(tmp_path / "managed"),
        protected_roots_provider=lambda: (str(application_root),),
    )
    service.repository.create(
        "workspace-1",
        "session-1",
        str(application_root),
        workspace_name="Unsafe Legacy Workspace",
    )

    with pytest.raises(WorkspaceProtectedPathError, match="access blocked"):
        service.authorize_session_workspace(str(application_root))


@pytest.mark.asyncio
async def test_activate_workspace_rejects_legacy_path_containing_application_source(
    tmp_path, db_path
):
    application_root = tmp_path / "installation" / "wright"
    application_root.mkdir(parents=True)
    unsafe_parent = application_root.parent
    service = WorkspaceService(
        db_path,
        parent_dir_provider=lambda: str(tmp_path / "managed"),
        protected_roots_provider=lambda: (str(application_root),),
    )
    service.repository.create(
        "workspace-1",
        "session-1",
        str(unsafe_parent),
        workspace_name="Unsafe Parent Workspace",
    )

    with pytest.raises(WorkspaceProtectedPathError, match="application files"):
        await service.activate_workspace("session-1", FakeEngine())


def test_workspace_tool_access_rejects_legacy_application_workspace(tmp_path, db_path):
    application_root = tmp_path / "wright-application"
    application_root.mkdir()
    service = WorkspaceService(
        db_path,
        parent_dir_provider=lambda: str(tmp_path / "managed"),
        protected_roots_provider=lambda: (str(application_root),),
    )
    service.repository.create(
        "workspace-1",
        "session-1",
        str(application_root),
        workspace_name="Unsafe Legacy Workspace",
    )

    with pytest.raises(WorkspaceProtectedPathError, match="access blocked"):
        service.list_workspace_tools_by_workspace("workspace-1")


def test_authorize_session_workspace_rejects_unregistered_path_without_creating(
    tmp_path, db_path
):
    managed_root = tmp_path / "managed"
    requested = managed_root / "caller-selected"
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(managed_root))

    with pytest.raises(WorkspaceInvalidRequestError, match="registered"):
        service.authorize_session_workspace(str(requested))

    assert not requested.exists()


def test_authorize_session_workspace_rejects_registered_missing_directory(
    tmp_path, db_path
):
    missing = tmp_path / "missing"
    service = WorkspaceService(
        db_path, parent_dir_provider=lambda: str(tmp_path / "managed")
    )
    service.repository.create(
        "workspace-1", "session-1", str(missing), workspace_name="Missing"
    )

    with pytest.raises(WorkspaceInvalidRequestError, match="existing"):
        service.authorize_session_workspace(str(missing))

    assert not missing.exists()


def test_authorize_session_workspace_rejects_symlink_alias(tmp_path, db_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(workspace, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"host cannot create symlinks: {exc}")
    service = WorkspaceService(
        db_path, parent_dir_provider=lambda: str(tmp_path / "managed")
    )
    service.repository.create(
        "workspace-1", "session-1", str(workspace), workspace_name="Workspace"
    )

    with pytest.raises(WorkspaceInvalidRequestError, match="registered"):
        service.authorize_session_workspace(str(alias))


def test_authorize_session_workspace_generates_managed_path_when_omitted(
    tmp_path, db_path
):
    managed_root = tmp_path / "managed"
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(managed_root))

    authorized = service.authorize_session_workspace(None)

    generated = Path(authorized.path)
    assert authorized.workspace_id is None
    assert authorized.created is True
    assert generated.is_dir()
    assert generated.parent == managed_root.resolve()
    assert generated.name.startswith("session-")


@pytest.mark.asyncio
async def test_update_config_refreshes_context(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    workspace_path = str(tmp_path / "config-workspace")
    record = await service.create_workspace("Config Workspace", workspace_path, engine)

    workspace_id = await service.update_workspace_config(
        record.session_id,
        engine,
        git_remote_url="https://example.invalid/repo.git",
        git_username="engineer",
        workspace_prompt="Always explain assumptions.",
    )

    assert workspace_id == record.workspace_id
    hermes_text = (tmp_path / "config-workspace" / ".hermes.md").read_text(
        encoding="utf-8"
    )
    assert "Always explain assumptions." in hermes_text


@pytest.mark.asyncio
async def test_execute_workspace_file_uses_policy_and_returns_output(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Run Workspace", str(tmp_path / "run-workspace"), engine
    )
    script = tmp_path / "run-workspace" / "hello.py"
    script.write_text("print('hello from service')\n", encoding="utf-8")

    result = await service.execute_workspace_file(
        record.session_id, "/hello.py", engine
    )

    assert result.success is True
    assert result.stdout.strip() == "hello from service"


@pytest.mark.asyncio
async def test_execute_workspace_file_rejects_non_python(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Run Workspace", str(tmp_path / "run-workspace"), engine
    )
    (tmp_path / "run-workspace" / "notes.txt").write_text("hello", encoding="utf-8")

    with pytest.raises(WorkspaceInvalidRequestError):
        await service.execute_workspace_file(record.session_id, "/notes.txt", engine)


@pytest.mark.asyncio
async def test_resolve_workspace_uses_persisted_binding_when_agent_disagrees(
    tmp_path, db_path
):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Bound Workspace", str(tmp_path / "bound-workspace"), engine
    )
    engine.sessions[0] = AgentSessionInfo(
        session_id=record.session_id,
        title="Fake",
        created_at=1,
        updated_at=2,
        message_count=0,
        workspace=str(tmp_path / "agent-controlled-path"),
    )

    resolved = await service.resolve_workspace_dir(record.session_id, engine)

    assert resolved == record.local_path
    assert (
        service.repository.get_by_session(record.session_id)["local_path"]
        == record.local_path
    )


@pytest.mark.asyncio
async def test_execute_workspace_file_rejects_traversal(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Safe Workspace", str(tmp_path / "safe-workspace"), engine
    )
    (tmp_path / "outside.py").write_text("print('outside')\n", encoding="utf-8")

    with pytest.raises(WorkspaceInvalidRequestError, match="inside the workspace"):
        await service.execute_workspace_file(record.session_id, "../outside.py", engine)


@pytest.mark.asyncio
async def test_execute_workspace_file_uses_static_command_and_stdin_path(
    tmp_path, db_path, monkeypatch
):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Command Workspace", str(tmp_path / "command-workspace"), engine
    )
    script = tmp_path / "command-workspace" / "hello.py"
    script.write_text("print('hello')\n", encoding="utf-8")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="hello\n", stderr="")

    monkeypatch.setattr(service_module.subprocess, "run", fake_run)

    result = await service.execute_workspace_file(record.session_id, "hello.py", engine)

    assert result.success is True
    assert str(script.resolve()) not in captured["command"]
    assert captured["input"].strip() == str(script.resolve())
    assert captured["cwd"] == record.local_path


@pytest.mark.asyncio
async def test_execute_workspace_file_injects_only_display_handle_and_revokes_it(
    tmp_path, db_path, monkeypatch
):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Display Workspace", str(tmp_path / "display-workspace"), engine
    )
    script = tmp_path / "display-workspace" / "graph.py"
    script.write_text("import wright\n", encoding="utf-8")
    captured = {}

    def fake_run(_command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(service_module.subprocess, "run", fake_run)
    tokens = DisplayExecutionTokenService(secret=b"test-secret" * 4)
    result = await service.execute_workspace_file(
        record.session_id,
        "graph.py",
        engine,
        display_tokens=tokens,
        display_endpoint="http://127.0.0.1:8000/api/workspace/surfaces/displays",
        principal_id="user-1",
        trace_id="a" * 32,
    )

    assert result.success is True
    environment = captured["env"]
    injected = {
        key
        for key, value in environment.items()
        if value != os.environ.get(key) and key.startswith("WRIGHT_DISPLAY_")
    }
    assert injected == {
        "WRIGHT_DISPLAY_ENDPOINT",
        "WRIGHT_DISPLAY_TOKEN",
        "WRIGHT_DISPLAY_WORKSPACE_ID",
        "WRIGHT_DISPLAY_CONTRACT",
    }
    assert "PROMPT" not in environment
    assert "SCRIPT" not in environment
    with pytest.raises(DisplayTokenRejected, match="revoked"):
        tokens.validate(
            environment["WRIGHT_DISPLAY_TOKEN"],
            audience="wright-display-ingest-v1",
            workspace_id=record.workspace_id,
        )
