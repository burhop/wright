import json
import pytest

from data_vault import (
    GatewayBindingError,
    GatewayRepository,
    database_status,
    upgrade_database,
)
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository


def _seed(tmp_path):
    db_path = str(tmp_path / "state.db")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(db_path)
    WorkspaceRepository(
        db_path, secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create("w1", "s1", str(workspace), workspace_name="One")
    return db_path, workspace


def test_gateway_binding_requires_exact_existing_session_workspace(tmp_path) -> None:
    db_path, workspace = _seed(tmp_path)
    repository = GatewayRepository(db_path)

    binding = repository.resolve_binding(
        session_id="s1", principal_id="p1", workspace_id="w1"
    )
    assert binding == {
        "session_id": "s1",
        "principal_id": "p1",
        "workspace_id": "w1",
        "workspace_path": str(workspace),
    }

    with pytest.raises(GatewayBindingError, match="not bound"):
        repository.resolve_binding(
            session_id="s1", principal_id="p1", workspace_id="foreign"
        )
    with pytest.raises(GatewayBindingError, match="principal_id"):
        repository.resolve_binding(session_id="s1", principal_id="", workspace_id="w1")


def test_gateway_audit_is_append_only_scoped_and_redacted(tmp_path) -> None:
    db_path, _ = _seed(tmp_path)
    repository = GatewayRepository(db_path)
    event = {
        "correlation_id": "c1",
        "request_id": "r1",
        "session_id": "s1",
        "principal_id": "p1",
        "workspace_id": "w1",
        "operation": "tool.call",
        "server_id": "cad",
        "target_name": "draw",
        "allowed": True,
        "reason_code": "allowed",
        "outcome": "succeeded",
        "duration_ms": 4,
        "metadata": {"token": "secret-value", "shape": "cube"},
    }
    first = repository.record_audit(event)
    second = repository.record_audit({**event, "request_id": "r2"})

    rows = repository.list_audit("s1")
    assert [row["event_id"] for row in rows] == [first, second]
    assert "secret-value" not in rows[0]["metadata_json"]
    assert json.loads(rows[0]["metadata_json"])["token"] == "[REDACTED]"
    assert repository.list_audit("foreign") == []

    assert database_status(db_path).current_version == 4
