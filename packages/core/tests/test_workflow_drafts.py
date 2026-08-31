from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from core.workflow_drafts import WorkflowDraft, canonical_sha256
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
