import pytest
from workspace_service.workflow_campaign import inventory
from workspace_service.workflow_campaign_fixtures import create_bundle, restore_bundle
from packages.workspace_service.tests.test_workflow_source_execution import task, source


def setup_bundle(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "workflows").mkdir(parents=True)
    (workspace / "workflows/report.wflow").write_text(source(task()))
    manifest = inventory(workspace)
    bundle = tmp_path / "bundle"
    create_bundle(manifest, [manifest["cases"][0]["id"]], bundle)
    return bundle, tmp_path / "restored"


def test_repeatable_setup_preserves_identical_files_and_rejects_different_content(
    tmp_path,
):
    bundle, target = setup_bundle(tmp_path)
    target.mkdir()
    assert restore_bundle(bundle, target)["restored_files"] == 1
    assert restore_bundle(bundle, target)["unchanged_files"] == 1
    path = target / "workflows/report.wflow"
    path.write_text("user changes")
    with pytest.raises(ValueError, match="differs"):
        restore_bundle(bundle, target)
    assert path.read_text() == "user changes"


def test_tampered_fixture_fails_before_any_workspace_write(tmp_path):
    bundle, target = setup_bundle(tmp_path)
    target.mkdir()
    (bundle / "files/workflows/report.wflow").write_text("tampered")
    with pytest.raises(ValueError, match="digest"):
        restore_bundle(bundle, target)
    assert not list(target.iterdir())


def test_bundle_rejects_source_changes_since_inventory(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "workflows").mkdir(parents=True)
    path = workspace / "workflows/report.wflow"
    path.write_text(source(task()))
    manifest = inventory(workspace)
    path.write_text(source(task(prompt="Changed")))
    with pytest.raises(ValueError, match="changed"):
        create_bundle(manifest, [manifest["cases"][0]["id"]], tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()
