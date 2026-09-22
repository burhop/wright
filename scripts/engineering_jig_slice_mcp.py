"""Confined MCP wrapper for additive drill-jig preparation.

The operation accepts only an immutable configuration and source staged in one
campaign attempt.  It can slice the attempt's generated jig STL, but it cannot
select an executable/profile/output destination or connect to a printer.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

import engineering_dataset_slice as operation


WORKSPACE = Path(os.environ["WRIGHT_JIG_WORKSPACE"]).resolve()
SERVER = FastMCP("wright-drill-jig-bambu-slicer")


def _path(relative: str) -> Path:
    value = Path(relative)
    if value.is_absolute():
        raise ValueError("A workspace-relative path is required")
    result = (WORKSPACE / value).resolve()
    if result == WORKSPACE or not result.is_relative_to(WORKSPACE):
        raise ValueError("Jig slicer path escapes the campaign workspace")
    return result


def _configuration(configuration_document: str, operation_source_document: str) -> Path:
    configuration = _path(configuration_document)
    source = _path(operation_source_document)
    if not configuration.is_file() or not source.is_file():
        raise ValueError("Staged slicer configuration and operation source are required")
    if configuration.parent != source.parent or configuration.parent.name != "inputs":
        raise ValueError("Jig slicer inputs must belong to one exact campaign attempt")
    if source.read_bytes() != Path(operation.__file__).read_bytes():
        raise ValueError("Staged slicer operation differs from the executing fixed source")
    values = json.loads(configuration.read_text(encoding="utf-8"))
    if Path(values.get("workspace_root", "")).resolve() != WORKSPACE:
        raise ValueError("Jig slicer configuration names a different workspace")
    attempt = configuration.parent.parent
    jig = _path(values.get("source", ""))
    output = _path(values.get("output_root", ""))
    if jig != attempt / "artifacts" / "jig.stl":
        raise ValueError("Jig slicer source must be this attempt's generated jig.stl")
    if output != attempt / "artifacts" / "additive-manufacturing":
        raise ValueError("Jig slicer output must use this attempt's additive package directory")
    return configuration


@SERVER.tool()
def slice_jig_file(configuration_document: str, operation_source_document: str) -> dict:
    """Slice this attempt's jig STL with the pinned local Bambu profile; never print it."""

    return operation.run(_configuration(configuration_document, operation_source_document))


if __name__ == "__main__":
    SERVER.run(transport="stdio")

