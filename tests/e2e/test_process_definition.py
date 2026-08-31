from __future__ import annotations

from pathlib import Path


def test_process_definition_api_and_spa_shell_do_not_change_workspace_or_rivet(
    offline_api_client,
    monkeypatch,
) -> None:
    """Smoke the packaged API and shell; rendered feature proof remains in Playwright."""

    from api import composition

    monkeypatch.setenv("WRIGHT_RIVET_WORKFLOWS_ENABLED", "1")
    composition.process_definition_reader.cache_clear()
    reader = composition.process_definition_reader()
    database_parent = Path(offline_api_client.app.state.mcp_engine.db_path).parent
    assert reader.installed_root == database_parent / "process-definitions"
    assert not reader.installed_root.exists()
    workspace_before = offline_api_client.get("/api/workspace/recent")
    rivet_before = offline_api_client.get("/api/workspace/workflow-templates")
    assert workspace_before.status_code == 200
    assert rivet_before.status_code == 200

    definition = offline_api_client.get(
        "/api/process-definitions/product-definition-v1"
    )
    assert definition.status_code == 200
    assert definition.headers["cache-control"] == "no-cache, private"
    assert definition.headers["etag"].startswith('"')
    payload = definition.json()
    assert payload["definition"]["process_id"] == "product-definition-v1"
    assert payload["source_kind"] == "packaged_fallback"
    assert payload["source_id"] == ("process-definitions/product-definition-v1.json")

    unchanged = offline_api_client.get(
        "/api/process-definitions/product-definition-v1",
        headers={"If-None-Match": definition.headers["etag"]},
    )
    assert unchanged.status_code == 304
    assert unchanged.content == b""

    shell = offline_api_client.get("/processes/product-definition-v1")
    assert shell.status_code == 200
    assert shell.headers["content-type"].startswith("text/html")
    assert '<div id="root"></div>' in shell.text

    workspace_after = offline_api_client.get("/api/workspace/recent")
    rivet_after = offline_api_client.get("/api/workspace/workflow-templates")
    assert workspace_after.status_code == 200
    assert rivet_after.status_code == 200
    assert workspace_after.json() == workspace_before.json()
    assert rivet_after.json() == rivet_before.json()
    assert not reader.installed_root.exists()
    composition.process_definition_reader.cache_clear()
