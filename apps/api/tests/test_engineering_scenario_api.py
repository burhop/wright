from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from api.routers import workspace as workspace_router
from api.schemas.workspace import (
    EngineeringScenarioCancelRequest,
    EngineeringScenarioPreflightRequest,
    EngineeringScenarioStartRequest,
)
from core.engineering_scenarios import (
    EngineeringScenarioError,
    ResourceClass,
    ScenarioCatalogEntry,
    ScenarioTier,
)
from core.workflow_runs import WorkflowRun, WorkflowRunState
from workspace_service.engineering_scenario_service import (
    ScenarioBlocker,
    ScenarioPreflight,
)


ENTRY = ScenarioCatalogEntry(
    scenario_id="structural-bracket",
    revision=1,
    title="Structural bracket",
    summary="CAD, Python, and FEA",
    domains=("cad", "python", "fea"),
    tier=ScenarioTier.TIER1,
    resource_class=ResourceClass.SMALL,
    expected_duration_seconds=20,
    manifest_digest="a" * 64,
)


def _service(scenarios):
    async def resolve(*_args):
        return "C:/workspace"

    return SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace"} if session == "session" else None
            )
        ),
        resolve_workspace_dir=resolve,
        engineering_scenarios=scenarios,
        workflow_runner=SimpleNamespace(
            result=lambda _run_id: SimpleNamespace(
                digest="b" * 64,
                graph="graph-structural",
                output_summary=None,
                output_truncated=False,
            ),
            manifest=lambda _run_id: None,
        ),
    )


def _report(
    scenario_run_id: str = "scenario-run",
    *,
    workspace_id: str = "workspace",
    session_id: str = "session",
    report_digest: str = "e" * 64,
) -> dict:
    return {
        "scenario_run_id": scenario_run_id,
        "workflow_run_id": f"workflow-{scenario_run_id}",
        "workspace_id": workspace_id,
        "session_id": session_id,
        "scenario_id": ENTRY.scenario_id,
        "scenario_revision": 1,
        "manifest_digest": "a" * 64,
        "workflow_digest": "b" * 64,
        "binding_set_digest": "d" * 64,
        "state": "passed",
        "identity": {"seed": 0},
        "artifacts": [],
        "environment": {"tier": "tier1"},
        "cleanup_state": "clean",
        "residue": {},
        "assertions": [],
        "report_digest": report_digest,
    }


@pytest.mark.asyncio
async def test_list_and_detail_are_bounded_public_contracts(monkeypatch) -> None:
    monkeypatch.setattr(workspace_router, "_workflow_feature_enabled", lambda: None)

    class Scenarios:
        def list(self, **_kwargs):
            return (ENTRY,)

        def detail(self, scenario_id):
            assert scenario_id == ENTRY.scenario_id
            return SimpleNamespace(
                document={
                    "scenario_id": ENTRY.scenario_id,
                    "safety": {"physical_actuation": False},
                },
                digest=ENTRY.manifest_digest,
            )

    service = _service(Scenarios())
    listing = await workspace_router.list_engineering_scenarios_endpoint(
        [], None, service
    )
    detail = await workspace_router.engineering_scenario_detail_endpoint(
        ENTRY.scenario_id, service
    )

    assert listing.scenarios[0].domains == ["cad", "python", "fea"]
    assert listing.scenarios[0].tier == "tier1"
    assert detail.manifest["safety"]["physical_actuation"] is False
    assert "credential" not in detail.model_dump_json().lower()


@pytest.mark.asyncio
async def test_preflight_projects_exact_binding_and_recovery(monkeypatch) -> None:
    monkeypatch.setattr(workspace_router, "_workflow_feature_enabled", lambda: None)
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)

    class Scenarios:
        async def preflight(self, **kwargs):
            assert kwargs["workspace_id"] == "workspace"
            return ScenarioPreflight(
                preflight_id="preflight",
                scenario_id=ENTRY.scenario_id,
                scenario_revision=1,
                manifest_digest=ENTRY.manifest_digest,
                workflow_slug="scenario-structural-bracket",
                workflow_revision=1,
                workflow_digest="b" * 64,
                graph_id="graph-structural",
                binding_set_digest=None,
                state="blocked",
                capabilities=(
                    {
                        "node_id": "node-cad",
                        "requested_tool": "cad__build_bracket",
                        "selected_tool": None,
                        "binding_digest": None,
                        "blockers": ("binding_missing",),
                    },
                ),
                environment={"tier": "tier1", "physical_actuation": False},
                blockers=(
                    ScenarioBlocker(
                        "scenario_binding_missing",
                        "CAD capability is missing",
                        "Enable the CAD fixture MCP.",
                    ),
                ),
                expires_at=datetime.now(UTC) + timedelta(minutes=5),
            )

    response = await workspace_router.engineering_scenario_preflight_endpoint(
        ENTRY.scenario_id,
        EngineeringScenarioPreflightRequest(session_id="session"),
        object(),
        _service(Scenarios()),
    )

    assert response.state == "blocked"
    assert response.blockers[0].code == "scenario_binding_missing"
    assert response.blockers[0].recovery == "Enable the CAD fixture MCP."


