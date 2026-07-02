from __future__ import annotations

import ast
from pathlib import Path


def _imports_apps_api(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "api" or alias.name.startswith("apps.api"):
                    violations.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if (
                module == "api"
                or module.startswith("api.")
                or module.startswith("apps.api")
            ):
                violations.append(module)
    return violations


def test_packages_do_not_import_api_application_code():
    package_roots = Path("packages").glob("*/src/**/*.py")
    violations = {
        str(path): imports
        for path in package_roots
        if (imports := _imports_apps_api(path))
    }

    assert violations == {}
