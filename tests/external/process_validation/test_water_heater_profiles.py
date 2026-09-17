from __future__ import annotations

import hashlib
import importlib.util
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


def evaluate(tmp_path, scenario_id):
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
