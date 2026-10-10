"""Instruction defaults share authenticated settings and optimistic concurrency."""

import copy
import sqlite3

import pytest

from api.main import app
from api.routers.settings import workflow_instruction_application
from workspace_service.workflow_instruction_settings import WorkflowInstructionSettings
from packages.workspace_service.tests.test_workflow_instruction_settings import profile


@pytest.fixture
def application(tmp_path):
    database = tmp_path / "defaults.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE system_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
    settings = WorkflowInstructionSettings(str(database), default_loader=profile)
    app.dependency_overrides[workflow_instruction_application] = lambda: settings
    try:
        yield settings
    finally:
        app.dependency_overrides.pop(workflow_instruction_application, None)


def test_defaults_update_revision_and_stale_edit_rejection(sync_client, application):
    first = sync_client.get("/api/settings/workflow-instructions")
    assert first.status_code == 200
    initial = first.json()
    changed = profile("New default B").model_dump(mode="json")
    payload = {"instructions": changed, "expected_revision": initial["revision"]}
    saved = sync_client.put("/api/settings/workflow-instructions", json=payload)
    assert saved.status_code == 200
    assert saved.json()["instructions"] == changed
    assert saved.json()["digest"] != initial["digest"]
    stale = sync_client.put("/api/settings/workflow-instructions", json=payload)
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "workflow_instructions_conflict"
    assert sync_client.get("/api/settings/workflow-instructions").json() == saved.json()


def test_invalid_body_digest_and_unknown_authority_cannot_be_saved(
    sync_client, application
):
    initial = application.read()
    changed = copy.deepcopy(initial["instructions"])
    changed["assets"][0]["body"] = "Changed without updating identity"
    result = sync_client.put(
        "/api/settings/workflow-instructions",
        json={"instructions": changed, "expected_revision": initial["revision"]},
    )
    assert result.status_code == 422
    assert application.read() == initial
    result = sync_client.put(
        "/api/settings/workflow-instructions",
        json={
            "instructions": initial["instructions"],
            "expected_revision": initial["revision"],
            "execution_approved": True,
        },
    )
    assert result.status_code == 422
    assert application.read() == initial


def test_upgrade_proposal_preserves_global_or_workflow_customization_and_requires_explicit_cas_apply(
    sync_client, application
):
    before = application.read()
    proposal_response = sync_client.post(
        "/api/settings/workflow-instructions/action-intent-upgrade", json={}
    )
    assert proposal_response.status_code == 200
    proposal = proposal_response.json()
    assert proposal["available"] is True
    assert proposal["current_revision"] == before["revision"]
    assert (
        proposal["instructions"]["assets"][: len(before["instructions"]["assets"])]
        == before["instructions"]["assets"]
    )
    assert application.read() == before
    custom = profile("A separate workflow's embedded instructions.").model_dump(
        mode="json"
    )
    workflow = sync_client.post(
        "/api/settings/workflow-instructions/action-intent-upgrade",
        json={"instructions": custom},
    )
    assert workflow.status_code == 200
    assert workflow.json()["scope"] == "workflow"
    assert workflow.json()["current_revision"] is None
    assert workflow.json()["instructions"]["assets"][0] == custom["assets"][0]
    assert application.read() == before
    applied = sync_client.put(
        "/api/settings/workflow-instructions",
        json={
            "instructions": proposal["instructions"],
            "expected_revision": proposal["current_revision"],
        },
    )
    assert applied.status_code == 200
    assert applied.json()["digest"] == proposal["proposed_digest"]
    repeated = sync_client.post(
        "/api/settings/workflow-instructions/action-intent-upgrade", json={}
    )
    assert repeated.status_code == 200 and repeated.json()["available"] is False


def test_upgrade_proposal_rejects_tampering_or_browser_authority_without_writing(
    sync_client, application
):
    before = application.read()
    tampered = copy.deepcopy(before["instructions"])
    tampered["assets"][0]["body"] = "Tampered body"
    for payload in ({"instructions": tampered}, {"execution_approved": True}):
        response = sync_client.post(
            "/api/settings/workflow-instructions/action-intent-upgrade", json=payload
        )
        assert response.status_code == 422
        assert "Tampered body" not in response.text
        assert application.read() == before
