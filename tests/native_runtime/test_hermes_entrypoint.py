from __future__ import annotations

import ast
import asyncio
from pathlib import Path

from wright_engineering import hermes_plugin


ROOT = Path(__file__).resolve().parents[2]


class FakeHermesContext:
    def __init__(self) -> None:
        self.commands: dict[str, object] = {}

    def register_command(self, *, name: str, handler: object, **_: object) -> None:
        self.commands[name] = handler


def test_entrypoint_registers_wright_command() -> None:
    context = FakeHermesContext()
    hermes_plugin.register(context)
    assert set(context.commands) == {"wright"}
    response = asyncio.run(context.commands["wright"](""))  # type: ignore[operator]
    assert "/wright <command>" in response


def test_entrypoint_module_has_dependency_safe_top_level_imports() -> None:
    source = (ROOT / "src/wright_engineering/hermes_plugin/__init__.py").read_text(
        encoding="utf-8"
    )
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
