from __future__ import annotations

import os
from pathlib import Path

import pytest

from wright_engineering.runtime.layout import LayoutError, NativeLayout


def test_layout_separates_versioned_runtime_from_stable_data(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    assert layout.root == (tmp_path / "wright-home").resolve()
    assert layout.wright_home == layout.root
    assert layout.runtimes.parent == layout.root
    assert layout.data.parent == layout.root
    assert layout.runtimes != layout.data
    assert layout.runtime_path("runtime-123").parent == layout.runtimes


def test_layout_discovery_ignores_manager_owned_homes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = tmp_path / "wright"
    monkeypatch.setenv("WRIGHT_HOME", str(expected))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    layout = NativeLayout.discover()
    assert layout.wright_home == expected.resolve()


def test_owned_path_rejects_root_home_and_external_workspace(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    external = tmp_path / "customer-workspace"
    external.mkdir()

    for unsafe in (Path(external.anchor), layout.wright_home, external):
        with pytest.raises(LayoutError):
            layout.require_owned(unsafe)


def test_runtime_id_cannot_escape_containment(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    with pytest.raises(LayoutError):
        layout.runtime_path("../escape")
    with pytest.raises(LayoutError):
        layout.runtime_path("nested/runtime")


@pytest.mark.skipif(
    os.name == "nt" and not hasattr(os, "symlink"), reason="symlink unavailable"
)
def test_deletion_target_rejects_symlink(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    layout.ensure()
    external = tmp_path / "outside"
    external.mkdir()
    link = layout.data / "linked"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is not permitted")

    with pytest.raises(LayoutError):
        layout.require_deletion_target(link, allowed_root=layout.data)
