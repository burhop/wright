"""Verify the root-level Hermes Git plugin without installing a wheel."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


class _Context:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def register_command(self, **kwargs: object) -> None:
        self.commands.append(str(kwargs["name"]))


def verify() -> None:
    root = Path(__file__).resolve().parent
    name = "wright_verified_adapter"
    spec = importlib.util.spec_from_file_location(
        name,
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    if spec is None or spec.loader is None:
        raise SystemExit("Wright adapter package could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        context = _Context()
        module.register(context)
    finally:
        for module_name in tuple(sys.modules):
            if module_name == name or module_name.startswith(f"{name}."):
                sys.modules.pop(module_name, None)
    if context.commands != ["wright"]:
        raise SystemExit(f"unexpected registered commands: {context.commands}")
    print("Wright Hermes Git adapter verification passed")


if __name__ == "__main__":
    verify()
