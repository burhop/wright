from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from data_vault import upgrade_database
from workspace_service.adapters.runtime import create_workspace
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
)
from workspace_service.support_diagnostic_service import SupportDiagnosticService


def test_representative_catalog_journeys_are_local_static_and_provider_explicit() -> (
    None
):
    catalog = EngineeringScenarioCatalog()
    mcp_only = catalog.get("structural-bracket")
    mixed = catalog.get("chatter-candidate-review")

    for manifest in (mcp_only, mixed):
        environment = manifest.document["environment"]
        assert not any(
            environment[name]
            for name in (
                "network",
                "credentials",
                "proprietary_application",
                "gpu",
                "hardware",
                "large_download",
            )
        )
        assert manifest.document["safety"] == {
            **manifest.document["safety"],
            "physical_actuation": False,
            "static_outputs_only": True,
        }
        assert manifest.document["cleanup"]["timeout_seconds"] <= 5
        assert fixture_documents(manifest.scenario_id, run_id="program-system-test")

    assert {
        item.get("provider_kind", "mcp") for item in mcp_only.document["capabilities"]
    } == {"mcp"}
    assert {
        item.get("provider_kind", "mcp") for item in mixed.document["capabilities"]
    } == {"mcp", "engineering_model"}


def test_provider_failure_projects_stable_attribution_cleanup_and_recovery(
    tmp_path,
) -> None:
    database = tmp_path / "program.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(database)
    create_workspace(
        str(database), "workspace-1", "session-1", str(workspace), "Program"
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO workspace_workflow_runs(
                   run_id, workspace_id, session_id, workflow_id, revision,
                   digest, graph, state, generation, started_at, completed_at,
                   reason_code)
               VALUES ('workflow-failed', 'workspace-1', 'session-1',
                       'workflow-1', 1, ?, 'Main', 'failed', 1, 1, 2,
                       'provider_failed')""",
            ("a" * 64,),
        )
        connection.execute(
            """INSERT INTO engineering_scenario_runs(
                   scenario_run_id, workflow_run_id, workspace_id, session_id,
                   scenario_id, scenario_revision, manifest_digest,
                   workflow_digest, state, identity_json, artifacts_json,
                   environment_json, cleanup_state, residue_json, created_at,
                   finalized_at)
               VALUES ('scenario-failed', 'workflow-failed', 'workspace-1',
                       'session-1', 'structural-bracket', 1, ?, ?, 'failed',
                       '{}', '[]', '{}', 'residue', '{}', 1, 2)""",
            ("b" * 64, "a" * 64),
        )
    tokens = iter(["snapshot_12345678", "confirmation-token"])
    service = SupportDiagnosticService(
        database,
        clock=lambda: datetime(2026, 8, 13, 12, tzinfo=UTC),
        token_factory=lambda _bytes: next(tokens),
        principal_digest_key=b"program-system-test-key",
    )
    preview = service.preview(
        principal_id="engineer-1",
        workspace_id="workspace-1",
        scope={"scenario_run_id": "scenario-failed"},
    )

    assert preview.snapshot.summary.status == "degraded"
    assert preview.snapshot.summary.next_action == "INSPECT_RECOVERY"
    assert [
        failure.model_dump(mode="json") for failure in preview.snapshot.failures
    ] == [
        {
            "stage": "engineering-scenario",
            "provider_kind": "rivet",
            "reason": "SCENARIO_FAILED",
            "cleanup": "residue-possible",
            "recovery": "INSPECT_BEFORE_RETRY",
        }
    ]
    exported = service.export(
        principal_id="engineer-1",
        workspace_id="workspace-1",
        snapshot_digest=preview.snapshot.snapshot_digest,
        confirmation_token=preview.confirmation_token,
    )
    assert b"provider_failed" not in exported.content
    assert b"INSPECT_BEFORE_RETRY" in exported.content
