"""Offline plan checks; actual KiCad execution is a separate opt-in proof."""

from collections import Counter
import csv
import importlib.util
from pathlib import Path

import pytest

from workspace_service.process_validation.profiles import load_profile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "native_harness_plan", ROOT / "scripts/qualify-harness-kicad-runtime.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def schedule(tmp_path, parameters):
    path = tmp_path / "pins.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("from_connector", "from_pin", "to_connector", "to_pin", "net"),
        )
        writer.writeheader()
        for row in parameters["expected_connections"]:
            left, left_pin = row["from"].split(":")
            right, right_pin = row["to"].split(":")
            writer.writerow(
                dict(
                    from_connector=left,
                    from_pin=left_pin,
                    to_connector=right,
                    to_pin=right_pin,
                    net=row["net"],
                )
            )
    return path


@pytest.mark.parametrize("number", (1, 2, 3))
def test_actual_pin_map_preserves_every_splice_connector_and_reserve(tmp_path, number):
    profile = load_profile(f"sensor-fan-harness-{number:02d}")
    parameters = next(
        check.parameters
        for check in profile.checks
        if check.id == "kicad-correspondence"
    )
    calls = MODULE.schematic_calls(
        schedule(tmp_path, parameters), parameters, "/work/output/harness.kicad_sch"
    )
    mapping = parameters["native_pin_map"]
    components = {
        call["reference"]: call
        for call in calls
        if call["operation"] == "add_component"
    }
    assert set(components) == {endpoint.split(":")[0] for endpoint in mapping.values()}
    assert ("B1" if number == 1 else "B0") in components
    if number == 3:
        assert {"S_ZX", "S_ZY"}.issubset(components)
    for reference, component in components.items():
        count = len(
            [
                endpoint
                for endpoint in mapping.values()
                if endpoint.startswith(reference + ":")
            ]
        )
        assert component["lib_id"] == f"Connector_Generic:Conn_01x{count:02d}"
    connections = [
        call for call in calls if call["operation"] == "connect_pins_with_labels"
    ]
    actual = Counter(
        (
            f"{c['comp1_ref']}:{c['pin1']}",
            f"{c['comp2_ref']}:{c['pin2']}",
            c["net_name"],
        )
        for c in connections
    )
    expected = Counter(
        (mapping[row["from"]], mapping[row["to"]], row["net"])
        for row in parameters["expected_connections"]
    )
    assert actual == expected
    connected = {endpoint for left, right, _ in actual for endpoint in (left, right)}
    assert not connected & {mapping[key] for key in parameters["reserved_endpoints"]}
    assert calls[0] == {"operation": "create", "name": "/work/output/harness.kicad_sch"}
    assert calls[-1] == {
        "operation": "save",
        "schematic_path": "/work/output/harness.kicad_sch",
    }


@pytest.mark.parametrize(
    "defect",
    (
        "missing_splice",
        "duplicate_pin",
        "numeric_pin_changed",
        "wrong_net",
        "duplicate_edge",
        "sparse_pins",
    ),
)
def test_invalid_or_mismatched_physical_schedule_is_rejected(tmp_path, defect):
    profile = load_profile("sensor-fan-harness-01")
    parameters = next(
        check.parameters
        for check in profile.checks
        if check.id == "kicad-correspondence"
    )
    path = schedule(tmp_path, parameters)
    if defect == "missing_splice":
        parameters["native_pin_map"].pop("B1:POWER")
    elif defect == "duplicate_pin":
        parameters["native_pin_map"]["B1:POWER"] = "J0:1"
    elif defect == "numeric_pin_changed":
        parameters["native_pin_map"]["J0:1"] = "J0:7"
    elif defect == "wrong_net":
        path.write_text(path.read_text().replace("FAN_GND", "SIGNAL_RETURN"))
    elif defect == "duplicate_edge":
        text = path.read_text()
        path.write_text(text + text.splitlines()[1] + "\n")
    else:
        parameters["native_pin_map"]["B1:POWER"] = "B1:3"
    with pytest.raises(ValueError):
        MODULE.schematic_calls(path, parameters, "/work/output/harness.kicad_sch")
