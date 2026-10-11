from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from collections import defaultdict
from xml.etree import ElementTree as ET

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


def evaluate(tmp_path, scenario_id, *, corrupt_kicad_binding=False, native_defect=None):
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
    schematic = workspace / "harness.kicad_sch"
    schematic.write_text("(kicad_sch (version 20231120) (generator wright-test))\n", encoding="utf-8")
    erc = workspace / "erc.json"
    erc.write_text(json.dumps({"$schema": "https://schemas.kicad.org/erc.v1.json", "sheets": [{"violations": []}]}), encoding="utf-8")
    # Synthetic native fixtures exercise the full reader boundary, not KiCad
    # provider qualification. Actual native-export evidence is kept separately.
    parameters = next(check.parameters for check in profile.checks if check.id == "kicad-correspondence")
    mapping = parameters["native_pin_map"]
    root = ET.Element("export", version="E")
    components = ET.SubElement(root, "components")
    libraries = ET.SubElement(root, "libparts")
    nets = ET.SubElement(root, "nets")
    grouped_pins, grouped_nets = defaultdict(set), defaultdict(set)
    for endpoint in mapping.values():
        reference, number = endpoint.split(":")
        grouped_pins[reference].add(number)
    for reference, numbers in grouped_pins.items():
        component = ET.SubElement(components, "comp", ref=reference)
        ET.SubElement(component, "libsource", lib="synthetic", part=reference)
        library = ET.SubElement(libraries, "libpart", lib="synthetic", part=reference)
        pins = ET.SubElement(library, "pins")
        for number in sorted(numbers):
            ET.SubElement(pins, "pin", num=number)
    for row in parameters["expected_connections"]:
        grouped_nets[row["net"]].update((mapping[row["from"]], mapping[row["to"]]))
    for code, (name, endpoints) in enumerate(grouped_nets.items(), 1):
        net = ET.SubElement(nets, "net", code=str(code), name="/" + name)
        for endpoint in sorted(endpoints):
            reference, number = endpoint.split(":")
            ET.SubElement(net, "node", ref=reference, pin=number)
    if native_defect == "missing_splice":
        components.remove(components.find("comp[@ref='B1']"))
    native_netlist = workspace / "netlist.xml"
    native_netlist.write_bytes(ET.tostring(root))

    def add_subject(role, path, fmt, step="ecad"):
        subjects.append(
            SubjectBinding(
                id=role.replace("_", "-"),
                role=role,
                result_id=f"run:{step}:{role}",
                producer=ProducerIdentity(
                    run_id="run", step_id=step, attempt=1, output_port=role
                ),
                kind="file",
                locator=path.name,
                format=fmt,
                encoding="raw-bytes",
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )

    add_subject("kicad_schematic", schematic, "kicad_sch")
    add_subject("kicad_erc", erc, "json")
    if native_defect != "missing_native_netlist":
        add_subject("kicad_native_netlist", native_netlist, "xml")
    digests = {item.role: item.sha256 for item in subjects}
    native_proof = workspace / "inspection.json"
    native_proof.write_text(json.dumps({
        "schema": "wright-native-kicad-interconnect-v1", "engine": "kicad-cli",
        "status": "exported_not_design_approval", "source_sha256": digests["kicad_schematic"],
        "netlist_sha256": hashlib.sha256(native_netlist.read_bytes()).hexdigest(),
        "erc_sha256": digests["kicad_erc"], "erc_error_count": 0, "erc_warning_count": 0,
    }), encoding="utf-8")
    add_subject("kicad_native_inspection", native_proof, "json")
    correspondence = workspace / "net-correspondence.json"
    correspondence.write_text(
        json.dumps(
            {
                "schema": "wright-harness-kicad-correspondence-v1",
                "status": "pass",
                "schematic_sha256": (
                    "0" * 64 if corrupt_kicad_binding else digests["kicad_schematic"]
                ),
                "pin_schedule_sha256": digests["pin_schedule"],
                "netlist_sha256": digests["netlist"],
                "erc_sha256": digests["kicad_erc"],
                "missing_rows": [],
                "extra_rows": [],
                "mismatched_rows": [],
                "erc_error_count": 0,
            }
        ),
        encoding="utf-8",
    )
    add_subject("net_correspondence", correspondence, "json")
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


def test_kicad_correspondence_rejects_a_wrong_schematic_hash(tmp_path):
    outcome = evaluate(
        tmp_path, "sensor-fan-harness-01", corrupt_kicad_binding=True
    )
    assert any(
        finding.code == "harness.kicad_correspondence"
        for finding in outcome.assessment.findings
    )
    assert not outcome.release_eligible


@pytest.mark.parametrize("defect", ["missing_native_netlist", "missing_splice"])
def test_full_profile_cannot_accept_a_pass_report_without_matching_native_wiring(tmp_path, defect):
    outcome = evaluate(tmp_path, "sensor-fan-harness-01", native_defect=defect)
    assert not outcome.release_eligible
    findings = {finding.check_id: finding for finding in outcome.assessment.findings}
    assert set(findings) == {"voltage-drop", "kicad-correspondence"}
    if defect == "missing_splice":
        assert findings["kicad-correspondence"].code == "harness.kicad_correspondence"
