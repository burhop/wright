from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_registry.models import (
    ModelPackage,
    ModelRegistryError,
    canonical_digest,
    canonical_json,
)


def package_document() -> dict[str, object]:
    path = Path(__file__).parent / "fixtures" / "contracts" / "valid-model-package.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_package_is_immutable_canonical_and_digest_stable() -> None:
    first = ModelPackage.model_validate(package_document())
    second = ModelPackage.model_validate(
        json.loads(json.dumps(package_document(), sort_keys=True))
    )
    assert first == second
    assert first.digest == second.digest == canonical_digest(first.canonical())
    assert canonical_json(first.canonical()) == canonical_json(second.canonical())
    with pytest.raises(Exception):
        first.display_name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutator", "code"),
    (
        (lambda value: value.update(schema_version="2.0"), "schema_unsupported"),
        (
            lambda value: value["variants"].append(value["variants"][0]),
            "variant_duplicate",
        ),
        (
            lambda value: value["tasks"].append(value["tasks"][0]),
            "task_duplicate",
        ),
        (
            lambda value: value["limitations"].append(value["limitations"][0]),
            "limitation_duplicate",
        ),
        (
            lambda value: value["variants"][0]["test_vectors"][0].update(
                task_id="missing"
            ),
            "test_task_unknown",
        ),
        (
            lambda value: value["variants"][0]["test_vectors"][0].update(
                limitations_exercised=["missing"]
            ),
            "test_limitation_unknown",
        ),
        (
            lambda value: value["variants"][0]["artifacts"].append(
                value["variants"][0]["artifacts"][0]
            ),
            "artifact_duplicate",
        ),
        (
            lambda value: value["variants"][0]["resources"].update(download_bytes=1),
            "resource_download_too_small",
        ),
    ),
)
def test_package_cross_field_failures_have_stable_codes(mutator, code: str) -> None:
    document = package_document()
    mutator(document)
    with pytest.raises(ModelRegistryError) as raised:
        ModelPackage.model_validate(document)
    assert raised.value.code == code


def test_approved_package_forbids_remote_code_and_acceptance() -> None:
    remote = package_document()
    remote["remote_code_policy"] = "required"
    with pytest.raises(Exception):
        ModelPackage.model_validate(remote)

    terms = package_document()
    terms["license"]["acceptance_required"] = True
    with pytest.raises(ModelRegistryError) as raised:
        ModelPackage.model_validate(terms)
    assert raised.value.code == "license_action_required"


def test_secret_like_material_is_rejected_without_echo() -> None:
    document = package_document()
    document["description"] = "api_key=test-secret-value"
    with pytest.raises(Exception) as raised:
        ModelPackage.model_validate(document)
    assert "synthetic-secret-value" not in str(raised.value)


def test_record_ceiling_rejects_oversized_metadata() -> None:
    document = package_document()
    document["description"] = "x" * 70_000
    with pytest.raises(Exception):
        ModelPackage.model_validate(document)
