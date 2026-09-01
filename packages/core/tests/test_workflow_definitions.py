from __future__ import annotations

import copy
import json
from pathlib import Path

from core.workflow_definitions import (
    WorkflowCommandBatch,
    WorkflowDefinition,
    accept_workflow_candidate,
    apply_workflow_commands,
    canonical_definition_bytes,
    canonical_definition_sha256,
    decode_workflow_definition,
    project_workflow_definition,
    promote_recovery_workflow_definition,
    promote_workflow_draft,
    rollback_recovery_workflow_definition,
    rollback_workflow_draft,
)
from core.workflow_drafts import WorkflowDraft, canonical_json_bytes


ROOT = Path(__file__).parents[3]
RECOVERY_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)
LEGACY_FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "workflow_drafts"
    / "representative-workflow.json"
)


def load_definition() -> WorkflowDefinition:
    return promote_recovery_workflow_definition(
        RECOVERY_FIXTURE.read_bytes()
    ).definition


def test_approved_definition_digest_and_projection_are_production_stable() -> None:
    promotion = promote_recovery_workflow_definition(RECOVERY_FIXTURE.read_bytes())
    definition = promotion.definition

    assert promotion.source_definition_sha256 == (
        "04cc79dad3b8177e52ab46d0c994d5d48b39f63d7483ccf504eb8d665b902b2d"
    )
    assert definition.schema_version == "2.0.0"
    assert canonical_definition_sha256(definition) == definition.semantic_sha256
    assert promotion.target_definition_sha256 != promotion.source_definition_sha256
    assert rollback_recovery_workflow_definition(promotion, definition) == (
        RECOVERY_FIXTURE.read_bytes()
    )
    assert b'"semantic_sha256"' not in canonical_definition_bytes(definition)

    projection = project_workflow_definition(definition)
    assert projection.workflow_id == definition.workflow_id
    assert projection.revision == definition.revision
    assert len(projection.nodes) == 9
    assert len(projection.edges) == 16
    assert projection.nodes[0].semantic_id == "block.check-manufacturability"
    assert projection.edges[0].semantic_id == "rel.context-to-specification"
    assert "reactflow" not in projection.model_dump_json().lower()


def test_decoder_fails_closed_and_preserves_unknown_version_bytes() -> None:
    payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
    payload["schema_version"] = "99.0.0"
    original = json.dumps(payload, separators=(",", ":")).encode()

    result = decode_workflow_definition(original)

    assert result.definition is None
    assert result.original == original
    assert result.diagnostics[0].code == "WFR-DEFINITION-VERSION-UNSUPPORTED"


def test_recovery_promotion_rejects_a_false_declared_digest() -> None:
    payload = json.loads(RECOVERY_FIXTURE.read_text(encoding="utf-8"))
    payload["semantic_sha256"] = "f" * 64

    try:
        promote_recovery_workflow_definition(json.dumps(payload).encode())
    except ValueError as error:
        assert "digest does not match" in str(error)
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("Promotion accepted a false recovery digest")


def test_command_application_is_atomic_and_accepts_one_revision() -> None:
    current = load_definition()
    batch = WorkflowCommandBatch.model_validate(
        {
            "document_kind": "workflow-command-batch",
            "schema_version": "1.0.0",
            "base_revision": 2,
            "origin": "form",
            "commands": [
                {
                    "kind": "set_block_title",
                    "block_id": "block.generate-geometry",
                    "title": "Generate approved bracket geometry",
                },
                {
                    "kind": "set_block_configuration",
                    "block_id": "block.generate-geometry",
                    "key": "thickness_mm",
                    "value": 8,
                },
            ],
        }
    )

    applied = apply_workflow_commands(current, batch)

    assert applied.ok is True
    assert applied.candidate is not None
    assert current.revision == 2
    assert next(block for block in current.blocks if block.id == "block.generate-geometry").title == "Create bracket CAD model"
    accepted = accept_workflow_candidate(current, applied.candidate)
    assert accepted.revision == 3
    assert accepted.parent_revision == 2
    assert next(block for block in accepted.blocks if block.id == "block.generate-geometry").title == "Generate approved bracket geometry"
    assert accepted.semantic_sha256 == canonical_definition_sha256(accepted)

    stale = apply_workflow_commands(accepted, batch)
    assert stale.ok is False
    assert stale.candidate is None
    assert stale.diagnostics[0].code == "WFR-COMMAND-STALE-BASE"


def test_invalid_multi_command_batch_preserves_exact_current_definition() -> None:
    current = load_definition()
    before = current.model_dump_json()
    batch = WorkflowCommandBatch.model_validate(
        {
            "document_kind": "workflow-command-batch",
            "schema_version": "1.0.0",
            "base_revision": 2,
            "origin": "graph",
            "commands": [
                {
                    "kind": "set_block_title",
                    "block_id": "block.generate-geometry",
                    "title": "This must not leak",
                },
                {
                    "kind": "connect",
                    "relationship": {
                        "id": "rel.invalid",
                        "kind": "data",
                        "source_id": "port.design-specification-in",
                        "target_id": "port.geometry-out",
                        "label": "backwards",
                        "condition": None,
                    },
                },
            ],
        }
    )

    result = apply_workflow_commands(current, batch)

    assert result.ok is False
    assert result.candidate is None
    assert current.model_dump_json() == before
    assert any(item.code == "WFR-RELATIONSHIP-DIRECTION" for item in result.diagnostics)


def test_legacy_promotion_is_exactly_rollbackable_without_layout_authority() -> None:
    legacy = WorkflowDraft.model_validate_json(LEGACY_FIXTURE.read_bytes())

    promotion = promote_workflow_draft(legacy)

    assert promotion.definition.workflow_id == legacy.draft_id
    assert promotion.definition.revision == legacy.revision
    assert promotion.definition.semantic_sha256 == canonical_definition_sha256(
        promotion.definition
    )
    assert not hasattr(promotion.definition, "layout")
    assert promotion.legacy_layout == legacy.layout
    assert promotion.source_envelope == canonical_json_bytes(legacy)
    assert rollback_workflow_draft(promotion, promotion.definition) == legacy

    changed_payload = copy.deepcopy(promotion.definition.model_dump(mode="json"))
    changed_payload["metadata"]["title"] = "Changed after promotion"
    changed_payload["semantic_sha256"] = None
    changed = WorkflowDefinition.model_validate(changed_payload)
    try:
        rollback_workflow_draft(promotion, changed)
    except ValueError as error:
        assert "target digest" in str(error)
    else:  # pragma: no cover - explicit fail-closed assertion
        raise AssertionError("Rollback accepted a changed promoted definition")
