from __future__ import annotations

from types import SimpleNamespace

from api.main import app
from api.routers.workspace import get_workspace_service


class _WorkflowTemplates:
    def list(self):
        return [
            SimpleNamespace(
                template_id="basic-flow",
                title="Basic Flow",
                description="Small starter graph.",
                kind="starter",
                requirements=(),
            )
        ]

    def instantiate(self, template_id: str) -> str:
        assert template_id == "basic-flow"
        return "version: 4\ndata:\n  graphs:\n    main: {}\n"


class _Workflows:
    async def create(
        self,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        project: str,
        datasets: dict[str, str],
    ):
        assert (workspace_id, workspace_dir, slug) == (
            "workspace-1",
            "/tmp/workspace-1",
            "basic-flow",
        )
        assert project.startswith("version: 4")
        assert datasets == {}
        return SimpleNamespace(
            workflow_id="workflow-1",
            slug=slug,
            revision=1,
            digest="etag-1",
        )


class _Service:
    workflow_templates = _WorkflowTemplates()
    workflows = _Workflows()
    lifecycle = SimpleNamespace(
        get_by_session=lambda session_id: {
            "workspace_id": "workspace-1",
            "session_id": session_id,
        }
    )

    async def resolve_workspace_dir(self, session_id: str, engine) -> str:
        assert session_id == "session-1"
        return "/tmp/workspace-1"


def test_template_catalog_and_instantiation_routes(sync_client, monkeypatch) -> None:
    monkeypatch.setenv("WRIGHT_RIVET_WORKFLOWS_ENABLED", "true")
    app.dependency_overrides[get_workspace_service] = lambda: _Service()
    try:
        catalog = sync_client.get("/api/workspace/workflow-templates")
        created = sync_client.post(
            "/api/workspace/workflow-templates/basic-flow/instantiate",
            json={"session_id": "session-1", "slug": "basic-flow"},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert catalog.status_code == 200
    assert catalog.json() == {
        "templates": [
            {
                "template_id": "basic-flow",
                "title": "Basic Flow",
                "description": "Small starter graph.",
                "kind": "starter",
                "requirements": [],
            }
        ]
    }
    assert created.status_code == 201
    assert created.json() == {
        "workflow_id": "workflow-1",
        "slug": "basic-flow",
        "revision": 1,
        "etag": "etag-1",
    }
