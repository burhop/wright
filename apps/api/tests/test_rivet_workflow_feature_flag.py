from api.config import (
    rivet_editor_enabled,
    rivet_runner_enabled,
    rivet_workflows_enabled,
)
from api.main import app
from fastapi.testclient import TestClient


def test_rivet_workflow_feature_defaults_off(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_WORKFLOWS_ENABLED", raising=False)
    assert not rivet_workflows_enabled()


def test_rivet_workflow_feature_can_be_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("WRIGHT_RIVET_WORKFLOWS_ENABLED", "true")
    assert rivet_workflows_enabled()


def test_rivet_runner_feature_defaults_off(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_RUNNER_ENABLED", raising=False)
    assert not rivet_runner_enabled()


def test_rivet_editor_feature_defaults_off(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_EDITOR_ENABLED", raising=False)
    assert not rivet_editor_enabled()


def test_disabled_workflow_endpoint_rejects_before_workspace_resolution(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_WORKFLOWS_ENABLED", raising=False)
    with TestClient(app) as client:
        response = client.post(
            "/api/workspace/workflows",
            json={
                "session_id": "untrusted",
                "slug": "example",
                "project": "version: 4",
            },
        )
    assert response.status_code == 404
    assert response.json()["message"] == "Rivet workflows are disabled"


def test_disabled_runner_endpoint_rejects_before_runner_discovery(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_RUNNER_ENABLED", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/workspace/workflows/runner/status")
    assert response.status_code == 404
    assert response.json()["message"] == "Rivet runner is disabled"


def test_disabled_editor_endpoint_rejects_before_workspace_resolution(monkeypatch):
    monkeypatch.delenv("WRIGHT_RIVET_EDITOR_ENABLED", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/workspace/workflows/editor/status")
    assert response.status_code == 404
    assert response.json()["message"] == "Rivet editor is disabled"
