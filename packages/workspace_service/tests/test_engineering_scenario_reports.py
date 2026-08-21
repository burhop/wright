from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

import pytest

from core.engineering_scenarios import (
    AssertionCategory,
    AssertionResult,
    AssertionState,
    EngineeringScenarioError,
    ScenarioState,
)
from data_vault import (
    EngineeringScenarioRepository,
    WorkflowRunRecord,
    WorkflowRunRepository,
    upgrade_database,
)
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
)
from workspace_service.engineering_scenario_service import (
    EngineeringScenarioService,
    canonical_assertion_digest,
)


DIGEST = "a" * 64


def _database(tmp_path):
    path = tmp_path / "scenario-reports.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'session', 'D:/workspace', 1, 1)"""
        )
        connection.commit()
    return path


def _workflow(path, run_id, *, state="succeeded", output=None, reason=None):
    WorkflowRunRepository(str(path)).create(
        WorkflowRunRecord(
            run_id=run_id,
            workspace_id="workspace",
            session_id="session",
            workflow_id=f"workflow-{run_id}",
            revision=1,
            digest=DIGEST,
            graph="graph-structural",
            state=state,
            generation=1,
            started_at=1,
            completed_at=2 if state in {"succeeded", "failed", "cancelled"} else None,
            reason_code=reason,
            output_summary=output,
            output_truncated=False,
        )
    )


def _assertion(state: AssertionState) -> AssertionResult:
    return AssertionResult(
        assertion_id="stress-limit",
        plugin="fea",
        plugin_version="1.0",
        state=state,
        category=AssertionCategory.CONVERGENCE,
        reason_code="stress_within_limit"
        if state == AssertionState.PASS
        else "range_exceeded",
        artifact_digests=(DIGEST,),
        producer={"node_id": "node-fea", "capability": "fea__solve_static"},
        expected={"maximum": 150, "unit": "MPa"},
        observed={"value": 135 if state == AssertionState.PASS else 175, "unit": "MPa"},
        message=None
        if state == AssertionState.PASS
        else "Peak stress exceeded the limit",
        recovery=None
        if state == AssertionState.PASS
        else "Inspect loads and constraints",
    )


def _finalized_report(path, run_id, *, seed, assertion_state):
    _workflow(path, f"workflow-{run_id}")
    catalog = EngineeringScenarioCatalog()
    manifest = catalog.get("structural-bracket")
    repository = EngineeringScenarioRepository(str(path))
    repository.create_draft(
        scenario_run_id=run_id,
        workflow_run_id=f"workflow-{run_id}",
        workspace_id="workspace",
        session_id="session",
        scenario_id=manifest.scenario_id,
        scenario_revision=int(manifest.document["revision"]),
        manifest_digest=manifest.digest,
        workflow_digest=DIGEST,
        binding_set_digest="b" * 64,
        identity={
            "seed": seed,
            "graph_id": "graph-structural",
            "assertion_set_digest": canonical_assertion_digest(manifest),
        },
        environment={"tier": "tier1", "platform": "test"},
        created_at=datetime.now(UTC),
    )
    repository.finalize(
        scenario_run_id=run_id,
        state=(
            ScenarioState.PASSED
            if assertion_state == AssertionState.PASS
            else ScenarioState.FAILED
        ),
        artifacts=({"artifact_id": "fea-result", "content_digest": DIGEST},),
        assertions=(_assertion(assertion_state),),
        cleanup_state="clean",
        residue={},
        finalized_at=datetime.now(UTC),
    )


def test_reports_survive_restart_export_safely_and_compare_material_changes(
    tmp_path,
) -> None:
    path = _database(tmp_path)
    _finalized_report(
        path, "scenario-left", seed=0, assertion_state=AssertionState.PASS
    )
    _finalized_report(
        path, "scenario-right", seed=1, assertion_state=AssertionState.FAIL
    )

    restarted = EngineeringScenarioService(str(path), operations=object())
    left = restarted.report("scenario-left")
    comparison = restarted.compare("scenario-left", "scenario-right")

    assert left is not None and left["state"] == "passed"
    assert json.loads(json.dumps(left))["report_digest"] == left["report_digest"]
    assert "credential" not in json.dumps(left).lower()
    assert comparison["strictly_reproducible"] is False
    assert {item["field"] for item in comparison["differences"]} == {"seed"}
    change = comparison["assertion_changes"][0]
    assert change["assertion_id"] == "stress-limit"
    assert change["left_state"] == "pass"
    assert change["right_state"] == "fail"
    assert change["left_digest"] != change["right_digest"]


def test_restart_rebuild_rejects_changed_manifest_identity(tmp_path) -> None:
    path = _database(tmp_path)
    claims = fixture_documents("structural-bracket", run_id="workflow-rebuild")
    _workflow(path, "workflow-rebuild", output={"artifacts": claims})
    manifest = EngineeringScenarioCatalog().get("structural-bracket")
    EngineeringScenarioRepository(str(path)).create_draft(
        scenario_run_id="scenario-rebuild",
        workflow_run_id="workflow-rebuild",
        workspace_id="workspace",
        session_id="session",
        scenario_id=manifest.scenario_id,
        scenario_revision=int(manifest.document["revision"]),
        manifest_digest="0" * 64,
        workflow_digest=DIGEST,
        binding_set_digest="b" * 64,
        identity={
            "seed": 0,
            "graph_id": "graph-structural",
            "assertion_set_digest": canonical_assertion_digest(manifest),
        },
        environment={"tier": "tier1", "platform": "test"},
        created_at=datetime.now(UTC),
    )

    with pytest.raises(EngineeringScenarioError) as error:
        EngineeringScenarioService(str(path), operations=object()).report(
            "scenario-rebuild"
        )
    assert error.value.code == "scenario_rebuild_identity_mismatch"


@pytest.mark.parametrize(
    ("state", "reason", "category"),
    [
        ("failed", "RIVET_CALL_APPROVAL_DENIED", "policy"),
        ("failed", "RIVET_MCP_PANEL_UNAVAILABLE", "transport"),
        ("failed", "MCP_TOOL_FAILED", "tool"),
        ("failed", "RUN_TIMEOUT", "timeout"),
        ("cancelled", "RIVET_MCP_CANCELLED", "cleanup"),
    ],
)
def test_terminal_workflow_failures_retain_stable_categories(
    tmp_path, state, reason, category
) -> None:
    path = _database(tmp_path)
    _workflow(path, "workflow-failure", state=state, reason=reason)
    manifest = EngineeringScenarioCatalog().get("structural-bracket")
    EngineeringScenarioRepository(str(path)).create_draft(
        scenario_run_id="scenario-failure",
        workflow_run_id="workflow-failure",
        workspace_id="workspace",
        session_id="session",
        scenario_id=manifest.scenario_id,
        scenario_revision=int(manifest.document["revision"]),
        manifest_digest=manifest.digest,
        workflow_digest=DIGEST,
        binding_set_digest="b" * 64,
        identity={
            "seed": 0,
            "graph_id": "graph-structural",
            "assertion_set_digest": canonical_assertion_digest(manifest),
        },
        environment={"tier": "tier1", "platform": "test"},
        created_at=datetime.now(UTC),
    )

    report = EngineeringScenarioService(str(path), operations=object()).report(
        "scenario-failure"
    )

    assert report is not None
    assert report["state"] == ("cancelled" if state == "cancelled" else "failed")
    assert report["assertions"][0]["category"] == category
    assert report["assertions"][0]["reason_code"] == reason.lower()
    assert report["assertions"][0]["recovery"]
