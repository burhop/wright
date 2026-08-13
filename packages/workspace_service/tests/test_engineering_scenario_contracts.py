from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    contract_document,
    fixture_documents,
)
from workspace_service.engineering_scenario_artifacts import (
    artifact_document,
    normalize_artifact,
)
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)


def test_public_scenario_contracts_are_valid_draft_2020_12() -> None:
    for name in (
        "scenario-manifest.schema.json",
        "artifact-envelope.schema.json",
        "assertion-result.schema.json",
    ):
        Draft202012Validator.check_schema(contract_document(name))


def test_public_scenario_contracts_match_the_reviewed_specification() -> None:
    root = Path(__file__).resolve().parents[3]
    public = (
        root
        / "packages"
        / "workspace_service"
        / "src"
        / "workspace_service"
        / "engineering_scenario_catalog"
        / "contracts"
    )
    specification = root / "specs" / "070-engineering-scenario-harness" / "contracts"
    for name in (
        "scenario-manifest.schema.json",
        "artifact-envelope.schema.json",
        "assertion-result.schema.json",
    ):
        assert (public / name).read_bytes() == (specification / name).read_bytes()


def test_packaged_manifests_validate_against_public_contract() -> None:
    validator = Draft202012Validator(contract_document("scenario-manifest.schema.json"))

    for entry in EngineeringScenarioCatalog().list():
        manifest = EngineeringScenarioCatalog().get(entry.scenario_id)
        assert list(validator.iter_errors(manifest.document)) == []


def test_packaged_artifacts_and_assertion_examples_validate_public_contracts() -> None:
    artifact_validator = Draft202012Validator(
        contract_document("artifact-envelope.schema.json")
    )
    assertion_validator = Draft202012Validator(
        contract_document("assertion-result.schema.json")
    )
    catalog = EngineeringScenarioCatalog()
    for entry in catalog.list():
        manifest = catalog.get(entry.scenario_id)
        artifacts = {
            artifact.artifact_id: artifact
            for artifact in (
                normalize_artifact(value)
                for value in fixture_documents(entry.scenario_id, run_id="contract-run")
            )
        }
        for artifact in artifacts.values():
            assert (
                list(artifact_validator.iter_errors(artifact_document(artifact))) == []
            )
        results = EngineeringAssertionRegistry().evaluate_manifest(
            manifest.document["assertions"], artifacts
        )
        for result in results:
            assert list(assertion_validator.iter_errors(result.canonical())) == []


def test_artifact_contract_requires_exactly_one_storage_form() -> None:
    schema = contract_document("artifact-envelope.schema.json")
    value = {
        "schema_version": "1.0",
        "artifact_id": "mesh",
        "domain": "cad",
        "kind": "mesh",
        "source_schema": {
            "name": "mesh",
            "version": "1",
            "media_type": "application/json",
        },
        "producer": {
            "run_id": "run",
            "node_id": "node",
            "call_id": "call",
            "capability": "cad__mesh",
        },
        "upstream_digests": [],
        "content_digest": "a" * 64,
        "validation_state": "valid",
        "content": {},
    }
    validator = Draft202012Validator(schema)
    assert list(validator.iter_errors(value)) == []
    both = deepcopy(value)
    both["vault_reference"] = {
        "artifact_id": "vault-1",
        "media_type": "application/json",
        "digest": "a" * 64,
    }
    assert list(validator.iter_errors(both))


def test_public_contract_fixture_matrix_covers_valid_and_invalid_boundaries() -> None:
    fixture_root = Path(__file__).with_name("fixtures") / "engineering_scenarios"
    valid = json.loads((fixture_root / "contract-valid.json").read_text("utf-8"))
    invalid = json.loads((fixture_root / "contract-invalid.json").read_text("utf-8"))

    for contract_name, documents in valid.items():
        validator = Draft202012Validator(contract_document(contract_name))
        for document in documents:
            assert list(validator.iter_errors(document)) == []

    covered_cases = set()
    for contract_name, cases in invalid.items():
        validator = Draft202012Validator(contract_document(contract_name))
        for case in cases:
            covered_cases.add(case["case"])
            assert list(validator.iter_errors(case["document"]))

    assert covered_cases == {
        "unsupported_contract_version",
        "artifact_id_exceeds_bound",
        "forbidden_extra_field",
        "content_and_vault_are_mutually_exclusive",
        "failed_assertion_requires_message_and_recovery",
    }
