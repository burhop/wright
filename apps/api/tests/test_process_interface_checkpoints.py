"""Authenticated input response routes on a real declared source and durable run."""

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers import process_interfaces as routes
from api.routers.workspace import get_workspace_service
from packages.workspace_service.tests.test_process_input_supervision import (
    control,
    waiting_case,
)

PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture
def checkpoint_case(tmp_path, monkeypatch):
    holder = {}

    @asynccontextmanager
    async def lifespan(_):
        yield
        if holder:
            await holder["owner"].close()

    monkeypatch.setattr(app.router, "lifespan_context", lifespan)
    try:
        with TestClient(app) as client:
            owner, reference, receipt, cp, calls, generate = client.portal.call(
                waiting_case, tmp_path
            )
            holder["owner"] = owner
            workspace = owner.workspace
            workspace.lifecycle = SimpleNamespace(
                get_by_session=lambda key: (
                    {"workspace_id": "workspace", "local_path": str(tmp_path)}
                    if key == "owned-session"
                    else None
                )
            )
            app.dependency_overrides[get_workspace_service] = lambda: workspace
            monkeypatch.setattr(routes, "generate_workflow_response", generate)
            query = {
                "session_id": "owned-session",
                "path": reference.source_path,
                "expected_storage_digest": reference.source_digest,
            }
            yield SimpleNamespace(
                client=client,
                owner=owner,
                reference=reference,
                receipt=receipt,
                checkpoint=cp,
                calls=calls,
                query=query,
                root=tmp_path,
                generate=generate,
            )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)


def response_body(case, **changes):
    return {
        **case.query,
        "subject_digest": case.checkpoint.subject_digest,
        "value": {"selection": "b"},
        "request_id": "api-answer",
        **changes,
    }


def submit(case, **changes):
    return case.client.post(
        f"{PREFIX}/interactions/{case.checkpoint.checkpoint_id}/response",
        json=response_body(case, **changes),
    )


def test_route_projects_form_accepts_server_actor_and_resumes_exact_run(
    checkpoint_case,
):
    case = checkpoint_case
    attached = case.client.get(
        f"{PREFIX}/runs/{case.receipt.run_id}", params=case.query
    )
    assert attached.status_code == 200
    snapshot = attached.json()
    assert snapshot["state"] == "waiting_human"
    assert snapshot["interactions"][0]["response_schema"]["properties"]["selection"][
        "enum"
    ] == ["a", "b"]
    assert next(item for item in snapshot["actions"] if item["operation"] == "respond")[
        "enabled"
    ]
    result = submit(case)
    assert result.status_code == 202, result.text
    assert result.headers["cache-control"] == "no-store"
    response = result.json()
    assert response["actor"] == "local-control-plane"
    assert response["run_id"] == case.receipt.run_id
    assert not response["integration_test"]
    completed = case.client.portal.call(
        case.owner.runs.wait, control(), case.reference, case.receipt.run_id
    )
    assert completed["status"] == "completed"
    assert submit(case).json() == response
    assert len(case.calls) == 2
    assert (
        case.client.get(
            f"{PREFIX}/runs/{case.receipt.run_id}", params=case.query
        ).json()["state"]
        == "completed"
    )


