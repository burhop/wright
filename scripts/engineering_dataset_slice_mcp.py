"""Confined MCP wrapper for the fixed local Bambu slicing operation.

This server accepts two same-attempt workspace documents. It does not accept a
command, executable, profile, output path, or printer destination from the tool
call; those values live in the immutable staged configuration created by the
campaign preparer and are checked again by the fixed operation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

import engineering_dataset_slice as operation


WORKSPACE = Path(os.environ["WRIGHT_PRINT_WORKSPACE"]).resolve()
SERVER = FastMCP("wright-printed-part-bambu-slicer")


def _path(relative: str) -> Path:
    value = Path(relative)
    if value.is_absolute():
        raise ValueError("A workspace-relative path is required")
    result = (WORKSPACE / value).resolve()
    if result == WORKSPACE or not result.is_relative_to(WORKSPACE):
        raise ValueError("Slicer path escapes the campaign workspace")
    return result


def _configuration(configuration_document: str, operation_source_document: str) -> Path:
    configuration = _path(configuration_document)
    source = _path(operation_source_document)
    if not configuration.is_file() or not source.is_file():
        raise ValueError("Staged slicer configuration and operation source are required")
    if configuration.parent != source.parent or configuration.parent.name != "inputs":
        raise ValueError("Slicer inputs must belong to one exact campaign attempt")
    if source.read_bytes() != Path(operation.__file__).read_bytes():
        raise ValueError("Staged slicer operation differs from the executing fixed source")
    values = json.loads(configuration.read_text(encoding="utf-8"))
    if Path(values.get("workspace_root", "")).resolve() != WORKSPACE:
        raise ValueError("Slicer configuration names a different workspace")
    attempt = configuration.parent.parent
    repaired = _path(values.get("source", ""))
    output = _path(values.get("output_root", ""))
    if repaired != attempt / "artifacts" / "repaired_mesh.stl" or output != attempt / "artifacts":
        raise ValueError("Slicer source/output must stay in this exact campaign attempt")
    return configuration


@SERVER.tool()
def slice_model_file(configuration_document: str, operation_source_document: str) -> dict:
    """Slice the same-attempt repaired STL with the fixed pinned P1S PETG operation; never contact a printer."""

    return operation.run(_configuration(configuration_document, operation_source_document))


if __name__ == "__main__":
    SERVER.run(transport="stdio")
