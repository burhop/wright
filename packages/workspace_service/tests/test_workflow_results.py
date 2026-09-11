"""Contract tests, not live cloud/CAD verification."""

import asyncio
import hashlib
import pytest
from workspace_service.workflow_results import (
    EngineeringResult,
    Representation,
    Provenance,
    InputRequirement,
    ResultCollection,
    validate_result_input,
)
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
    HTML,
)


def cloud_model():
    return EngineeringResult(
        "run:cad:model",
        "cad_model",
        "Bracket",
        (
            Representation(
                "cloud_resource",
                "https://cad.example/doc/123",
                provider_id="cloud-cad",
                resource_id="123",
                revision="v7",
                durability="persistent",
            ),
        ),
        Provenance("run", "cad", "model"),
    )


def test_persistent_cloud_model_needs_no_native_file():
    model = cloud_model()
    assert model.persistent
    (selected,) = validate_result_input(
        model,
        InputRequirement(("cad_model",), provider_id="cloud-cad", persistent=True),
    )
    assert selected.resource_id == "123" and selected.revision == "v7"
    assert model.to_dict()["schema_version"] == 1


def test_incompatible_application_and_format_require_explicit_export():
    with pytest.raises(ValueError, match="Configure an export.*step"):
        validate_result_input(
            cloud_model(), InputRequirement(("cad_model",), formats=("step",))
        )
    with pytest.raises(ValueError, match="consuming application"):
        validate_result_input(
            cloud_model(), InputRequirement(("cad_model",), provider_id="other-cad")
        )


def test_collection_is_not_silently_changed_to_single_item():
    with pytest.raises(ValueError, match="collection"):
        validate_result_input(
            ResultCollection((cloud_model(),)), InputRequirement(("cad_model",))
        )
    with pytest.raises(ValueError, match="collection"):
        validate_result_input(
            cloud_model(), InputRequirement(("cad_model",), collection=True)
        )
    assert (
        len(
            validate_result_input(
                ResultCollection((cloud_model(),)),
                InputRequirement(("cad_model",), collection=True),
            )
        )
        == 1
    )


def test_temporary_model_does_not_satisfy_persistent_input():
    model = EngineeringResult(
        "r",
        "cad_model",
        "Unsaved part",
        (
            Representation(
                "application_document",
                "doc1",
                provider_id="cad",
                resource_id="doc1",
                durability="session",
            ),
        ),
        Provenance("run", "task", "model"),
    )
    assert not model.persistent
    with pytest.raises(ValueError, match="compatible representation"):
        validate_result_input(model, InputRequirement(("cad_model",), persistent=True))


@pytest.mark.parametrize("path", ["../secret", "/absolute", "C:/private", "..\\secret"])
def test_workspace_representation_cannot_escape_workspace(path):
    with pytest.raises(ValueError, match="relative"):
        Representation("workspace_file", path)


def test_prompt_run_publishes_one_result_with_response_and_saved_file(tmp_path):
    async def generate(*args):
        return HTML

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=compile_prompt_workflow(source(task())),
            input_values={},
            response_generator=generate,
        )
    )
    assert len(result["results"]) == 1
    value, file = result["results"][0]["representations"]
    assert value["kind"] == "value" and file["location"] == "report.html"
    assert (
        file["sha256"]
        == hashlib.sha256((tmp_path / "report.html").read_bytes()).hexdigest()
    )
    assert result["results"][0]["provenance"]["run_id"] == result["run_id"]
