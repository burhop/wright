from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def workspace_surfaces_fixture_root() -> Path:
    """Return the cross-platform absolute Workspace Surfaces fixture root."""

    root = Path(__file__).resolve().parent / "fixtures" / "workspace_surfaces"
    if not root.is_dir():
        raise RuntimeError(f"Workspace Surfaces fixture root is missing: {root}")
    return root


@pytest.fixture
def workspace_surface_fixture(workspace_surfaces_fixture_root: Path):
    """Resolve a named fixture while rejecting absolute paths and traversal."""

    def resolve(*parts: str) -> Path:
        candidate = workspace_surfaces_fixture_root.joinpath(*parts).resolve()
        if not candidate.is_relative_to(workspace_surfaces_fixture_root.resolve()):
            raise ValueError("fixture path must remain under workspace_surfaces")
        return candidate

    return resolve
