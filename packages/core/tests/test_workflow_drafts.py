from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from core.workflow_drafts import WorkflowDraft, canonical_json_bytes, canonical_sha256
from core.workflow_draft_validation import validate_workflow_draft


FIXTURES = Path(__file__).parent / "fixtures" / "workflow_drafts"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def assign_path(document: Any, path: list[str | int], value: Any) -> None:
    target = document
    for segment in path[:-1]:
        target = target[segment]
    target[path[-1]] = value


def test_representative_workflow_is_closed_immutable_and_digest_bound() -> None:
    payload = load_fixture("representative-workflow.json")

    draft = WorkflowDraft.model_validate(payload)

    assert draft.model_dump(mode="json") == payload
    assert canonical_sha256(draft.semantic) == payload["semantic_sha256"]
    assert canonical_sha256(draft.layout) == payload["layout_sha256"]
    with pytest.raises(ValidationError):
        draft.revision = 2


def test_representative_workflow_round_trips_as_exact_canonical_bytes() -> None:
    draft = WorkflowDraft.model_validate(load_fixture("representative-workflow.json"))

    canonical = canonical_json_bytes(draft)
    reopened = WorkflowDraft.model_validate_json(canonical)

    assert reopened == draft
    assert canonical_json_bytes(reopened) == canonical
    assert canonical_sha256(reopened.semantic) == draft.semantic_sha256
    assert canonical_sha256(reopened.layout) == draft.layout_sha256


def test_representative_graph_and_layout_cover_each_semantic_identity_once() -> None:
    draft = WorkflowDraft.model_validate(load_fixture("representative-workflow.json"))
    semantic_ids = [
        *(item.id for item in draft.semantic.phases),
        *(item.id for item in draft.semantic.blocks),
        *(item.id for item in draft.semantic.ports),
        *(item.id for item in draft.semantic.connections),
        *(item.id for item in draft.semantic.gates),
        *(item.id for item in draft.semantic.feedback_paths),
        *(item.id for item in draft.semantic.intended_artifacts),
    ]

    assert len(semantic_ids) == 23
    assert len(set(semantic_ids)) == len(semantic_ids)
    assert {item.semantic_id for item in draft.layout.positions} == {
        item.id for item in draft.semantic.blocks
    }
    assert validate_workflow_draft(draft) == ()
    assert [(phase.id, phase.block_ids) for phase in draft.semantic.phases] == [
        (
            "phase.define",
            ("block.capture-requirements", "block.define-product"),
        ),
        ("phase.review", ("block.review-product-definition",)),
        ("phase.release", ("block.release-product-definition",)),
    ]
    assert [
        (item.source_port_id, item.target_port_id)
        for item in draft.semantic.connections
    ] == [
        ("port.requirements-out", "port.requirements-in"),
        ("port.product-definition-out", "port.product-definition-in"),
        ("port.accepted-definition-out", "port.accepted-definition-in"),
    ]
    gate = draft.semantic.gates[0]
    assert (
        gate.owner_block_id,
        gate.proceed_target_block_id,
        gate.revise_target_block_id,
        gate.feedback_path_id,
    ) == (
        "block.review-product-definition",
        "block.release-product-definition",
        "block.define-product",
        "feedback.revise-definition",
    )
    assert {
        item.id: item.produced_by_block_id
        for item in draft.semantic.intended_artifacts
    } == {
        "artifact.requirements": "block.capture-requirements",
        "artifact.product-definition": "block.define-product",
        "artifact.review-record": "block.review-product-definition",
        "artifact.release-package": "block.release-product-definition",
    }
    assert {
        item.semantic_id: (item.x, item.y) for item in draft.layout.positions
    } == {
        "block.capture-requirements": (0, 0),
        "block.define-product": (320, 0),
        "block.review-product-definition": (680, 0),
        "block.release-product-definition": (1040, 0),
    }


@pytest.mark.parametrize(
    "path",
    [
        ("phases", 0, "block_ids"),
        ("blocks", 1, "input_port_ids"),
        ("blocks", 0, "output_port_ids"),
        ("blocks", 2, "gate_ids"),
        ("blocks", 0, "intended_artifact_ids"),
    ],
)
def test_relationship_identity_lists_reject_duplicates(path) -> None:
    payload = copy.deepcopy(load_fixture("representative-workflow.json"))
    collection, index, field = path
    values = payload["semantic"][collection][index][field]
    values.append(values[0])
    payload["semantic_sha256"] = canonical_sha256(payload["semantic"])

    with pytest.raises(ValidationError, match="unique"):
        WorkflowDraft.model_validate(payload)


@pytest.mark.parametrize(
    "case",
    load_fixture("strict-rejection-cases.json"),
    ids=lambda case: case["name"],
)
def test_strict_contract_rejects_unknown_identity_and_digest_changes(
    case: dict[str, Any],
) -> None:
    payload = copy.deepcopy(load_fixture("representative-workflow.json"))
    assign_path(payload, case["path"], case["value"])

    with pytest.raises(ValidationError):
        WorkflowDraft.model_validate(payload)


def semantic_candidate(mutator) -> WorkflowDraft:
    payload = copy.deepcopy(load_fixture("representative-workflow.json"))
    mutator(payload)
    payload["semantic_sha256"] = canonical_sha256(payload["semantic"])
    payload["layout_sha256"] = canonical_sha256(payload["layout"])
    return WorkflowDraft.model_validate(payload)


def test_representative_workflow_has_no_graph_or_layout_diagnostics() -> None:
    draft = WorkflowDraft.model_validate(load_fixture("representative-workflow.json"))
    assert validate_workflow_draft(draft) == ()


def test_validation_reports_stable_connection_and_layout_diagnostics() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["semantic"]["ports"][1]["value_type_id"] = "type.incompatible"
        duplicate = copy.deepcopy(payload["semantic"]["connections"][0])
        duplicate["id"] = "connection.duplicate"
        payload["semantic"]["connections"].append(duplicate)
        payload["layout"]["positions"].pop()

    diagnostics = validate_workflow_draft(semantic_candidate(mutate))

    assert [item.code for item in diagnostics] == [
        "CONNECTION_ENDPOINT_DUPLICATE",
        "CONNECTION_VALUE_TYPE_MISMATCH",
        "CONNECTION_VALUE_TYPE_MISMATCH",
        "LAYOUT_BLOCK_POSITION_MISSING",
    ]
    assert diagnostics[0].affected_semantic_ids == (
        "connection.duplicate",
        "connection.requirements-to-definition",
    )
    assert diagnostics[-1].affected_semantic_ids == (
        "block.release-product-definition",
    )


def test_validation_reports_global_identity_and_reciprocity_conflicts() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["semantic"]["intended_artifacts"][0]["id"] = "phase.define"
        payload["semantic"]["blocks"][0]["output_port_ids"] = []
        payload["semantic"]["feedback_paths"][0]["to_block_id"] = (
            "block.capture-requirements"
        )

    codes = {item.code for item in validate_workflow_draft(semantic_candidate(mutate))}

    assert {
        "SEMANTIC_ID_DUPLICATE",
        "PORT_BLOCK_RECIPROCITY",
        "FEEDBACK_REVISE_TARGET_MISMATCH",
        "ARTIFACT_BLOCK_RECIPROCITY",
    }.issubset(codes)
