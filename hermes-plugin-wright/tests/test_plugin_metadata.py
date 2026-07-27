from pathlib import Path
import importlib.util
import sys
from unittest.mock import MagicMock

import yaml
from packaging.version import Version


def test_plugin_manifest_supports_current_hermes_agent():
    manifest_path = Path(__file__).resolve().parents[1] / "plugin.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "wright"
    assert "commands" in manifest["capabilities"]
    assert Version(manifest["min_hermes_version"]) == Version("0.18.0")


def test_flat_directory_plugin_load_registers_wright_command(monkeypatch):
    plugin_dir = Path(__file__).resolve().parents[1]
    init_path = plugin_dir / "__init__.py"
    module_name = "wright_flat_plugin_test"

    monkeypatch.delitem(sys.modules, "hermes_plugin_wright", raising=False)
    spec = importlib.util.spec_from_file_location(
        module_name,
        init_path,
        submodule_search_locations=[str(plugin_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
        ctx = MagicMock()

        module.register(ctx)

        ctx.register_command.assert_called_once()
        assert ctx.register_command.call_args.kwargs["name"] == "wright"
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop("hermes_plugin_wright", None)
        for name in list(sys.modules):
            if name.startswith("hermes_plugin_wright."):
                sys.modules.pop(name, None)


def test_plugin_dependency_policy_is_mirror_release_ready():
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as fh:
        project = tomllib.load(fh)["project"]

    deps = project["dependencies"]
    assert deps == [
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "httpx>=0.27",
        "structlog>=24.0",
    ]
    assert not any(dep.startswith("wright-") for dep in deps)


def test_plugin_runtime_does_not_import_private_wright_packages():
    plugin_dir = Path(__file__).resolve().parents[1]

    for module_name in [
        "__init__.py",
        "bridge.py",
        "catalog.py",
        "commands.py",
        "schemas.py",
    ]:
        source = (plugin_dir / module_name).read_text(encoding="utf-8")
        assert "from tool_registry" not in source
        assert "import tool_registry" not in source
