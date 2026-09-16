"""Qualification controls for independent thermal field validation."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

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
FIXTURES = REPOSITORY / "tests/datasets/process-validation/thermal"
RETAINED_HEAT = REPOSITORY / (
    "artifacts/engineering-workflow-datasets/output/heat-spreader-sizing-01/"
    "attempt-008/artifacts"
)
DEFAULT_FILES = {
    "baseline_coarse": "baseline-coarse.csv",
    "baseline_fine": "baseline-fine.csv",
    "revision_coarse": "revision-coarse.csv",
    "revision_fine": "revision-fine.csv",
    "decision": "decision.json",
}


def _only_checks(profile, *check_ids):
    raw = profile.model_dump(mode="json")
    selected = [item for item in raw["checks"] if item["id"] in check_ids]
    covered = {rid for item in selected for rid in item["requirement_ids"]}
    for requirement in raw["baseline"]["requirements"]:
        requirement["mandatory"] = requirement["id"] in covered
    raw["checks"] = selected
    raw["version"] = "qualification-" + "-".join(check_ids)
    return ValidationProfile.model_validate(raw)


def _evaluate(
    tmp_path: Path,
    *,
    files=None,
    profile=None,
    source_root=FIXTURES,
    key="thermal",
):
    files = dict(DEFAULT_FILES if files is None else files)
    profile = profile or load_profile("heat-spreader-sizing-01")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, source_name in files.items():
        source = source_root / source_name
        suffix = source.suffix.lower()
        target_name = role + suffix
        target = workspace / target_name
        shutil.copyfile(source, target)
        content = target.read_bytes()
        subjects.append(
            SubjectBinding(
                id=role.replace("_", "-"),
                role=role,
                result_id=f"run:analysis:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="analysis", attempt=1, output_port=role
                ),
                kind="file",
                locator=target_name,
                format="json" if suffix == ".json" else "csv",
                encoding="raw-bytes",
                sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="thermal-qualification",
        workspace_id="workspace",
        invocation_id=key,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )
    service = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    )
    return service.evaluate(request, profile)


def test_analytical_fields_balance_refinement_and_selection_pass(tmp_path):
    outcome = _evaluate(tmp_path)

    assert outcome.release_eligible
    assert len(outcome.assessment.measurements) == 15
    assert {item.reader.id for item in outcome.assessment.measurements} == {
        "thermal-field"
    }
    assert {item.reader.method for item in outcome.assessment.measurements} == {
        "independent_measurement"
    }


def test_wrong_load_reaches_analytical_and_heat_balance_checks(tmp_path):
    files = {**DEFAULT_FILES, "revision_fine": "revision-wrong-load.csv"}
    outcome = _evaluate(tmp_path, files=files)
    failures = {item.check_id: item for item in outcome.assessment.findings}

    assert "revision_fine-analytical" in failures
    assert "revision-fine-balance" in failures
    assert failures["revision_fine-analytical"].code == "requirement.out_of_bounds"
    assert failures["revision-fine-balance"].code == "requirement.out_of_bounds"


def test_missing_candidate_is_blocked_as_missing_evidence(tmp_path):
    files = {key: value for key, value in DEFAULT_FILES.items() if key != "baseline_fine"}
    outcome = _evaluate(tmp_path, files=files)
    selection = next(
        item for item in outcome.assessment.findings if item.check_id == "candidate-selection"
    )

    assert selection.code == "subject.related_role_missing"
    assert selection.state == "blocked"
    assert selection.category == "missing_evidence"


def test_fabricated_selection_summary_is_rejected_against_bound_fields(tmp_path):
    files = {**DEFAULT_FILES, "decision": "fabricated-decision.json"}
    outcome = _evaluate(tmp_path, files=files)
    selection = next(
        item for item in outcome.assessment.findings if item.check_id == "candidate-selection"
    )

    assert selection.code == "thermal.selection_mismatch"
    assert selection.category == "output_defect"


def test_wrong_coordinate_units_are_invalid_analysis_not_a_design_result(tmp_path):
    files = {**DEFAULT_FILES, "revision_fine": "revision-wrong-units.csv"}
    outcome = _evaluate(tmp_path, files=files)
    affected = [
        item for item in outcome.assessment.findings if item.subject_id == "revision-fine"
    ]

    assert affected
    assert {item.code for item in affected} == {"thermal.invalid_field"}
    assert all(item.observed is None for item in affected)


def test_temperature_limit_is_inclusive_at_exact_boundary(tmp_path):
    base = load_profile("heat-spreader-sizing-01")
    profile = _only_checks(base, "revision-maximum")
    outcome = _evaluate(
        tmp_path,
        files={"revision_fine": "revision-threshold.csv"},
        profile=profile,
        key="threshold",
    )

    assert outcome.release_eligible
    assert outcome.assessment.measurements[0].value == 45.0


def test_accurate_infeasibility_is_a_measured_requirement_failure(tmp_path):
    base = load_profile("heat-spreader-sizing-01")
    profile = _only_checks(base, "revision-maximum")
    outcome = _evaluate(
        tmp_path,
        files={"revision_fine": "revision-infeasible.csv"},
        profile=profile,
        key="infeasible",
    )
    finding = outcome.assessment.findings[0]

    assert finding.code == "requirement.out_of_bounds"
    assert finding.observed == 46.0
    assert finding.category == "output_defect"


def test_retained_generated_heat_fields_pass_independent_checks(tmp_path):
    retained_files = {
        "baseline_coarse": "baseline_40-coarse-temperature.csv",
        "baseline_fine": "baseline_40-fine-temperature.csv",
        "revision_coarse": "revision_60-coarse-temperature.csv",
        "revision_fine": "revision_60-fine-temperature.csv",
        "decision": "sizing-decision.json",
    }
    if not all((RETAINED_HEAT / item).exists() for item in retained_files.values()):
        import pytest

        pytest.skip("read-only generation-campaign thermal artifacts are not present")

    outcome = _evaluate(
        tmp_path,
        files=retained_files,
        source_root=RETAINED_HEAT,
        key="retained-generated-heat",
    )

    assert outcome.release_eligible
    assert outcome.assessment.summary.content_verified
