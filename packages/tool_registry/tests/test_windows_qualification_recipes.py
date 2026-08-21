from pathlib import Path

import pytest
from pydantic import ValidationError

from tool_registry.windows_qualification_models import QualificationOperation
from tool_registry.windows_qualification_recipes import (
    QualificationDenied,
    assert_allowlisted,
    load_windows_qualification_recipes,
    recipe_digest,
)


def test_bundled_recipes_are_exactly_ordered_allowlist() -> None:
    recipes = load_windows_qualification_recipes()
    assert list(recipes) == [
        "brep-mcp",
        "solid-edge-mcp-burhop",
        "aps-mcp-server-nodejs",
        "autodesk-product-help-mcp",
        "autodesk-fusion-desktop-mcp",
        "autodesk-fusion-data-mcp",
        "onshape-labs-featurescript-mcp",
    ]
    assert all(len(recipe_digest(recipe)) == 64 for recipe in recipes.values())


@pytest.mark.parametrize(
    "server_id",
    [
        "aps-mcp-server-petr",
        "autodesk-fusion-mcp-python",
        "jarvis-onshape-mcp",
        "onshape-mcp-hedless",
        "autocad-mcp",
    ],
)
def test_non_allowlisted_ids_fail_closed(server_id: str) -> None:
    with pytest.raises(
        QualificationDenied, match="not in the Windows qualification allowlist"
    ):
        assert_allowlisted(server_id)


def test_recipe_file_is_bundled_not_operator_supplied() -> None:
    recipes = load_windows_qualification_recipes()
    assert Path(recipes["brep-mcp"].source.url).name != ""


@pytest.mark.parametrize(
    "key", ["command", "shell", "powershell", "cmd", "script", "environment"]
)
def test_operations_reject_arbitrary_execution_authority(key: str) -> None:
    with pytest.raises(ValidationError, match="forbidden operation parameter"):
        QualificationOperation(
            operation_id="bad",
            stage="mcp_started",
            kind="stdio_mcp",
            parameters={key: "danger"},
        )


def test_only_brep_recipe_may_use_disposable_geometry_probe() -> None:
    recipes = load_windows_qualification_recipes()
    assert recipes["brep-mcp"].safe_probe is not None
    assert recipes["brep-mcp"].safe_probe.mode == "disposable_brep_geometry"
    assert all(
        recipe.safe_probe is None
        or recipe.safe_probe.mode == "read_only"
        or server_id == "brep-mcp"
        for server_id, recipe in recipes.items()
    )
