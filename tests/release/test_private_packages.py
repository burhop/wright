from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_wright_engineering_is_the_only_publishable_distribution() -> None:
    public = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    assert public["name"] == "wright-engineering"
    assert "Private :: Do Not Upload" not in public["classifiers"]
    assert public["dependencies"] == []

    internal = [
        ROOT / "apps/api/pyproject.toml",
        ROOT / "hermes-plugin-wright/pyproject.toml",
        *sorted((ROOT / "packages").glob("*/pyproject.toml")),
    ]
    for path in internal:
        project = tomllib.loads(path.read_text(encoding="utf-8"))["project"]
        assert "Private :: Do Not Upload" in project.get("classifiers", []), path


def test_publication_workflows_never_name_private_distributions() -> None:
    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / ".github/workflows").glob("*.yml")
        if "publish" in path.name or path.name == "release.yml"
    )
    for forbidden in (
        "wright-core",
        "wright-tool-registry",
        "wright-data-vault",
        "wright-agent-adapters",
        "wright-workspace-service",
        "wright-api",
        "hermes-plugin-wright",
    ):
        assert forbidden not in workflows
