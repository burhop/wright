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
from workspace_service.surfaces.manifests import WorkspaceManifestStore


def _write_manifest(tmp_path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    assets = tmp_path / "dist"
    assets.mkdir()
    asset = assets / "index.html"
    asset.write_text("<html></html>", encoding="utf-8")
    patch = tmp_path / "editor.patch"
    patch.write_text("reviewed patch", encoding="utf-8")
    wrapper = tmp_path / "wrapper.tsx"
    wrapper.write_text("reviewed wrapper", encoding="utf-8")
    asset_digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    tree_input = f"{asset_digest}  dist/index.html\n".encode()
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "rivet_version": "2.8.9",
                "source": {
                    "repository": "https://github.com/valerypopoff/rivet2.0.git",
                    "revision": "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053",
                    "package": "@valerypopoff/rivet-app",
                    "package_version": "2.8.9",
                },
                "patches": [
                    {
                        "path": "editor.patch",
                        "sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                    }
                ],
                "wrapper": [
                    {
                        "path": "wrapper.tsx",
                        "sha256": hashlib.sha256(wrapper.read_bytes()).hexdigest(),
                    }
                ],
                "entrypoint": "dist/index.html",
                "sha256": asset_digest,
                "tree_sha256": hashlib.sha256(tree_input).hexdigest(),
                "files": [
                    {
                        "path": "dist/index.html",
                        "bytes": asset.stat().st_size,
                        "sha256": asset_digest,
                    }
                ],
                "license": "MIT",
            }
        ),
        encoding="utf-8",
    )


def _catalog(tmp_path) -> EditorAssetCatalog:
    _write_manifest(tmp_path)
    return EditorAssetCatalog(tmp_path / "manifest.json")


def _hosted_catalog(tmp_path) -> EditorAssetCatalog:
    _write_manifest(tmp_path)
    (tmp_path / "host.py").write_text("# test host\n", encoding="utf-8")
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
    (assets / "dist" / "index.html").write_text("changed", encoding="utf-8")
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


def test_manual_surface_manifest_is_verified_and_collision_safe(tmp_path):
    editor = WorkspaceWorkflowEditor(
        workflows=None,  # type: ignore[arg-type]
        settings=EditorSettings(enabled=True),
        catalog=_hosted_catalog(tmp_path / "assets"),
    )
    workspace = tmp_path / "workspace"
    manifest = editor.manual_surface_manifest(str(workspace))
    assert manifest is not None
    assert manifest["id"] == "wright.rivet-editor"
    assert manifest["capabilities"] == []
    assert manifest["presentation"]["sharing"] == "isolated"  # type: ignore[index]
    generated = workspace / ".wright" / "apps" / "rivet-editor.surface.json"
    assert generated.is_file()
    discovered = WorkspaceManifestStore(workspace).get("wright.rivet-editor")
    assert discovered.manifest.presentation.sharing == "isolated"
    assert discovered.manifest.capabilities == frozenset()
    assert editor.manual_surface_manifest(str(workspace)) == manifest
    generated.write_text("{}", encoding="utf-8")
    with pytest.raises(WorkflowEditorError, match="conflicts"):
        editor.manual_surface_manifest(str(workspace))


def test_manual_surface_manifest_enables_local_ai_without_embedding_credentials(
    tmp_path,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    editor = WorkspaceWorkflowEditor(
        workflows=None,  # type: ignore[arg-type]
        settings=EditorSettings(
            enabled=True,
            ai_enabled=True,
            ai_token_ttl_seconds=123,
            ai_request_bytes=4096,
            ai_timeout_seconds=45,
        ),
        catalog=_hosted_catalog(tmp_path / "catalog"),
    )
    manifest = editor.manual_surface_manifest(str(workspace))
    assert manifest is not None
    launch = manifest["launch"]
    argv = launch["argv"]
    assert argv[-7:] == [
        "--ai-enabled",
        "--ai-token-ttl",
        "123",
        "--ai-request-bytes",
        "4096",
        "--ai-timeout",
        "45",
    ]
    encoded = json.dumps(manifest)
    assert "HERMES_API_KEY" not in encoded
    assert "api_key" not in encoded
    assert launch["environment"] == {}


def test_manual_surface_manifest_never_provisions_without_a_verified_host(tmp_path):
    editor = WorkspaceWorkflowEditor(
        workflows=None,  # type: ignore[arg-type]
        settings=EditorSettings(enabled=True),
        catalog=_catalog(tmp_path / "assets"),
    )
    assert editor.manual_surface_manifest(str(tmp_path / "workspace")) is None


def test_manual_surface_manifest_is_confined_to_its_workspace(tmp_path):
    editor = WorkspaceWorkflowEditor(
        workflows=None,  # type: ignore[arg-type]
        settings=EditorSettings(enabled=True),
        catalog=_hosted_catalog(tmp_path / "assets"),
    )
    first = tmp_path / "workspace-a"
    second = tmp_path / "workspace-b"
    editor.manual_surface_manifest(str(first))

    assert (first / ".wright" / "apps" / "rivet-editor.surface.json").is_file()
    assert not (second / ".wright" / "apps" / "rivet-editor.surface.json").exists()
    assert WorkspaceManifestStore(second).discover() == {}
    editor.manual_surface_manifest(str(second))
    assert WorkspaceManifestStore(first).get("wright.rivet-editor").relative_path == (
        ".wright/apps/rivet-editor.surface.json"
    )
    assert WorkspaceManifestStore(second).get("wright.rivet-editor").relative_path == (
        ".wright/apps/rivet-editor.surface.json"
    )


def test_manual_surface_manifest_rejects_linked_workspace_app_directory(tmp_path):
    editor = WorkspaceWorkflowEditor(
        workflows=None,  # type: ignore[arg-type]
        settings=EditorSettings(enabled=True),
        catalog=_hosted_catalog(tmp_path / "assets"),
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / ".wright").mkdir()
    try:
        (workspace / ".wright" / "apps").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symbolic links are unavailable on this host")
    with pytest.raises(ValueError, match="symbolic links"):
        editor.manual_surface_manifest(str(workspace))
