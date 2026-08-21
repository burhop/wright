from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


SCHEMAS = "model_registry.schemas"


def _documents() -> dict[str, dict[str, object]]:
    root = files(SCHEMAS)
    return {
        item.name: json.loads(item.read_text(encoding="utf-8"))
        for item in root.iterdir()
        if item.name.endswith(".json")
    }


def _registry(documents: dict[str, dict[str, object]]) -> Registry:
    registry = Registry()
    for document in documents.values():
        registry = registry.with_resource(
            str(document["$id"]), Resource.from_contents(document)
        )
    return registry


def _fixture(name: str) -> dict[str, object]:
    path = Path(__file__).parent / "fixtures" / "contracts" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_public_contracts_are_valid_draft_2020_12_schemas() -> None:
    for document in _documents().values():
        Draft202012Validator.check_schema(document)


def test_valid_package_resolves_and_validates_nested_test_vector() -> None:
    documents = _documents()
    validator = Draft202012Validator(
        documents["model-package.schema.json"], registry=_registry(documents)
    )
    validator.validate(_fixture("valid-model-package.json"))


def test_contracts_reject_unknown_versions_and_extra_fields() -> None:
    documents = _documents()
    vector = _fixture("invalid-extra-field.json")
    vector_validator = Draft202012Validator(
        documents["model-test-vector.schema.json"], registry=_registry(documents)
    )
    with pytest.raises(Exception):
        vector_validator.validate(vector)

    package = _fixture("valid-model-package.json")
    package["schema_version"] = "2.0"
    package_validator = Draft202012Validator(
        documents["model-package.schema.json"], registry=_registry(documents)
    )
    with pytest.raises(Exception):
        package_validator.validate(package)


@pytest.mark.parametrize(
    ("kind", "expected", "valid"),
    (
        ("exact", {"kind": "exact", "value": 1}, True),
        ("exact", {"kind": "exact"}, False),
        ("range", {"kind": "range", "minimum": 0, "maximum": 1}, True),
        ("range", {"kind": "range", "value": 1}, False),
        (
            "relative_tolerance",
            {"kind": "relative_tolerance", "value": 1, "relative_tolerance": 0.1},
            True,
        ),
    ),
)
def test_expected_predicates_have_kind_specific_fields(
    kind: str, expected: dict[str, object], valid: bool
) -> None:
    del kind
    documents = _documents()
    vector = _fixture("invalid-extra-field.json")
    vector.pop("unexpected")
    vector["expected"] = expected
    validator = Draft202012Validator(documents["model-test-vector.schema.json"])
    assert validator.is_valid(vector) is valid
