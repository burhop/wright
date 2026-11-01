"""Adversarial authoring boundaries; these do not qualify a CAD producer."""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, ValidationError
from core.workflow_instructions import WorkflowInstructionAsset
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)
from index_evidence import confined, image_ids

BUNDLE = Path(__file__).resolve().parents[2] / "examples/reverse-engineering-workflow"


def basis():
    return {
        "intended_claim": "envelope",
        "object_revision": "unknown",
        "configuration": "unknown",
        "components": [],
        "evidence_index": "unavailable",
        "requirements_register": "unknown",
        "coordinate_and_scale_basis": "unknown",
        "unresolved_inputs": ["all metric requirements"],
    }


def test_unknowns_are_valid_preparation_but_approval_is_not_an_input():
    schema = json.loads((BUNDLE / "preparation-basis.schema.json").read_text())
    validator = Draft202012Validator(schema)
    validator.validate(basis())
    for change in [
        {"approved": True},
        {"readiness_passed": True},
        {"intended_claim": "print_ready"},
    ]:
        with pytest.raises(ValidationError):
            validator.validate({**basis(), **change})


def test_missing_and_unbounded_inputs_rejected():
    validator = Draft202012Validator(
        json.loads((BUNDLE / "preparation-basis.schema.json").read_text())
    )
    for change in [
        {"object_revision": ""},
        {"components": ["a"] * 101},
        {"evidence_index": "x" * 16001},
    ]:
        with pytest.raises(ValidationError):
            validator.validate({**basis(), **change})
    value = basis()
    del value["requirements_register"]
    with pytest.raises(ValidationError):
        validator.validate(value)


def test_instruction_tamper_rejected_by_existing_contract():
    value = json.loads((BUNDLE / "preparation-instruction.json").read_text())
    WorkflowInstructionAsset.model_validate(value)
    with pytest.raises(ValueError):
        WorkflowInstructionAsset.model_validate(
            {**value, "body": value["body"] + " Changed policy."}
        )


def test_saved_source_uses_real_authoring_and_compiler_validation():
    source = (BUNDLE / "preparation.workflow.wflow").read_text(encoding="utf-8")
    validate_workspace_authoring_shape(source)
    compile_prompt_workflow(source)


@pytest.mark.parametrize(
    "name",
    ["../escape.png", "D:/outside.png", "C:relative.png", "//server/share/file.png"],
)
def test_reference_index_cannot_escape_local_asset_root(tmp_path, name):
    with pytest.raises(ValueError):
        confined(tmp_path, name)


def test_many_component_links_preserve_only_explicit_image_ids():
    assert image_ids("imagesI01-I03,I07; event 15:09; unknown flank") == [
        "I01",
        "I02",
        "I03",
        "I07",
    ]
    assert image_ids("no photographic evidence; patent paragraph 123") == []
    with pytest.raises(ValueError):
        image_ids("I08-I01")
