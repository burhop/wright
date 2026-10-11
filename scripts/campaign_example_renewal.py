"""Approved R1 engineering-example renewal contract helpers.

This module is deliberately small and read-only.  It projects the approved
lineup and independently reviewed engineering inputs into canonical campaign
preparers without editing historical attempts or inventing a second runner.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LINEUP = (
    ROOT
    / "specs/082-output-content-validation/campaign-example-renewal-lineup.json"
)
ENGINEERING_INPUTS = (
    ROOT
    / "specs/082-output-content-validation/"
    "campaign-example-renewal-engineering-input-proposal.json"
)
DECISION = (
    ROOT
    / "specs/082-output-content-validation/campaign-example-renewal-decision.json"
)

APPROVED_STATUS = "approved_2026-09-22"
CONTRACT_SCHEMA = "wright.engineering-example-renewal/1"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approved_documents() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load and cross-check the three human-approved R1 records."""
    lineup = _load(LINEUP)
    engineering = _load(ENGINEERING_INPUTS)
    decision = _load(DECISION)
    statuses = {lineup.get("decision_status"), engineering.get("decision_status")}
    if statuses != {APPROVED_STATUS} or decision.get("decision") != "approved":
        raise ValueError(
            "Campaign renewal is not approved consistently across the R1 records"
        )
    approved = set(decision.get("approved_artifacts", []))
    for path in (LINEUP, ENGINEERING_INPUTS):
        if path.relative_to(ROOT).as_posix() not in approved:
            raise ValueError(f"R1 decision does not identify {path.name}")
    cases = lineup.get("cases", [])
    if len(cases) != 30 or len({case.get("id") for case in cases}) != 30:
        raise ValueError("The approved R1 lineup must contain 30 unique cases")
    return lineup, engineering, decision


def case_contract(scenario_manifest: dict[str, Any]) -> dict[str, Any]:
    """Return the immutable, engineer-readable R1 contract for one scenario."""
    lineup, engineering, decision = approved_documents()
    scenario_id = scenario_manifest["scenario_id"]
    try:
        case = next(item for item in lineup["cases"] if item["id"] == scenario_id)
    except StopIteration as exc:
        raise ValueError(f"Scenario {scenario_id!r} is absent from approved R1 lineup") from exc
    numerical = next(
        (item for item in engineering.get("cases", []) if item["scenario_id"] == scenario_id),
        None,
    )
    return {
        "schema_version": CONTRACT_SCHEMA,
        "revision_id": lineup["proposal_id"],
        "approval": {
            "status": APPROVED_STATUS,
            "decision_id": decision["decision_id"],
            "decision_sha256": _sha256(DECISION),
            "lineup_sha256": _sha256(LINEUP),
            "engineering_inputs_sha256": _sha256(ENGINEERING_INPUTS),
        },
        "scenario": {
            "scenario_id": scenario_id,
            "template_id": scenario_manifest["template_id"],
            "original_manifest_sha256": hashlib.sha256(
                (json.dumps(scenario_manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
            ).hexdigest(),
            "title": case["title"],
            "engineering_job": case["purpose"],
            "final_deliverable": case["final_deliverable"],
            "verification_scope": case["verification_scope"],
            "fixed_requirements": case["fixed_requirements"],
            "permitted_design_choices": case["permitted_design_choices"],
            "requirements_change": case["requirements_change"],
            "disposition": case["disposition"],
            "outcome_kind": case["outcome_kind"],
        },
        "approved_engineering_inputs": numerical,
        "claim_boundary": {
            "digital_verification_only": True,
            "physical_validation": "not_assessed_unless_separate_evidence_is_attached",
            "candidate_cannot_change_requirements": True,
            "final_revision_must_match_analyzed_and_exported_artifacts": True,
        },
    }


_RENEWAL_OUTPUTS: dict[str, list[dict[str, Any]]] = {
    "parametric-drill-jig": [
        {
            "role": "additive_manufacturing_package",
            "patterns": ["**/*jig*.3mf", "**/*jig*.gcode", "**/*slice*report*.json"],
        }
    ],
    "sensor-fan-harness": [
        {
            "role": "independent_interconnect_check",
            "patterns": ["**/*.kicad_sch", "**/*erc*.json", "**/*net*correspondence*.json"],
        }
    ],
    "sheet-metal-supplier-handoff": [
        {
            "role": "independent_flat_pattern_review",
            "patterns": ["**/*review*.dxf", "**/*dxf*review*.json"],
        }
    ],
    "heat-spreader-sizing": [
        {
            "role": "geometry_analysis_correspondence",
            "patterns": ["**/*geometry*analysis*correspondence*.json"],
        }
    ],
    "water-heater-sizing": [
        {"role": "thermal_package_cad", "patterns": ["**/*thermal*package*.step"]},
        {"role": "thermal_package_field", "patterns": ["**/*thermal*field*.csv"]},
        {"role": "thermal_package_verification", "patterns": ["**/*thermal*package*verification*.json"]},
    ],
    "robot-tracking-diagnosis": [
        {"role": "corrective_hardware_cad", "patterns": ["**/*corrective*.step"]},
        {"role": "corrective_hardware_fea", "patterns": ["**/*corrective*fea*.json"]},
        {"role": "commissioning_package", "patterns": ["**/*commissioning*package*.md"]},
    ],
}


def expected_outputs(scenario_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Overlay approved R1 roles without mutating the source manifest."""
    outputs = [dict(item) for item in scenario_manifest.get("expected_outputs", [])]
    existing = {item["role"] for item in outputs}
    for item in _RENEWAL_OUTPUTS.get(scenario_manifest["template_id"], []):
        if item["role"] not in existing:
            outputs.append(dict(item))
    return outputs


def contract_bytes(scenario_manifest: dict[str, Any]) -> bytes:
    return (json.dumps(case_contract(scenario_manifest), indent=2) + "\n").encode("utf-8")