@pytest.mark.asyncio
async def test_start_returns_linked_scenario_and_workflow_runs(monkeypatch) -> None:
    for name in (
        "_workflow_feature_enabled",
        "_runner_feature_enabled",
        "_operations_feature_enabled",
    ):
        monkeypatch.setattr(workspace_router, name, lambda: None)

    class Scenarios:
        async def start(self, **kwargs):
            assert kwargs["binding_set_digest"] == "d" * 64
            return "scenario-run", WorkflowRun(
                "workflow-run",
                "workspace",
                "session",
                "workflow",
                1,
                1,
                WorkflowRunState.RUNNING,
            )

    response = await workspace_router.start_engineering_scenario_endpoint(
        ENTRY.scenario_id,
        EngineeringScenarioStartRequest(
            session_id="session",
            manifest_digest="a" * 64,
            workflow_revision=1,
            workflow_digest="b" * 64,
            binding_set_digest="d" * 64,
        ),
        object(),
        _service(Scenarios()),
    )

    assert response.scenario_run_id == "scenario-run"
    assert response.workflow_run.run_id == "workflow-run"
    assert response.state == "running"


@pytest.mark.asyncio
async def test_report_scope_hides_cross_workspace_evidence(monkeypatch) -> None:
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)

    class Scenarios:
        def report(self, _scenario_run_id):
            return _report(workspace_id="another-workspace")

    with pytest.raises(Exception) as error:
        await workspace_router.engineering_scenario_report_endpoint(
            "scenario-run", "session", _service(Scenarios())
        )
    assert getattr(error.value, "status_code") == 404


@pytest.mark.asyncio
async def test_export_is_canonical_scoped_json_with_safe_headers(monkeypatch) -> None:
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)

    class Scenarios:
        def report(self, scenario_run_id):
            assert scenario_run_id == "scenario-run"
            return _report()

    response = await workspace_router.engineering_scenario_export_endpoint(
        "scenario-run", "session", _service(Scenarios())
    )

    assert response.media_type == "application/json"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"].endswith(
        'wright-engineering-scenario-scenario-run.json"'
    )
    assert b'"report_digest":"eeee' in response.body
    assert b"credential" not in response.body.lower()


@pytest.mark.asyncio
async def test_compare_requires_scope_and_projects_structured_differences(
    monkeypatch,
) -> None:
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)

    class Scenarios:
        def report(self, scenario_run_id):
            return _report(scenario_run_id)

        def compare(self, left, right):
            assert (left, right) == ("left", "right")
            return {
                "strictly_reproducible": False,
                "differences": [{"field": "identity.seed", "left": 0, "right": 1}],
                "assertion_changes": [
                    {
                        "assertion_id": "fea-converged",
                        "left": "passed",
                        "right": "failed",
                    }
                ],
            }

    response = await workspace_router.compare_engineering_scenario_runs_endpoint(
        "left", "right", "session", _service(Scenarios())
    )

    assert response.strictly_reproducible is False
    assert response.differences[0]["field"] == "identity.seed"
    assert response.assertion_changes[0]["right"] == "failed"


@pytest.mark.asyncio
async def test_cancel_is_scope_bound_and_returns_workflow_state(monkeypatch) -> None:
    for name in ("_runner_feature_enabled", "_operations_feature_enabled"):
        monkeypatch.setattr(workspace_router, name, lambda: None)

    class Scenarios:
        async def cancel(self, **kwargs):
            assert kwargs == {
                "workspace_id": "workspace",
                "session_id": "session",
                "scenario_run_id": "scenario-run",
            }
            return WorkflowRun(
                "workflow-run",
                "workspace",
                "session",
                "workflow",
                1,
                1,
                WorkflowRunState.CANCELLED,
                reason="user_cancelled",
            )

    response = await workspace_router.cancel_engineering_scenario_endpoint(
        "scenario-run",
        EngineeringScenarioCancelRequest(session_id="session"),
        _service(Scenarios()),
    )

    assert response.run_id == "workflow-run"
    assert response.state == "cancelled"
    assert response.reason == "user_cancelled"


@pytest.mark.asyncio
async def test_scenario_errors_keep_stable_code_and_status(monkeypatch) -> None:
    for name in (
        "_workflow_feature_enabled",
        "_runner_feature_enabled",
        "_operations_feature_enabled",
    ):
        monkeypatch.setattr(workspace_router, name, lambda: None)

    class Scenarios:
        async def start(self, **_kwargs):
            raise EngineeringScenarioError(
                "scenario_preflight_stale", "Review the updated preflight"
            )

    with pytest.raises(Exception) as error:
        await workspace_router.start_engineering_scenario_endpoint(
            ENTRY.scenario_id,
            EngineeringScenarioStartRequest(
                session_id="session",
                manifest_digest="a" * 64,
                workflow_revision=1,
                workflow_digest="b" * 64,
                binding_set_digest="d" * 64,
            ),
            object(),
            _service(Scenarios()),
        )

    assert getattr(error.value, "status_code") == 409
    assert getattr(error.value, "detail") == {
        "code": "scenario_preflight_stale",
        "message": "Review the updated preflight",
    }
