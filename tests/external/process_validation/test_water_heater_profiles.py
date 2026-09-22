from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationProfile,
    ValidationRequest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


REPOSITORY = Path(__file__).parents[3]
ATTEMPTS = {
    "water-heater-sizing-01": "attempt-005",
    "water-heater-sizing-02": "attempt-003",
    "water-heater-sizing-03": "attempt-003",
}
FILES = {
    "timeline": ("temperature-time.csv", "csv"),
    "comparison": ("power-comparison.csv", "csv"),
    "energy": ("energy-summary.csv", "csv"),
    "curve": ("temperature-curve.svg", "svg"),
    "report": ("heater-selection.md", "markdown"),
    "parameters": ("kit-run-parameters.json", "json"),
}
SELECTED = {
    "water-heater-sizing-01": 700,
    "water-heater-sizing-02": 600,
    "water-heater-sizing-03": 1500,
}


def automated(profile):
    raw = profile.model_dump(mode="json")
    raw["checks"] = [
        c for c in raw["checks"] if c["constraint"]["operator"] != "review"
    ]
    covered = {rid for c in raw["checks"] for rid in c["requirement_ids"]}
    for req in raw["baseline"]["requirements"]:
        req["mandatory"] = req["id"] in covered
        req["review_required"] = False
    raw["version"] = "automated-qualification"
    return ValidationProfile.model_validate(raw)


def evaluate(tmp_path, scenario_id, *, corrupt=None):
    profile = automated(load_profile(scenario_id))
    source = (
        REPOSITORY
        / "artifacts/engineering-workflow-datasets/output"
        / scenario_id
        / ATTEMPTS[scenario_id]
        / "artifacts"
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (name, fmt) in FILES.items():
        target = workspace / name
        shutil.copyfile(source / name, target)
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:analysis:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="analysis", attempt=1, output_port=role
                ),
                kind="file",
                locator=name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    source_step = (
        REPOSITORY
        / "artifacts/engineering-workflow-datasets/output/heat-spreader-sizing-01/attempt-008/artifacts/baseline_40.step"
    )
    if not source_step.is_file():
        pytest.skip("Retained STEP fixture is unavailable")
    package_step = workspace / "thermal-package.step"
    shutil.copyfile(source_step, package_step)
    measurements = workspace / "thermal-package-measurements.json"
    measurements.write_text(json.dumps({"fixture": True}) + "\n")
    field = workspace / "thermal-package-field.csv"
    field.write_text("model,x_m,temperature_c\ncarrier,0,90\ncarrier,.005,95\n")
    comparison = workspace / "power-comparison.csv"
    verification = {
        "schema": "wright-water-thermal-package-verification-v1",
        "status": "pass",
        "selected_electrical_power_w": SELECTED[scenario_id],
        "geometry": {
            "sha256": hashlib.sha256(package_step.read_bytes()).hexdigest(),
            "measurements_sha256": hashlib.sha256(measurements.read_bytes()).hexdigest(),
        },
        "field": {"sha256": hashlib.sha256(field.read_bytes()).hexdigest()},
        "modelica_selection_sha256": hashlib.sha256(comparison.read_bytes()).hexdigest(),
        "checks": {
            name: {"pass": True}
            for name in (
                "carrier_temperature",
                "accessible_shell_temperature",
                "envelope",
                "dry_mass",
            )
        },
    }
    if corrupt:
        corrupt(verification)
    verification_path = workspace / "thermal-package-verification.json"
    verification_path.write_text(json.dumps(verification) + "\n")
    for role, target, fmt in (
        ("package_step", package_step, "step"),
        ("package_measurements", measurements, "json"),
        ("package_field", field, "csv"),
        ("package_verification", verification_path, "json"),
    ):
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:analysis:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="analysis", attempt=1, output_port=role
                ),
                kind="file",
                locator=target.name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="water-profile",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=scenario_id,
    )
    return ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    ).evaluate(request, profile)


def test_generated_profiles_are_reproducible():
    path = REPOSITORY / "scripts/build_water_heater_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("water_profiles", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    for resource, expected in module.render().items():
        assert resource.read_bytes() == expected
        assert load_profile(resource.stem).id == resource.stem + "-full"


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_trajectories_pass_independent_checks_but_expose_missing_kit_identity(
    tmp_path, scenario_id
):
    outcome = evaluate(tmp_path, scenario_id)
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert set(findings) == {"kit-id", "kit-version"}, [
        (item.check_id, item.code, item.summary) for item in findings.values()
    ]
    assert {item.code for item in findings.values()} == {
        "output.required_value_missing"
    }
    passing = {
        item.check_id for item in outcome.assessment.checks if item.state == "pass"
    }
    assert {"trajectory-grid", "candidate-selection"} <= passing


def test_package_verification_rejects_wrong_cad_identity(tmp_path):
    def corrupt(document):
        document["geometry"]["sha256"] = "0" * 64

    outcome = evaluate(tmp_path, "water-heater-sizing-01", corrupt=corrupt)
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert findings["package-verification"].code == "water.package_geometry_identity"
