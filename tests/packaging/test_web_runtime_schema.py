"""The Docker frontend must carry the exact authoritative milestone schema."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps/web"
SERVICE = WEB / "src/services/milestone-status.ts"


def runtime_schema() -> dict:
    source = SERVICE.read_text(encoding="utf-8")
    imported = re.search(r'import contract from "([^"]+)";', source)
    assert imported, "Milestone decoder must import its checked schema asset"
    asset = (SERVICE.parent / imported.group(1)).resolve()
    assert asset.is_relative_to(WEB.resolve()), (
        "The standard Docker frontend contains apps/web, without the specs tree"
    )
    return json.loads(asset.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "authority",
    [
        "specs/077-browser-program-status/contracts/program-status-bundle.schema.json",
        "src/wright_engineering/static/program-status/program-status-bundle.schema.json",
    ],
)
def test_frontend_runtime_projection_matches_authoritative_schema(
    authority: str,
) -> None:
    document = json.loads((ROOT / authority).read_text(encoding="utf-8"))
    assert runtime_schema() == document["$defs"]["work"]["properties"]["milestone"], (
        "Regenerate apps/web/src/contracts/native-milestone.schema.json from the "
        "authoritative bundle's $defs.work.properties.milestone"
    )


def test_frontend_runtime_schema_is_valid_without_external_definitions() -> None:
    schema = runtime_schema()
    Draft202012Validator.check_schema(schema)
    assert '"$ref":' not in json.dumps(schema), (
        "A new schema reference requires its dependency to be packaged in apps/web"
    )
