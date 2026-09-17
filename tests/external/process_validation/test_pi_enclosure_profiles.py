"""Full Raspberry Pi enclosure profile controls over retained artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import shutil

import pytest

from core.process_validation import (
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
    ValidationProfile,
    ValidationRequest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


REPOSITORY = Path(__file__).parents[3]
RETAINED = REPOSITORY / "artifacts/engineering-workflow-datasets/output"
ATTEMPTS = {
    "raspberry-pi-enclosure-01": "attempt-032",
    "raspberry-pi-enclosure-02": "attempt-031",
    "raspberry-pi-enclosure-03": "attempt-046",
}


def automated(profile):
    raw = profile.model_dump(mode="json")
    raw["checks"] = [
        item for item in raw["checks"] if item["constraint"]["operator"] != "review"
    ]
    covered = {rid for item in raw["checks"] for rid in item["requirement_ids"]}
    for requirement in raw["baseline"]["requirements"]:
        requirement["mandatory"] = requirement["id"] in covered
        requirement["review_required"] = False
    raw["version"] = "automated-qualification"
    return ValidationProfile.model_validate(raw)


def files(scenario_id):
    result = {
        "design_basis": ("design-basis.md", "markdown"),
        "manufacturer_research": ("manufacturer-research.md", "markdown"),
        "cad_source": ("enclosure-source.py", "text"),
        "comparison": ("cfd-comparison.json", "json"),
        "field_archive": ("cfd-fields.zip", "zip"),
    }
    for variant in ("a", "b"):
        result.update(
            {
                f"enclosure_{variant}": (f"enclosure-{variant}.step", "step"),
                f"fluid_domain_{variant}": (f"fluid-domain-{variant}.step", "step"),
                f"board_{variant}": (f"board-{variant}.step", "step"),
                f"contract_{variant}": (f"cfd-contract-{variant}.json", "json"),
            }
        )
        if scenario_id.endswith("01"):
            result[f"source_primary_{variant}"] = (
                f"board_hot_patch-{variant}.step",
                "step",
            )
        elif scenario_id.endswith("02"):
            result[f"source_primary_{variant}"] = (
                f"pi_surrogate-{variant}.step",
                "step",
            )
            result[f"source_secondary_{variant}"] = (
                f"sensor_interface-{variant}.step",
                "step",
            )
        else:
            result[f"source_primary_{variant}"] = (
                f"board_hot_patch-{variant}.step",
                "step",
            )
            result[f"source_secondary_{variant}"] = (
                f"power_interface-{variant}.step",
                "step",
            )
    return result


def evaluate(tmp_path, scenario_id):
    profile = automated(load_profile(scenario_id))
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip(f"Retained Pi enclosure artifacts are unavailable: {source}")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (relative, fmt) in files(scenario_id).items():
        target = workspace / relative
        shutil.copyfile(source / relative, target)
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:pi:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="pi", attempt=1, output_port=role
                ),
                kind="file",
                locator=relative,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="pi-profile-qualification",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=scenario_id,
        budget=ResourceBudget(max_bytes=64 * 1024 * 1024),
    )
    return ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    ).evaluate(request, profile)


def test_generated_pi_profiles_are_reproducible_and_reviewable():
    script = REPOSITORY / "scripts/build_pi_enclosure_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("pi_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected
        profile = load_profile(path.stem)
        review_ids = {
            rid
            for item in profile.checks
            if item.constraint.operator == "review"
            for rid in item.requirement_ids
        }
        assert review_ids == {
            item.id for item in profile.baseline.requirements if item.review_required
        }


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_fields_expose_unsettled_solve_and_missing_heat_balance(
    tmp_path, scenario_id
):
    outcome = evaluate(tmp_path, scenario_id)
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert findings["convergence-evidence"].code == "cfd.convergence_failed"
    assert "initial residual" in findings["convergence-evidence"].summary
    assert findings["heat-balance-evidence"].code == "cfd.heat_balance_missing"
    assert outcome.assessment.summary.counts["fail"] > 0
    assert outcome.assessment.summary.counts["blocked"] > 0
    passed = {item.check_id for item in outcome.assessment.checks if item.state == "pass"}
    assert {
        "field-archive-binding",
        "patch-temperature-a",
        "patch-temperature-b",
        "mass-balance-a",
        "mass-balance-b",
    } <= passed


def test_case_two_chimney_exceeds_frozen_height(tmp_path):
    outcome = evaluate(tmp_path, "raspberry-pi-enclosure-02")
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert findings["enclosure-b-z"].code == "requirement.out_of_bounds"
