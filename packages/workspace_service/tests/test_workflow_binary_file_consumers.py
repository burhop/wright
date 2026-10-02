"""Only declared file consumers accept opaque root inputs; documents stay strict."""

from types import SimpleNamespace

import pytest

from workspace_service.workflow_references import (
    WorkflowReference,
    allows_binary_file_reference,
)
from workspace_service.process_interfaces.inputs import input_file_reference
from workspace_service.workflow_execution_continuation import approval_input_files


def step(**overrides):
    return SimpleNamespace(
        **{
            "application_from": None,
            "prompt_from": None,
            "arguments_from": None,
            "argument_sources": {},
            "references": (),
            "file_dependencies": {},
            "external_action": None,
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


@pytest.mark.parametrize(
    "kind",
    [
        "local_review",
        "printer_transfer",
        "supplier_upload_preview",
        "cart_quote_handoff",
    ],
)
def test_fixed_artifact_approval_accepts_binary_reference_without_text_interpretation(
    kind,
):
    approval = step(
        references=(("package", "mesh.file"),),
        external_action={
            "action_kind": kind,
            "settings": {"include_supplied_files": True},
        },
    )
    assert allows_binary_file_reference([approval], {"mesh.file"})
    reference = input_file_reference(
        SimpleNamespace(steps=[approval]),
        {"outputs": [{"key": "file", "kind": "workspace_file"}]},
        "mesh",
        "inputs/package.3mf",
        b"PK\xff\0\x80",
    )
    assert reference.file_only and not reference.text
    assert reference.size_bytes == 5
    assert not allows_binary_file_reference(
        [approval, step(references=(("document", "mesh.file"),))], {"mesh.file"}
    )


@pytest.mark.parametrize("kind", ["mcp-operation", "unknown"])
def test_approval_label_does_not_make_mcp_or_unknown_argument_consumers_binary(kind):
    approval = step(
        references=(("argument", "mesh.file"),), external_action={"action_kind": kind}
    )
    assert not allows_binary_file_reference([approval], {"mesh.file"})


def test_artifact_approval_never_overrides_explicit_text_or_argument_use():
    for overrides in (
        {"prompt_from": "mesh.file"},
        {"arguments_from": "mesh.file"},
        {"argument_sources": {"data": "mesh.file"}},
        {"references": (("package", "mesh.file"), ("document", "mesh.file"))},
    ):
        approval = step(
            **{
                "references": (("package", "mesh.file"),),
                "external_action": {"action_kind": "supplier_upload_preview"},
                **overrides,
            }
        )
        assert not allows_binary_file_reference([approval], {"mesh.file"})


@pytest.mark.parametrize("option", [None, False, 1, "true"])
def test_supplied_handoff_artifacts_require_exact_explicit_opt_in(option):
    approval = step(
        references=(("package", "mesh.file"),),
        external_action={
            "action_kind": "supplier_upload_preview",
            "settings": {"include_supplied_files": option},
        },
    )
    supplied = {
        "mesh": WorkflowReference.from_bytes(
            "inputs/part.bin", b"\xff\0", image=False, allow_binary=True
        )
    }
    assert approval_input_files(approval, supplied) == {}
    assert not allows_binary_file_reference([approval], {"mesh.file"})


def test_opt_in_binds_connected_supplied_files_only_without_changing_provenance():
    approval = step(
        references=(("package", "mesh.file"),),
        external_action={
            "action_kind": "supplier_upload_preview",
            "settings": {"include_supplied_files": True},
        },
    )
    selected = WorkflowReference.from_bytes(
        "inputs/part.bin", b"\xff\0", image=False, allow_binary=True
    )
    unrelated = WorkflowReference.from_bytes(
        "inputs/other.bin", b"\x80\0", image=False, allow_binary=True
    )
    assert approval_input_files(
        approval, {"mesh": selected, "other": unrelated, "text": "not a file"}
    ) == {selected.path: selected.sha256}
