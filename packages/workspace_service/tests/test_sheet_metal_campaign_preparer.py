"""Draft binding preserves engineering scope without executing provider tools."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import compile_prompt_workflow, _parse

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "sheet_metal_preparer", ROOT / "scripts/prepare-sheet-metal-dataset-campaign.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
@pytest.mark.parametrize("cad_server_id", [None, "isolated-cad-installation"])
def test_prepared_case_retains_every_original_gate_and_human_input(
    tmp_path, ordinal, cad_server_id
):
    config = json.loads(preparer.BINDING.read_text())
    tools = [
        {
            "server_id": server,
            "tool_name": name,
            "name": server + "__" + name,
            "schema_digest": "a" * 64,
        }
        for server, names in config["allowed_tools"].items()
        for name in names
    ]
    tools.extend(
        {
            "server_id": "dxf",
            "tool_name": name,
            "name": "dxf__" + name,
            "schema_digest": "a" * 64,
        }
        for name in config["headless_dxf_review"]["tools"]
    )
    if cad_server_id:
        for tool in tools:
            if tool["server_id"] == preparer.SERVER:
                tool["server_id"] = cad_server_id
                tool["name"] = cad_server_id + "__" + tool["tool_name"]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "drafts"),
        attempt="attempt-test",
        instance_source=None,
        campaign_id="test-campaign",
        cad_server_id=cad_server_id,
    )
    directory = next(
        path
        for path in (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff"
        ).iterdir()
        if path.name.startswith(f"{ordinal:02d}-")
    )
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text()
    plan = compile_prompt_workflow(source)
    selected_cad = cad_server_id or preparer.SERVER
    cad_steps = [
        step
        for step in plan.steps
        if step.agent_task and step.server_id == selected_cad
    ]
    assert cad_steps
    if cad_server_id:
        assert not any(step.server_id == preparer.SERVER for step in plan.steps)
    manifest = json.loads(
        Path(result["draft"]).with_name("staging-manifest.json").read_text()
    )
    assert result["executed"] is False
    research = next(
        step for step in plan.steps if step.id.startswith("supplier_research_")
    )
    seal = next(
        step for step in plan.steps if step.id.startswith("seal_supplier_evidence_")
    )
    assert seal.arguments["sourcePath"] in research.expected_files
    assert seal.arguments["sourcePath"].endswith("/supplier-evidence.json")
    assert plan.steps.index(research) < plan.steps.index(seal)
    sealed = Path(args.workspace_root) / seal.arguments["destinationPath"]
    assert sealed.parent.is_dir()
    assert not sealed.exists()
    assert len(manifest["preserved_original_stages"]) == 6
    assert len(manifest["preserved_original_edges"]) == 6
    assert len(plan.revisions) == 1
    assert any(step.design_check and step.max_revisions == 2 for step in plan.steps)
    gates = [step for step in plan.steps if step.external_action]
    assert [step.external_action["action_kind"] for step in gates] == [
        "local_review",
        "supplier_upload_preview",
        "cart_quote_handoff",
        "local_review",
    ]
    assert any(step.id.startswith("collect_handoff_") for step in plan.steps)
    assert plan.steps[-1].id.startswith("validate_sheet_content_")
    for gate in gates[1:3]:
        assert gate.external_action["destination"]["id"].startswith(
            "test://test-campaign/supplier/"
        )
        assert gate.external_action["settings"]["simulation"] is True
        assert gate.external_action["settings"]["manufacturing_release"] == "HOLD"
        assert gate.external_action["settings"]["supplier_acceptance"] == "unverified"
        assert gate.external_action["action"]["order"] is False
    assert gates[-1].external_action["settings"]["validation_review"]["requirement_ids"]
    assert len(
        [step for step in plan.steps if step.cad and step.cad["source"] == "new"]
    ) == (2 if ordinal == 3 else 1)
    assert len(
        [
            export
            for step in plan.steps
            if step.cad
            for export in step.cad.get("exports", [])
            if export["format"] == "flat_dxf"
        ]
    ) == (2 if ordinal == 3 else 1)
    assert all(
        step.cad["policy"] == "indexed"
        for step in plan.steps
        if step.cad and step.cad["source"] == "new"
    )
    context_file = next(
        item
        for item in manifest["input_manifest"]
        if item["path"].endswith("assembled-context.md")
    )
    context = (Path(args.workspace_root) / context_file["path"]).read_text()
    assert (directory / "prompt.txt").read_text().strip() in context
    assert (directory / "manufacturing-policy.md").read_text().strip() in context
    assert (directory / "stock-selection-revision-r1.md").read_text().strip() in context
    for table in directory.glob("*.csv"):
        assert table.read_text().strip() in context
    sections = _parse(source)
    images = [
        section
        for section in sections
        if section["kind"] == "input"
        and section["fields"]["outputs"][0]["kind"] == "reference_images"
    ]
    assert len(images) == 1
    assert (
        (Path(args.workspace_root) / images[0]["fields"]["settings"]["workspace_file"])
        .read_bytes()
        .startswith(b"\x89PNG")
    )
    assert not any(
        item.is_file()
        for item in (Path(args.workspace_root) / manifest["output_root"]).rglob("*")
    )
    if ordinal == 3:
        assert any(
            item["role"] == "base-tray_native_sheet_metal"
            for item in manifest["expected_outputs"]
        )
        assert any(
            item["role"] == "removable-lid_developed_flat_pattern"
            for item in manifest["expected_outputs"]
        )
