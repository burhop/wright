"""Full printed-part profile controls over retained campaign artifacts."""

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
RETAINED = REPOSITORY / "artifacts/engineering-workflow-datasets/output"
ATTEMPTS = {
    "printed-replacement-part-01": "attempt-003",
    "printed-replacement-part-02": "attempt-002",
    "printed-replacement-part-03": "attempt-016",
}
FILES = {
    "source_mesh": ("source_mesh.stl", "stl"),
    "repaired_mesh": ("repaired_mesh.stl", "stl"),
    "support_preview": ("support-preview.svg", "svg"),
    "slice_package": ("slice_package.gcode.3mf", "3mf"),
    "slice_evidence": ("slice-evidence.json", "json"),
    "machine_profile": ("machine-profile.json", "json"),
    "filament_profile": ("filament-profile.json", "json"),
    "process_profile": ("process-profile.json", "json"),
    "transfer_receipt": ("printer-transfer-receipt.json", "json"),
    "source_report": ("source-model-report.json", "json"),
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


def evaluate(tmp_path, scenario_id, mutate=None):
    profile = automated(load_profile(scenario_id))
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip(f"Retained printed-part artifacts are unavailable: {source}")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (relative, fmt) in FILES.items():
        path = source / relative
        if not path.is_file():
            pytest.skip(f"Retained printed-part artifact is unavailable: {path}")
        target = workspace / relative
        shutil.copyfile(path, target)
        if mutate and role == mutate[0]:
            value = json.loads(target.read_text(encoding="utf-8-sig"))
            value[mutate[1]] = mutate[2]
            target.write_text(json.dumps(value), encoding="utf-8")
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:print:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="print", attempt=1, output_port=role
                ),
                kind="file",
                locator=relative,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="printed-profile-qualification",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=scenario_id + ("-mutated" if mutate else ""),
    )
    return ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    ).evaluate(request, profile)


def test_generated_printed_profiles_are_reproducible_and_reviewable():
    script = REPOSITORY / "scripts/build_printed_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("printed_profile_builder", script)
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
        assert review_ids
        assert review_ids == {
            item.id for item in profile.baseline.requirements if item.review_required
        }


@pytest.mark.parametrize(
    "scenario_id",
    ["printed-replacement-part-01", "printed-replacement-part-03"],
)
def test_retained_printed_outputs_pass_independent_automated_checks(
    tmp_path, scenario_id
):
    outcome = evaluate(tmp_path, scenario_id)
    assert outcome.release_eligible, [
        (item.check_id, item.code) for item in outcome.assessment.findings
    ]
    assert {item.reader.id for item in outcome.assessment.measurements} >= {
        "printing",
        "structured",
    }


def test_identical_source_and_repaired_case_is_actionable_failure(tmp_path):
    outcome = evaluate(tmp_path, "printed-replacement-part-02")
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert findings["distinct-mesh-lineage"].code == "printing.mesh_not_distinct"
    assert findings["distinct-mesh-lineage"].correction.action == "revise_output"
    assert not outcome.release_eligible


def test_altered_slice_source_digest_fails_exact_lineage(tmp_path):
    outcome = evaluate(
        tmp_path,
        "printed-replacement-part-01",
        ("slice_evidence", "source_sha256", "0" * 64),
    )
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert findings["slice-lineage"].code == "printing.slice_binding"
