from __future__ import annotations

import socket
import sqlite3
from datetime import UTC, datetime

from data_vault import upgrade_database
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import SupportDiagnosticService


def _seed_program_state(database, workspace_path) -> None:
    upgrade_database(database)
    create_workspace(
        str(database),
        "workspace-offline",
        "session-offline",
        str(workspace_path),
        "Offline engineering",
    )
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """INSERT INTO catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version, issued_at,
                   expires_at, payload_sha256, payload_json, verification_state)
               VALUES ('catalog-offline', 'stable', 1, 1, 1, 2, ?, '{}', 'active')""",
            ("a" * 64,),
        )
        connection.execute(
            """INSERT INTO catalog_state(
                   state_id, active_snapshot_id, active_generation, updated_at,
                   updated_by)
               VALUES (1, 'catalog-offline', 1, 1, 'offline-test')"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs(
                   run_id, workspace_id, session_id, workflow_id, revision,
                   digest, graph, state, generation, started_at, completed_at)
               VALUES ('workflow-run-offline', 'workspace-offline',
                       'session-offline', 'workflow-offline', 1, ?, 'Main',
                       'succeeded', 1, 1, 2)""",
            ("b" * 64,),
        )
        connection.execute(
            """INSERT INTO engineering_scenario_runs(
                   scenario_run_id, workflow_run_id, workspace_id, session_id,
                   scenario_id, scenario_revision, manifest_digest,
                   workflow_digest, state, identity_json, artifacts_json,
                   environment_json, cleanup_state, residue_json, report_digest,
                   created_at, finalized_at)
               VALUES ('scenario-run-offline', 'workflow-run-offline',
                       'workspace-offline', 'session-offline',
                       'scenario-offline', 1, ?, ?, 'passed', '{}', '[]', '{}',
                       'clean', '{}', ?, 1, 2)""",
            ("c" * 64, "b" * 64, "d" * 64),
        )
        connection.execute(
            """INSERT INTO model_catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version,
                   catalog_digest, source_kind, trust_state, freshness,
                   metadata_json, created_at, activated_at)
               VALUES ('models-offline', 'stable', 1, '1.0', ?, 'bundled',
                       'bundled', 'cached', '{}', 1, 1)""",
            ("e" * 64,),
        )
        connection.execute(
            """INSERT INTO model_content_objects(
                   content_digest, size, state, storage_key, verification_json,
                   verified_at, updated_at)
               VALUES (?, 64, 'verified', 'objects/offline', '{}', 1, 1)""",
            ("f" * 64,),
        )
        connection.execute(
            """INSERT INTO model_installations(
                   installation_id, model_id, package_revision, variant_id,
                   manifest_digest, installation_digest, state,
                   runtime_adapter_id, runtime_adapter_version,
                   active_revision, installed_at, last_verified_at)
               VALUES ('model-install-offline', 'model-offline', 1, 'cpu', ?,
                       ?, 'ready', 'fixture-adapter', '1.0', 1, 1, 1)""",
            ("1" * 64, "2" * 64),
        )
        connection.execute(
            """INSERT INTO model_capability_bindings(
                   binding_id, workspace_id, installation_id, task_id,
                   tool_name, binding_digest, policy_snapshot_digest, state,
                   created_at, updated_at)
               VALUES ('model-binding-offline', 'workspace-offline',
                       'model-install-offline', 'screen', 'model__screen', ?, ?,
                       'enabled', 1, 1)""",
            ("3" * 64, "4" * 64),
        )


def test_cached_catalog_model_and_scenario_state_survives_restart_with_zero_network(
    tmp_path, monkeypatch
) -> None:
    database = tmp_path / "program.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _seed_program_state(database, workspace)
    network_calls: list[object] = []

    def refuse_network(*args, **kwargs):
        network_calls.append((args, kwargs))
        raise AssertionError("offline program path attempted network access")

    monkeypatch.setattr(socket, "create_connection", refuse_network)

    def clock() -> datetime:
        return datetime(2026, 8, 13, 12, tzinfo=UTC)

    first = SupportDiagnosticService(database, clock=clock)
    first_preview = first.preview(
        principal_id="engineer-offline",
        workspace_id="workspace-offline",
        scope={"session_id": "session-offline"},
    )
    first.invalidate_all()
    restarted = SupportDiagnosticService(database, clock=clock)
    restored = restarted.preview(
        principal_id="engineer-offline",
        workspace_id="workspace-offline",
        scope={"scenario_run_id": "scenario-run-offline"},
    )

    assert network_calls == []
    assert first_preview.snapshot.state_inventory.catalog_snapshot.state == "active"
    assert restored.snapshot.state_inventory.counts["scenario_reports"] == 1
    assert restored.snapshot.state_inventory.counts["model_packages"] == 1
    assert restored.snapshot.state_inventory.counts["model_bindings"] == 1
    assert restored.snapshot.state_inventory.counts["model_cache"] == 1
