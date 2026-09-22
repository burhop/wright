"""Full sheet-metal profile controls and retained missing-output behavior."""

from __future__ import annotations

import hashlib
import importlib.util
import json
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
    "sheet-metal-supplier-handoff-01": "attempt-006",
    "sheet-metal-supplier-handoff-02": "attempt-006",
    "sheet-metal-supplier-handoff-03": "attempt-005",
}


def test_generated_sheet_metal_profiles_are_reproducible_and_reviewable():
    script = REPOSITORY / "scripts/build_sheet_metal_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("sheet_profile_builder", script)
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
def test_retained_partial_sheet_runs_pass_material_identity_but_block_missing_cad(
    tmp_path, scenario_id
):
    profile = load_profile(scenario_id)
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip(f"Retained sheet-metal attempt is unavailable: {source}")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, filename, fmt in (
        ("installed_materials", "installed-materials.json", "json"),
        ("manufacturing_intent", "manufacturing-intent.md", "markdown"),
    ):
        source_file = source / filename
        if not source_file.is_file():
            continue
        target = workspace / filename
        target.write_bytes(source_file.read_bytes())
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="intent", attempt=1, output_port=role
                ),
                kind="file",
                locator=filename,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="sheet-retained",
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
    checks = {item.check_id: item.state for item in outcome.assessment.checks}
    assert checks["installed-material-label"] == "pass"
    assert any(
        item.code == "subject.role_missing" for item in outcome.assessment.findings
    )
    assert outcome.assessment.summary.release_eligible is False


def test_headless_dxf_review_rejects_a_report_bound_to_the_wrong_copy(tmp_path):
    scenario_id = "sheet-metal-supplier-handoff-01"
    profile = load_profile(scenario_id)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dxf = (
        "0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n"
        "0\nSECTION\n2\nENTITIES\n0\nLINE\n10\n0\n20\n0\n"
        "11\n10\n21\n0\n0\nENDSEC\n0\nEOF\n"
    ).encode()
    source = workspace / "wall-dock.dxf"
    reviewed = workspace / "wall-dock-reviewed.dxf"
    source.write_bytes(dxf)
    reviewed.write_bytes(dxf)
    report = workspace / "wall-dock-dxf-review.json"
    report.write_text(
        json.dumps(
            {
                "schema": "wright-headless-dxf-review-v1",
                "status": "pass",
                "source_sha256": hashlib.sha256(dxf).hexdigest(),
                "reviewed_sha256": "0" * 64,
                "inventories_equal": True,
                "differences": [],
            }
        ),
        encoding="utf-8",
    )
    subjects = []
    for role, path, fmt in (
        ("wall_dock_dxf", source, "dxf"),
        ("wall_dock_review_dxf", reviewed, "dxf"),
        ("wall_dock_review_report", report, "json"),
    ):
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:review:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="review", attempt=1, output_port=role
                ),
                kind="file",
                locator=path.name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="sheet-dxf-corruption",
        workspace_id="workspace",
        invocation_id=scenario_id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="sheet-dxf-corruption",
    )
    outcome = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(workspace)),
    ).evaluate(request, profile)
    assert any(
        finding.code == "sheet_metal.dxf_review_mismatch"
        for finding in outcome.assessment.findings
    )
    assert not outcome.release_eligible
