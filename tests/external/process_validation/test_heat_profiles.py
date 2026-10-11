"""Full heat-spreader profile controls over retained campaign artifacts."""

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
    "heat-spreader-sizing-01": "attempt-008",
    "heat-spreader-sizing-02": "attempt-010",
    "heat-spreader-sizing-03": "attempt-008",
}
CANDIDATES = {
    "heat-spreader-sizing-01": ("baseline_40", "revision_60"),
    "heat-spreader-sizing-02": ("narrow_30", "middle_45", "wide_60"),
    "heat-spreader-sizing-03": ("copper_60", "copper_80", "copper_100"),
}


def _automated(profile: ValidationProfile) -> ValidationProfile:
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


def _evaluate(tmp_path: Path, scenario_id: str, *, mutate=None):
    profile = _automated(load_profile(scenario_id + "-full"))
    source = RETAINED / scenario_id / ATTEMPTS[scenario_id] / "artifacts"
    if not source.is_dir():
        pytest.skip("Read-only retained campaign output is unavailable")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    role_files = {
        "decision": ("sizing-decision.json", "json"),
        "basis": ("thermal-basis.md", "markdown"),
    }
    for case_id in CANDIDATES[scenario_id]:
        role_files.update(
            {
                case_id + "_geometry": (case_id + ".step", "step"),
                case_id + "_coarse": (case_id + "-coarse-temperature.csv", "csv"),
                case_id + "_fine": (case_id + "-fine-temperature.csv", "csv"),
            }
        )
    role_files["correspondence"] = ("geometry-analysis-correspondence.json", "json")
    subjects = []
    for role, (name, fmt) in role_files.items():
        target = workspace / name
        if role == "correspondence":
            decision = json.loads((workspace / "sizing-decision.json").read_text())
            by_id = {item["case_id"]: item for item in decision["cases"]}
            document = {
                "schema": "wright-heat-geometry-analysis-correspondence-v1",
                "operation": decision["operation"],
                "cases": [
                    {
                        "case_id": case_id,
                        "geometry": {
                            "path": str(workspace / f"{case_id}.step"),
                            "sha256": hashlib.sha256(
                                (workspace / f"{case_id}.step").read_bytes()
                            ).hexdigest(),
                        },
                        "solver_input": by_id[case_id]["input"],
                        "fields": {
                            level: {
                                "csv": {
                                    "path": str(
                                        workspace
                                        / f"{case_id}-{level}-temperature.csv"
                                    ),
                                    "sha256": hashlib.sha256(
                                        (
                                            workspace
                                            / f"{case_id}-{level}-temperature.csv"
                                        ).read_bytes()
                                    ).hexdigest(),
                                }
                            }
                            for level in ("coarse", "fine")
                        },
                    }
                    for case_id in CANDIDATES[scenario_id]
                ],
            }
            target.write_text(json.dumps(document, indent=2) + "\n")
        else:
            shutil.copyfile(source / name, target)
        if mutate is not None:
            mutate(role, target)
        subjects.append(
            SubjectBinding(
                id=role.replace("_", "-"),
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
        trace_id="heat-profile-qualification",
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


def test_generated_heat_profiles_are_reproducible_and_loadable():
    script = REPOSITORY / "scripts/build_heat_spreader_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("heat_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected
        assert load_profile(path.stem).id == path.stem.removesuffix("-full") + "-full"


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_outputs_pass_every_automated_full_profile_check(
    tmp_path, scenario_id
):
    outcome = _evaluate(tmp_path, scenario_id)
    assert outcome.release_eligible, [
        (item.check_id, item.code) for item in outcome.assessment.findings
    ]
    assert outcome.assessment.summary.content_verified
    assert {
        measurement.reader.id for measurement in outcome.assessment.measurements
    } >= {"step-bounding-box", "thermal-field", "structured"}


def test_geometry_analysis_correspondence_rejects_wrong_step_identity(tmp_path):
    def corrupt_correspondence(role, path):
        if role != "correspondence":
            return
        document = json.loads(path.read_text())
        document["cases"][0]["geometry"]["sha256"] = "0" * 64
        path.write_text(json.dumps(document) + "\n")

    outcome = _evaluate(
        tmp_path, "heat-spreader-sizing-01", mutate=corrupt_correspondence
    )
    failures = {item.check_id: item for item in outcome.assessment.findings}
    assert failures["geometry-analysis-correspondence"].code == (
        "thermal.geometry_identity_mismatch"
    )


def test_case_three_ideal_contact_substitution_reaches_analytical_check(tmp_path):
    def remove_contact_rise(role, path):
        if role != "copper_80_fine":
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        rewritten = [lines[0]]
        for line in lines[1:]:
            cells = line.split(",")
            cells[-1] = str(float(cells[-1]) - 2.7)
            rewritten.append(",".join(cells))
        path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    outcome = _evaluate(tmp_path, "heat-spreader-sizing-03", mutate=remove_contact_rise)
    failures = {item.check_id: item for item in outcome.assessment.findings}
    assert "copper_80_fine-analytical" in failures
    assert failures["copper_80_fine-analytical"].code == "requirement.out_of_bounds"
