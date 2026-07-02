from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def read_project(relative_path: str) -> dict:
    with (ROOT / relative_path).open("rb") as fh:
        return tomllib.load(fh)["project"]


def assert_pypi_metadata(project: dict) -> None:
    for key in [
        "name",
        "version",
        "description",
        "readme",
        "requires-python",
        "license",
        "dependencies",
        "urls",
    ]:
        assert key in project
    for url_key in ["Homepage", "Source", "Issues", "Documentation", "Releases"]:
        assert project["urls"][url_key].startswith("https://")


def test_wright_core_has_pypi_ready_metadata() -> None:
    project = read_project("packages/core/pyproject.toml")

    assert project["name"] == "wright-core"
    assert project["readme"] == "README.md"
    assert_pypi_metadata(project)
    assert any(dep.startswith("opentelemetry-api>=") for dep in project["dependencies"])
    assert (ROOT / "packages/core/README.md").exists()


def test_wright_tool_registry_has_pypi_ready_metadata_and_bounded_core_dependency() -> (
    None
):
    project = read_project("packages/tool_registry/pyproject.toml")

    assert project["name"] == "wright-tool-registry"
    assert project["readme"] == "README.md"
    assert_pypi_metadata(project)
    assert any(
        dep.startswith("wright-core>=") and ",<" in dep
        for dep in project["dependencies"]
    )
    assert any(dep.startswith("PyYAML>=") for dep in project["dependencies"])
    assert (ROOT / "packages/tool_registry/README.md").exists()
