"""Native validator dependencies stay with the selected isolated MCP."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import tomllib


REPOSITORY = Path(__file__).parents[2]
FORBIDDEN_RUNTIME_PACKAGES = {"agentcad", "build123d", "cadquery", "ocp"}


def _dependency_names(path: Path) -> set[str]:
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    values = list(document.get("project", {}).get("dependencies", []))
    for group in document.get("project", {}).get("optional-dependencies", {}).values():
        values.extend(group)
    names = set()
    for value in values:
        name = value.split("[", 1)[0]
        for separator in ("<", ">", "=", "!", "~", ";", " "):
            name = name.split(separator, 1)[0]
        names.add(name.lower().replace("_", "-"))
    return names


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".", 1)[0].lower())
    return names


def test_base_runtime_and_packaged_readers_do_not_embed_selected_mcp_cad_stack():
    dependencies = _dependency_names(REPOSITORY / "pyproject.toml")
    dependencies |= _dependency_names(
        REPOSITORY / "packages/workspace_service/pyproject.toml"
    )
    assert not dependencies.intersection(FORBIDDEN_RUNTIME_PACKAGES)

    for dockerfile in (
        REPOSITORY / "docker/Dockerfile",
        REPOSITORY / "docker/Dockerfile.dev",
        REPOSITORY / "docker/Dockerfile.base",
    ):
        active = "\n".join(
            line for line in dockerfile.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ).lower()
        assert not any(package in active for package in FORBIDDEN_RUNTIME_PACKAGES)

    reader_root = (
        REPOSITORY
        / "packages/workspace_service/src/workspace_service/process_validation/readers"
    )
    for reader in (reader_root / "geometry.py", reader_root / "thermal.py"):
        assert not _imports(reader).intersection(FORBIDDEN_RUNTIME_PACKAGES)


def test_engineering_demo_declares_native_stack_on_isolated_selected_mcp():
    script = REPOSITORY / "scripts/run_process_validation_engineering.py"
    spec = importlib.util.spec_from_file_location("engineering_validation_runner", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    server = Path("isolated/engineering_validation_mcp.py")
    command = module._native_command(server)
    assert command[:6] == [
        "uv",
        "run",
        "--no-project",
        "--isolated",
        "--python",
        "3.12.11",
    ]
    assert "agentcad[mcp]==0.6.0" in command
    assert "build123d==0.10.0" in command
    assert command[-3:] == ["python", "-B", str(server)]

    mcp_source = REPOSITORY / (
        "tests/datasets/process-validation/processes/engineering_validation_mcp.py"
    )
    assert {"build123d", "mcp"} <= _imports(mcp_source)
