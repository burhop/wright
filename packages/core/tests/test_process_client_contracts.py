"""The public client is generated from core, not a private UI schema copy."""

import runpy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "packages/process_client/scripts/generate_contracts.py"


def test_public_client_contract_resources_are_current():
    generator = runpy.run_path(str(GENERATOR))
    for filename, expected in generator["generate"]().items():
        actual = ROOT / "packages/process_client/src" / filename
        assert actual.read_text(encoding="utf-8") == expected


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "allOf": []},
        {"type": "string", "format": "date-time"},
        {"type": "array", "items": {"type": "integer", "multipleOf": 2}},
        {"type": "object", "properties": {"value": {"not": {}}}},
        {"$ref": "#/$defs/ProcessRef", "minimum": 1},
    ],
)
def test_future_schema_features_require_a_validator_extension(schema):
    generator = runpy.run_path(str(GENERATOR))
    with pytest.raises(ValueError):
        generator["check_keywords"](schema)


def test_only_local_owning_references_can_generate():
    generator = runpy.run_path(str(GENERATOR))
    with pytest.raises(ValueError):
        generator["shape"]({"$ref": "https://example.invalid/schema"})


def test_api_union_bindings_keep_the_required_discriminator():
    generator = runpy.run_path(str(GENERATOR))
    content = generator["generate"]()["contracts.generated.ts"]
    assert "ValueBinding & { readonly kind: 'value' }" in content
    assert "FileBinding & { readonly kind: 'file' }" in content
    assert "OptionBinding & { readonly kind: 'option' }" in content
