from __future__ import annotations

import sqlite3
import pytest

from data_vault import database_status, upgrade_database
from workspace_service import WorkspaceService
from workspace_service.adapters.runtime import create_workspace


PROGRAM_TABLES = (
    "catalog_snapshots",
    "catalog_state",
    "engineering_workspaces",
    "workspace_workflow_runs",
    "engineering_scenario_runs",
    "model_catalog_snapshots",
    "model_content_objects",
)


def _counts(database: str) -> dict[str, int]:
    with sqlite3.connect(database) as connection:
        return {
            table: int(
                connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            )
            for table in PROGRAM_TABLES
        }


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


@pytest.mark.asyncio
async def test_complete_program_state_opens_without_catalog_model_or_rivet_rewrite(
    tmp_path,
):
    db_path = str(tmp_path / "program-state.db")
    upgrade_database(db_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    create_workspace(
        db_path, "ws-program", "session-program", str(workspace), "Program"
    )
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """INSERT INTO catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version, issued_at,
                   expires_at, payload_sha256, payload_json, verification_state)
               VALUES ('catalog-program', 'stable', 1, 1, 1, 2, ?, '{}', 'active')""",
            ("a" * 64,),
        )
        connection.execute(
            """INSERT INTO catalog_state(
                   state_id, active_snapshot_id, active_generation, updated_at,
                   updated_by)
               VALUES (1, 'catalog-program', 1, 1, 'compatibility-test')"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs(
                   run_id, workspace_id, session_id, workflow_id, revision,
                   digest, graph, state, generation, started_at, completed_at)
               VALUES ('workflow-run-program', 'ws-program', 'session-program',
                       'workflow-program', 1, ?, 'Main', 'succeeded', 1, 1, 2)""",
            ("b" * 64,),
        )
        connection.execute(
            """INSERT INTO engineering_scenario_runs(
                   scenario_run_id, workflow_run_id, workspace_id, session_id,
                   scenario_id, scenario_revision, manifest_digest,
                   workflow_digest, state, identity_json, artifacts_json,
                   environment_json, cleanup_state, residue_json, report_digest,
                   created_at, finalized_at)
               VALUES ('scenario-run-program', 'workflow-run-program',
                       'ws-program', 'session-program', 'scenario-program', 1,
                       ?, ?, 'passed', '{}', '[]', '{}', 'clean', '{}', ?, 1, 2)""",
            ("c" * 64, "b" * 64, "d" * 64),
        )
        connection.execute(
            """INSERT INTO model_catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version,
                   catalog_digest, source_kind, trust_state, freshness,
                   metadata_json, created_at, activated_at)
               VALUES ('models-program', 'stable', 1, '1.0', ?, 'bundled',
                       'bundled', 'cached', '{}', 1, 1)""",
            ("e" * 64,),
        )
        connection.execute(
            """INSERT INTO model_content_objects(
                   content_digest, size, state, storage_key, verification_json,
                   verified_at, updated_at)
               VALUES (?, 64, 'verified', 'objects/program', '{}', 1, 1)""",
            ("f" * 64,),
        )
    before = _counts(db_path)
    before_status = database_status(db_path)

    service = WorkspaceService(db_path)
    assert service.lifecycle.get_by_id("ws-program")["workspace_name"] == "Program"
    await service.close()

    assert _counts(db_path) == before
    assert database_status(db_path).current_version == before_status.current_version
