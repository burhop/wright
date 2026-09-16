"""Identity and numerical checks for the vented-enclosure CFD workflow."""

from __future__ import annotations

from typing import Any, Mapping

from .workflow_engineering_assertions import (
    EngineeringAssertionResult,
    evaluate_assertion,
)


def verify_enclosure_cfd(
    evidence: Mapping[str, Any],
) -> tuple[EngineeringAssertionResult, ...]:
    refs = tuple(str(value) for value in evidence.get("evidence", ()))
    boundaries = set(str(value) for value in evidence.get("boundary_names", ()))
    return (
        evaluate_assertion(
            "enclosure.manufacturer-reference",
            observed=evidence.get("reference_authority"),
            expected="manufacturer",
            predicate=lambda value: (
                value == "manufacturer" and bool(evidence.get("reference_document_id"))
            ),
            evidence=refs,
            correction="Resolve dimensions against an identified manufacturer-controlled document.",
        ),
        evaluate_assertion(
            "enclosure.cad-domain-identity",
            observed={
                "cad": evidence.get("cad_geometry_digest"),
                "domain": evidence.get("domain_geometry_digest"),
            },
            expected="matching geometry digest",
            predicate=lambda value: (
                bool(value["cad"]) and value["cad"] == value["domain"]
            ),
            evidence=refs,
            correction="Rebuild the fluid domain from the measured CAD and verify its geometry manifest.",
        ),
        evaluate_assertion(
            "enclosure.boundary-contract",
            observed=sorted(boundaries),
            expected=["inlet", "outlet", "walls"],
            predicate=lambda _value: {"inlet", "outlet", "walls"} <= boundaries,
            evidence=refs,
            correction="Name and verify inlet, outlet, and wall boundaries before solving.",
        ),
        evaluate_assertion(
            "enclosure.solver-quality",
            observed={
                "field_derived": evidence.get("field_derived"),
                "converged": evidence.get("converged"),
                "mass_imbalance_percent": evidence.get("mass_imbalance_percent"),
                "mesh_change_percent": evidence.get("mesh_change_percent"),
            },
            expected="computed fields, converged, mass imbalance <= 1%, mesh change <= 2%",
            predicate=lambda value: (
                bool(value["field_derived"])
                and bool(value["converged"])
                and float(value["mass_imbalance_percent"]) <= 1
                and float(value["mesh_change_percent"]) <= 2
            ),
            evidence=refs,
            units="percent",
            correction="Run the matching solver case to convergence and repeat balance and mesh-sensitivity checks.",
        ),
    )
