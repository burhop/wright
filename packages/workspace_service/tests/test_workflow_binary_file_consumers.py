"""Only declared file consumers accept opaque root inputs; documents stay strict."""

from types import SimpleNamespace

import pytest

from workspace_service.workflow_references import (
    WorkflowReference,
    allows_binary_file_reference,
)
from workspace_service.process_interfaces.inputs import input_file_reference


def step(**overrides):
    return SimpleNamespace(
        **{
            "application_from": None,
            "prompt_from": None,
            "arguments_from": None,
            "argument_sources": {},
            "references": (),
            "file_dependencies": {},
            **overrides,
        }
    )


@pytest.mark.parametrize(
    "consumer",
    [
        step(application_from="mesh.file"),
        step(
            references=(("actual_source", "mesh.file"),),
            file_dependencies={"mesh.file": "inputs/part.stl"},
        ),
    ],
)
def test_declared_file_consumers_allow_opaque_inputs(consumer):
    assert allows_binary_file_reference([consumer], {"mesh.file"})
    reference = input_file_reference(
        SimpleNamespace(steps=[consumer]),
        {"outputs": [{"key": "file", "kind": "workspace_file"}]},
        "mesh",
        "inputs/part.stl",
        b"\xff\0\x80",
    )
    assert isinstance(reference, WorkflowReference)


@pytest.mark.parametrize(
    "document",
    [
        step(prompt_from="mesh.file"),
        step(arguments_from="mesh.file"),
        step(argument_sources={"query": "mesh.file"}),
        step(references=(("document", "mesh.file"),)),
    ],
)
def test_mixed_file_and_document_consumers_remain_strict(document):
    binary = step(
        references=(("source", "mesh.file"),),
        file_dependencies={"mesh.file": "inputs/part.stl"},
    )
    assert not allows_binary_file_reference([binary, document], {"mesh.file"})
    with pytest.raises((ValueError, UnicodeError)):
        input_file_reference(
            SimpleNamespace(steps=[binary, document]),
            {"outputs": [{"key": "file", "kind": "workspace_file"}]},
            "mesh",
            "inputs/part.stl",
            b"\xff\0\x80",
        )


def test_unconsumed_input_or_unrelated_file_dependency_does_not_allow_binary():
    assert not allows_binary_file_reference([], {"mesh.file"})
    assert not allows_binary_file_reference(
        [
            step(
                references=(("document", "mesh.file"),),
                file_dependencies={"other_port": "inputs/other.stl"},
            )
        ],
        {"mesh.file"},
    )


def test_duplicate_reference_is_not_assumed_to_be_only_a_file_consumer():
    mixed = step(
        references=(("source", "mesh.file"), ("document", "mesh.file")),
        file_dependencies={"mesh.file": "inputs/part.stl"},
    )
    assert not allows_binary_file_reference([mixed], {"mesh.file"})
