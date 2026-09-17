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
RETAINED = REPOSITORY / "artifacts/engineering-workflow-datasets/output"
ATTEMPTS = {f"sensor-fan-harness-0{i}": "attempt-003" for i in range(1, 4)}
FILES = {
    "netlist": ("verified/independent-netlist.csv", "csv"),
    "voltage_drop": ("verified/voltage-drop.json", "json"),
    "shield": ("generated/shield-termination.json", "json"),
    "basis": ("research-and-design-basis.md", "markdown"),
    "plan": ("generated/harness-plan.svg", "svg"),
    "pin_schedule": ("generated/pin-schedule.csv", "csv"),
    "cut_list": ("generated/cut-list.csv", "csv"),
    "bom": ("generated/bom.csv", "csv"),
    "assembly": ("generated/assembly.md", "markdown"),
    "handoff": ("harness-handoff.md", "markdown"),
}


def automated(profile):
    raw = profile.model_dump(mode="json")
    raw["checks"] = [
        c for c in raw["checks"] if c["constraint"]["operator"] != "review"
    ]
    covered = {rid for check in raw["checks"] for rid in check["requirement_ids"]}
    for requirement in raw["baseline"]["requirements"]:
        requirement["mandatory"] = requirement["id"] in covered
        requirement["review_required"] = False
    raw["version"] = "automated-qualification"
    return ValidationProfile.model_validate(raw)


def evaluate(tmp_path, scenario_id):
    profile = automated(load_profile(scenario_id))
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (relative, fmt) in FILES.items():
        path = source / relative
        if not path.is_file():
            if role == "shield" and not scenario_id.endswith("03"):
                continue
            pytest.skip(f"Retained harness artifact is unavailable: {path}")
        target = workspace / path.name
        shutil.copyfile(path, target)
        subjects.append(
            SubjectBinding(
                id=role.replace("_", "-"),
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
        trace_id="harness-profile-qualification",
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


def test_generated_harness_profiles_are_reproducible():
    script = REPOSITORY / "scripts/build_harness_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("harness_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected
        assert load_profile(path.stem).id == path.stem + "-full"


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_outputs_reach_contact_inclusive_drop_failure(tmp_path, scenario_id):
    outcome = evaluate(tmp_path, scenario_id)
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert set(findings) == {"voltage-drop"}
    assert findings["voltage-drop"].code == "harness.invalid_number"
    assert findings["voltage-drop"].correction.target_step_id == "analysis"
