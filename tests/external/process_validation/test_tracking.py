"""Independent controls for tracking-timeline measurements."""

import hashlib
import importlib.util
from pathlib import Path

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
from workspace_service.process_validation.readers.tracking import TrackingTimelineReader


HEADER = "time_s,acquisition_time_s,original_header_time_s,raw_x_m,raw_y_m,aligned_x_m,aligned_y_m,planned_x_m,planned_y_m,dx_m,dy_m,lateral_error_m,yaw_error_rad\n"

OPERATIONS_PATH = Path(__file__).parents[3] / "scripts/robot_tracking_operations.py"
OPERATIONS_SPEC = importlib.util.spec_from_file_location(
    "robot_tracking_operations_test", OPERATIONS_PATH
)
OPERATIONS = importlib.util.module_from_spec(OPERATIONS_SPEC)
assert OPERATIONS_SPEC.loader is not None
OPERATIONS_SPEC.loader.exec_module(OPERATIONS)


def test_exact_boundary_interval_is_not_reported_as_a_gap():
    assert not OPERATIONS.exceeds_interval_limit(0.9999999999999999, 1.5, 0.5)
    assert not OPERATIONS.exceeds_interval_limit(15.999999999999998, 16.5, 0.5)
    assert OPERATIONS.exceeds_interval_limit(13.5, 16.5, 0.5)


def snapshot(rows):
    content = (HEADER + "\n".join(rows) + "\n").encode()
    subject = SubjectBinding(
        id="timeline",
        role="timeline",
        result_id="run:analysis:timeline",
        producer=ProducerIdentity(
            run_id="run", step_id="analysis", attempt=1, output_port="timeline"
        ),
        kind="file",
        locator="timeline.csv",
        format="csv",
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    return SubjectSnapshot(subject, content)


def measure(rows, operation, unit):
    check = CheckDefinition(
        id="check-" + operation,
        requirement_ids=("REQ",),
        subject_role="timeline",
        reader="tracking-timeline",
        selector="timeline/" + operation,
        constraint=Constraint(operator="range", minimum=0),
        unit=unit,
        evidence_method="independent_measurement",
        parameters={"operation": operation},
    )
    return TrackingTimelineReader().measure(
        snapshot(rows), check, ReaderContext.create(ResourceBudget(), "tracking-test")
    )


VALID = [
    "0,0,0,0,0,0,0,0,0,0,0,0,0",
    "0.5,0.5,0.5,1,2,1.3,1.6,1,2,0.3,-0.4,-0.4,3.141592653589793",
]


def test_recomputes_metrics_sample_scope_and_wrapped_yaw():
    assert measure(VALID, "retained_samples", "1").value == 2
    assert measure(VALID, "position_rmse", "m").value == pytest.approx(
        (0.25 / 2) ** 0.5
    )
    assert measure(VALID, "lateral_rmse", "m").value == pytest.approx((0.16 / 2) ** 0.5)
    assert measure(VALID, "largest_gap", "s").value == 0.5
    assert measure(VALID, "max_yaw_residual", "rad").value == pytest.approx(
        3.141592653589793
    )


@pytest.mark.parametrize(
    "row",
    [
        "0,0,0,0,0,1,0,0,0,0,0,0,0",
        "0,0,0,0,0,0,0,0,0,nan,0,0,0",
        "0,0,0,0,0,0,0,0,0,0,0,0,3.2",
    ],
)
def test_targeted_bad_rows_are_output_defects(row):
    with pytest.raises(ValidationIssue) as captured:
        measure([row], "position_rmse", "m")
    assert captured.value.code == "tracking.invalid_timeline"
    assert captured.value.state == "fail"
    assert captured.value.action == "revise_output"


def test_alternative_valid_timeline_is_not_fixture_specific():
    rows = [
        "2,2,2,4,5,4,5,4,5,0,0,0,-0.2",
        "3,3,3,6,7,6.1,7.2,6,7,0.1,0.2,0.2,0.2",
    ]
    assert measure(rows, "start_time", "s").value == 2
    assert measure(rows, "end_time", "s").value == 3
    assert measure(rows, "position_rmse", "m").value == pytest.approx((0.05 / 2) ** 0.5)
