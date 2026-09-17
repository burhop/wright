"""Full bracket profile controls and retained missing-output behavior."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

from core.process_validation import ProducerIdentity, SubjectBinding, ValidationRequest
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


REPOSITORY = Path(__file__).parents[3]
RETAINED = REPOSITORY / "artifacts/engineering-workflow-datasets/output"
ATTEMPTS = {
    "lightweight-equipment-bracket-01": "attempt-006",
    "lightweight-equipment-bracket-02": "attempt-005",
    "lightweight-equipment-bracket-03": "attempt-012",
}


def test_generated_bracket_profiles_are_reproducible_and_reviewable():
    script = REPOSITORY / "scripts/build_bracket_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("bracket_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected
        profile = load_profile(path.stem)
        review_ids = {
            requirement_id
            for item in profile.checks
            if item.constraint.operator == "review"
            for requirement_id in item.requirement_ids
        }
        assert review_ids == {
            item.id for item in profile.baseline.requirements if item.review_required
        }


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_incomplete_bracket_runs_return_actionable_missing_roles(
    tmp_path, scenario_id
):
    profile = load_profile(scenario_id)
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip(f"Retained bracket attempt is unavailable: {source}")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    basis = source / "mechanical-basis.md"
    if basis.is_file():
        target = workspace / basis.name
        target.write_bytes(basis.read_bytes())
        subjects.append(
            SubjectBinding(
                id="mechanical_basis",
                role="mechanical_basis",
                result_id="run:basis",
                producer=ProducerIdentity(
                    run_id="run", step_id="define_load_case", attempt=1, output_port="basis"
                ),
                kind="file",
                locator=basis.name,
                format="markdown",
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="bracket-retained",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=scenario_id,
    )
    outcome = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    ).evaluate(request, profile)
    missing = {
        item.selector
        for item in outcome.assessment.findings
        if item.code == "subject.role_missing"
    }
    assert "box/x_span_mm" in missing
    assert "structural/request-contract" in missing
    assert outcome.assessment.summary.release_eligible is False
