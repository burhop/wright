from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from core.workflow_drafts import WorkflowDraft, canonical_sha256
from core.workflow_draft_validation import (
    MAX_WORKFLOW_DRAFT_DIAGNOSTICS,
    WorkflowDraftDiagnostic,
    validate_workflow_draft,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "workflow_drafts"
    / "representative-workflow.json"
)


def candidate(mutator: Callable[[dict[str, Any]], None]) -> WorkflowDraft:
    payload = copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
    mutator(payload)
    payload["semantic_sha256"] = canonical_sha256(payload["semantic"])
    payload["layout_sha256"] = canonical_sha256(payload["layout"])
    return WorkflowDraft.model_validate(payload)


def diagnostic(
    code: str,
    path: str,
    affected: tuple[str, ...],
    explanation: str,
    correction: str,
) -> WorkflowDraftDiagnostic:
    return WorkflowDraftDiagnostic(
        code=code,
        path=path,
        affected_semantic_ids=affected,
        explanation=explanation,
        correction=correction,
    )


@pytest.mark.parametrize(
    ("mutator", "expected"),
    [
        (
            lambda payload: payload["semantic"]["connections"][0].__setitem__(
                "target_port_id", "port.requirements-out"
            ),
            (
                diagnostic(
                    "CONNECTION_TARGET_INVALID",
                    "/semantic/connections/connection.requirements-to-definition/target_port_id",
                    (
                        "connection.requirements-to-definition",
                        "port.requirements-out",
                    ),
                    "The connection target is not an existing input port.",
                    "Choose an existing input port as the target.",
                ),
            ),
        ),
        (
            lambda payload: payload["semantic"]["ports"][1].__setitem__(
                "value_type_id", "type.incompatible"
            ),
            (
                diagnostic(
                    "CONNECTION_VALUE_TYPE_MISMATCH",
                    "/semantic/connections/connection.requirements-to-definition",
                    (
                        "connection.requirements-to-definition",
                        "port.requirements-in",
                        "port.requirements-out",
                    ),
                    "The connected port value types do not match.",
                    "Connect ports with exactly matching value-type identities.",
                ),
            ),
        ),
        (
            lambda payload: payload["semantic"]["connections"].append(
                {
                    **payload["semantic"]["connections"][0],
                    "id": "connection.duplicate",
                }
            ),
            (
                diagnostic(
                    "CONNECTION_ENDPOINT_DUPLICATE",
                    "/semantic/connections",
                    (
                        "connection.duplicate",
                        "connection.requirements-to-definition",
                    ),
                    "More than one connection uses the same source and target.",
                    "Keep one connection for this endpoint pair.",
                ),
            ),
        ),
        (
            lambda payload: payload["semantic"]["feedback_paths"][0].__setitem__(
                "to_block_id", "block.capture-requirements"
            ),
            (
                diagnostic(
                    "FEEDBACK_REVISE_TARGET_MISMATCH",
                    "/semantic/gates/gate.definition-accepted/revise_target_block_id",
                    (
                        "block.capture-requirements",
                        "block.define-product",
                        "feedback.revise-definition",
                        "gate.definition-accepted",
                    ),
                    "The feedback target differs from the gate revise target.",
                    "Use the same block identity for feedback and revise targets.",
                ),
            ),
        ),
    ],
    ids=(
        "output-to-output",
        "incompatible-value-type",
        "duplicate-endpoint",
        "feedback-gate-mismatch",
    ),
)
def test_connection_and_feedback_fixtures_return_exact_stable_diagnostics(
    mutator: Callable[[dict[str, Any]], None],
    expected: tuple[WorkflowDraftDiagnostic, ...],
) -> None:
    assert validate_workflow_draft(candidate(mutator)) == expected


def test_dangling_block_fixture_identifies_every_affected_relationship() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["semantic"]["blocks"].pop(1)

    diagnostics = validate_workflow_draft(candidate(mutate))

    assert [(item.code, item.path, item.affected_semantic_ids) for item in diagnostics] == [
        (
            "ARTIFACT_PRODUCER_RECIPROCITY",
            "/semantic/intended_artifacts/artifact.product-definition/produced_by_block_id",
            ("artifact.product-definition", "block.define-product"),
        ),
        (
            "FEEDBACK_TARGET_MISSING",
            "/semantic/feedback_paths/feedback.revise-definition/to_block_id",
            ("block.define-product", "feedback.revise-definition"),
        ),
        (
            "GATE_TARGET_MISSING",
            "/semantic/gates/gate.definition-accepted/revise_target_block_id",
            ("block.define-product", "gate.definition-accepted"),
        ),
        (
            "LAYOUT_SEMANTIC_ID_INVALID",
            "/layout/positions",
            ("block.define-product",),
        ),
        (
            "PHASE_BLOCK_RECIPROCITY",
            "/semantic/phases/phase.define/block_ids",
            ("block.define-product", "phase.define"),
        ),
        (
            "PORT_BLOCK_RECIPROCITY",
            "/semantic/ports/port.product-definition-out/owner_block_id",
            ("block.define-product", "port.product-definition-out"),
        ),
        (
            "PORT_BLOCK_RECIPROCITY",
            "/semantic/ports/port.requirements-in/owner_block_id",
            ("block.define-product", "port.requirements-in"),
        ),
    ]
    assert all(item.explanation and item.correction for item in diagnostics)


