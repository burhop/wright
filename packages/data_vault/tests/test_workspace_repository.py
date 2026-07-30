from __future__ import annotations

from core.secrets import CredentialReference, CredentialStatus
from data_vault import WorkspaceRepository, upgrade_database


class MemorySecrets:
    def __init__(self) -> None:
        self.values: dict[CredentialReference, str] = {}

    def get(self, reference: CredentialReference) -> str | None:
        return self.values.get(reference)

    def set(self, reference: CredentialReference, value: str) -> None:
        self.values[reference] = value

    def delete(self, reference: CredentialReference) -> None:
        self.values.pop(reference, None)

    def status(self, reference: CredentialReference) -> CredentialStatus:
        return CredentialStatus(reference in self.values, "memory")


def test_workspace_repository_preserves_records_sessions_tools_and_secret_refs(
    tmp_path,
):
    db_path = str(tmp_path / "state.db")
    upgrade_database(db_path)
    secrets = MemorySecrets()
    repository = WorkspaceRepository(db_path, secrets=secrets)
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()

    repository.create(
        "ws-1",
        "session-1",
        str(workspace_path),
        workspace_name="Workspace",
        git_token="private-value",
    )
    repository.associate_session("ws-1", "session-2", title="Second", agent_id="hermes")
    repository.set_enabled_tools("ws-1", ["cad", "solver"])

    assert repository.get_by_id("ws-1")["git_token"] is None
    assert repository.get_by_session("session-2")["workspace_id"] == "ws-1"
    assert {item["session_id"] for item in repository.list_sessions("ws-1")} == {
        "session-1",
        "session-2",
    }
    assert repository.enabled_tools("ws-1") == ["cad", "solver"]
    assert repository.git_token("ws-1") == "private-value"


def test_workspace_repository_filters_synthetic_rows_and_updates_session(tmp_path):
    db_path = str(tmp_path / "state.db")
    upgrade_database(db_path)
    repository = WorkspaceRepository(db_path, secrets=MemorySecrets())
    real = tmp_path / "real"
    synthetic = tmp_path / "local-session-123"
    api_synthetic = tmp_path / "api_1782845491_1094a132"
    uuid_synthetic = tmp_path / "482f544c-a15b-4c51-aa80-c6a44b3298ce"
    hermes_synthetic = tmp_path / "20260719_194559_339f6f"
    generic_synthetic = tmp_path / "session-1"
    real.mkdir()
    synthetic.mkdir()
    api_synthetic.mkdir()
    uuid_synthetic.mkdir()
    hermes_synthetic.mkdir()
    generic_synthetic.mkdir()
    repository.create("real", "session-real", str(real), workspace_name="Real")
    repository.create(
        "synthetic",
        "local-session-123",
        str(synthetic),
        workspace_name="local-session-123",
    )
    repository.create(
        "api-synthetic",
        "api_1782845491_1094a132",
        str(api_synthetic),
        workspace_name="api_1782845491_1094a132",
    )
    repository.create(
        "uuid-synthetic",
        "482f544c-a15b-4c51-aa80-c6a44b3298ce",
        str(uuid_synthetic),
        workspace_name="482f544c-a15b-4c51-aa80-c6a44b3298ce",
    )
    repository.create(
        "hermes-synthetic",
        "20260719_194559_339f6f",
        str(hermes_synthetic),
        workspace_name="20260719_194559_339f6f",
    )
    repository.create(
        "generic-synthetic",
        "session-1",
        str(generic_synthetic),
        workspace_name="session-1",
    )

    assert [row["workspace_id"] for row in repository.list_all()] == ["real"]
    assert [row["workspace_id"] for row in repository.list_recent(limit=10)] == ["real"]
    repository.update_session("real", "session-next")
    assert repository.get_by_session("session-next")["workspace_id"] == "real"
