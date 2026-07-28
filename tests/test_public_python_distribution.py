from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DISTRIBUTIONS = {
    "wright-core",
    "wright-tool-registry",
    "wright-data-vault",
    "wright-agent-adapters",
    "wright-workspace-service",
    "wright-api",
    "hermes-plugin-wright",
}


def test_one_public_distribution_carries_the_complete_native_application() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = project["project"]
    assert metadata["name"] == "wright-engineering"
    assert metadata["entry-points"]["hermes_agent.plugins"] == {
        "wright": "wright_engineering.hermes_plugin:register"
    }
    runtime = metadata["optional-dependencies"]["runtime"]
    normalized = {
        item.split("[", 1)[0].split("<", 1)[0].split(">", 1)[0] for item in runtime
    }
    assert normalized.isdisjoint(PRIVATE_DISTRIBUTIONS)

    wheel_packages = set(
        project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    )
    assert {
        "src/wright_engineering",
        "apps/api/src/api",
        "packages/core/src/core",
        "packages/agent_adapters/src/agent_adapters",
        "packages/tool_registry/src/tool_registry",
        "packages/data_vault/src/data_vault",
        "packages/workspace_service/src/workspace_service",
    }.issubset(wheel_packages)


def test_all_workspace_component_distributions_remain_private() -> None:
    projects = [
        ROOT / "apps/api/pyproject.toml",
        ROOT / "hermes-plugin-wright/pyproject.toml",
        *sorted((ROOT / "packages").glob("*/pyproject.toml")),
    ]
    observed = set()
    for path in projects:
        metadata = tomllib.loads(path.read_text(encoding="utf-8"))["project"]
        observed.add(metadata["name"])
        assert "Private :: Do Not Upload" in metadata.get("classifiers", []), path
    assert PRIVATE_DISTRIBUTIONS.issubset(observed)
