"""Independent evidence checks for additive-manufacturing workflow outputs."""

from __future__ import annotations

from typing import Any, Mapping

from .workflow_engineering_assertions import (
    EngineeringAssertionResult,
    evaluate_assertion,
)


def verify_print_package(
    evidence: Mapping[str, Any],
) -> tuple[EngineeringAssertionResult, ...]:
    refs = tuple(str(value) for value in evidence.get("evidence", ()))
    dimensions = evidence.get("dimensions_mm", ())
    volume = evidence.get("build_volume_mm", ())
    fits = (
        isinstance(dimensions, (list, tuple))
        and isinstance(volume, (list, tuple))
        and len(dimensions) == len(volume) == 3
        and all(float(value) > 0 for value in dimensions)
        and all(float(part) <= float(limit) for part, limit in zip(dimensions, volume))
    )
    return (
        evaluate_assertion(
            "additive.reference-scale",
            observed=evidence.get("reference_dimension_mm"),
            expected="> 0 mm and applied to measured mesh",
            predicate=lambda value: (
                float(value) > 0 and bool(evidence.get("scale_applied"))
            ),
            evidence=refs,
            units="mm",
            correction="Provide an explicit reference dimension and remeasure the scaled mesh.",
        ),
        evaluate_assertion(
            "additive.mesh-topology",
            observed={
                "manifold": evidence.get("manifold"),
                "watertight": evidence.get("watertight"),
            },
            expected={"manifold": True, "watertight": True},
            predicate=lambda value: value == {"manifold": True, "watertight": True},
            evidence=refs,
            correction="Repair the exact mesh and repeat topology inspection.",
        ),
        evaluate_assertion(
            "additive.build-volume",
            observed={"dimensions_mm": dimensions, "build_volume_mm": volume},
            expected="each oriented dimension within selected printer volume",
            predicate=lambda _value: fits,
            evidence=refs,
            units="mm",
            correction="Rescale or reorient the part, then regenerate supports and slicing evidence.",
        ),
        evaluate_assertion(
            "additive.supported-slice",
            observed={
                "supports": evidence.get("supports_generated"),
                "toolpath_valid": evidence.get("toolpath_valid"),
                "profile_match": evidence.get("profile_compatible"),
            },
            expected="support-bearing valid toolpath with compatible machine/material/process profiles",
            predicate=lambda value: all(value.values()),
            evidence=refs,
            correction="Regenerate and inspect the support-bearing slice with the selected P1S profiles.",
        ),
    )
