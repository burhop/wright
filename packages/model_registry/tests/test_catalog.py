from __future__ import annotations

import copy
from importlib.resources import files

import pytest

from model_registry.catalog import (
    ModelCatalog,
    ModelCatalogError,
    catalog_document,
    validate_catalog_document,
)


def test_bundled_catalog_resource_has_stable_valid_identity() -> None:
    resource = files("model_registry").joinpath("catalog/catalog.yaml")
    assert resource.is_file()
    catalog = ModelCatalog.load_bundled()

    assert catalog.snapshot.snapshot_id == "wright-models-bundled-1"
    assert catalog.snapshot.freshness == "bundled"
    assert len(catalog.snapshot.catalog_digest) == 64
    assert catalog.ids == (
        "blocked-gated-geometry-model",
        "blocked-remote-code-model",
        "incompatible-cuda-mesh-model",
        "keras-io-pointnet",
        "wright-affine-test",
    )
    generated = catalog.get("wright-affine-test")
    assert generated.package is not None
    assert generated.package.digest == generated.manifest_digest
    assert generated.generator is not None
    assert generated.generator["kind"] == "deterministic_recipe"


def test_catalog_digest_is_canonical_and_repeated_loads_match() -> None:
    first = ModelCatalog.load_bundled()
    second = ModelCatalog.load_bundled()

    assert first.snapshot.catalog_digest == second.snapshot.catalog_digest
    assert [item.digest for item in first.entries] == [
        item.digest for item in second.entries
    ]


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda value: value.update({"format_version": 99}), "catalog_version"),
        (
            lambda value: value["entries"].append(copy.deepcopy(value["entries"][0])),
            "catalog_duplicate",
        ),
        (
            lambda value: value["entries"][0].update({"model_id": "../escape"}),
            "catalog_entry_invalid",
        ),
        (
            lambda value: value["entries"][0].update(
                {"package_resource": "../outside.json"}
            ),
            "catalog_resource_invalid",
        ),
    ],
)
def test_catalog_validation_fails_closed(mutate, code: str) -> None:
    document = copy.deepcopy(catalog_document())
    mutate(document)

    with pytest.raises(ModelCatalogError) as caught:
        validate_catalog_document(document)
    assert caught.value.code == code


def test_catalog_contains_no_payload_or_runtime_install_material() -> None:
    keys: set[str] = set()

    def visit(value) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                keys.add(str(key).lower())
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(catalog_document())
    assert not {
        "trust_remote_code",
        "runtime_command",
        "model_weights",
        "api_token",
    }.intersection(keys)
