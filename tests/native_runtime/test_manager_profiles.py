from __future__ import annotations

from pathlib import Path

import pytest

from wright_engineering.manager_profiles import build_manager_profile


def test_all_manager_profiles_resolve_one_wright_owned_home(tmp_path: Path) -> None:
    home = tmp_path / "wright-home"
    workspace = tmp_path / "workspace"
    profiles = [
        build_manager_profile(
            manager_id,
            workspace=workspace,
            session_id="session-1",
            workspace_id="workspace-1",
            wright_home=home,
        )
        for manager_id in ("hermes", "codex")
    ]
    assert {profile.wright_home for profile in profiles} == {home.resolve()}
    assert {profile.args[:4] for profile in profiles} == {
        ("mcp", "serve", "--stdio", "--workspace")
    }
    assert profiles[0].prerequisites == ("git",)
    assert "git" not in profiles[1].prerequisites


def test_unknown_manager_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="manager_unsupported"):
        build_manager_profile("unknown", workspace=tmp_path)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"workspace_id": "workspace-1"}, "stdio_profile_requires_session_id"),
        ({"session_id": "session-1"}, "stdio_profile_requires_workspace_id"),
    ],
)
def test_stdio_profile_requires_real_gateway_binding_ids(
    tmp_path: Path, kwargs: dict[str, str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        build_manager_profile("codex", workspace=tmp_path, **kwargs)
