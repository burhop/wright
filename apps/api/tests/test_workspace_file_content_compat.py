from __future__ import annotations

import ast
from pathlib import Path

import pytest

from api.main import app


pytestmark = pytest.mark.workspace_surfaces
ROOT = Path(__file__).resolve().parents[3]


def test_existing_workspace_file_content_contract_is_unchanged() -> None:
    operation = app.openapi()["paths"]["/api/workspace/files/content"]["get"]
    parameters = {
        (parameter["name"], parameter["in"], parameter.get("required", False))
        for parameter in operation["parameters"]
    }
    assert parameters == {
        ("session_id", "query", True),
        ("path", "query", True),
        ("backup_id", "query", False),
    }
    assert "200" in operation["responses"]


def test_file_content_route_remains_a_workspace_service_translation() -> None:
    path = ROOT / "apps/api/src/api/routers/workspace.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    route = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "get_file_content"
    )
    calls = [node for node in ast.walk(route) if isinstance(node, ast.Call)]
    assert any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "read"
        and isinstance(call.func.value, ast.Attribute)
        and call.func.value.attr == "files"
        for call in calls
    )
    assert not any(
        isinstance(call.func, ast.Name) and call.func.id == "open" for call in calls
    )
