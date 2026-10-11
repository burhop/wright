"""Independent controls for STEP solid-envelope measurement."""

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
from workspace_service.process_validation.readers.step_box import StepBoundingBoxReader


def step(points, unit="SI_UNIT(.MILLI.,.METRE.)"):
    entities = [f"#1={unit};"]
    for index, point in enumerate(points, start=1):
        coordinate_id = index * 2
        entities.append(
            f"#{coordinate_id}=CARTESIAN_POINT('',({point[0]},{point[1]},{point[2]}));"
        )
        entities.append(f"#{coordinate_id + 1}=VERTEX_POINT('',#{coordinate_id});")
    return (
        "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n"
        + "\n".join(entities)
        + "\nENDSEC;\nEND-ISO-10303-21;\n"
    ).encode()


def measure(content, axis):
    subject = SubjectBinding(
        id="geometry",
        role="geometry",
        result_id="run:cad:geometry",
        producer=ProducerIdentity(
            run_id="run", step_id="cad", attempt=1, output_port="geometry"
        ),
        kind="file",
        locator="plate.step",
        format="step",
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    check = CheckDefinition(
        id=f"span-{axis}",
        requirement_ids=("GEOMETRY",),
        subject_role="geometry",
        reader="step-bounding-box",
        selector=f"box/{axis}_span_mm",
        constraint=Constraint(operator="within", target=1, tolerance=1),
        unit="mm",
        evidence_method="native_inspection",
    )
    return StepBoundingBoxReader().measure(
        SubjectSnapshot(subject, content),
        check,
        ReaderContext.create(ResourceBudget(), "step-box-test"),
    )


def test_measures_each_axis_from_referenced_solid_vertices():
    content = step([(10, -4, 2), (90, -4, 2), (10, 56, 2), (10, -4, 5)])
    assert measure(content, "x").value == 80
    assert measure(content, "y").value == 60
    assert measure(content, "z").value == 3


def test_alternative_origin_does_not_change_span():
    content = step([(-2, 7, 9), (3, 7, 9), (-2, 11, 9), (-2, 7, 11)])
    assert measure(content, "x").value == 5


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (
            step([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], "SI_UNIT($,.METRE.)"),
            "geometry.step_unit",
        ),
        (step([(0, 0, 0), (1, 0, 0), (0, 1, 0)]), "geometry.insufficient_vertices"),
    ],
)
def test_unknown_unit_and_insufficient_vertices_are_output_defects(content, code):
    with pytest.raises(ValidationIssue) as captured:
        measure(content, "x")
    assert captured.value.code == code
    assert captured.value.action == "revise_output"
