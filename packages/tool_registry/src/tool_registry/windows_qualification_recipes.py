from __future__ import annotations

import hashlib
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .catalog_signing import canonical_json
from .windows_qualification_models import (
    WINDOWS_MCP_ALLOWLIST,
    WindowsQualificationRecipe,
)


class QualificationDenied(ValueError):
    def __init__(self, server_id: str) -> None:
        self.server_id = server_id
        self.code = "windows_qualification_not_allowlisted"
        super().__init__(
            f"MCP server '{server_id}' is not in the Windows qualification allowlist."
        )


class QualificationRecipeError(ValueError):
    pass


def assert_allowlisted(server_id: str) -> None:
    if server_id not in WINDOWS_MCP_ALLOWLIST:
        raise QualificationDenied(server_id)


def _catalog_path(name: str) -> Path:
    return Path(str(files("tool_registry").joinpath("catalog", name)))


def load_windows_qualification_recipes(
    path: str | Path | None = None,
) -> dict[str, WindowsQualificationRecipe]:
    recipe_path = (
        Path(path) if path else _catalog_path("windows-qualification-recipes.yaml")
    )
    schema_path = _catalog_path("windows-qualification-recipe.schema.json")
    document = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise QualificationRecipeError("qualification recipe bundle must be a mapping")
    if document.get("schema_version") != "1.0":
        raise QualificationRecipeError(
            "unsupported qualification recipe bundle version"
        )
    ordered = document.get("ordered_server_ids")
    if ordered != list(WINDOWS_MCP_ALLOWLIST):
        raise QualificationRecipeError(
            "qualification recipe order must exactly match the hard allowlist"
        )
    raw_recipes = document.get("recipes")
    if not isinstance(raw_recipes, list) or len(raw_recipes) != len(
        WINDOWS_MCP_ALLOWLIST
    ):
        raise QualificationRecipeError(
            "exactly seven qualification recipes are required"
        )

    import json

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    parsed: dict[str, WindowsQualificationRecipe] = {}
    for index, raw in enumerate(raw_recipes):
        errors = sorted(validator.iter_errors(raw), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.path) or "recipe"
            raise QualificationRecipeError(f"{location}: {first.message}")
        recipe = WindowsQualificationRecipe.model_validate(raw)
        expected = WINDOWS_MCP_ALLOWLIST[index]
        if recipe.server_id != expected:
            raise QualificationRecipeError(
                f"recipe {index} must be '{expected}', not '{recipe.server_id}'"
            )
        parsed[recipe.server_id] = recipe
    return parsed


def get_windows_qualification_recipe(server_id: str) -> WindowsQualificationRecipe:
    assert_allowlisted(server_id)
    return load_windows_qualification_recipes()[server_id]


def recipe_digest(recipe: WindowsQualificationRecipe | dict[str, Any]) -> str:
    payload = (
        recipe.model_dump(mode="json") if hasattr(recipe, "model_dump") else recipe
    )
    return hashlib.sha256(canonical_json(payload)).hexdigest()
