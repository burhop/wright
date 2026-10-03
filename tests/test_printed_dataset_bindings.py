"""Structural binding tests, not CAD correctness or campaign run evidence."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
fixture_spec = importlib.util.spec_from_file_location("external_slice_fixture", ROOT / "tests/fixtures/external_slice_binding.py")
slice_fixture = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(slice_fixture)
mesh_fixture_spec = importlib.util.spec_from_file_location("external_mesh_fixture", ROOT / "tests/fixtures/external_mesh_binding.py")
mesh_fixture = importlib.util.module_from_spec(mesh_fixture_spec)
mesh_fixture_spec.loader.exec_module(mesh_fixture)

BLENDER_MCP_FIXTURE = ROOT / "tests/fixtures/blender_mcp_5f8ddaf6"
BLENDER_MCP_SOURCE = BLENDER_MCP_FIXTURE / "src"
BLENDER_SAFE_MODE = BLENDER_MCP_SOURCE / "blender_mcp/safe_mode.py"
BLENDER_SAFE_MODE_SHA256 = (
    "d3bc1f43f4707476e595efed111d514b3f81bf4358993b8accb18962c5c4bf35"
)


def text_sha256(path: Path) -> str:
    """Hash Git text content independently of checkout line-ending policy."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


spec = importlib.util.spec_from_file_location(
    "prepare_printed", ROOT / "scripts/prepare-printed-dataset-campaign.py"
)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
probe_spec = importlib.util.spec_from_file_location(
    "probe_printed_binding", ROOT / "scripts/probe_printed_blender_binding.py"
)
probe = importlib.util.module_from_spec(probe_spec)
probe_spec.loader.exec_module(probe)


