from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "campaign_example_renewal", ROOT / "scripts/campaign_example_renewal.py"
)
renewal = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(renewal)


def _manifests() -> list[dict]:
    root = ROOT / "tests/datasets/engineering-workflows/scenarios"
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.glob("*/*/scenario.json"))
    ]


def test_approved_lineup_covers_exactly_the_30_scenarios() -> None:
    lineup, engineering, decision = renewal.approved_documents()
    manifests = _manifests()
    assert {case["id"] for case in lineup["cases"]} == {
        manifest["scenario_id"] for manifest in manifests
    }
    assert len(engineering["cases"]) == 6
    assert "broad_campaign_dispatch" in decision["not_authorized"]
    assert "approve_robot_010" in decision["not_authorized"]


def test_every_contract_is_engineer_readable_and_design_package_scoped() -> None:
    for manifest in _manifests():
        contract = renewal.case_contract(manifest)
        case = contract["scenario"]
        assert case["engineering_job"]
        assert case["final_deliverable"]
        assert case["verification_scope"]
        assert case["fixed_requirements"]
        assert case["permitted_design_choices"]
        assert case["outcome_kind"] == "digitally_verified_design_package"
        assert contract["claim_boundary"]["digital_verification_only"] is True


def test_changed_families_gain_the_approved_output_roles() -> None:
    expected = {
        "parametric-drill-jig": "additive_manufacturing_package",
        "sensor-fan-harness": "independent_interconnect_check",
        "sheet-metal-supplier-handoff": "independent_flat_pattern_review",
        "heat-spreader-sizing": "geometry_analysis_correspondence",
        "water-heater-sizing": "thermal_package_cad",
        "robot-tracking-diagnosis": "corrective_hardware_cad",
    }
    for manifest in _manifests():
        role = expected.get(manifest["template_id"])
        if role:
            assert role in {item["role"] for item in renewal.expected_outputs(manifest)}
