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
    "parametric-drill-jig-01": "attempt-012",
    "parametric-drill-jig-02": "attempt-012",
    "parametric-drill-jig-03": "attempt-011",
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


def evaluate(tmp_path, scenario_id, *, corrupt_slice_binding=False):
    resource = scenario_id + ("-full" if scenario_id.endswith("01") else "")
    profile = automated(load_profile(resource))
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
    for role, name, fmt in (
        ("jig_step", "jig.step", "step"),
        ("jig_stl", "jig.stl", "stl"),
        ("dxf", "hole-layout.dxf", "dxf"),
        ("report", "dimension-report.json", "json"),
    ):
        target = workspace / name
        shutil.copyfile(source / name, target)
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:cad:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="cad", attempt=1, output_port=role
                ),
                kind="file",
                locator=name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    package = workspace / "jig-slice.3mf"
    package.write_bytes(b"qualified-local-bambu-slice-package")
    package_digest = hashlib.sha256(package.read_bytes()).hexdigest()
    mesh_digest = next(item.sha256 for item in subjects if item.role == "jig_stl")
    evidence = workspace / "jig-slice-evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "operation": "actual_local_bambu_slice",
                "simulation": False,
                "exit_code": 0,
                "source_sha256": "0" * 64 if corrupt_slice_binding else mesh_digest,
                "package_sha256": package_digest,
            }
        ),
        encoding="utf-8",
    )
    for role, path, fmt in (
        ("slice_package", package, "3mf"),
        ("slice_evidence", evidence, "json"),
    ):
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:slice:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="slice", attempt=1, output_port=role
                ),
                kind="file",
                locator=path.name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="jig-full",
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
    path = REPOSITORY / "scripts/build_jig_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("jig_profiles", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    for resource, expected in module.render().items():
        assert resource.read_bytes() == expected
        assert load_profile(resource.stem).id.endswith("-full")


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_step_outputs_reach_every_automated_full_profile_check(
    tmp_path, scenario_id
):
    outcome = evaluate(tmp_path, scenario_id)
    assert outcome.release_eligible, [
        (f.check_id, f.code, f.summary) for f in outcome.assessment.findings
    ]
    assert outcome.assessment.summary.content_verified


def test_slice_evidence_rejects_the_wrong_source_mesh_hash(tmp_path):
    outcome = evaluate(
        tmp_path, "parametric-drill-jig-01", corrupt_slice_binding=True
    )
    assert any(
        finding.code == "printing.slice_binding"
        for finding in outcome.assessment.findings
    )
    assert not outcome.release_eligible
