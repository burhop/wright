from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from core.engineering_scenarios import (
    AssertionCategory,
    AssertionResult,
    AssertionState,
    ScenarioState,
)
from data_vault import EngineeringScenarioRepository, MIGRATIONS, upgrade_database


DIGEST = "a" * 64


def _database(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'session', 'D:/workspace', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, started_at)
            VALUES ('workflow-run', 'workspace', 'session', 'workflow', 1, ?,
                    'graph', 'running', 1, 1)""",
            (DIGEST,),
        )
        connection.commit()
    return path


def _result(state=AssertionState.PASS):
    return AssertionResult(
        assertion_id="geometry-valid",
        plugin="geometry",
        plugin_version="1.0",
        state=state,
        category=AssertionCategory.GEOMETRY,
        reason_code="geometry_valid"
        if state == AssertionState.PASS
        else "geometry_invalid",
        artifact_digests=(DIGEST,),
        producer={"node_id": "node-cad", "capability": "cad__build"},
        message=None if state == AssertionState.PASS else "Geometry is invalid",
        recovery=None if state == AssertionState.PASS else "Inspect geometry",
    )


def test_migration_15_adds_scenario_report_tables(tmp_path) -> None:
    path = tmp_path / "migration.db"
    result = upgrade_database(path, migrations=MIGRATIONS[:14])
    assert result.ending_version == 14

    result = upgrade_database(path)

    assert result.applied == (
        {"version": 15, "name": "rivet_engineering_scenario_reports"},
    )
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {"engineering_scenario_runs", "engineering_scenario_assertions"} <= tables


def test_repository_finalizes_and_reloads_ordered_bounded_evidence(tmp_path) -> None:
    path = _database(tmp_path)
    repository = EngineeringScenarioRepository(str(path))
    now = datetime.now(UTC)
    repository.create_draft(
        scenario_run_id="scenario-run",
        workflow_run_id="workflow-run",
        workspace_id="workspace",
        session_id="session",
        scenario_id="structural-bracket",
        scenario_revision=1,
        manifest_digest=DIGEST,
        workflow_digest=DIGEST,
        binding_set_digest=None,
        identity={"scenario_id": "structural-bracket", "seed": 0},
        environment={"tier": "tier1", "network": False},
        created_at=now,
    )

    digest = repository.finalize(
        scenario_run_id="scenario-run",
        state=ScenarioState.PASSED,
        artifacts=({"artifact_id": "mesh", "content_digest": DIGEST},),
        assertions=(_result(),),
        cleanup_state="clean",
        residue={},
        finalized_at=now,
    )
    report = repository.get("scenario-run")

    assert report is not None
    assert report["state"] == "passed"
    assert report["report_digest"] == digest
    assert report["assertions"][0]["assertion_id"] == "geometry-valid"
    assert (
        repository.get_by_workflow_run("workflow-run")["scenario_run_id"]
        == "scenario-run"
    )


def test_terminal_report_is_immutable_but_idempotent(tmp_path) -> None:
    path = _database(tmp_path)
    repository = EngineeringScenarioRepository(str(path))
    now = datetime.now(UTC)
    repository.create_draft(
        scenario_run_id="scenario-run",
        workflow_run_id="workflow-run",
        workspace_id="workspace",
        session_id="session",
        scenario_id="structural-bracket",
        scenario_revision=1,
        manifest_digest=DIGEST,
        workflow_digest=DIGEST,
        binding_set_digest=None,
        identity={"scenario_id": "structural-bracket"},
        environment={},
        created_at=now,
    )
    arguments = dict(
        scenario_run_id="scenario-run",
        state=ScenarioState.PASSED,
        artifacts=(),
        assertions=(_result(),),
        cleanup_state="clean",
        residue={},
        finalized_at=now,
    )
    first = repository.finalize(**arguments)
    assert repository.finalize(**arguments) == first

    with pytest.raises(ValueError, match="immutable"):
        repository.finalize(
            **{
                **arguments,
                "state": ScenarioState.FAILED,
                "assertions": (_result(AssertionState.FAIL),),
            }
        )


def test_repository_rejects_secret_like_report_fields(tmp_path) -> None:
    repository = EngineeringScenarioRepository(str(_database(tmp_path)))
    with pytest.raises(ValueError, match="secret-like"):
        repository.create_draft(
            scenario_run_id="scenario-run",
            workflow_run_id="workflow-run",
            workspace_id="workspace",
            session_id="session",
            scenario_id="structural-bracket",
            scenario_revision=1,
            manifest_digest=DIGEST,
            workflow_digest=DIGEST,
            binding_set_digest=None,
            identity={"api_key": "forbidden"},
            environment={},
            created_at=datetime.now(UTC),
        )
