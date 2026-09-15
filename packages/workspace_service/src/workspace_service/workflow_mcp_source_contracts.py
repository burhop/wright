"""Bounded source checks declared by exact configured MCP operations."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import re

from .workflow_source_execution import _invalid


AGENTCAD_BUILD123D_010 = "agentcad-build123d-0.10"
SUPPORTED_MCP_SOURCE_CONTRACTS = frozenset({AGENTCAD_BUILD123D_010})
MAX_SOURCE_BYTES = 1_048_576


def _step_filename_patterns(tree: ast.AST) -> set[str]:
    patterns: set[str] = set()
    for node in ast.walk(tree):
        value = None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    parts.append(part.value)
                elif isinstance(part, ast.FormattedValue):
                    parts.append("{}")
            value = "".join(parts)
        if value and ".step" in value.lower():
            patterns.add(re.sub(r"-([ab])\.step$", "-{}.step", value))
    return patterns


def validate_mcp_source_contract(step, workspace_dir, arguments):
    """Reject a declared, known-incompatible source form before MCP dispatch."""
    contract = step.source_contract
    if not contract:
        return
    if contract != AGENTCAD_BUILD123D_010:
        raise _invalid(f"{step.title}: the MCP source contract is unsupported.")
    if step.server_id != "agentcad" or not step.tool_name.endswith("__run"):
        raise _invalid(
            f"{step.title}: the AgentCAD source contract requires its run tool."
        )
    script = arguments.get("script")
    if not isinstance(script, str) or not script:
        raise _invalid(f"{step.title}: the AgentCAD script path is missing.")
    root = Path(workspace_dir).resolve()
    source_path = Path(script)
    cwd = Path(arguments.get("cwd", ""))
    build_dir = arguments.get("build_dir")
    output = arguments.get("output")
    headless = all(arguments.get(key) is False for key in ("preview", "view", "diff"))
    if (
        not source_path.is_absolute()
        or not cwd.is_absolute()
        or not isinstance(build_dir, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", build_dir)
        or not isinstance(output, str)
        or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", output)
        or not headless
    ):
        raise _invalid(
            f"{step.title}: the AgentCAD run arguments violate the bounded headless contract."
        )
    source_path = source_path.resolve()
    cwd = cwd.resolve()
    try:
        source_path.relative_to(root)
        cwd.relative_to(root)
    except ValueError:
        raise _invalid(
            f"{step.title}: the AgentCAD run arguments must stay inside this workspace."
        ) from None
    try:
        if not cwd.is_dir():
            raise OSError("project directory is missing")
        if source_path.stat().st_size > MAX_SOURCE_BYTES:
            raise _invalid(f"{step.title}: the AgentCAD source exceeds 1 MiB.")
        source_bytes = source_path.read_bytes()
        source = source_bytes.decode("utf-8")
        tree = ast.parse(source, filename=str(source_path))
    except (OSError, UnicodeError, SyntaxError):
        raise _invalid(
            f"{step.title}: the AgentCAD source is missing or invalid Python.",
            "Correct the authored source before running the native tool.",
        ) from None
    invalid = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "is_valid"
    ]
    if invalid:
        line = min(node.lineno for node in invalid)
        raise _invalid(
            f"{step.title}: line {line} calls build123d is_valid as a function.",
            "Use the build123d 0.10 boolean property `shape.is_valid`, then run a newly enrolled attempt.",
        )
    abstract_casts = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "cast"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "Shape"
    ]
    if abstract_casts:
        line = min(node.lineno for node in abstract_casts)
        raise _invalid(
            f"{step.title}: line {line} calls abstract build123d Shape.cast.",
            "Use a concrete wrapper such as `Solid.cast(raw_solid)`, or pass a valid raw TopoDS_Shape directly, then run a newly enrolled attempt.",
        )
    patterns = _step_filename_patterns(tree)
    for expected_path in getattr(step, "expected_files", ()):
        expected = Path(expected_path).name
        if not expected.lower().endswith(".step") or "_" not in expected:
            continue
        canonical = re.sub(r"-([ab])\.step$", "-{}.step", expected)
        hyphen_alias = canonical.replace("_", "-")
        if hyphen_alias != canonical and hyphen_alias in patterns:
            raise _invalid(
                f"{step.title}: AgentCAD source uses {hyphen_alias!r} instead of the declared {canonical!r} STEP filename pattern.",
                "Use the exact declared output basename in both export calls and CFD contracts, then run a newly enrolled attempt.",
            )
    return {
        "contract": contract,
        "script": source_path.relative_to(root).as_posix(),
        "script_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "script_bytes": len(source_bytes),
        "project": cwd.relative_to(root).as_posix(),
        "build_dir": build_dir,
        "output": output,
        "headless": True,
        "expected_file_count": len(getattr(step, "expected_files", ())),
    }
