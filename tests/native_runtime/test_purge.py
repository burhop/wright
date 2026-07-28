from __future__ import annotations

from pathlib import Path

import pytest

from wright_engineering.runtime.layout import LayoutError

from .support import lifecycle


def test_purge_requires_path_bound_confirmation_and_deletes_only_owned_data(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path)
    owned = runtime.layout.data / "workspaces" / "managed" / "part.step"
    owned.parent.mkdir(parents=True)
    owned.write_text("owned", encoding="utf-8")
    external = tmp_path / "external-workspace" / "part.step"
    external.parent.mkdir()
    external.write_text("external", encoding="utf-8")
    hermes_config = runtime.layout.hermes_home / "config.yaml"
    hermes_config.parent.mkdir(parents=True, exist_ok=True)
    hermes_config.write_text("unrelated", encoding="utf-8")

    preview = runtime.purge()
    assert not preview.ok and preview.code == "purge_confirmation_required"
    assert owned.exists()
    wrong = runtime.purge(confirmation="wrong")
    assert not wrong.ok and wrong.code == "invalid_confirmation"
    result = runtime.purge(confirmation=preview.details["confirmation_code"])

    assert result.ok
    assert not runtime.layout.data.exists()
    assert external.read_text(encoding="utf-8") == "external"
    assert hermes_config.read_text(encoding="utf-8") == "unrelated"


def test_purge_refuses_symlinked_owned_data(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path)
    runtime.layout.data.mkdir(parents=True)
    external = tmp_path / "outside"
    external.mkdir()
    link = runtime.layout.data / "link"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not permitted")
    preview = runtime.purge()
    assert not preview.ok
    assert preview.code == "unsafe_path"
    assert external.exists()


def test_purge_manager_rejects_broad_or_ambiguous_scope(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path)
    from wright_engineering.runtime.purge import PurgeManager

    manager = PurgeManager(runtime.layout)
    for unsafe in (
        runtime.layout.root,
        runtime.layout.hermes_home,
        tmp_path / "external",
    ):
        with pytest.raises(LayoutError):
            manager.validate_target(unsafe)
