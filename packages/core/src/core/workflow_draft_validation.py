"""Pure deterministic graph and layout validation for workflow drafts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .workflow_drafts import WorkflowDraft


MAX_WORKFLOW_DRAFT_DIAGNOSTICS = 256


@dataclass(frozen=True, slots=True)
class WorkflowDraftDiagnostic:
    code: str
    path: str
    affected_semantic_ids: tuple[str, ...]
    explanation: str
    correction: str


def _diagnostic(
    code: str,
    path: str,
    identities: Iterable[str],
    explanation: str,
    correction: str,
) -> WorkflowDraftDiagnostic:
    return WorkflowDraftDiagnostic(
        code=code,
        path=path,
        affected_semantic_ids=tuple(sorted(set(identities))),
        explanation=explanation,
        correction=correction,
    )


def validate_workflow_draft(
    draft: WorkflowDraft,
) -> tuple[WorkflowDraftDiagnostic, ...]:
    """Return stable content-safe diagnostics without mutating the draft."""

    semantic = draft.semantic
    diagnostics: list[WorkflowDraftDiagnostic] = []
    collections = {
        "phases": semantic.phases,
        "blocks": semantic.blocks,
        "ports": semantic.ports,
        "connections": semantic.connections,
        "gates": semantic.gates,
        "feedback_paths": semantic.feedback_paths,
        "intended_artifacts": semantic.intended_artifacts,
    }
    identities: dict[str, list[str]] = {}
    for collection_name, records in collections.items():
        for record in records:
            identities.setdefault(record.id, []).append(collection_name)
    for identity, owners in identities.items():
        if len(owners) > 1:
            diagnostics.append(
                _diagnostic(
                    "SEMANTIC_ID_DUPLICATE",
                    "/semantic",
                    [identity],
                    "One semantic identity is assigned to more than one concept.",
                    "Assign a distinct stable identity to each concept.",
                )
            )

    phases = {item.id: item for item in semantic.phases}
    blocks = {item.id: item for item in semantic.blocks}
    ports = {item.id: item for item in semantic.ports}
    gates = {item.id: item for item in semantic.gates}
    feedback = {item.id: item for item in semantic.feedback_paths}
    artifacts = {item.id: item for item in semantic.intended_artifacts}

    phase_orders: dict[int, list[str]] = {}
    for phase in semantic.phases:
        phase_orders.setdefault(phase.order, []).append(phase.id)
        for block_id in phase.block_ids:
            block = blocks.get(block_id)
            if block is None or block.phase_id != phase.id:
                diagnostics.append(
                    _diagnostic(
                        "PHASE_BLOCK_RECIPROCITY",
                        f"/semantic/phases/{phase.id}/block_ids",
                        [phase.id, block_id],
                        "The phase and block ownership references do not agree.",
                        "Make the phase block list and block phase identity reciprocal.",
                    )
                )
    for order, phase_ids in phase_orders.items():
        if len(phase_ids) > 1:
            diagnostics.append(
                _diagnostic(
                    "PHASE_ORDER_DUPLICATE",
                    f"/semantic/phases/order/{order}",
                    phase_ids,
                    "More than one phase uses the same order.",
                    "Assign each phase a distinct contiguous order.",
                )
            )
    if sorted(phase_orders) != list(range(len(semantic.phases))):
        diagnostics.append(
            _diagnostic(
                "PHASE_ORDER_NOT_CONTIGUOUS",
                "/semantic/phases/order",
                phases,
                "Phase order values are not one contiguous zero-based sequence.",
                "Assign phase orders from zero through the phase count minus one.",
            )
        )

    for block in semantic.blocks:
        phase = phases.get(block.phase_id)
        if phase is None or block.id not in phase.block_ids:
            diagnostics.append(
                _diagnostic(
                    "BLOCK_PHASE_RECIPROCITY",
                    f"/semantic/blocks/{block.id}/phase_id",
                    [block.id, block.phase_id],
                    "The block phase reference is missing or not reciprocal.",
                    "Reference an existing phase that lists this block exactly once.",
                )
            )
        for direction, port_ids in (
            ("input", block.input_port_ids),
            ("output", block.output_port_ids),
        ):
            for port_id in port_ids:
                port = ports.get(port_id)
                if (
                    port is None
                    or port.owner_block_id != block.id
                    or port.direction != direction
                ):
                    diagnostics.append(
                        _diagnostic(
                            f"BLOCK_{direction.upper()}_PORT_RECIPROCITY",
                            f"/semantic/blocks/{block.id}/{direction}_port_ids",
                            [block.id, port_id],
                            "The block and typed-port references do not agree.",
                            "Make port ownership, direction, and the block port list reciprocal.",
                        )
                    )
        for gate_id in block.gate_ids:
            gate = gates.get(gate_id)
            if gate is None or gate.owner_block_id != block.id:
                diagnostics.append(
                    _diagnostic(
                        "BLOCK_GATE_RECIPROCITY",
                        f"/semantic/blocks/{block.id}/gate_ids",
                        [block.id, gate_id],
                        "The block and gate ownership references do not agree.",
                        "Make gate ownership and the block gate list reciprocal.",
                    )
                )
        for artifact_id in block.intended_artifact_ids:
            artifact = artifacts.get(artifact_id)
            if artifact is None or artifact.produced_by_block_id != block.id:
                diagnostics.append(
                    _diagnostic(
                        "ARTIFACT_BLOCK_RECIPROCITY",
                        f"/semantic/blocks/{block.id}/intended_artifact_ids",
                        [block.id, artifact_id],
                        "The block and intended-artifact references do not agree.",
                        "Make artifact producer and the block artifact list reciprocal.",
                    )
                )

    for port in semantic.ports:
        owner = blocks.get(port.owner_block_id)
        expected = (
            owner.input_port_ids
            if owner is not None and port.direction == "input"
            else owner.output_port_ids
            if owner is not None
            else ()
        )
        if owner is None or port.id not in expected:
            diagnostics.append(
                _diagnostic(
                    "PORT_BLOCK_RECIPROCITY",
                    f"/semantic/ports/{port.id}/owner_block_id",
                    [port.id, port.owner_block_id],
                    "The typed port owner does not list this port in its direction.",
                    "Reference an existing owner and list the port exactly once.",
                )
            )

    endpoints: dict[tuple[str, str], list[str]] = {}
    for connection in semantic.connections:
        endpoints.setdefault(
            (connection.source_port_id, connection.target_port_id), []
        ).append(connection.id)
        source = ports.get(connection.source_port_id)
        target = ports.get(connection.target_port_id)
        if source is None or source.direction != "output":
            diagnostics.append(
                _diagnostic(
                    "CONNECTION_SOURCE_INVALID",
                    f"/semantic/connections/{connection.id}/source_port_id",
                    [connection.id, connection.source_port_id],
                    "The connection source is not an existing output port.",
                    "Choose an existing output port as the source.",
                )
            )
        if target is None or target.direction != "input":
            diagnostics.append(
                _diagnostic(
                    "CONNECTION_TARGET_INVALID",
                    f"/semantic/connections/{connection.id}/target_port_id",
                    [connection.id, connection.target_port_id],
                    "The connection target is not an existing input port.",
                    "Choose an existing input port as the target.",
                )
            )
        if (
            source is not None
            and target is not None
            and (source.value_type_id != target.value_type_id)
        ):
            diagnostics.append(
                _diagnostic(
                    "CONNECTION_VALUE_TYPE_MISMATCH",
                    f"/semantic/connections/{connection.id}",
                    [connection.id, source.id, target.id],
                    "The connected port value types do not match.",
                    "Connect ports with exactly matching value-type identities.",
                )
            )
    for endpoint, connection_ids in endpoints.items():
        if len(connection_ids) > 1:
            diagnostics.append(
                _diagnostic(
                    "CONNECTION_ENDPOINT_DUPLICATE",
                    "/semantic/connections",
                    connection_ids,
                    "More than one connection uses the same source and target.",
                    "Keep one connection for this endpoint pair.",
                )
            )

    for gate in semantic.gates:
        owner = blocks.get(gate.owner_block_id)
        path = feedback.get(gate.feedback_path_id)
        if owner is None or gate.id not in owner.gate_ids:
            diagnostics.append(
                _diagnostic(
                    "GATE_BLOCK_RECIPROCITY",
                    f"/semantic/gates/{gate.id}/owner_block_id",
                    [gate.id, gate.owner_block_id],
                    "The gate owner does not list this gate.",
                    "Make gate ownership reciprocal.",
                )
            )
        for field, target_id in (
            ("proceed_target_block_id", gate.proceed_target_block_id),
            ("revise_target_block_id", gate.revise_target_block_id),
        ):
            if target_id not in blocks:
                diagnostics.append(
                    _diagnostic(
                        "GATE_TARGET_MISSING",
                        f"/semantic/gates/{gate.id}/{field}",
                        [gate.id, target_id],
                        "The gate target block does not exist.",
                        "Choose an existing block target.",
                    )
                )
        if path is None or path.from_gate_id != gate.id:
            diagnostics.append(
                _diagnostic(
                    "GATE_FEEDBACK_RECIPROCITY",
                    f"/semantic/gates/{gate.id}/feedback_path_id",
                    [gate.id, gate.feedback_path_id],
                    "The gate feedback reference is missing or not reciprocal.",
                    "Reference one feedback path that points back to this gate.",
                )
            )
        elif path.to_block_id != gate.revise_target_block_id:
            diagnostics.append(
                _diagnostic(
                    "FEEDBACK_REVISE_TARGET_MISMATCH",
                    f"/semantic/gates/{gate.id}/revise_target_block_id",
                    [gate.id, path.id, path.to_block_id, gate.revise_target_block_id],
                    "The feedback target differs from the gate revise target.",
                    "Use the same block identity for feedback and revise targets.",
                )
            )

    for path in semantic.feedback_paths:
        gate = gates.get(path.from_gate_id)
        if gate is None or gate.feedback_path_id != path.id:
            diagnostics.append(
                _diagnostic(
                    "FEEDBACK_GATE_RECIPROCITY",
                    f"/semantic/feedback_paths/{path.id}/from_gate_id",
                    [path.id, path.from_gate_id],
                    "The feedback path gate reference is missing or not reciprocal.",
                    "Reference a gate that lists this feedback path.",
                )
            )
        if path.to_block_id not in blocks:
            diagnostics.append(
                _diagnostic(
                    "FEEDBACK_TARGET_MISSING",
                    f"/semantic/feedback_paths/{path.id}/to_block_id",
                    [path.id, path.to_block_id],
                    "The feedback target block does not exist.",
                    "Choose an existing block target.",
                )
            )

    for artifact in semantic.intended_artifacts:
        producer = blocks.get(artifact.produced_by_block_id)
        if producer is None or artifact.id not in producer.intended_artifact_ids:
            diagnostics.append(
                _diagnostic(
                    "ARTIFACT_PRODUCER_RECIPROCITY",
                    f"/semantic/intended_artifacts/{artifact.id}/produced_by_block_id",
                    [artifact.id, artifact.produced_by_block_id],
                    "The intended artifact producer does not list this artifact.",
                    "Make artifact producer references reciprocal.",
                )
            )

    positions: dict[str, int] = {}
    for position in draft.layout.positions:
        positions[position.semantic_id] = positions.get(position.semantic_id, 0) + 1
        if position.semantic_id not in blocks:
            diagnostics.append(
                _diagnostic(
                    "LAYOUT_SEMANTIC_ID_INVALID",
                    "/layout/positions",
                    [position.semantic_id],
                    "A layout position refers to a non-block concept.",
                    "Keep exactly one position for each workflow block only.",
                )
            )
    for block_id in blocks:
        count = positions.get(block_id, 0)
        if count == 0:
            diagnostics.append(
                _diagnostic(
                    "LAYOUT_BLOCK_POSITION_MISSING",
                    "/layout/positions",
                    [block_id],
                    "A workflow block has no saved layout position.",
                    "Add exactly one integer-grid position for this block.",
                )
            )
        elif count > 1:
            diagnostics.append(
                _diagnostic(
                    "LAYOUT_BLOCK_POSITION_DUPLICATE",
                    "/layout/positions",
                    [block_id],
                    "A workflow block has more than one layout position.",
                    "Keep exactly one position for this block.",
                )
            )

    ordered = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.code, item.path, item.affected_semantic_ids),
        )
    )
    if len(ordered) > MAX_WORKFLOW_DRAFT_DIAGNOSTICS:
        return ordered[: MAX_WORKFLOW_DRAFT_DIAGNOSTICS - 1] + (
            _diagnostic(
                "DIAGNOSTICS_TRUNCATED",
                "/",
                (),
                "Additional validation diagnostics were omitted from this bounded response.",
                "Correct the reported issues, then validate the complete draft again.",
            ),
        )
    return ordered


__all__ = [
    "MAX_WORKFLOW_DRAFT_DIAGNOSTICS",
    "WorkflowDraftDiagnostic",
    "validate_workflow_draft",
]
