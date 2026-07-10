from __future__ import annotations

import sqlite3
import pytest

from data_vault import database_status, upgrade_database
from workspace_service import WorkspaceService
from workspace_service.adapters.runtime import create_workspace


@pytest.mark.asyncio
async def test_feature_044_state_opens_without_schema_or_workspace_conversion(tmp_path):
    db_path = str(tmp_path / "state.db")
    upgrade_database(db_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    create_workspace(db_path, "ws-1", "session-1", str(workspace), "Existing")
    before = database_status(db_path)
    with sqlite3.connect(db_path) as connection:
        schema_before = connection.execute("PRAGMA schema_version").fetchone()[0]

    service = WorkspaceService(db_path)
    assert service.lifecycle.get_by_id("ws-1")["local_path"] == str(workspace)

    after = database_status(db_path)
    with sqlite3.connect(db_path) as connection:
        schema_after = connection.execute("PRAGMA schema_version").fetchone()[0]
    assert before.current_version == after.current_version
    assert schema_before == schema_after
    await service.close()
