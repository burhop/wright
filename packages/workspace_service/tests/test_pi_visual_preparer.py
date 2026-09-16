import importlib.util
import ast
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from workspace_service.workflow_references import WorkflowReference
from workspace_service.workflow_source_execution import (
    _parse,
    _reference_prompt_context,
    compile_prompt_workflow,
)

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "pi_visual_prepare_tests", ROOT / "scripts/prepare-pi-visual-dataset-campaign.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_visual_pi_preserves_real_stages_review_and_bounded_artifacts(
    tmp_path, ordinal
):
    config = json.loads(preparer.BINDING.read_text())
    tools = [
        {
            "server_id": server,
            "tool_name": name,
            "name": f"{server}__{name}",
            "schema_digest": "a" * 64,
        }
        for server, names in config["allowed_tools"].items()
        for name in names
    ]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"),
        instance_source=None,
        attempt="unit",
        initialize_agentcad=False,
    )
    directory = next(
        path
        for path in (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure"
        ).iterdir()
        if path.name.startswith(f"{ordinal:02d}")
    )
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    report = json.loads(
        Path(result["draft"]).with_name("staging-manifest.json").read_text()
    )
    assert len(plan.steps) == 11
    assert len(report["preserved_original_stages"]) == 4
    assert all(
        any(step.id == original for step in plan.steps)
        for original in report["preserved_original_stages"]
    )
    assert plan.steps[2].external_action["action_kind"] == "local_review"
    original_edges = [
        part
        for part in _parse(
            preparer.TEMPLATE.read_text().replace(
                "__instance__", report["scenario_id"].replace("-", "_") + "_unit"
            )
        )
        if part["kind"] == "connection"
    ]
    assert all(edge in _parse(source) for edge in original_edges)
    assert all(len(step.expected_files) <= 16 for step in plan.steps)
    assert all(
        tool["server_id"] != "blender-mcp-ahujasid" for tool in report["tool_allowlist"]
    )
    assert "execute_blender_code" not in source
    assert "observe_pi_primary_page" in source and "4000characters" in source
    assert "insert-dimensions.jpg" in source
    assert "inspect_file" in source
    author = next(s for s in plan.steps if s.id.startswith("author_cad_source_"))
    basis = next(s for s in plan.steps if s.id.startswith("design_basis_"))
    assert "at or below 12000 characters" in basis.prompt
    assert "at most 64 closed solids" in author.prompt
    assert "enclosure-a/b STEP and matching STL contain only PETG" in author.prompt
    assert (
        "contain no board, inserts, heat sources or display assembly" in author.prompt
    )
    assert (
        "subtract the complete board, brass inserts and heat sources from PETG"
        in author.prompt
    )
    assert "subtract complete brass-insert outer solids" in author.prompt
    assert "Subtract fluid cutters one solid at a time" in author.prompt
    assert "power_interface-a.step and power_interface-b.step" in author.prompt
    assert "never as a multi-solid Compound" in author.prompt
    assert "petg_shell points to the matching PETG-only STEP" in author.prompt
    assert "Never export overlapping regions" in author.prompt
    assert (
        "Do not add pairwise pre-export Compound intersection checks" in author.prompt
    )
    assert "Null TopoDS_Shape" in author.prompt
    assert "align=(Align.MIN, Align.MIN, Align.MIN)" in author.prompt
    assert "final fluid shape bounding_box()" in author.prompt
    assert "observed plane coordinates, not constructor inputs" in author.prompt
    assert "__agentcad_script__" in author.prompt
    assert "Shape.rotate(Axis, angle_degrees)" in author.prompt
    assert "Compound(shape_list)" in author.prompt
    assert "Align enum members" in author.prompt
    assert "list(shape.solids())" in author.prompt
    assert "Never wrap shape.solids() in a temporary Compound" in author.prompt
    assert "children is not the solid enumeration and can be empty" in author.prompt
    inspection = next(s for s in plan.steps if s.id.startswith("inspect_cad_exports_"))
    cad = next(s for s in plan.steps if s.id.startswith("agentcad_enclosure_"))
    assert not cad.agent_task
    assert cad.server_id == "agentcad"
    assert cad.tool_name == "agentcad__run"
    assert cad.source_contract == "agentcad-build123d-0.10"
    assert cad.arguments == {
        "script": str(
            Path(args.workspace_root).resolve()
            / report["output_root"]
            / "enclosure-source.py"
        ),
        "output": "pi-comparison",
        "cwd": str(
            Path(args.workspace_root).resolve()
            / report["output_root"]
            / "agentcad-project"
        ),
        "build_dir": "build",
        "preview": False,
        "view": False,
        "diff": False,
    }
    assert "includeText=true,maxTextBytes=4096" in author.prompt
    assert "deliberately omitted from connected reference text" in author.prompt
    assert "maxTextBytes=4096" in author.prompt
    assert "includeText=false" in inspection.prompt
    assert "complete durable files remain on disk" in inspection.prompt
    assert "must not be copied into the model response" in inspection.prompt
    assert "maxTextBytes=32768" not in source
    assert inspection.max_tool_calls == 18
    # Resolve the actual inspection arguments against the compiled producer
    # and staged bytes. The generated basis does not live beside input files.
    inspected = [
        ast.literal_eval(value)
        for value in re.findall(
            r"inspect_file\(relativePath=('[^']+'),includeText=true,maxTextBytes=4096\)",
            author.prompt,
        )
    ]
    basis = next(s for s in plan.steps if s.id.startswith("design_basis_"))
    contract = next(
        item
        for item in report["input_manifest"]
        if item["path"].endswith("/fixed-cfd-contract.md")
    )
    assert inspected == [basis.output_path, contract["path"]]
    contract_bytes = (Path(args.workspace_root) / contract["path"]).read_bytes()
    assert hashlib.sha256(contract_bytes).hexdigest() == contract["sha256"]
    assert contract_bytes == (ROOT / "scripts/pi_cfd_contract.md").read_bytes()
    assert not (Path(args.workspace_root) / basis.output_path).exists()
    assert basis.output_path not in {item["path"] for item in report["input_manifest"]}
    # Paging changes the observation transport, not the complete connected
    # design/contract references or the archived human input bytes.
    author_section = next(s for s in _parse(source) if s["id"] == author.id)
    assert not any(
        p["key"].endswith("accepted_design") for p in author_section["fields"]["inputs"]
    )
    assert not any(
        p["key"].endswith("fixed_contract") for p in author_section["fields"]["inputs"]
    )
    assert not any(
        p["key"].endswith("human_context") for p in author_section["fields"]["inputs"]
    )
    assert any(s.id.startswith("inspect_cad_exports_") for s in plan.steps)
    assert "prototype design authority" in (
        Path(args.workspace_root)
        / report["output_root"].replace("/artifacts", "/inputs/assembled-context.md")
    ).read_text(encoding="utf-8")
    assert ("NO fan" in source) == (ordinal != 3)
    assert ("This case includes the exact uploaded synthetic fan curve" in source) == (
        ordinal == 3
    )
    assert "cfd-contract-a.json" in source and "cfd-contract-b.json" in source
    assert source.count("prepare_pi_cfd_variant exactly once") == 2
    assert "/pi-cfd/variant-a" in source and "/pi-cfd/variant-b" in source
    foam_runs = [step for step in plan.steps if step.server_id == "foam-agent-csml-rpi"]
    assert len(foam_runs) == 2
    assert all(not step.agent_task for step in foam_runs)
    assert all(step.tool_name == "foam-agent-csml-rpi__run" for step in foam_runs)
    assert {step.arguments["request"]["case_dir"] for step in foam_runs} == {
        f"/workspace/campaign/{report['scenario_id']}/unit/pi-cfd/variant-a",
        f"/workspace/campaign/{report['scenario_id']}/unit/pi-cfd/variant-b",
    }
    assert all(step.arguments["request"]["timeout"] == 540 for step in foam_runs)
    compact_reference_tasks = [
        step
        for step in plan.steps
        if step.id.startswith(("prepare_cfd_case_", "prepare_cfd_variant_b_"))
    ]
    assert len(compact_reference_tasks) == 2
    assert all(
        step.reference_inline_max_bytes == 12000 for step in compact_reference_tasks
    )
    assert any(
        path.endswith("board-a.step") for path in report["expected_tool_created_files"]
    )
    assert report["native_initialization"] == "requires_native_initialization"
    assert report["blockers"]
    for path in directory.iterdir():
        if path.is_file():
            item = next(
                item
                for item in report["input_manifest"]
                if item.get("original") == path.relative_to(ROOT).as_posix()
            )
            assert (
                Path(args.workspace_root) / item["path"]
            ).read_bytes() == path.read_bytes()
            if path.suffix in {".csv", ".tsv"}:
                assembled = (
                    Path(args.workspace_root)
                    / report["output_root"].replace(
                        "/artifacts", "/inputs/assembled-context.md"
                    )
                ).read_text(encoding="utf-8")
                assert path.read_text(encoding="utf-8") in assembled


def test_large_connected_compiler_source_keeps_identity_without_prompt_bytes():
    source = (ROOT / "scripts/pi_cfd_operations.py").read_bytes()
    reference = WorkflowReference.from_bytes(
        "campaign/pi03/inputs/pi_cfd_operations.py",
        source,
        image=False,
    )

    context, record = _reference_prompt_context(
        "fixed_compiler_source", reference, 12000
    )

    assert len(source) > 12000
    assert reference.text not in context
    assert reference.path in context
    assert reference.sha256 in context
    assert record == {
        "path": reference.path,
        "sha256": reference.sha256,
        "kind": "text",
        "size_bytes": len(source),
        "contents_inlined": False,
    }
