from __future__ import annotations

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
from workspace_service.process_validation.readers.kicad import KiCadReader


def measure(content, fmt, operation, parameters):
    raw = content if isinstance(content, bytes) else content.encode()
    subject = SubjectBinding(
        id="pcb",
        role="board",
        result_id="run:pcb:board",
        producer=ProducerIdentity(
            run_id="run", step_id="pcb", attempt=1, output_port="board"
        ),
        kind="file",
        locator="design." + fmt,
        format=fmt,
        encoding="raw-bytes",
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    check = CheckDefinition(
        id="pcb-check",
        requirement_ids=("REQ",),
        subject_role="board",
        reader="kicad",
        selector="pcb/" + operation,
        constraint=Constraint(operator="equals", expected=1),
        unit="1",
        evidence_method="independent_measurement",
        parameters={"operation": operation, **parameters},
    )
    return KiCadReader().measure(
        SubjectSnapshot(subject, raw),
        check,
        ReaderContext.create(ResourceBudget(), "pcb-test"),
    )


BOARD = """(kicad_pcb
  (net 0 \"\") (net 1 \"POWER\") (net 2 \"GND\")
  (footprint \"R_0603\" (at 10 5)
    (property \"Reference\" \"R1\") (property \"Value\" \"10k\")
    (pad \"1\" smd rect (at -1 0) (net 1 \"POWER\"))
    (pad \"2\" smd rect (at 1 0) (net 2 \"GND\")))
  (gr_line (start 0 0) (end 40 0) (layer \"Edge.Cuts\"))
  (gr_line (start 40 0) (end 40 30) (layer \"Edge.Cuts\"))
  (gr_line (start 40 30) (end 0 30) (layer \"Edge.Cuts\"))
  (gr_line (start 0 30) (end 0 0) (layer \"Edge.Cuts\"))
  (segment (start 0 0) (end 1 0) (width 1.5) (net 1)))"""


def test_native_pin_mapping_and_component_values_are_measured():
    assert (
        measure(
            BOARD,
            "kicad_pcb",
            "netlist",
            {
                "expected_connections": [
                    {"reference": "R1", "pin": "1", "net": "POWER"},
                    {"reference": "R1", "pin": "2", "net": "GND"},
                ]
            },
        ).value
        == 2
    )
    assert (
        measure(
            BOARD,
            "kicad_pcb",
            "components",
            {
                "expected_components": {
                    "R1": {"value": "10k", "footprint_contains": "R_0603"}
                }
            },
        ).value
        == 1
    )


def test_swapped_pin_and_clean_report_with_error_are_rejected():
    swapped = BOARD.replace('(net 1 "POWER"))', '(net 2 "GND"))', 1)
    with pytest.raises(ValidationIssue) as captured:
        measure(
            swapped,
            "kicad_pcb",
            "netlist",
            {
                "expected_connections": [
                    {"reference": "R1", "pin": "1", "net": "POWER"},
                    {"reference": "R1", "pin": "2", "net": "GND"},
                ]
            },
        )
    assert captured.value.code == "kicad.netlist_mismatch"
    report = json.dumps({"violations": [{"severity": "error"}]})
    with pytest.raises(ValidationIssue) as captured:
        measure(report, "json", "report", {})
    assert captured.value.code == "kicad.check_errors"
