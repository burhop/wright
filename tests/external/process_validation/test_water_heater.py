import hashlib

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
from workspace_service.process_validation.readers.water_heater import (
    WaterHeaterTimelineReader,
)


HEADER = "request_id,time_s,temperature_C,electrical_power_W,electrical_energy_J,thermal_power_W,thermal_energy_J\n"


def measure(rows, operation="selection"):
    content = (HEADER + "\n".join(rows) + "\n").encode()
    subject = SubjectBinding(
        id="timeline",
        role="timeline",
        result_id="run:analysis:timeline",
        producer=ProducerIdentity(
            run_id="run", step_id="analysis", attempt=1, output_port="timeline"
        ),
        kind="file",
        locator="temperature-time.csv",
        format="csv",
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    check = CheckDefinition(
        id="water",
        requirement_ids=("REQ",),
        subject_role="timeline",
        reader="water-heater-timeline",
        selector="water/" + operation,
        constraint=Constraint(
            operator="equals", expected=200 if operation == "selection" else 2
        ),
        unit="W" if operation == "selection" else "1",
        evidence_method="independent_measurement",
        parameters={
            "operation": operation,
            "powers_w": [100, 200],
            "loss_labels": ["nominal"],
            "efficiency": 0.9,
            "initial_temperature_c": 20,
            "target_temperature_c": 90,
            "time_limit_s": 2,
            "horizon_s": 3,
        },
    )
    return WaterHeaterTimelineReader().measure(
        SubjectSnapshot(subject, content),
        check,
        ReaderContext.create(ResourceBudget(), "water-test"),
    )


VALID = [
    "case-p100-nominal-baseline,0,20,100,0,90,0",
    "case-p100-nominal-baseline,1,40,100,100,90,90",
    "case-p100-nominal-baseline,2,60,100,200,90,180",
    "case-p100-nominal-baseline,3,80,100,300,90,270",
    "case-p200-nominal-baseline,0,20,200,0,180,0",
    "case-p200-nominal-baseline,1,60,200,200,180,180",
    "case-p200-nominal-baseline,2,100,0,400,0,360",
    "case-p200-nominal-baseline,3,95,0,400,0,360",
]


def test_derives_lowest_feasible_power_and_exact_grid():
    assert measure(VALID).value == 200
    assert measure(VALID, "grid_count").value == 2


@pytest.mark.parametrize(
    ("rows", "code"),
    [
        ([row for row in VALID if "p100" not in row], "water.candidate_grid"),
        (
            [row.replace(",180,", ",170,") if "p200" in row else row for row in VALID],
            "water.efficiency",
        ),
        (
            [
                row.replace(",20,100,", ",21,100,")
                if "p100" in row and ",0," in row
                else row
                for row in VALID
            ],
            "water.initial_condition",
        ),
    ],
)
def test_targeted_valid_csv_defects_reach_intended_checks(rows, code):
    with pytest.raises(ValidationIssue) as captured:
        measure(rows)
    assert captured.value.code == code
    assert captured.value.action == "revise_output"
