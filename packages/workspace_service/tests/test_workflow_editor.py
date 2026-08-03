from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from core.workflow_editor import EditorAvailability, WorkflowEditorError
from data_vault import WorkflowRepository
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.workflows import WorkspaceWorkflowUseCases
from workspace_service.workflow_editor import (
    EditorAssetCatalog,
    EditorSettings,
    WorkspaceWorkflowEditor,
)


def _catalog(tmp_path) -> EditorAssetCatalog:
    tmp_path.mkdir(parents=True, exist_ok=True)
    asset = tmp_path / "index.html"
    asset.write_text("<html></html>", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "rivet_version": "1.25.0",
                "entrypoint": "index.html",
                "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
                "license": "MIT",
            }
        ),
        encoding="utf-8",
    )
    return EditorAssetCatalog(tmp_path / "manifest.json")


@pytest.mark.asyncio
async def test_editor_grant_is_workspace_session_and_revision_scoped(tmp_path):
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    await workflows.create("workspace-a", str(tmp_path), "fixture", "version: 4")
    editor = WorkspaceWorkflowEditor(
        workflows,
        settings=EditorSettings(enabled=True),
        catalog=_catalog(tmp_path / "assets"),
    )
    bootstrap = await editor.bootstrap(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    assert bootstrap.availability is EditorAvailability.AVAILABLE
    assert bootstrap.grant_id
    document = await editor.read(
        bootstrap.grant_id,
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
    )
    assert document.revision == 1
    with pytest.raises(WorkflowEditorError):
        await editor.read(
            bootstrap.grant_id,
            workspace_id="workspace-b",
            session_id="session-a",
            workspace_dir=str(tmp_path),
        )
    await editor.save(
        bootstrap.grant_id,
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        expected_revision=1,
        project="version: 4\nname: edited",
        datasets={},
    )
    with pytest.raises(WorkflowEditorError, match="stale"):
        await editor.save(
            bootstrap.grant_id,
            workspace_id="workspace-a",
            session_id="session-a",
            workspace_dir=str(tmp_path),
            expected_revision=2,
            project="version: 4",
            datasets={},
        )
    await executor.close()


def test_asset_catalog_never_accepts_missing_or_changed_assets(tmp_path):
    catalog = EditorAssetCatalog(tmp_path / "missing.json")
    assert catalog.status()[0] is EditorAvailability.MISSING
    assets = tmp_path / "assets"
    assets.mkdir()
    catalog = _catalog(assets)
    assert catalog.status()[0] is EditorAvailability.AVAILABLE
    (assets / "index.html").write_text("changed", encoding="utf-8")
    assert catalog.status()[0] is EditorAvailability.INCOMPATIBLE


@pytest.mark.asyncio
async def test_editor_grant_expiry_and_missing_manifest_are_safe(tmp_path):
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    await workflows.create("workspace", str(tmp_path), "fixture", "version: 4")
    now = datetime(2026, 8, 3, tzinfo=UTC)
    editor = WorkspaceWorkflowEditor(
        workflows,
        settings=EditorSettings(enabled=True, grant_ttl_seconds=1),
        catalog=EditorAssetCatalog(tmp_path / "no-manifest.json"),
        clock=lambda: now,
    )
    missing = await editor.bootstrap(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    assert missing.availability is EditorAvailability.MISSING
    clock = [now]
    editor = WorkspaceWorkflowEditor(
        workflows,
        settings=EditorSettings(enabled=True, grant_ttl_seconds=1),
        catalog=_catalog(tmp_path / "assets"),
        clock=lambda: clock[0],
    )
    bootstrap = await editor.bootstrap(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    clock[0] += timedelta(seconds=2)
    with pytest.raises(WorkflowEditorError, match="expired"):
        await editor.read(
            bootstrap.grant_id or "",
            workspace_id="workspace",
            session_id="session",
            workspace_dir=str(tmp_path),
        )
    await executor.close()
