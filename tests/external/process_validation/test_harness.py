import hashlib
import json

import pytest

from core.process_validation import (
    CheckDefinition,
    Constraint,
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
)
from workspace_service.process_validation.readers.base import (
    ReaderContext,
    SubjectSnapshot,
    ValidationIssue,
)
from workspace_service.process_validation.readers.harness import HarnessReader


def measure(content, fmt, operation, parameters):
    raw = content.encode()
    subject = SubjectBinding(
        id="harness",
        role="harness",
        result_id="run:analysis:harness",
        producer=ProducerIdentity(
            run_id="run", step_id="analysis", attempt=1, output_port="harness"
        ),
        kind="file",
        locator="harness." + fmt,
        format=fmt,
        encoding="raw-bytes",
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    check = CheckDefinition(
        id="harness-check",
        requirement_ids=("REQ",),
        subject_role="harness",
        reader="harness",
        selector="harness/" + operation,
        constraint=Constraint(operator="range", minimum=0),
        unit="V" if operation == "voltage_drop" else "1",
        evidence_method="independent_measurement",
        parameters={"operation": operation, **parameters},
    )
    return HarnessReader().measure(
        SubjectSnapshot(subject, raw),
        check,
        ReaderContext.create(ResourceBudget(), "harness-test"),
    )


NETLIST = "from_endpoint,to_endpoint,cable,conductor\nJ0:1,B0:P,W1,1\nB0:P,JF:1,W2,1\nJ0:2,JF:2,W3,1\n"
EXPECTED = [
    {"from": "J0:1", "to": "B0:P", "net": "24V"},
    {"from": "B0:P", "to": "JF:1", "net": "24V"},
    {"from": "J0:2", "to": "JF:2", "net": "RETURN"},
]


def test_topology_uses_connectivity_and_keeps_declared_nets_separate():
    assert (
        measure(NETLIST, "csv", "topology", {"expected_connections": EXPECTED}).value
        == 3
    )
    assert (
        measure(
            NETLIST, "csv", "reserve_unconnected", {"reserved_endpoints": ["JF:6"]}
        ).value
        == 1
    )


def test_missing_connection_and_reserved_pin_are_targeted_defects():
    for content, operation, parameters, code in [
        (
            NETLIST.replace("B0:P,JF:1,W2,1\n", ""),
            "topology",
            {"expected_connections": EXPECTED},
            "harness.connection_missing",
        ),
        (
            NETLIST + "JF:6,J0:2,W4,1\n",
            "reserve_unconnected",
            {"reserved_endpoints": ["JF:6"]},
            "harness.reserve_connected",
        ),
    ]:
        with pytest.raises(ValidationIssue) as captured:
            measure(content, "csv", operation, parameters)
        assert captured.value.code == code


def test_cut_length_formula_and_voltage_drop_require_complete_values():
    cuts = "cable_id,mpn,conductors,installed_route_mm,cut_mm,service_plus_strip_mm,quantity,note\nW1,P,1,100,168,68,1,ok\n"
    assert measure(cuts, "csv", "cut_lengths", {}).value == 1
    drops = json.dumps({"branches": [{"total_drop_v": 0.5, "limit_v": 0.72}]})
    assert measure(drops, "json", "voltage_drop", {}).value == 0.5
    with pytest.raises(ValidationIssue) as captured:
        measure(
            json.dumps({"branches": [{"total_drop_v": None, "limit_v": 0.72}]}),
            "json",
            "voltage_drop",
            {},
        )
    assert captured.value.code == "harness.invalid_number"
