"""Stable, renderer-neutral workflow layout documents and recovery migration."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from .workflow_definitions import WorkflowDefinition, WorkflowDiagnostic


WORKFLOW_LAYOUT_KIND = "workflow-layout"
WORKFLOW_LAYOUT_VERSION = "1.0.0"
RECOVERY_WORKFLOW_LAYOUT_VERSION = "1.0.0-recovery.1"

Identifier = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=160,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
Coordinate = Annotated[float, Field(ge=-10_000_000, le=10_000_000)]
Zoom = Annotated[float, Field(gt=0, le=64)]


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkflowPosition(_ClosedModel):
    x: Coordinate
    y: Coordinate


class WorkflowViewport(_ClosedModel):
    x: Coordinate
    y: Coordinate
    zoom: Zoom


class WorkflowLayout(_ClosedModel):
    document_kind: Literal["workflow-layout"]
    schema_version: Literal["1.0.0"]
    workflow_id: Identifier
    semantic_revision: Annotated[int, Field(ge=1)]
    layout_revision: Annotated[int, Field(ge=1)]
    positions: Annotated[dict[Identifier, WorkflowPosition], Field(max_length=4000)]
    viewport: WorkflowViewport


class _RecoveryWorkflowLayout(_ClosedModel):
    document_kind: Literal["workflow-layout"]
    schema_version: Literal["1.0.0-recovery.1"]
    workflow_id: Identifier
    semantic_revision: Annotated[int, Field(ge=1)]
    layout_revision: Annotated[int, Field(ge=1)]
    positions: Annotated[dict[Identifier, WorkflowPosition], Field(max_length=4000)]
    viewport: WorkflowViewport


@dataclass(frozen=True, slots=True)
class WorkflowLayoutDecodeResult:
    layout: WorkflowLayout | None
    diagnostics: tuple[WorkflowDiagnostic, ...]
    original: bytes


@dataclass(frozen=True, slots=True)
class WorkflowLayoutPromotion:
    layout: WorkflowLayout
    source_envelope: bytes
    source_envelope_sha256: str
    source_layout_sha256: str
    layout_sha256: str


def layout_envelope_bytes(layout: WorkflowLayout) -> bytes:
    return json.dumps(
        layout.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_layout_sha256(layout: WorkflowLayout) -> str:
    return hashlib.sha256(layout_envelope_bytes(layout)).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key}")
        value[key] = item
    return value


def _parse_strict_json(original: bytes) -> Any:
    try:
        return json.loads(
            original,
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ValueError(f"non-finite number {item}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("Workflow layout is not strict UTF-8 JSON") from error


def _diagnostics_from_validation(
    error: ValidationError,
) -> tuple[WorkflowDiagnostic, ...]:
    return tuple(
        WorkflowDiagnostic(
            "WFR-LAYOUT-INVALID",
            str(item["msg"]),
            "Correct the complete layout document and retry without changing the definition.",
            tuple(str(part) for part in item["loc"]),
        )
        for item in error.errors(include_url=False)
    )


def decode_workflow_layout(original: bytes) -> WorkflowLayoutDecodeResult:
    """Decode a supported stable layout or preserve an unsupported input exactly."""

    try:
        value = _parse_strict_json(original)
    except ValueError:
        return WorkflowLayoutDecodeResult(
            None,
            (
                WorkflowDiagnostic(
                    "WFR-LAYOUT-DECODE",
                    "The workflow layout is not strict UTF-8 JSON.",
                    "Restore the original supported layout bytes.",
                ),
            ),
            original,
        )
    if (
        not isinstance(value, dict)
        or value.get("document_kind") != WORKFLOW_LAYOUT_KIND
    ):
        code = "WFR-LAYOUT-KIND-UNSUPPORTED"
    elif value.get("schema_version") != WORKFLOW_LAYOUT_VERSION:
        code = "WFR-LAYOUT-VERSION-UNSUPPORTED"
    else:
        try:
            return WorkflowLayoutDecodeResult(
                WorkflowLayout.model_validate(value), (), original
            )
        except ValidationError as error:
            return WorkflowLayoutDecodeResult(
                None, _diagnostics_from_validation(error), original
            )
    return WorkflowLayoutDecodeResult(
        None,
        (
            WorkflowDiagnostic(
                code,
                "The layout kind or version is not supported by this reader.",
                "Open it with an explicitly compatible reader; do not rewrite it.",
            ),
        ),
        original,
    )


def validate_workflow_layout_subject(
    definition: WorkflowDefinition, layout: WorkflowLayout
) -> None:
    if (
        layout.workflow_id != definition.workflow_id
        or layout.semantic_revision != definition.revision
    ):
        raise ValueError(
            "WFR-LAYOUT-SUBJECT-MISMATCH: layout does not target the accepted definition revision"
        )
    block_ids = {block.id for block in definition.blocks}
    unknown = sorted(set(layout.positions) - block_ids)
    if unknown:
        raise ValueError(
            f"WFR-LAYOUT-IDENTITY-UNKNOWN: layout references {', '.join(unknown)}"
        )
    numbers = [
        layout.viewport.x,
        layout.viewport.y,
        layout.viewport.zoom,
        *(
            number
            for position in layout.positions.values()
            for number in (position.x, position.y)
        ),
    ]
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError("WFR-LAYOUT-NUMBER-NONFINITE: layout numbers must be finite")


def promote_recovery_workflow_layout(
    original: bytes, definition: WorkflowDefinition
) -> WorkflowLayoutPromotion:
    """Promote exact approved recovery layout bytes into the stable v1 boundary."""

    value = _parse_strict_json(original)
    try:
        recovery = _RecoveryWorkflowLayout.model_validate(value)
    except ValidationError as error:
        if isinstance(value, dict) and (
            value.get("document_kind") != WORKFLOW_LAYOUT_KIND
            or value.get("schema_version") != RECOVERY_WORKFLOW_LAYOUT_VERSION
        ):
            raise ValueError(
                "Recovery workflow layout kind or version is unsupported"
            ) from error
        raise ValueError("Recovery workflow layout is invalid") from error
    source_layout_sha256 = hashlib.sha256(
        json.dumps(
            recovery.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    payload = recovery.model_dump(mode="json")
    payload["schema_version"] = WORKFLOW_LAYOUT_VERSION
    layout = WorkflowLayout.model_validate(payload)
    validate_workflow_layout_subject(definition, layout)
    return WorkflowLayoutPromotion(
        layout=layout,
        source_envelope=original,
        source_envelope_sha256=hashlib.sha256(original).hexdigest(),
        source_layout_sha256=source_layout_sha256,
        layout_sha256=canonical_layout_sha256(layout),
    )


def rollback_recovery_workflow_layout(
    promotion: WorkflowLayoutPromotion, layout: WorkflowLayout
) -> bytes:
    if canonical_layout_sha256(layout) != promotion.layout_sha256:
        raise ValueError(
            "Workflow layout promotion target digest changed; exact recovery rollback is unavailable"
        )
    if hashlib.sha256(promotion.source_envelope).hexdigest() != (
        promotion.source_envelope_sha256
    ):
        raise ValueError("Workflow layout promotion source envelope digest changed")
    return promotion.source_envelope


__all__ = [
    "RECOVERY_WORKFLOW_LAYOUT_VERSION",
    "WORKFLOW_LAYOUT_KIND",
    "WORKFLOW_LAYOUT_VERSION",
    "WorkflowLayout",
    "WorkflowLayoutDecodeResult",
    "WorkflowLayoutPromotion",
    "WorkflowPosition",
    "WorkflowViewport",
    "canonical_layout_sha256",
    "decode_workflow_layout",
    "layout_envelope_bytes",
    "promote_recovery_workflow_layout",
    "rollback_recovery_workflow_layout",
    "validate_workflow_layout_subject",
]
