from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from core.workflow_runs import WorkflowRun, WorkflowRunState
from data_vault import WorkflowRunRecord, WorkflowRunRepository, upgrade_database
from workspace_service.engineering_scenario_service import EngineeringScenarioService
from workspace_service.rivet_validation import extract_rivet_mcp_requirements


class FakeOperations:
    def __init__(self, db_path: str) -> None:
        self.repository = WorkflowRunRepository(db_path)
        self.last_preview = None

    async def preview_mcp_bindings(self, **kwargs):
        self.last_preview = kwargs
        nodes = tuple(
            SimpleNamespace(
                requirement=SimpleNamespace(
                    node_id=node_id, static_tool_name=tool_name
                ),
                selected_tool=tool_name,
                binding=SimpleNamespace(binding_digest=(str(index) * 64)[:64]),
                blockers=(),
            )
            for index, (node_id, tool_name) in enumerate(
                sorted(kwargs["selections"].items()), 1
            )
        )
        return SimpleNamespace(
            nodes=nodes,
            binding_set=SimpleNamespace(binding_set_digest="b" * 64),
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )

    async def start(self, **kwargs):
        run = WorkflowRun(
            run_id="workflow-run",
            workspace_id=kwargs["workspace_id"],
            session_id=kwargs["session_id"],
            workflow_id="workflow",
            revision=kwargs["expected_revision"],
            generation=1,
            state=WorkflowRunState.RUNNING,
        )
        self.repository.create(
            WorkflowRunRecord(
                run_id=run.run_id,
                workspace_id=run.workspace_id,
                session_id=run.session_id,
                workflow_id=run.workflow_id,
                revision=run.revision,
                digest=kwargs["expected_digest"],
                graph=kwargs["graph"],
                state="running",
                generation=run.generation,
                started_at=1,
                completed_at=None,
                reason_code=None,
                output_summary=None,
                output_truncated=False,
            )
        )
        return run


def _service(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'session', ?, 1, 1)""",
            (str(tmp_path / "workspace"),),
        )
        connection.commit()
    operations = FakeOperations(str(database))
    return EngineeringScenarioService(str(database), operations=operations), operations


def test_prepare_materializes_static_gateway_only_rivet_graphs(tmp_path) -> None:
    service, _operations = _service(tmp_path)
    workspace = tmp_path / "workspace"

    document = service.prepare(
        workspace_dir=str(workspace), scenario_id="structural-bracket"
    )
    requirements = extract_rivet_mcp_requirements(document.project)

    assert document.slug == "scenario-structural-bracket"
    assert {value.static_tool_name for value in requirements.nodes} == {
        "cad__build_bracket",
        "python__mass_properties",
        "fea__solve_static",
    }
    assert "serverUrl" not in document.project
    assert "command:" not in document.project


@pytest.mark.asyncio
async def test_preflight_selects_exact_manifest_tools_and_is_ready(tmp_path) -> None:
    service, operations = _service(tmp_path)

    preflight = await service.preflight(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path / "workspace"),
        scenario_id="electronics-enclosure-cooling",
        platform_tag="windows-amd64",
    )

    assert preflight.state == "ready"
    assert preflight.binding_set_digest == "b" * 64
    assert set(operations.last_preview["selections"].values()) == {
        "ecad__board_envelope",
        "cad__build_enclosure",
        "cfd__solve_thermal",
        "python__thermal_margin",
    }
    assert preflight.environment["physical_actuation"] is False


@pytest.mark.asyncio
async def test_started_scenario_finalizes_deterministic_engineering_report(
    tmp_path,
) -> None:
    service, _operations = _service(tmp_path)
    preflight = await service.preflight(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path / "workspace"),
        scenario_id="parametric-manufacturing",
        platform_tag="windows-amd64",
    )

    scenario_run_id, run = await service.start(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path / "workspace"),
        scenario_id=preflight.scenario_id,
        manifest_digest=preflight.manifest_digest,
        workflow_revision=preflight.workflow_revision,
        workflow_digest=preflight.workflow_digest,
        review_digest="c" * 64,
        binding_set_digest=preflight.binding_set_digest,
    )
    report = service.finalize_with_fixture_evidence(scenario_run_id)

    assert run.run_id == "workflow-run"
    assert report["state"] == "passed"
    assert len(report["artifacts"]) == 5
    assert all(value["state"] == "pass" for value in report["assertions"])
    assert report["cleanup_state"] == "clean"


@pytest.mark.asyncio
async def test_stale_manifest_is_blocked_before_workflow_start(tmp_path) -> None:
    service, _operations = _service(tmp_path)
    preflight = await service.preflight(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path / "workspace"),
        scenario_id="structural-bracket",
        platform_tag="windows-amd64",
    )

    with pytest.raises(ValueError) as error:
        await service.start(
            workspace_id="workspace",
            session_id="session",
            workspace_dir=str(tmp_path / "workspace"),
            scenario_id=preflight.scenario_id,
            manifest_digest="0" * 64,
            workflow_revision=preflight.workflow_revision,
            workflow_digest=preflight.workflow_digest,
            review_digest="c" * 64,
            binding_set_digest=preflight.binding_set_digest,
        )
    assert getattr(error.value, "code") == "scenario_preflight_stale"
