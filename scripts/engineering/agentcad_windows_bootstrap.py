"""Selected Windows AgentCAD startup: load native runtime before MCP reads stdin.

This is a pinned host prerequisite, not a Wright base-runtime modification.
It does not execute a CAD command or open a project during startup.
"""
from __future__ import annotations

import importlib
import importlib.metadata
import json
import runpy
import sys

EXPECTED_VERSIONS = {"agentcad": "0.6.0", "numpy": "2.5.2", "build123d": "0.10.0"}


def main():
    if sys.platform != "win32":
        raise RuntimeError("This selected bootstrap is qualified only on Windows")
    versions = {name: importlib.metadata.version(name) for name in EXPECTED_VERSIONS}
    if versions != EXPECTED_VERSIONS:
        raise RuntimeError("Selected AgentCAD prerequisite versions differ from the qualified pins")
    # Cold NumPy loading can wait on an already-blocked stdin reader on this
    # Windows host. MCP starts that reader, so complete loading beforehand.
    importlib.import_module("numpy")
    # build123d also loads a separate SciPy BLAS extension with the same
    # observed dependency on a blocked stdin reader. Load the whole runtime.
    importlib.import_module("build123d")
    print(json.dumps({"agentcad_bootstrap": "native_runtime_loaded_before_mcp_stdin", "versions": versions}),
          file=sys.stderr, flush=True)
    runpy.run_module("agentcad.mcp", run_name="__main__")


if __name__ == "__main__":
    main()
