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
    "sensor-interface-pcb-01": "attempt-007",
    "sensor-interface-pcb-02": "attempt-021",
    "sensor-interface-pcb-03": "attempt-015",
}
FILES = {
    "board": ("design.kicad_pcb", "kicad_pcb"),
    "schematic": ("design.kicad_sch", "kicad_sch"),
    "bom": ("design_bom.csv", "csv"),
    "fabrication": ("design-gerbers.zip", "zip"),
    "erc": ("erc.json", "json"),
    "drc": ("drc.json", "json"),
    "basis": ("electrical-basis.md", "markdown"),
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
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subjects = []
    for role, (relative, fmt) in FILES.items():
        path = source / relative
        if not path.is_file():
            pytest.skip(f"Retained PCB artifact is unavailable: {path}")
        target = workspace / relative
        shutil.copyfile(path, target)
        if mutate and role == mutate[0]:
            target.write_text(
                target.read_text(encoding="utf-8").replace(*mutate[1:]),
                encoding="utf-8",
            )
        subjects.append(
            SubjectBinding(
                id=role,
                role=role,
                result_id=f"run:pcb:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id="pcb", attempt=1, output_port=role
                ),
                kind="file",
                locator=relative,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            )
        )
    request = ValidationRequest(
        trace_id="pcb-profile-qualification",
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


def test_generated_pcb_profiles_are_reproducible():
    script = REPOSITORY / "scripts/build_pcb_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("pcb_profile_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected
        assert load_profile(path.stem).id == path.stem + "-full"


@pytest.mark.parametrize("scenario_id", sorted(ATTEMPTS))
def test_retained_pcb_outputs_pass_independent_automated_checks(tmp_path, scenario_id):
    outcome = evaluate(tmp_path, scenario_id)
    assert outcome.assessment.summary.release_eligible
    assert not outcome.assessment.findings


def test_clean_pcb_with_swapped_connector_pin_fails_frozen_netlist(tmp_path):
    outcome = evaluate(
        tmp_path,
        "sensor-interface-pcb-01",
        ("board", '(net 1 "3V3")', '(net 4 "SENSE")'),
    )
    findings = {item.check_id: item for item in outcome.assessment.findings}
    assert "native-netlist" in findings
    assert findings["native-netlist"].code == "kicad.netlist_mismatch"
