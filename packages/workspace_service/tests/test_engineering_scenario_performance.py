from __future__ import annotations

import sqlite3
import time
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from core.engineering_scenarios import (
    AssertionCategory,
    AssertionResult,
    AssertionState,
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
    validate_manifest,
)
from workspace_service.engineering_scenario_service import EngineeringScenarioService


DIGEST = "a" * 64


def _database(tmp_path):
    path = tmp_path / "scenario-performance.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'session', 'D:/workspace', 1, 1)"""
        )
        connection.commit()
    WorkflowRunRepository(str(path)).create(
        WorkflowRunRecord(
            run_id="workflow-run",
            workspace_id="workspace",
            session_id="session",
            workflow_id="workflow",
            revision=1,
            digest=DIGEST,
            graph="Main",
            state="succeeded",
            generation=1,
            started_at=1,
            completed_at=2,
            reason_code=None,
            output_summary=None,
            output_truncated=False,
        )
    )
    return path


def test_catalog_listing_and_manifest_validation_meet_interaction_budgets() -> None:
    catalog = EngineeringScenarioCatalog()
    started = time.perf_counter()
    for _ in range(100):
        assert catalog.list()
    listing_seconds = time.perf_counter() - started

    document = catalog.get("structural-bracket").document
    started = time.perf_counter()
    validate_manifest(document)
    validation_seconds = time.perf_counter() - started

    assert listing_seconds < 0.3
    assert validation_seconds < 0.5


def test_loading_one_thousand_assertions_stays_below_one_second(tmp_path) -> None:
    path = _database(tmp_path)
    repository = EngineeringScenarioRepository(str(path))
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
        identity={"seed": 0},
        environment={"tier": "tier1"},
        created_at=datetime.now(UTC),
    )
    assertions = tuple(
        AssertionResult(
            assertion_id=f"assertion-{index}",
            plugin="numeric",
            plugin_version="1.0",
            state=AssertionState.PASS,
            category=AssertionCategory.NUMERIC,
            reason_code="range_satisfied",
            artifact_digests=(DIGEST,),
            producer={"node_id": "node-python", "capability": "python__check"},
        )
        for index in range(1_000)
    )
    repository.finalize(
        scenario_run_id="scenario-run",
        state=ScenarioState.PASSED,
        artifacts=(),
        assertions=assertions,
        cleanup_state="clean",
        residue={},
        finalized_at=datetime.now(UTC),
    )

    started = time.perf_counter()
    report = repository.get("scenario-run")
    elapsed = time.perf_counter() - started

    assert report is not None and len(report["assertions"]) == 1_000
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_scenario_cancellation_is_delivered_within_one_second(tmp_path) -> None:
    path = _database(tmp_path)
    repository = EngineeringScenarioRepository(str(path))
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
        identity={"seed": 0},
        environment={"tier": "tier1"},
        created_at=datetime.now(UTC),
    )

    class Operations:
        def run(self, **_kwargs):
            return SimpleNamespace(run_id="workflow-run", generation=1)

        async def cancel(self, **kwargs):
            return SimpleNamespace(**kwargs, state="cancelled")

    service = EngineeringScenarioService(str(path), operations=Operations())
    started = time.perf_counter()
    result = await service.cancel(
        workspace_id="workspace",
        session_id="session",
        scenario_run_id="scenario-run",
    )
    elapsed = time.perf_counter() - started

    assert result.state == "cancelled"
    assert elapsed < 1.0


def test_all_tier1_cleanup_deadlines_are_bounded_to_five_seconds() -> None:
    catalog = EngineeringScenarioCatalog()
    assert all(
        catalog.get(entry.scenario_id).document["cleanup"]["timeout_seconds"] <= 5
        for entry in catalog.list(tier="tier1")
    )
