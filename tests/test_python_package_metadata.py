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


def test_wright_engineering_root_package_has_public_alpha_metadata() -> None:
    project = read_project("pyproject.toml")

    assert project["name"] == "wright-engineering"
    assert project["readme"] == "README.md"
    assert project["dependencies"] == []
    assert project["scripts"]["wright"] == "wright_engineering.cli:main"
    assert "Public-alpha helper CLI" in project["description"]
    assert_pypi_metadata(project)
    assert (ROOT / "src/wright_engineering/__init__.py").exists()
    assert (ROOT / "src/wright_engineering/cli.py").exists()


def test_component_packages_are_not_advertised_as_alpha_pypi_packages() -> None:
    python_packages = (ROOT / "docs/getting-started/python-packages.md").read_text(
        encoding="utf-8"
    )

    assert "pip install wright-engineering" in python_packages
    assert "are workspace-local for alpha" in python_packages
    assert "https://pypi.org/project/wright-core/" not in python_packages
    assert "https://pypi.org/project/wright-tool-registry/" not in python_packages
