import json
import sqlite3
import pytest

from data_vault import (
    GatewayBindingError,
    GatewayRepository,
    database_status,
    upgrade_database,
)
from data_vault.secret_provider import FileSecretProvider
from data_vault.migrations import MIGRATIONS
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

    assert database_status(db_path).current_version == len(MIGRATIONS)


def _discovery_event(index=0):
    return dict(
        correlation_id=f"c{index}",
        session_id="s1",
        principal_id="p1",
        workspace_id="w1",
        operation="tool.list",
        reason_code="policy",
        outcome="listed" if index == 0 else "hidden",
        allowed=index == 0,
        target_name=f"tool-{index}",
        occurred_at=index + 1,
        metadata={"token": "private-value", "index": index},
    )


def test_discovery_batch_keeps_order_redaction_and_one_commit(tmp_path, monkeypatch):
    from data_vault import gateway_repository

    db_path, _ = _seed(tmp_path)
    original = gateway_repository.connect_state_db
    statements, connections = [], []

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        connections.append(connection)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(gateway_repository, "connect_state_db", connect)
    repository = GatewayRepository(db_path)
    identities = repository.record_audits([_discovery_event(0), _discovery_event(1)])
    assert len(connections) == 1
    assert statements.count("BEGIN IMMEDIATE") == 1
    assert statements.count("COMMIT") == 1
    rows = repository.list_audit("s1")
    assert [row["event_id"] for row in rows] == identities
    assert [row["allowed"] for row in rows] == [1, 0]
    assert [row["target_name"] for row in rows] == ["tool-0", "tool-1"]
    assert "private-value" not in json.dumps(rows)
    assert all(
        json.loads(row["metadata_json"])["token"] == "[REDACTED]" for row in rows
    )


@pytest.mark.parametrize(
    "failure", ["missing_field", "duplicate_id", "foreign_workspace"]
)
def test_discovery_batch_failure_never_leaves_partial_audit(tmp_path, failure):
    db_path, _ = _seed(tmp_path)
    repository = GatewayRepository(db_path)
    first, second = _discovery_event(0), _discovery_event(1)
    if failure == "missing_field":
        second.pop("principal_id")
    elif failure == "duplicate_id":
        first["event_id"] = second["event_id"] = "same-event"
    else:
        second["workspace_id"] = "missing"
    with pytest.raises((ValueError, sqlite3.IntegrityError)):
        repository.record_audits([first, second])
    assert repository.list_audit("s1") == []
