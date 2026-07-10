from __future__ import annotations

import ast
from pathlib import Path

from api.composition import workspace_service


def test_workspace_service_is_composition_owned_singleton():
    assert workspace_service() is workspace_service()


def test_workspace_router_has_no_infrastructure_construction_or_global_selection():
    path = Path("apps/api/src/api/routers/workspace.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    constructed = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert constructed.isdisjoint(
        {"WorkspaceManager", "WorkspaceRepository", "BoundedExecutor", "subprocess"}
    )
