from __future__ import annotations

import ast
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_public_wheel_declares_single_hermes_entrypoint_and_runtime_extra() -> None:
    project = PYPROJECT["project"]
    assert project["name"] == "wright-engineering"
    assert project["entry-points"]["hermes_agent.plugins"] == {
        "wright": "wright_engineering.hermes_plugin:register"
    }
    assert "runtime" in project["optional-dependencies"]
    private_names = {
        "wright-core",
        "wright-agent-adapters",
        "wright-tool-registry",
        "wright-data-vault",
        "wright-workspace-service",
    }
    assert not any(
        dependency.split("[", 1)[0].split("=", 1)[0] in private_names
        for dependency in project["optional-dependencies"]["runtime"]
    )


def test_required_application_and_resource_packages_are_included() -> None:
    packages = set(PYPROJECT["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"])
    assert {
        "src/wright_engineering",
        "apps/api/src/api",
        "packages/core/src/core",
        "packages/agent_adapters/src/agent_adapters",
        "packages/tool_registry/src/tool_registry",
        "packages/data_vault/src/data_vault",
        "packages/workspace_service/src/workspace_service",
    }.issubset(packages)
    assert (ROOT / "src/wright_engineering/compatibility.json").is_file()
    assert (ROOT / "src/wright_engineering/static/README.md").is_file()


def test_thin_entrypoint_has_no_runtime_only_imports() -> None:
    source = (ROOT / "src/wright_engineering/hermes_plugin/__init__.py").read_text(
        encoding="utf-8"
    )
    imported = {
        node.names[0].name.split(".", 1)[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
    }
    imported.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported.isdisjoint({"api", "fastapi", "mcp", "uvicorn"})
