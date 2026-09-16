"""Exact-package checks for sheet-metal supplier preview and user handoff."""

from __future__ import annotations

from typing import Any, Mapping

from .workflow_engineering_assertions import (
    EngineeringAssertionResult,
    evaluate_assertion,
)


def verify_supplier_preview(
    evidence: Mapping[str, Any],
) -> tuple[EngineeringAssertionResult, ...]:
    refs = tuple(str(value) for value in evidence.get("evidence", ()))
    required_files = {"psm", "step", "dxf"}
    files = evidence.get("files", {})
    quote_fields = (
        "price",
        "currency",
        "quantity",
        "material",
        "thickness",
        "timestamp",
    )
    return (
        evaluate_assertion(
            "sheet-metal.design-check",
            observed={
                "verdict": evidence.get("design_check"),
                "revisions": evidence.get("revision_count"),
            },
            expected="pass after no more than two corrective revisions",
            predicate=lambda value: (
                value["verdict"] == "pass" and 0 <= int(value["revisions"]) <= 2
            ),
            evidence=refs,
            correction="Resolve the measured design-check findings within the bounded two-revision policy.",
        ),
        evaluate_assertion(
            "sheet-metal.export-set",
            observed=files,
            expected="digest-bound PSM, folded STEP, and genuine developed DXF",
            predicate=lambda value: (
                isinstance(value, Mapping)
                and required_files <= set(value)
                and all(
                    isinstance(value[key], str) and len(value[key]) == 64
                    for key in required_files
                )
                and bool(evidence.get("dxf_verified"))
            ),
            evidence=refs,
            correction="Regenerate and independently verify the exact PSM, STEP, and developed DXF files.",
        ),
        evaluate_assertion(
            "sheet-metal.supplier-association",
            observed=evidence.get("uploaded_digest"),
            expected=evidence.get("dxf_digest"),
            predicate=lambda value: bool(value) and value == evidence.get("dxf_digest"),
            evidence=refs,
            correction="Prove that the supplier preview is associated with the verified uploaded file.",
        ),
        evaluate_assertion(
            "sheet-metal.quote-preview",
            observed={field: evidence.get(field) for field in quote_fields},
            expected="complete quote selections and timestamp",
            predicate=lambda value: (
                all(value[field] not in (None, "") for field in quote_fields)
                and bool(evidence.get("units_verified"))
                and bool(evidence.get("bends_verified"))
                and evidence.get("order") is False
                and evidence.get("payment") is False
            ),
            evidence=refs,
            correction="Resolve supplier selections, bend recognition, warnings, and quote fields without ordering or payment.",
        ),
    )
