"""Qualification controls for the bounded STEP seat reader."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

import pytest

from core.process_validation import ProducerIdentity, SubjectBinding, ValidationRequest
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


REPOSITORY = Path(__file__).parents[3]
FIXTURES = REPOSITORY / "tests/datasets/process-validation/geometry"
RETAINED_JIG = REPOSITORY / (
    "artifacts/engineering-workflow-datasets/output/parametric-drill-jig-01/"
    "attempt-012/artifacts/jig.step"
)
RETAINED_JIG_SHA256 = (
    "2e4b9c5a137ef9d32c6ca0a4b58b4a74806bc2d94b68a6af77b496016fb6df84"
)


def _evaluate(tmp_path: Path, source: Path, *, key: str = "geometry"):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "jig.step"
    shutil.copyfile(source, target)
    content = target.read_bytes()
    profile = load_profile("parametric-drill-jig-01")
    subject = SubjectBinding(
        id="jig-step",
        role="jig_step",
        result_id="run:cad-producer:jig_step",
        producer=ProducerIdentity(
            run_id="run", step_id="cad-producer", attempt=1, output_port="jig_step"
        ),
        kind="file",
        locator="jig.step",
        format="step",
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    request = ValidationRequest(
        trace_id="geometry-qualification",
        workspace_id="workspace",
        invocation_id=key,
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )
    service = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    )
    return service.evaluate(request, profile)


@pytest.mark.parametrize(
    "fixture", ["good.step", "alternative.step", "arc-center-control.step", "boundary.step"]
)
def test_equivalent_and_boundary_geometry_passes(tmp_path, fixture):
    outcome = _evaluate(tmp_path, FIXTURES / fixture, key=fixture.removesuffix(".step"))

    assert outcome.release_eligible
    assert len(outcome.assessment.measurements) == 6
    assert {item.reader.id for item in outcome.assessment.measurements} == {
        "step-seat-geometry"
    }
    assert {item.reader.method for item in outcome.assessment.measurements} == {
        "native_inspection"
    }


def test_arc_center_is_measured_instead_of_unrelated_point_on_curve(tmp_path):
    outcome = _evaluate(tmp_path, FIXTURES / "arc-center-control.step")
    measured = {
        item.selector: item.value for item in outcome.assessment.measurements
    }

    assert measured["seat/H1/center_x_mm"] == 30.0
    assert measured["seat/H1/center_x_mm"] != 35.1


def test_wrong_datum_reaches_center_checks_without_a_parse_failure(tmp_path):
    outcome = _evaluate(tmp_path, FIXTURES / "wrong-datum.step")
    failures = {item.check_id: item for item in outcome.assessment.findings}

    assert set(failures) == {"h1-seat-center-x", "h2-seat-center-x"}
    assert {item.code for item in failures.values()} == {"requirement.out_of_bounds"}
    assert {item.observed for item in failures.values()} == {31.0, 171.0}


def test_radial_clearance_error_reaches_diameter_checks(tmp_path):
    outcome = _evaluate(tmp_path, FIXTURES / "radial-clearance.step")
    failures = {item.check_id: item for item in outcome.assessment.findings}

    assert set(failures) == {"h1-seat-diameter", "h2-seat-diameter"}
    assert {item.code for item in failures.values()} == {"requirement.out_of_bounds"}
    assert {item.observed for item in failures.values()} == {10.4}


def test_missing_geometry_is_distinct_from_an_invalid_step(tmp_path):
    outcome = _evaluate(tmp_path, FIXTURES / "missing-h2.step")
    h2 = [item for item in outcome.assessment.findings if item.check_id.startswith("h2-")]

    assert len(h2) == 3
    assert {item.code for item in h2} == {"geometry.required_feature_missing"}
    assert all(item.category == "output_defect" for item in h2)


def test_hash_pinned_retained_generated_jig_passes_actual_file_inspection(tmp_path):
    if not RETAINED_JIG.exists():
        pytest.skip("read-only generation-campaign artifact is not present")
    assert hashlib.sha256(RETAINED_JIG.read_bytes()).hexdigest() == RETAINED_JIG_SHA256

    outcome = _evaluate(tmp_path, RETAINED_JIG, key="retained-generated-jig")

    assert outcome.release_eligible
    measured = {item.selector: item.value for item in outcome.assessment.measurements}
    assert measured == {
        "seat/H1/center_x_mm": 30.0,
        "seat/H1/center_y_mm": 30.0,
        "seat/H1/diameter_mm": 10.2,
        "seat/H2/center_x_mm": 170.0,
        "seat/H2/center_y_mm": 30.0,
        "seat/H2/diameter_mm": 10.2,
    }
