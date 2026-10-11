"""Harness voltage-drop assumptions remain explicit and review-bound."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "harness_engineering_operations", ROOT / "scripts/harness_engineering_operations.py"
)
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


ASSUMPTION = {
    "contact_ohm_each": 0.003,
    "splice_port_ohm_each": 0.001,
    "basis": "Reviewed prototype screening assumption pending production measurement.",
    "status": "reviewed_engineering_assumption",
}


def test_resistance_assumption_requires_closed_reviewed_schema():
    assert operations.resistance_assumption({}) is None
    assert operations.resistance_assumption(
        {"resistance_assumption": ASSUMPTION}
    ) == ASSUMPTION
    with pytest.raises(ValueError, match="review-approved"):
        operations.resistance_assumption(
            {
                "resistance_assumption": {
                    **ASSUMPTION,
                    "status": "model_selected",
                }
            }
        )
    with pytest.raises(ValueError, match="at most 0.1 ohm"):
        operations.resistance_assumption(
            {
                "resistance_assumption": {
                    **ASSUMPTION,
                    "contact_ohm_each": 0.2,
                }
            }
        )


def test_resistance_terms_count_each_contact_and_splice_port():
    physical = [
        {"id": "W1", "from": "J0:1", "to": "S_J1:POWER"},
        {"id": "W2", "from": "S_J1:POWER", "to": "JF:1"},
    ]
    terms = operations.resistance_terms([0, 1], physical, {0: 2.0, 1: 1.0}, ASSUMPTION)
    assert [item["kind"] for item in terms] == [
        "contact",
        "splice_port",
        "splice_port",
        "contact",
    ]
    assert sum(item["drop_v"] for item in terms) == pytest.approx(0.012)
