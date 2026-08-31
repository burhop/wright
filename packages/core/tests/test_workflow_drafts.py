from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from core.workflow_drafts import WorkflowDraft, canonical_sha256


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
