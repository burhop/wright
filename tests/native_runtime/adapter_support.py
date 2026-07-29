from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_NAME = "wright_hermes_adapter_test"


def load_adapter() -> ModuleType:
    module = sys.modules.get(PACKAGE_NAME)
    if module is not None:
        return module
    plugin_dir = ROOT / "hermes-plugin-wright"
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("adapter_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    return module


def load_adapter_commands() -> ModuleType:
    load_adapter()
    return importlib.import_module(f"{PACKAGE_NAME}.commands")


def load_adapter_bootstrap() -> ModuleType:
    load_adapter()
    return importlib.import_module(f"{PACKAGE_NAME}.bootstrap")
