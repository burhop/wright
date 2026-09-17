"""Profile and retained-output controls for robot tracking validation."""

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
ATTEMPTS = {
    "robot-tracking-diagnosis-01": "attempt-003",
    "robot-tracking-diagnosis-02": "attempt-004",
    "robot-tracking-diagnosis-03": "attempt-005",
}
FILES = {
    "timeline": ("analysis/timeline.csv", "csv"),
    "metrics": ("analysis/tracking-metrics.json", "json"),
    "plot": ("analysis/trajectory-overlay.svg", "svg"),
    "diagnosis": ("diagnosis.md", "markdown"),
    "conversion_manifest": ("converted/conversion-manifest.json", "json"),
}


def _automated_profile(profile: ValidationProfile) -> ValidationProfile:
    raw = profile.model_dump(mode="json")
    raw["checks"] = [
        check for check in raw["checks"] if check["constraint"]["operator"] != "review"
    ]
    covered = {rid for check in raw["checks"] for rid in check["requirement_ids"]}
    for requirement in raw["baseline"]["requirements"]:
        requirement["mandatory"] = requirement["id"] in covered
        requirement["review_required"] = False
    raw["version"] = "automated-qualification"
    return ValidationProfile.model_validate(raw)


def _evaluate(tmp_path: Path, scenario_id: str):
    profile = _automated_profile(load_profile(scenario_id))
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip("Read-only retained campaign output is unavailable")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (relative, fmt) in FILES.items():
        source_file = source / relative
        target = workspace / Path(relative).name
        shutil.copyfile(source_file, target)
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
        trace_id="tracking-profile-qualification",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=scenario_id,
    )
    service = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    )
    return service.evaluate(request, profile)


def test_generated_robot_profiles_are_reproducible_and_loadable():
    script = REPOSITORY / "scripts/build_robot_tracking_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("robot_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    generated = module.render()
    assert len(generated) == 3
    for path, expected in generated.items():
        assert path.read_bytes() == expected
        profile = load_profile(path.stem)
        assert profile.id == path.stem + "-full"


@pytest.mark.parametrize(
    "scenario_id",
    ["robot-tracking-diagnosis-01", "robot-tracking-diagnosis-03"],
)
def test_retained_outputs_pass_all_automated_profile_checks(tmp_path, scenario_id):
    outcome = _evaluate(tmp_path, scenario_id)
    assert outcome.release_eligible, [
        (item.check_id, item.code, item.observed)
        for item in outcome.assessment.findings
    ]
    assert outcome.assessment.summary.content_verified
    assert {item.reader.id for item in outcome.assessment.measurements} >= {
        "tracking-timeline",
        "structured",
    }


def test_case_two_retained_summary_exposes_false_gap_records(tmp_path):
    outcome = _evaluate(tmp_path, "robot-tracking-diagnosis-02")
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert set(findings) == {"gap-record"}
    assert findings["gap-record"].code == "requirement.out_of_bounds"
    assert findings["gap-record"].category == "output_defect"
