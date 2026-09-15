"""Structural binding tests, not CAD correctness or campaign run evidence."""
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from tool_registry.runners.stdio import StdioRunner

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_printed", ROOT / "scripts/prepare-printed-dataset-campaign.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
probe_spec = importlib.util.spec_from_file_location(
    "probe_printed_binding", ROOT / "scripts/probe_printed_blender_binding.py"
)
probe = importlib.util.module_from_spec(probe_spec)
probe_spec.loader.exec_module(probe)
repair_spec = importlib.util.spec_from_file_location(
    "printed_mesh_repair", ROOT / "scripts/engineering_dataset_mesh_repair.py"
)
repair_operation = importlib.util.module_from_spec(repair_spec)
repair_spec.loader.exec_module(repair_operation)


@pytest.mark.parametrize("number", [1, 2, 3])
def test_original_full_graph_and_human_inputs_remain_bound(tmp_path, number):
    folder = next((ROOT / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part").glob(f"0{number}-*"))
    source = prepare.TEMPLATE.read_text().replace("__instance__", "api_created_identity")
    instance = tmp_path / "api-instance.wflow"
    instance.write_text(source)
    blender_server = "runtime-blender-id" if number == 3 else prepare.SERVER
    args = SimpleNamespace(attempt="isolated", campaign_id="test-campaign", workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "drafts"), instance_source=str(instance), blender_server=blender_server)
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
    tools[("wright-printed-part-slicer", "slice_model_file")] = {
        "name": "wright-printed-part-slicer__slice_model_file",
        "tool_name": "slice_model_file",
        "server_id": "wright-printed-part-slicer",
        "schema_digest": "fixed-slicer-schema",
    }
    tools[("wright-printed-part-mesh-repair", "repair_model_file")] = {
        "name": "wright-printed-part-mesh-repair__repair_model_file",
        "tool_name": "repair_model_file",
        "server_id": "wright-printed-part-mesh-repair",
        "schema_digest": "fixed-repair-schema",
    }
    result = prepare.prepare(args, folder, tools)
    bound = Path(result["draft"]).read_text()
    plan = prepare.compile_prompt_workflow(bound)
    assert len(plan.steps) == 4
    assert all(step.id.endswith("api_created_identity") for step in plan.steps)
    assert all(step.expected_files for step in plan.steps[:3])
    assert plan.steps[0].server_id == blender_server
    assert plan.steps[1].server_id == "wright-printed-part-mesh-repair"
    assert plan.steps[1].tool_name == "wright-printed-part-mesh-repair__repair_model_file"
    assert plan.steps[1].schema_digest == "fixed-repair-schema"
    assert not plan.steps[1].agent_task
    assert plan.steps[2].server_id == "wright-printed-part-slicer"
    assert plan.steps[2].tool_name == "wright-printed-part-slicer__slice_model_file"
    assert plan.steps[2].schema_digest == "fixed-slicer-schema"
    assert not plan.steps[2].agent_task
    assert "runpy.run_path" not in plan.steps[2].prompt
    assert "runpy.run_path" not in plan.steps[0].prompt
    assert "runpy.run_path" not in plan.steps[1].prompt
    assert plan.steps[0].expected_files == (
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/source_mesh.stl",
    )
    assert plan.steps[1].expected_files == (
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/repaired_mesh.stl",
        f"campaign/printed-replacement-part-0{number}/isolated/artifacts/mesh-preview.png",
    )
    assert plan.steps[1].arguments["configuration_document"].endswith(
        "/mesh-repair-operation.json"
    )
    assert plan.steps[1].arguments["operation_source_document"].endswith(
        "/mesh-repair-operation.py"
    )
    assert plan.steps[1].timeout_seconds == 600
    assert plan.steps[1].max_tool_calls == 8
    assert "do not repeat submitted source code" in plan.steps[0].prompt
    assert "do not pass lambda functions or helper-function parameters" in plan.steps[0].task_guidance
    assert "Explicitly import mathutils" in plan.steps[0].task_guidance
    assert "Call bpy.ops.wm.stl_export(...) directly" in plan.steps[0].task_guidance
    assert "never inspect bpy.ops" in plan.steps[0].task_guidance
    assert "Never rebuild already-watertight geometry" in plan.steps[0].task_guidance
    assert "zero boundary/non-manifold edges" in plan.steps[0].task_guidance
    assert plan.steps[-1].external_action["destination"] == {"kind":"integration_test", "id":f"test://test-campaign/printer/printed-replacement-part-0{number}"}
    assert plan.steps[-1].external_action["settings"]["nozzle_mm"] == "0.4"
    sections = prepare._parse(bound)
    image = next(s for s in sections if s["id"].startswith("image_and_scale_"))
    assert image["fields"]["settings"]["workspace_file"].endswith("/concept.png")
    assert len(plan.steps[0].references) == 3  # PNG, natural prompt, assembled human context.
    record = json.loads(Path(result["draft"]).with_name("staging-manifest.json").read_text())
    output_directory = Path(args.workspace_root) / record["output_root"]
    assert output_directory.is_dir()
    assert not any(output_directory.iterdir())
    assert record["requires_template_instance_api"] is False
    assert record["status"] == "prepared_not_dispatched"
    assert record["fixed_slicer_wrapper"]["sha256"] == prepare.digest(
        prepare.SLICE_WRAPPER.read_bytes()
    )
    assert record["fixed_mesh_repair_wrapper"]["operation_sha256"] == prepare.digest(
        prepare.REPAIR_OPERATION.read_bytes()
    )
    assert record["execution_lineage_authority"] == {
        "kind": "canonical_mcp_step_record",
        "model_reports_are_authoritative": False,
        "actual_code": "tool_calls[].arguments.code",
        "input_hashes": "references[].sha256",
        "output_hashes": "produced_files[].sha256",
        "persistence": "canonical run/step evidence written by Wright outside Blender",
    }
    assert plan.steps[0].output_path.endswith("/source-model-report.json")
    assert plan.steps[1].output_path.endswith("/repair-model-report.json")


def test_preparation_rejects_escape_and_different_staged_input(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        prepare.confined(tmp_path, "../outside.txt")
    target = tmp_path / "input.txt"
    prepare.write_once(target, b"human original")
    with pytest.raises(ValueError, match="replace"):
        prepare.write_once(target, b"different text")
    assert target.read_bytes() == b"human original"


@pytest.mark.asyncio
async def test_fixed_slicer_is_a_separate_configured_mcp_tool(tmp_path):
    runner = StdioRunner(
        [sys.executable, str(prepare.SLICE_WRAPPER)],
        env={"WRIGHT_PRINT_WORKSPACE": str(tmp_path)},
        cwd=str(ROOT),
    )
    await runner.start()
    try:
        tools = await runner.list_tools()
    finally:
        await runner.stop()
    assert len(tools) == 1
    assert tools[0]["name"] == "slice_model_file"
    assert set(tools[0]["inputSchema"]["required"]) == {
        "configuration_document",
        "operation_source_document",
    }


@pytest.mark.asyncio
async def test_fixed_mesh_repair_is_a_separate_configured_mcp_tool(tmp_path):
    python_path = os.pathsep.join(
        [
            str(ROOT / "scripts"),
            str(ROOT / ".local-run/feature-081-live/sources/blender-mcp/src"),
        ]
    )
    runner = StdioRunner(
        [sys.executable, str(prepare.REPAIR_WRAPPER)],
        env={
            "WRIGHT_PRINT_WORKSPACE": str(tmp_path),
            "BLENDER_HOST": "127.0.0.1",
            "BLENDER_PORT": "9",
            "PYTHONPATH": python_path,
        },
        cwd=str(ROOT),
    )
    await runner.start()
    try:
        tools = await runner.list_tools()
    finally:
        await runner.stop()
    assert len(tools) == 1
    assert tools[0]["name"] == "repair_model_file"
    assert set(tools[0]["inputSchema"]["required"]) == {
        "configuration_document",
        "operation_source_document",
    }


def test_diagnostic_mesh_code_clears_exact_pinned_guard(tmp_path):
    safe_spec = importlib.util.spec_from_file_location(
        "pinned_blender_safe_mode",
        ROOT
        / ".local-run/feature-081-live/sources/blender-mcp/src/blender_mcp/safe_mode.py",
    )
    safe_mode = importlib.util.module_from_spec(safe_spec)
    safe_spec.loader.exec_module(safe_mode)
    code = probe.guarded_mesh_code(tmp_path / "source.stl", tmp_path / "repaired.stl")
    assert safe_mode.is_safe(code) == (True, "")
    assert safe_mode.is_safe("open('blocked', 'w')")[0] is False
    assert safe_mode.is_safe("import runpy\nrunpy.run_path('blocked.py')")[0] is False


def test_fixed_mesh_repair_code_clears_exact_pinned_guard(tmp_path):
    safe_spec = importlib.util.spec_from_file_location(
        "pinned_blender_safe_mode_fixed_repair",
        ROOT
        / ".local-run/feature-081-live/sources/blender-mcp/src/blender_mcp/safe_mode.py",
    )
    safe_mode = importlib.util.module_from_spec(safe_spec)
    safe_spec.loader.exec_module(safe_mode)
    code = repair_operation.blender_code(
        {
            "source": str(tmp_path / "source_mesh.stl"),
            "repaired": str(tmp_path / "repaired_mesh.stl"),
            "preview": str(tmp_path / "mesh-preview.png"),
            "object_name": "wright_test_repaired",
            "triangle_limit": 80000,
        }
    )
    assert safe_mode.is_safe(code) == (True, "")
    assert "subprocess" not in code
    assert "open(" not in code
