from __future__ import annotations

import zipfile
from pathlib import Path

from agent_adapters.hermes_gateway import hermes_wright_gateway_profile


ROOT = Path(__file__).resolve().parents[2]


def test_native_runtime_source_has_no_provider_specific_lifecycle_branch() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src/wright_engineering/runtime").glob("*.py")
    ).lower()
    assert "solid edge" not in text
    assert "brep" not in text


def test_built_candidate_contains_catalog_gateway_workspace_and_ui() -> None:
    wheels = list((ROOT / "dist/native-candidate").glob("*.whl"))
    if not wheels:
        import pytest

        pytest.skip("local native candidate has not been built")
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
    required = {
        "wright_engineering/static/web/index.html",
        "tool_registry/catalog/engineering-catalog.yaml",
        "tool_registry/gateway_service.py",
        "workspace_service/__init__.py",
        "agent_adapters/hermes.py",
        "api/main.py",
    }
    assert required.issubset(names)


def test_native_gateway_profile_uses_installed_module_not_repo_or_uv(
    tmp_path: Path,
) -> None:
    profile = hermes_wright_gateway_profile(
        None,
        session_id="session-1",
        workspace_id="workspace-1",
        terminal_cwd=str(tmp_path),
    )
    rendered = " ".join([profile.command, *profile.args]).lower()
    assert "wright_engineering.cli" in rendered
    assert "--project" not in profile.args
    assert profile.command.lower() != "uv"
