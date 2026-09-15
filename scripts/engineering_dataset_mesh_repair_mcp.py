"""Confined MCP wrapper for the fixed printed-part Blender repair operation."""

from __future__ import annotations

import json
import os
from pathlib import Path

from blender_mcp.safe_mode import validate_code
from blender_mcp.server import BlenderConnection
from mcp.server.fastmcp import FastMCP

import engineering_dataset_mesh_repair as operation


WORKSPACE = Path(os.environ["WRIGHT_PRINT_WORKSPACE"]).resolve()
BLENDER_HOST = os.environ.get("BLENDER_HOST", "127.0.0.1")
BLENDER_PORT = int(os.environ["BLENDER_PORT"])
SERVER = FastMCP("wright-printed-part-mesh-repair")


def _path(relative: str) -> Path:
    value = Path(relative)
    if value.is_absolute():
        raise ValueError("A workspace-relative path is required")
    result = (WORKSPACE / value).resolve()
    if result == WORKSPACE or not result.is_relative_to(WORKSPACE):
        raise ValueError("Mesh-repair path escapes the campaign workspace")
    return result


def _configuration(configuration_document: str, operation_source_document: str) -> Path:
    configuration = _path(configuration_document)
    source = _path(operation_source_document)
    if not configuration.is_file() or not source.is_file():
        raise ValueError("Staged mesh-repair configuration and operation source are required")
    if configuration.parent != source.parent or configuration.parent.name != "inputs":
        raise ValueError("Mesh-repair inputs must belong to one exact campaign attempt")
    if source.read_bytes() != Path(operation.__file__).read_bytes():
        raise ValueError("Staged mesh-repair operation differs from the executing fixed source")
    values = json.loads(configuration.read_text(encoding="utf-8"))
    if Path(values.get("workspace_root", "")).resolve() != WORKSPACE:
        raise ValueError("Mesh-repair configuration names a different workspace")
    attempt = configuration.parent.parent
    expected = {
        "source": attempt / "artifacts" / "source_mesh.stl",
        "repaired": attempt / "artifacts" / "repaired_mesh.stl",
        "preview": attempt / "artifacts" / "mesh-preview.png",
    }
    for key, expected_path in expected.items():
        if Path(values.get(key, "")).resolve() != expected_path:
            raise ValueError(f"Mesh-repair {key} must stay in this exact campaign attempt")
    if not expected["source"].is_file():
        raise ValueError("The same-attempt source mesh is missing")
    if expected["repaired"].exists() or expected["preview"].exists():
        raise ValueError("Mesh-repair outputs already exist; reconcile instead of replaying")
    return configuration


@SERVER.tool()
def repair_model_file(configuration_document: str, operation_source_document: str) -> dict:
    """Repair and inspect the same-attempt source STL in the owned Blender session."""

    configuration = _configuration(configuration_document, operation_source_document)
    connection = BlenderConnection(host=BLENDER_HOST, port=BLENDER_PORT)
    try:
        return operation.run(
            configuration,
            blender_connection=connection,
            validate_code=validate_code,
        )
    finally:
        connection.disconnect()


if __name__ == "__main__":
    SERVER.run(transport="stdio")
