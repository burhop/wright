from __future__ import annotations

from pathlib import Path
import tomllib


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_mirror_packages_only_the_migration_delegate_surface() -> None:
    with (PLUGIN_ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    included = project["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert set(included) == {
        "__init__.py",
        "plugin.yaml",
        "bridge.py",
        "commands.py",
    }
    assert not {"catalog.py", "catalog.yaml", "schemas.py"} & set(included)
