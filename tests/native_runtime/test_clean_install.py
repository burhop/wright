from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_native_install_and_start_modules_never_name_forbidden_executables() -> None:
    paths = [
        ROOT / "src/wright_engineering/hermes_plugin/commands.py",
        ROOT / "src/wright_engineering/runtime/artifacts.py",
        ROOT / "src/wright_engineering/runtime/installer.py",
        ROOT / "src/wright_engineering/runtime/lifecycle.py",
        ROOT / "src/wright_engineering/runtime/process.py",
    ]
    string_literals: set[str] = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        string_literals.update(
            node.value.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )
    forbidden_commands = {"git", "docker", "node", "nodejs", "npm", "npx", "pnpm"}
    assert forbidden_commands.isdisjoint(string_literals)


def test_runtime_cli_launches_packaged_module_not_repository_path() -> None:
    source = (ROOT / "src/wright_engineering/runtime/lifecycle.py").read_text(
        encoding="utf-8"
    )
    assert '"-m",\n                            "wright_engineering.cli"' in source
    assert "cwd=" not in source