@pytest.mark.parametrize("invalid_envelope", [False, True])
def test_undeclared_question_after_response_is_a_diagnostic_not_another_form(
    checkpoint_case, monkeypatch, invalid_envelope
):
    import json

    from agent_adapters.report_generation import generate_workflow_response
    from packages.agent_adapters.tests.test_workflow_unattended_outcomes import (
        model_transport,
        outcome,
    )

    case = checkpoint_case
    content = (
        "Which load should I use?"
        if invalid_envelope
        else json.dumps(
            outcome(
                "The allowable load is missing",
                status="blocked",
                reason="input_required",
            )
        )
    )
    requests = model_transport(monkeypatch, [{"content": content}])
    monkeypatch.setattr(
        routes, "generate_workflow_response", generate_workflow_response
    )
    accepted = submit(case)
    assert accepted.status_code == 202, accepted.text
    failed = case.client.portal.call(
        case.owner.runs.wait, control(), case.reference, case.receipt.run_id
    )
    expected = (
        "MODEL_OUTCOME_INVALID" if invalid_envelope else "INTERACTION_NOT_DECLARED"
    )
    assert failed["status"] == "failed" and failed["code"] == expected
    projected = case.client.get(
        f"{PREFIX}/runs/{case.receipt.run_id}", params=case.query
    )
    assert projected.status_code == 200, projected.text
    snapshot = projected.json()
    assert snapshot["diagnostics"][0]["code"] == expected
    assert snapshot["diagnostics"][0]["navigation"]["block_id"] == "second"
    assert not any(item["state"] == "waiting" for item in snapshot["interactions"])
    assert not any(
        item["enabled"] and item["operation"] == "respond"
        for item in snapshot["actions"]
    )
    assert snapshot["outputs"]
    assert len(requests) == 1
    # A failed claimed segment may have effects. Its saved answer remains, but
    # the existing consume authority requires reconciliation rather than replay.
    retry = submit(case)
    assert retry.status_code == 503
    assert retry.json()["error_code"] == "OUTCOME_UNKNOWN"
    assert len(requests) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"actor": "forged-reviewer"},
        {"integration_test": True},
        {"run_id": "other-run"},
        {"reason": "Override authority"},
        {"destination": "other-device"},
    ],
)
def test_public_body_cannot_supply_authority_or_run(checkpoint_case, changes):
    case = checkpoint_case
    assert submit(case, **changes).status_code == 422
    assert len(case.calls) == 1
    assert (
        case.owner.human_inputs.repository.get(case.checkpoint.checkpoint_id).state
        == "pending"
    )


@pytest.mark.parametrize(
    "changes,status,code",
    [
        ({"subject_digest": "0" * 64}, 409, "SUBJECT_STALE"),
        ({"value": {"selection": "c"}}, 422, "RESPONSE_INVALID"),
        ({"path": "workflows/other.workflow.wflow"}, 403, "SCOPE_DENIED"),
    ],
)
def test_route_rejects_stale_invalid_and_cross_process_answer(
    checkpoint_case, changes, status, code
):
    case = checkpoint_case
    result = submit(case, **changes)
    assert result.status_code == status, result.text
    assert result.json()["error_code"] == code
    assert len(case.calls) == 1
    assert (
        case.owner.human_inputs.repository.get(
            case.checkpoint.checkpoint_id
        ).continuation["response_id"]
        is None
    )


def test_changed_actual_artifact_returns_actionable_conflict(checkpoint_case):
    case = checkpoint_case
    (case.root / "first.txt").write_text("Revised upstream output", encoding="utf-8")
    result = submit(case)
    assert result.status_code == 409
    assert result.json()["error_code"] == "SUBJECT_STALE"
    assert result.json()["details"]["correction"]
    assert len(case.calls) == 1


def test_response_endpoint_denies_viewer_before_resolving_workspace():
    from fastapi import FastAPI, Request

    probe = FastAPI()
    probe.state.security_settings = SimpleNamespace(enforced=True)

    @probe.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal_role = "viewer"
        return await call_next(request)

    probe.dependency_overrides[get_workspace_service] = lambda: (_ for _ in ()).throw(
        AssertionError("Denied caller must not resolve a workspace")
    )
    probe.include_router(routes.router, prefix=PREFIX)
    with TestClient(probe) as client:
        result = client.post(
            f"{PREFIX}/interactions/checkpoint/response",
            json={
                "session_id": "session",
                "path": "workflows/test.workflow.wflow",
                "expected_storage_digest": "0" * 64,
                "subject_digest": "0" * 64,
                "value": {"selection": "b"},
                "request_id": "request",
            },
        )
    assert result.status_code == 403
