from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.workflow_definitions import (
    canonical_definition_bytes,
    promote_recovery_workflow_definition,
)
from core.workflow_layouts import (
    WorkflowLayout,
    canonical_layout_sha256,
    decode_workflow_layout,
    promote_recovery_workflow_layout,
    rollback_recovery_workflow_layout,
    validate_workflow_layout_subject,
)


ROOT = Path(__file__).parents[3]
DEFINITION_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)
LAYOUT_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.layout.json"
)


def load_definition():
    return promote_recovery_workflow_definition(
        DEFINITION_FIXTURE.read_bytes()
    ).definition


def load_promotion():
    return promote_recovery_workflow_layout(
        LAYOUT_FIXTURE.read_bytes(), load_definition()
    )


def test_recovery_layout_promotes_to_stable_and_rolls_back_exactly() -> None:
    source = LAYOUT_FIXTURE.read_bytes()
    promotion = promote_recovery_workflow_layout(source, load_definition())

    assert promotion.layout.schema_version == "1.0.0"
    assert promotion.layout.layout_revision == 1
    assert promotion.layout_sha256 == canonical_layout_sha256(promotion.layout)
    assert promotion.source_envelope_sha256 != promotion.layout_sha256
    assert rollback_recovery_workflow_layout(promotion, promotion.layout) == source


def test_layout_subject_validation_and_edits_preserve_definition_bytes() -> None:
    definition = load_definition()
    before = canonical_definition_bytes(definition)
    payload = load_promotion().layout.model_dump(mode="json")
    payload["layout_revision"] = 2
    payload["positions"]["block.capture-brief"] = {"x": 640, "y": 220}
    changed = WorkflowLayout.model_validate(payload)

    validate_workflow_layout_subject(definition, changed)

    assert canonical_definition_bytes(definition) == before
    assert changed.positions["block.capture-brief"].x == 640


def test_unknown_layout_version_is_preserved_without_rewrite() -> None:
    payload = json.loads(LAYOUT_FIXTURE.read_text(encoding="utf-8"))
    payload["schema_version"] = "99.0.0"
    original = json.dumps(payload, separators=(",", ":")).encode()

    result = decode_workflow_layout(original)

    assert result.layout is None
    assert result.original == original
    assert result.diagnostics[0].code == "WFR-LAYOUT-VERSION-UNSUPPORTED"


def test_recovery_promotion_rejects_unknown_semantic_identity() -> None:
    payload = json.loads(LAYOUT_FIXTURE.read_text(encoding="utf-8"))
    payload["positions"]["block.not-in-definition"] = {"x": 1, "y": 2}

    with pytest.raises(ValueError, match="WFR-LAYOUT-IDENTITY-UNKNOWN"):
        promote_recovery_workflow_layout(
            json.dumps(payload).encode(), load_definition()
        )


def test_layout_rollback_refuses_a_changed_target() -> None:
    promotion = load_promotion()
    payload = copy.deepcopy(promotion.layout.model_dump(mode="json"))
    payload["viewport"]["zoom"] = 1.1
    changed = WorkflowLayout.model_validate(payload)

    with pytest.raises(ValueError, match="target digest"):
        rollback_recovery_workflow_layout(promotion, changed)
