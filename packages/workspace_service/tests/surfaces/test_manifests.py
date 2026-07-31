from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from workspace_service.surfaces.manifests import (
    ManifestDiscoveryError,
    WorkspaceManifestStore,
)


pytestmark = pytest.mark.workspace_surfaces


def _manifest(*, manifest_id: str = "demo.app", cwd: str = ".") -> dict:
    return {
        "schemaVersion": 1,
        "id": manifest_id,
        "version": "1.0.0",
        "title": "Demo",
        "ownershipPolicy": "wright-owned",
        "launch": {
            "mode": "command",
            "argv": ["python", "app.py", "--port", "${WRIGHT_PORT}"],
            "workingDirectory": cwd,
        },
        "readiness": {
            "path": "/health",
            "expectedStatus": 200,
            "timeoutMs": 1_000,
        },
        "presentation": {"panel": True, "browser": True, "sharing": "shared"},
        "transports": {"http": True, "websocket": False, "sse": False},
        "capabilities": [],
    }


def _write(workspace, value: dict, name: str = "demo.surface.json"):
    directory = workspace / ".wright" / "apps"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_discovers_valid_workspace_manifest_and_resolves_confined_cwd(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "src").mkdir(parents=True)
    _write(workspace, _manifest(cwd="src"))
    store = WorkspaceManifestStore(workspace)

    discovered = store.discover()

    assert tuple(discovered) == ("demo.app",)
    assert discovered["demo.app"].relative_path == ".wright/apps/demo.surface.json"
    assert discovered["demo.app"].working_directory == (workspace / "src").resolve()
    assert store.authorize("demo.app").manifest.manifest_id == "demo.app"


@pytest.mark.parametrize("cwd", ["../outside", "C:\\outside", "linked"])
def test_rejects_working_directory_escape_or_link(tmp_path, cwd) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    if cwd == "linked":
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            (workspace / "linked").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            pytest.skip(f"host cannot create symlink: {error}")
    _write(workspace, _manifest(cwd=cwd))

    with pytest.raises(ManifestDiscoveryError, match="working directory"):
        WorkspaceManifestStore(workspace).discover()


@pytest.mark.parametrize(
    "name", ["PATH", "PYTHONPATH", "NODE_OPTIONS", "LD_PRELOAD", "WRIGHT_PORT"]
)
def test_rejects_process_control_environment_variables(tmp_path, name) -> None:
    workspace = tmp_path / "workspace"
    value = _manifest()
    value["launch"]["environment"] = {name: "unsafe"}
    _write(workspace, value)

    with pytest.raises(ManifestDiscoveryError) as error:
        WorkspaceManifestStore(workspace).discover()
    assert error.value.code == "SURFACE_MANIFEST_ENVIRONMENT_DENIED"


def test_duplicate_ids_and_duplicate_json_keys_fail_closed(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    _write(workspace, _manifest(), "one.surface.json")
    _write(workspace, _manifest(), "two.surface.json")
    with pytest.raises(ManifestDiscoveryError, match="duplicate manifest id"):
        WorkspaceManifestStore(workspace).discover()

    (workspace / ".wright/apps/two.surface.json").unlink()
    (workspace / ".wright/apps/one.surface.json").write_text(
        '{"schemaVersion":1,"schemaVersion":1}', encoding="utf-8"
    )
    with pytest.raises(ManifestDiscoveryError, match="duplicate JSON key"):
        WorkspaceManifestStore(workspace).discover()


def test_attach_approval_is_explicit_admin_scoped_and_hash_bound(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    value = _manifest(manifest_id="remote.app")
    value.update(
        ownershipPolicy="approved-attach",
        launch={
            "mode": "attach",
            "url": "https://app.example.test/base",
            "ownershipProof": "operator-approved",
        },
    )
    path = _write(workspace, value)
    store = WorkspaceManifestStore(
        workspace,
        administrator_check=lambda actor_id: actor_id == "admin-1",
        clock=lambda: datetime(2026, 7, 30, tzinfo=UTC),
    )

    with pytest.raises(ManifestDiscoveryError, match="approval"):
        store.authorize("remote.app")
    with pytest.raises(ManifestDiscoveryError, match="administrator"):
        store.approve_attach("remote.app", administrator_id="engineer-1")

    approval = store.approve_attach("remote.app", administrator_id="admin-1")
    authorized = store.authorize("remote.app", attach_approval=approval)
    assert authorized.manifest.canonical_hash == approval.manifest_hash
    assert approval.normalized_url == "https://app.example.test/base"
    assert approval.administrator_id == "admin-1"

    value["version"] = "1.0.1"
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ManifestDiscoveryError, match="changed"):
        store.authorize("remote.app", attach_approval=approval)


def test_manifest_file_symlink_is_never_followed(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    apps = workspace / ".wright/apps"
    apps.mkdir(parents=True)
    outside = tmp_path / "outside.surface.json"
    outside.write_text(json.dumps(_manifest()), encoding="utf-8")
    try:
        (apps / "linked.surface.json").symlink_to(outside)
    except OSError as error:
        pytest.skip(f"host cannot create symlink: {error}")

    with pytest.raises(ManifestDiscoveryError, match="symbolic link"):
        WorkspaceManifestStore(workspace).discover()
