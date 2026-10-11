"""Operational prototype implementations must not ship in the workspace owner."""

import ast
import importlib.util
from pathlib import Path

import pytest
import workspace_service


RETIRED_MODULES = ("print_part_demo", "print_part_demo_printer")


@pytest.mark.parametrize("module", RETIRED_MODULES)
def test_retired_vendor_prototype_is_not_an_importable_workspace_module(module):
    assert importlib.util.find_spec("workspace_service." + module) is None


def test_workspace_owner_has_no_imports_of_retired_operational_implementations():
    root = Path(workspace_service.__file__).resolve().parent
    assert root.is_dir()
    checked = 0
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or "", *[alias.name for alias in node.names]]
            else:
                continue
            for name in names:
                assert not set(name.split(".")).intersection(RETIRED_MODULES), (
                    path,
                    name,
                )
        checked += 1
    assert checked > 0
