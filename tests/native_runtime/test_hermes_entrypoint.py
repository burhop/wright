from __future__ import annotations

import ast
import asyncio
from pathlib import Path

from .adapter_support import load_adapter


ROOT = Path(__file__).resolve().parents[2]


class FakeHermesContext:
    def __init__(self) -> None:
        self.commands: dict[str, object] = {}

    def register_command(self, *, name: str, handler: object, **_: object) -> None:
        self.commands[name] = handler


def test_real_git_adapter_registers_wright_command() -> None:
    context = FakeHermesContext()
    load_adapter().register(context)
    assert set(context.commands) == {"wright"}
    response = asyncio.run(context.commands["wright"](""))  # type: ignore[operator]
    assert "/wright <command>" in response


def test_adapter_entrypoint_has_dependency_safe_top_level_imports() -> None:
    source = (ROOT / "hermes-plugin-wright/__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module.split(".", 1)[0]
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imports.update(
        node.names[0].name.split(".", 1)[0]
        for node in tree.body
        if isinstance(node, ast.Import)
    )
    assert imports <= {"__future__", "typing"}


def test_adapter_files_do_not_import_wright_runtime_or_third_party_packages() -> None:
    for name in ("__init__.py", "bootstrap.py", "commands.py"):
        source = (ROOT / "hermes-plugin-wright" / name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imported.update(
            node.names[0].name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        )
        assert imported.isdisjoint(
            {"wright_engineering", "httpx", "packaging", "fastapi", "mcp"}
        )
