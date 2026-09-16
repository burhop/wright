import sqlite3

import pytest

from data_vault.workflow_integration_repository import WorkflowIntegrationRepository


def test_grants_are_immutable_and_revocation_preserves_history(tmp_path):
    path = str(tmp_path / "state.db")
    repository = WorkflowIntegrationRepository(path)
    identity = "a" * 64
    document = {"created_at": 1, "workspace_id": "workspace"}
    repository.enroll(identity, document)
    repository.enroll(identity, document)
    with pytest.raises(ValueError, match="conflict"):
        repository.enroll(identity, {**document, "workspace_id": "other"})
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("UPDATE workflow_integration_grants SET document='{}'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM workflow_integration_grants")
    repository.revoke(identity, 2)
    repository.revoke(identity, 3)
    assert repository.get(identity) == {"document": document, "revoked_at": 2}