def test_gate_feedback_and_artifact_reciprocity_have_exact_recovery_contracts() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["semantic"]["gates"][0]["feedback_path_id"] = "feedback.missing"
        payload["semantic"]["intended_artifacts"][0]["produced_by_block_id"] = (
            "block.define-product"
        )

    diagnostics = validate_workflow_draft(candidate(mutate))

    assert [(item.code, item.affected_semantic_ids) for item in diagnostics] == [
        (
            "ARTIFACT_BLOCK_RECIPROCITY",
            ("artifact.requirements", "block.capture-requirements"),
        ),
        (
            "ARTIFACT_PRODUCER_RECIPROCITY",
            ("artifact.requirements", "block.define-product"),
        ),
        (
            "FEEDBACK_GATE_RECIPROCITY",
            ("feedback.revise-definition", "gate.definition-accepted"),
        ),
        (
            "GATE_FEEDBACK_RECIPROCITY",
            ("feedback.missing", "gate.definition-accepted"),
        ),
    ]
    assert all(item.path.startswith("/semantic/") for item in diagnostics)
    assert all(item.explanation and item.correction for item in diagnostics)


def test_cross_kind_identity_conflict_is_reported_once_with_stable_identity() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        artifact = copy.deepcopy(payload["semantic"]["intended_artifacts"][0])
        artifact["id"] = "phase.define"
        payload["semantic"]["intended_artifacts"].append(artifact)
        payload["semantic"]["blocks"][0]["intended_artifact_ids"].append(
            "phase.define"
        )

    assert validate_workflow_draft(candidate(mutate)) == (
        diagnostic(
            "SEMANTIC_ID_DUPLICATE",
            "/semantic",
            ("phase.define",),
            "One semantic identity is assigned to more than one concept.",
            "Assign a distinct stable identity to each concept.",
        ),
    )


def test_phase_orders_must_be_distinct_and_contiguous() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["semantic"]["phases"][1]["order"] = 3
        payload["semantic"]["phases"][2]["order"] = 4

    diagnostics = validate_workflow_draft(candidate(mutate))

    assert diagnostics == (
        diagnostic(
            "PHASE_ORDER_NOT_CONTIGUOUS",
            "/semantic/phases/order",
            ("phase.define", "phase.release", "phase.review"),
            "Phase order values are not one contiguous zero-based sequence.",
            "Assign phase orders from zero through the phase count minus one.",
        ),
    )


def test_diagnostic_projection_is_bounded_and_discloses_truncation() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        template = payload["semantic"]["blocks"][0]
        payload["semantic"]["blocks"] = []
        payload["semantic"]["phases"][0]["block_ids"] = []
        payload["semantic"]["phases"] = payload["semantic"]["phases"][:1]
        payload["semantic"]["ports"] = []
        payload["semantic"]["connections"] = []
        payload["semantic"]["gates"] = []
        payload["semantic"]["feedback_paths"] = []
        payload["semantic"]["intended_artifacts"] = []
        payload["layout"]["positions"] = []
        for index in range(100):
            block_id = f"block.invalid-{index}"
            payload["semantic"]["blocks"].append(
                {
                    **template,
                    "id": block_id,
                    "phase_id": "phase.missing",
                    "input_port_ids": tuple(
                        f"port.missing-in-{index}-{port}" for port in range(3)
                    ),
                    "output_port_ids": (),
                    "gate_ids": (),
                    "intended_artifact_ids": (),
                }
            )

    diagnostics = validate_workflow_draft(candidate(mutate))

    assert len(diagnostics) == MAX_WORKFLOW_DRAFT_DIAGNOSTICS
    assert diagnostics[-1] == diagnostic(
        "DIAGNOSTICS_TRUNCATED",
        "/",
        (),
        "Additional validation diagnostics were omitted from this bounded response.",
        "Correct the reported issues, then validate the complete draft again.",
    )
