from __future__ import annotations

import os
from pathlib import Path

import pytest

from wright_engineering.runtime.layout import LayoutError, NativeLayout


def test_layout_separates_versioned_runtime_from_stable_data(tmp_path: Path) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    assert layout.root == (tmp_path / "hermes" / "wright").resolve()
    assert layout.runtimes.parent == layout.root
    assert layout.data.parent == layout.root
    assert layout.runtimes != layout.data
    assert layout.runtime_path("runtime-123").parent == layout.runtimes


def test_owned_path_rejects_root_home_and_external_workspace(tmp_path: Path) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    external = tmp_path / "customer-workspace"
    external.mkdir()

    for unsafe in (Path(external.anchor), layout.hermes_home, external):
        with pytest.raises(LayoutError):
            layout.require_owned(unsafe)


def test_runtime_id_cannot_escape_containment(tmp_path: Path) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    with pytest.raises(LayoutError):
        layout.runtime_path("../escape")
    with pytest.raises(LayoutError):
        layout.runtime_path("nested/runtime")


@pytest.mark.skipif(
    os.name == "nt" and not hasattr(os, "symlink"), reason="symlink unavailable"
)
def test_deletion_target_rejects_symlink(tmp_path: Path) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
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
