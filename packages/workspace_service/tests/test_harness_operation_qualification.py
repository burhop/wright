"""Opt-in fault injection against real retrieved/generated qualification outputs.

Set WRIGHT_HARNESS_QUALIFICATION_INPUT to the completed probe directory. These
checks never fabricate native tool results and do not award campaign credit.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil

import pytest


@pytest.fixture
def actual_case(tmp_path):
    location = os.environ.get("WRIGHT_HARNESS_QUALIFICATION_INPUT")
    if not location:
        pytest.skip("Requires an explicit completed actual harness qualification")
    source = Path(location) / "sensor-fan-harness-03"
    shutil.copytree(source, tmp_path / "case")
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "harness_operation_under_test",
        root / "scripts/harness_engineering_operations.py",
    )
    operation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operation)
    case = tmp_path / "case"

    def check():
        return operation.independent_verify(
            case / "inputs",
            case / "artifacts/research",
            case / "artifacts/generated",
            case / "test-verification",
        )

    return case, check


def test_actual_native_outputs_retain_unknown_contact_drop(actual_case):
    _, check = actual_case
    result = check()
    assert not result["netlist_and_numeric_failures"]
    assert result["release"] == "hold_for_missing_application_evidence"
    assert result["engineering_validation_complete"] is False
    assert all(row["total_drop_v"] is None for row in result["voltage_drop"])


def test_actual_native_pin_mutation_is_rejected(actual_case):
    import yaml

    case, check = actual_case
    path = case / "artifacts/generated/harness-source.yml"
    source = yaml.safe_load(path.read_text())
    first = source["connections"][0][0]
    first[next(iter(first))] = [99]
    path.write_text(yaml.safe_dump(source))
    result = check()
    assert result["release"] == "rejected"
    assert (
        "Native emitted netlist differs from the physical pin schedule"
        in result["netlist_and_numeric_failures"]
    )


def test_shared_segment_current_mutation_is_rejected(actual_case):
    case, check = actual_case
    path = case / "artifacts/generated/harness-plan.json"
    source = json.loads(path.read_text())
    supply = next(
        edge
        for edge in source["physical_edges"]
        if edge["net"] == "24V" and edge["from"].startswith("J0:")
    )
    supply["startup_a"] += 1
    path.write_text(json.dumps(source))
    result = check()
    assert result["release"] == "rejected"
    assert any(
        "Shared segment current mismatch" in message
        for message in result["netlist_and_numeric_failures"]
    )


def test_source_record_tampering_fails_closed(actual_case):
    case, check = actual_case
    path = case / "artifacts/research/plug6.pdf"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Primary component evidence has changed"):
        check()