@pytest.mark.parametrize("number, with_correction", [(1, False), (2, False), (2, True), (3, False)])
def test_original_full_graph_and_human_inputs_remain_bound(tmp_path, number, with_correction):
    folder = next(
        (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part"
        ).glob(f"0{number}-*")
    )
    source = prepare.TEMPLATE.read_text().replace(
        "__instance__", "api_created_identity"
    )
    instance = tmp_path / "api-instance.wflow"
    instance.write_text(source)
    blender_server = "runtime-blender-id" if number == 3 else prepare.SERVER
    args = SimpleNamespace(
        attempt="isolated",
        campaign_id="test-campaign",
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "drafts"),
        instance_source=str(instance),
        blender_server=blender_server,
    )
    if with_correction:
        correction = tmp_path / "retained-correction.py"
        correction.write_bytes(b"import bpy\n# Test of input binding only; never executed.\n")
        proof = tmp_path / "qualification.json"
        proof.write_text(json.dumps({
            "status": "qualified",
            "source_code_after_sha256": prepare.digest(correction.read_bytes()),
            "operation_sha256": json.loads(prepare.REPAIR_POLICY.read_bytes())["archived_operation_sha256"],
            "cleanup": {"status": "cleaned", "post_cleanup_identity": None},
        }), encoding="utf-8")
        args.review_correction_source = str(correction)
        args.review_correction_proof = str(proof)
    names = json.loads(prepare.BINDING.read_text())["allowed_tools"]
    tools = {
        (blender_server, name): {
            "name": f"{blender_server}__{name}",
            "tool_name": name,
            "server_id": blender_server,
            "schema_digest": "test-only",
        }
        for name in names
    }
    args.slicer_binding, extra_tools = slice_fixture.make_binding(
        tmp_path / "external-binding", f"printed-replacement-part-0{number}",
        json.loads(prepare.BINDING.read_text())["scenarios"][f"printed-replacement-part-0{number}"]["process"],
    )
    tools.update({(item["server_id"], item["tool_name"]): item for item in extra_tools})
    machine_profile = json.loads(Path(args.slicer_binding).read_bytes())["profiles"]["machine"]["path"]
    args.repair_binding = mesh_fixture.make_binding(
        tmp_path / "mesh-binding", f"printed-replacement-part-0{number}", args.workspace_root,
        args.attempt, prepare.REPAIR_POLICY, machine_profile,
        tools[(blender_server, "execute_blender_code")],
    )
    result = prepare.prepare(args, folder, tools)
    bound = Path(result["draft"]).read_text()
    plan = prepare.compile_prompt_workflow(bound)
    original_steps = [step for step in plan.steps if not step.id.startswith(("invoke_external_slice_", "retain_slice_response_", "inspect_repaired_mesh_", "validate_repaired_mesh_"))]
    assert len(plan.steps) == 10
    actual_inspection = next(step for step in plan.steps if step.id.startswith("inspect_repaired_mesh_"))
    mesh_gate = next(step for step in plan.steps if step.id.startswith("validate_repaired_mesh_"))
    assert not mesh_gate.tool_name and mesh_gate.validation
    assert dict(mesh_gate.validation_sources) == {
        "repaired_mesh": original_steps[1].id + ".repaired_mesh",
        "mesh_evidence": actual_inspection.id + ".mesh_evidence",
    }
    from core.process_validation import ValidationProfile

    mesh_profile = ValidationProfile.model_validate_json(
        (Path(args.workspace_root) / mesh_gate.validation["profile"]["name"]).read_bytes()
    )
    assert mesh_profile.reference().model_dump(mode="json") == mesh_gate.validation["profile"]["reference"]
    assert len(mesh_profile.checks) == (14 if number == 2 else 13)
    raw_checks = {check.id: check for check in mesh_profile.checks if check.reader == "printing"}
    assert len(raw_checks) == 7 and all(check.evidence_method == "independent_measurement" for check in raw_checks.values())
    assert raw_checks["actual-connected_components"].constraint.expected == 1
    assert raw_checks["actual-signed_volume_mm3"].constraint.minimum == 0.0
    assert raw_checks["actual-signed_volume_mm3"].constraint.inclusive is False
    assert raw_checks["actual-triangle_count"].constraint.maximum == (24000 if number == 2 else 80000)
    assert all(check.evidence_method == "structured_value" for check in mesh_profile.checks if check.reader == "structured")
    assert all(requirement.mandatory and not requirement.review_required for requirement in mesh_profile.baseline.requirements)
    mesh_gate = next(step for step in plan.steps if step.id.startswith("validate_repaired_mesh_"))
    assert not mesh_gate.tool_name and mesh_gate.validation
    assert dict(mesh_gate.validation_sources) == {
        "repaired_mesh": original_steps[1].id + ".repaired_mesh",
        "mesh_evidence": actual_inspection.id + ".mesh_evidence",
    }
    from core.process_validation import ValidationProfile

    mesh_profile = ValidationProfile.model_validate_json(
        (Path(args.workspace_root) / mesh_gate.validation["profile"]["name"]).read_bytes()
    )
    assert mesh_profile.reference().model_dump(mode="json") == mesh_gate.validation["profile"]["reference"]
    assert len(mesh_profile.checks) == (14 if number == 2 else 13)
    raw_checks = {check.id: check for check in mesh_profile.checks if check.reader == "printing"}
    assert len(raw_checks) == 7 and all(check.evidence_method == "independent_measurement" for check in raw_checks.values())
    assert raw_checks["actual-connected_components"].constraint.expected == 1
    assert raw_checks["actual-signed_volume_mm3"].constraint.minimum == 0.0
    assert raw_checks["actual-signed_volume_mm3"].constraint.inclusive is False
    assert raw_checks["actual-triangle_count"].constraint.maximum == (24000 if number == 2 else 80000)
    assert all(check.evidence_method == "structured_value" for check in mesh_profile.checks if check.reader == "structured")
    assert all(requirement.mandatory and not requirement.review_required for requirement in mesh_profile.baseline.requirements)
    assert actual_inspection.server_id == "independent-python"
    assert actual_inspection.arguments["critic_approved"] is False
    assert actual_inspection.arguments["job_name"].startswith("/workspace/campaign/")
    assert "'measure_handle_features': " + str(number == 2) in actual_inspection.arguments["input_content"]
    native_slice = next(step for step in plan.steps if step.id.startswith("invoke_external_slice_"))
    assert native_slice.tool_name == "independent-offline-slicer__slice_model_file"
    assert Path(native_slice.arguments["source"]).name == "repaired_mesh.stl"
    assert Path(native_slice.arguments["output"]).name == "slice_package.gcode.3mf"
    repair_configuration = json.loads(
        (
            Path(args.workspace_root)
            / f"campaign/printed-replacement-part-0{number}/isolated/inputs/mesh-inspection-policy.json"
        ).read_text()
    )
    assert repair_configuration["force_voxel_remesh"] is False
    assert repair_configuration["triangle_limit"] == (24000 if number == 2 else 80000)
    assert repair_configuration["envelope_margin_mm"] == 0.0
    assert repair_configuration["planar_cleanup"] is (number == 2)
    assert repair_configuration["build_volume_mm"] == [256, 256, 256]
    assert len(original_steps) == 6
    assert all(step.id.endswith("api_created_identity") for step in original_steps[:4])
    assert all(step.expected_files for step in original_steps[:3])
    assert original_steps[0].server_id == blender_server
    assert original_steps[1].server_id == blender_server
    assert (
        original_steps[1].tool_name == blender_server + "__execute_blender_code"
    )
    assert original_steps[1].schema_digest == "test-only"
    assert not original_steps[1].agent_task
    assert original_steps[2].server_id == "independent-python"
    assert original_steps[2].tool_name == "independent-python__run_simulation"
    assert original_steps[2].schema_digest == "c" * 64
    assert not original_steps[2].agent_task
    assert "runpy.run_path" not in original_steps[2].prompt
    assert "runpy.run_path" not in original_steps[0].prompt
    assert "runpy.run_path" not in original_steps[1].prompt
    expected_source_files = (
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/source_mesh.stl",
    )
    if number == 2:
        expected_source_files += ("campaign/printed-replacement-part-02/isolated/artifacts/native-design.blend",)
        assert "X=15.5 and X=80.5" in original_steps[0].prompt
        assert "save_as_mainfile" in original_steps[0].prompt
        assert "copy=True" in original_steps[0].prompt
    assert original_steps[0].expected_files == expected_source_files
    if with_correction:
        assert "changing only the two export paths" in original_steps[0].prompt
        assert any("review correction source" in reference[0] for reference in original_steps[0].references)
        staged = Path(args.workspace_root) / "campaign/printed-replacement-part-02/isolated/inputs/review-correction-source.py"
        assert staged.read_bytes() == correction.read_bytes()
        # A changed source cannot reuse this qualification in a fresh attempt.
        correction.write_bytes(b"# Modified and not qualified\n")
        args.attempt = "tampered"
        args.repair_binding = mesh_fixture.make_binding(
            tmp_path / "mesh-binding-tampered", f"printed-replacement-part-0{number}", args.workspace_root,
            args.attempt, prepare.REPAIR_POLICY, machine_profile,
            tools[(blender_server, "execute_blender_code")],
        )
        with pytest.raises(ValueError, match="qualification identity"):
            prepare.prepare(args, folder, tools)
        assert not (Path(args.workspace_root) / "campaign/printed-replacement-part-02/tampered").exists()
    assert original_steps[1].expected_files == (
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/repaired_mesh.stl",
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/mesh-preview.png",
    )
    assert original_steps[1].arguments == {}
    assert original_steps[1].arguments_from
    native_arguments = Path(args.workspace_root) / f"campaign/printed-replacement-part-0{number}/isolated/inputs/mesh-provider-arguments.json"
    original_arguments = tmp_path / "mesh-binding/provider-arguments.json"
    assert native_arguments.read_bytes() == original_arguments.read_bytes()
    assert dict(original_steps[1].file_dependencies)[original_steps[0].id + ".source_mesh"].endswith("/source_mesh.stl")
    assert original_steps[1].timeout_seconds == 600
    assert original_steps[1].max_tool_calls == 8
    assert "do not repeat submitted source code" in original_steps[0].prompt
    assert (
        "do not pass lambda functions or helper-function parameters"
        in original_steps[0].task_guidance
    )
    assert "Explicitly import mathutils" in original_steps[0].task_guidance
    assert "Call bpy.ops.wm.stl_export(...) directly" in original_steps[0].task_guidance
    assert "never inspect bpy.ops" in original_steps[0].task_guidance
    assert "Never rebuild already-watertight geometry" in original_steps[0].task_guidance
    assert "zero boundary/non-manifold edges" in original_steps[0].task_guidance
    assert original_steps[3].external_action["destination"] == {
        "kind": "integration_test",
        "id": f"test://test-campaign/printer/printed-replacement-part-0{number}",
    }
    assert original_steps[3].external_action["settings"]["nozzle_mm"] == "0.4"
    assert original_steps[3].output_ports == (("receipt", "workspace_file"),)
    assert set(original_steps[0].expected_file_ports) == ({"source_mesh", "native_design"} if number == 2 else {"source_mesh"})
    assert set(original_steps[1].expected_file_ports) == {"repaired_mesh", "geometry_preview"}
    assert set(original_steps[2].expected_file_ports) == {
        "support_preview",
        "slice_evidence",
        "machine_profile",
        "filament_profile",
        "process_profile",
        "toolpath_preview",
        "toolpath_summary",
        "slice_preview",
    }
    review = original_steps[4]
    validator = original_steps[5]
    assert dict(validator.validation_sources)["slice_package"] == native_slice.id + ".external_slice_package"
    assert native_slice.expected_file_ports["external_slice_package"] not in original_steps[2].expected_files
    assert review.external_action["action_kind"] == "local_review"
    assert {role for role, _ in validator.validation_sources} == {
        "source_mesh",
        "source_report",
        "repaired_mesh",
        "support_preview",
        "slice_package",
        "slice_evidence",
        "machine_profile",
        "filament_profile",
        "process_profile",
        "transfer_receipt",
    }
    assert validator.validation["profile"]["name"] == (
        f"printed-replacement-part-0{number}"
    )
    configured_review = review.external_action["settings"]["validation_review"]
    assert configured_review["profile_ref"] == validator.validation["profile"][
        "reference"
    ]
    assert configured_review["requirement_ids"]
    if number == 2:
        assert any("native design" in reference[0].lower() for reference in review.references), review.references
        assert any("final feature measurements" in reference[0].lower() for reference in review.references), review.references
    assert plan.revisions == {}
    sections = prepare._parse(bound)
    connections = [s["fields"] for s in sections if s["kind"] == "connection"]
    endpoint_pairs = [(s["from"], s["to"]) for s in connections]
    assert len(endpoint_pairs) == len(set(endpoint_pairs))
    assert sum(
        s["type"] == "order"
        and s["from"] == original_steps[0].id
        and s["to"] == original_steps[1].id
        for s in connections
    ) == 1
    image = next(s for s in sections if s["id"].startswith("image_and_scale_"))
    assert image["fields"]["settings"]["workspace_file"].endswith("/concept.png")
    assert len(original_steps[0].references) == (6 if with_correction else 4)
    # PNG, natural prompt, assembled human context, approved engineering brief.
    record = json.loads(
        Path(result["draft"]).with_name("staging-manifest.json").read_text()
    )
    output_directory = Path(args.workspace_root) / record["output_root"]
    assert output_directory.is_dir()
    assert not any(output_directory.iterdir())
    assert record["requires_template_instance_api"] is False
    assert record["status"] == "prepared_not_dispatched"
    assert record["external_slicer_binding"]["vendor_implementation"] == "independent_provider"
    assert not any("slice-operation.py" in row["path"] for row in record["input_manifest"])
    assert "engineering_dataset_slice" not in bound
    assert record["external_mesh_binding"]["vendor_implementation"] == "independent_provider"
    assert record["external_mesh_binding"]["arguments_sha256"] == prepare.digest(original_arguments.read_bytes())
    assert "fixed_mesh_repair_wrapper" not in record
    assert not any("mesh-repair-operation.py" in item["path"] for item in record["input_manifest"])
    assert any(
        connection["type"] == "order" and connection["from"] == record["external_mesh_binding"]["validation_step_id"]
        and connection["to"] == native_slice.id for connection in connections
    )
    assert record["execution_lineage_authority"] == {
        "kind": "canonical_mcp_step_record",
        "model_reports_are_authoritative": False,
        "actual_code": "tool_calls[].arguments.code",
        "input_hashes": "references[].sha256",
        "output_hashes": "produced_files[].sha256",
        "persistence": "canonical run/step evidence written by Wright outside Blender",
    }
    assert original_steps[0].output_path.endswith("/source-model-report.json")
    assert original_steps[1].output_path.endswith("/repair-model-report.json")


def test_preparation_rejects_escape_and_different_staged_input(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        prepare.confined(tmp_path, "../outside.txt")
    target = tmp_path / "input.txt"
    prepare.write_once(target, b"human original")
    with pytest.raises(ValueError, match="replace"):
        prepare.write_once(target, b"different text")
    assert target.read_bytes() == b"human original"




def test_diagnostic_mesh_code_clears_exact_pinned_guard(tmp_path):
    assert text_sha256(BLENDER_SAFE_MODE) == BLENDER_SAFE_MODE_SHA256
    safe_spec = importlib.util.spec_from_file_location(
        "pinned_blender_safe_mode",
        BLENDER_SAFE_MODE,
    )
    safe_mode = importlib.util.module_from_spec(safe_spec)
    safe_spec.loader.exec_module(safe_mode)
    code = probe.guarded_mesh_code(tmp_path / "source.stl", tmp_path / "repaired.stl")
    assert safe_mode.is_safe(code) == (True, "")
    assert safe_mode.is_safe("open('blocked', 'w')")[0] is False
    assert safe_mode.is_safe("import runpy\nrunpy.run_path('blocked.py')")[0] is False
