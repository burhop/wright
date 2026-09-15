"""Future graphs preserve inputs while separating bounded native operations."""
import csv
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pcb_bounded_preparer", ROOT / "scripts/prepare-pcb-dataset-campaign.py")
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("index,component_count,pair_calls,combined_minimum", [(1, 6, 8, 22), (2, 14, 15, 37), (3, 15, 16, 39)])
def test_complete_tables_fit_separate_native_stages(tmp_path, index, component_count, pair_calls, combined_minimum):
    directory = next((ROOT / "tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb").glob(f"{index:02d}-*"))
    with (directory / "component-library.csv").open(encoding="utf-8") as stream:
        components = list(csv.DictReader(stream))
    with (directory / "netlist.csv").open(encoding="utf-8") as stream:
        nets = Counter(row["net"] for row in csv.DictReader(stream))
    assert sum(len(row["reference"].split(";")) for row in components) == component_count
    assert sum(math.ceil(count / 2) for count in nets.values()) == pair_calls
    # Optimistic lower bound: two library searches, create/save schematic,
    # create board/set project rules, one build and one inspection. Excludes
    # all mounting-hole work, repairs, and extra distinct library searches.
    assert component_count + pair_calls + 8 == combined_minimum
    assert (combined_minimum > 32) == (index > 1)
    result = preparer.prepare(SimpleNamespace(workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "draft"), attempt="test", instance_source=None, server_id="selected-kicad", tool_catalog=None), directory)
    source = Path(result["source"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 17
    prefixes = ["capture_electrical_basis", "review_electrical_basis", "author_pcb", "connect_native_schematic", "stage_build_schematic", "initialize_native_project", "build_native_board", "finish_native_board", "finish_remaining_native_board", "seal_native_board", "stage_routing_board", "stage_routing_project", "route_native_board", "publish_final_board", "publish_final_project", "publish_final_schematic", "verify_and_export"]
    assert all(step.id.startswith(prefix + "_") for step, prefix in zip(plan.steps, prefixes))
    assert all(step.max_tool_calls == 32 for step in plan.steps if step.agent_task)
    assert all(step.timeout_seconds == 600 for step in plan.steps if step.agent_task)
    assert "/symbols/design.kicad_sch" in plan.steps[2].expected_files[0]
    assert "leave enough room for a 2.54 mm label wire stub" in plan.steps[2].prompt
    assert "do not stack adjacent vertical passives" in plan.steps[2].prompt
    assert "/connected/design.kicad_sch" in plan.steps[3].expected_files[0]
    assert "Save exactly once, as the final tool mutation" in plan.steps[3].prompt
    assert "do not mutate or save again" in plan.steps[3].prompt
    assert "approved=false" in plan.steps[6].prompt
    assert "Never call the build again" in plan.steps[6].prompt
    assert "project_rules_updated=true" in plan.steps[5].prompt
    assert not plan.steps[5].expected_files  # initial project is working context
    assert not plan.steps[6].expected_files
    assert "move only electrical references whose source supplies an exact coordinate or named edge location" in plan.steps[6].prompt
    assert "full rotated copper and courtyard extent" in plan.steps[6].prompt
    assert "whose response reports no geometry violation completes that reference" in plan.steps[6].prompt
    assert "at most one corrective move" in plan.steps[6].prompt
    assert "different coordinates calculated from the returned native bounds" in plan.steps[6].prompt
    assert "Never repeat identical move arguments" in plan.steps[6].prompt
    assert "connector center is the geometric center" in plan.steps[6].prompt
    assert "actual pad extents" in plan.steps[6].prompt
    assert "rotated footprint-origin offset" in plan.steps[6].prompt
    assert "rotation 180 places pin 1 toward the top edge" in plan.steps[6].prompt
    assert "no KiCad rule-area keepout authoring operation" in plan.steps[6].prompt
    assert "Never call build_pcb_from_schematic" in plan.steps[7].prompt
    assert "starts with R or C" in plan.steps[7].prompt
    assert "Do not run a whole-board audit" in plan.steps[7].prompt
    assert "Do not set design rules or net classes" in plan.steps[7].prompt
    assert not plan.steps[7].expected_files
    assert "including remaining test points" in plan.steps[8].prompt
    assert "move an R/C reference" in plan.steps[8].prompt
    assert "run one audit" in plan.steps[8].prompt
    assert not plan.steps[8].expected_files
    assert "Reapply every original supplied design rule" in plan.steps[9].prompt
    assert "Make no geometry or text mutation after these rule calls" in plan.steps[9].prompt
    assert "final two tool calls" in plan.steps[9].prompt
    assert "Never call build_pcb_from_schematic" in plan.steps[9].prompt
    assert "move a footprint" in plan.steps[9].prompt
    assert "net_classes=None" in plan.steps[12].prompt
    assert "Before autoroute" in plan.steps[12].prompt
    assert "native_rule_check" in plan.steps[12].prompt
    assert "Call autoroute exactly once" in plan.steps[12].prompt
    assert "exclude only unconnected_items from the pre-route blocking-error count" in plan.steps[12].prompt
    assert "zero other DRC errors" in plan.steps[12].prompt
    assert "Do not move footprints" in plan.steps[12].prompt
    assert "never call board save" in plan.steps[16].prompt
    declared = [path for step in plan.steps for path in step.expected_files]
    assert len(declared) == len(set(declared))  # no immutable native path is recaptured after mutation
    for index in [4, 6, 7, 8, 10, 11]:
        assert not plan.steps[index].expected_files  # mutable staging copies
    for index in [13, 14, 15]:
        assert len(plan.steps[index].expected_files) == 1  # final copies are captured once
    tasks = {section["id"]: section for section in _parse(source) if section["kind"] == "task"}
    produced_before = set()
    copies = []
    for step in plan.steps:
        settings = tasks[step.id]["fields"]["settings"]
        if settings.get("mcp_tool") == "wright-workspace-files__copy_file":
            arguments = json.loads(settings["mcp_arguments"])
            assert arguments["sourcePath"] in produced_before
            assert arguments["sourcePath"] != arguments["destinationPath"]
            assert (tmp_path / "workspace" / arguments["destinationPath"]).parent.is_dir()
            copies.append(arguments)
        produced_before.update(step.expected_files)
    assert len(copies) == 6
    report = json.loads(Path(result["source"]).with_name("staging-manifest.json").read_text())
    assert report["input_binding_evidence"]["complete"]
    original = _parse(preparer.TEMPLATE.read_text().replace("__instance__", report["scenario_id"].replace("-", "_") + "_test"))
    assert all(edge in _parse(source) for edge in original if edge["kind"] == "connection")
