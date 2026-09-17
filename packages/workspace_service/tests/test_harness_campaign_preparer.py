import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from workspace_service.workflow_source_execution import compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "harness_preparer", ROOT / "scripts/prepare-harness-dataset-campaign.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_harness_keeps_original_review_nets_and_all_outputs(tmp_path, ordinal):
    config = json.loads(preparer.BINDING.read_text())
    server = "harness-test-server"
    tools = [
        {"server_id": server, "tool_name": name, "schema_digest": "a" * 64}
        for name in config["allowed_tools"]
    ]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"),
        instance_source=None,
        attempt="unit",
        server_id=server,
    )
    directory = next(
        p
        for p in (
            ROOT / "tests/datasets/engineering-workflows/scenarios/sensor-fan-harness"
        ).iterdir()
        if p.name.startswith(f"{ordinal:02d}")
    )
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text()
    plan = compile_prompt_workflow(source)
    manifest = json.loads(
        Path(result["draft"]).with_name("staging-manifest.json").read_text()
    )
    assert len(plan.steps) == 7
    assert plan.steps[0].id.startswith("research_exact_parts_")
    assert plan.steps[1].id.startswith("define_harness_")
    assert plan.steps[1].external_action["action_kind"] == "local_review"
    assert plan.steps[2].id.startswith("generate_harness_")
    assert plan.steps[3].id.startswith("verify_harness_")
    assert plan.steps[4].id.startswith("collect_harness_")
    review = plan.steps[5]
    validator = plan.steps[6]
    assert review.id.startswith("review_harness_outputs_")
    assert review.external_action["action_kind"] == "local_review"
    assert validator.id.startswith("validate_harness_content_")
    assert validator.validation["profile"]["name"] == f"sensor-fan-harness-0{ordinal}"
    expected_roles = {
        "basis",
        "plan",
        "pin_schedule",
        "cut_list",
        "bom",
        "assembly",
        "netlist",
        "voltage_drop",
        "handoff",
    }
    if ordinal == 3:
        expected_roles.add("shield")
    assert {role for role, _ in validator.validation_sources} == expected_roles
    configured_review = review.external_action["settings"]["validation_review"]
    assert configured_review["profile_ref"] == validator.validation["profile"][
        "reference"
    ]
    assert configured_review["requirement_ids"]
    assert plan.revisions == {}
    assert set(plan.steps[2].expected_file_ports) == expected_roles & {
        "plan",
        "pin_schedule",
        "cut_list",
        "bom",
        "assembly",
        "shield",
    }
    assert set(plan.steps[3].expected_file_ports) == {"netlist", "voltage_drop"}
    assert len(manifest["preserved_original_stages"]) == 3
    assert len(manifest["preserved_original_edges"]) == 2
    assert "never zero" in source and "WireViz" in manifest["recorded_substitution"]
    assert "following process validator" in source
    assert "No correctness-validation dashboard credit" not in source
    assert len(manifest["expected_outputs"]) == 6
    assert not any(
        path.endswith(".py") for path in manifest["expected_tool_created_files"]
    )
    assert not (Path(args.workspace_root) / manifest["output_root"]).exists()
    for filename in (
        "wiring-schedule.csv",
        "connector-requirements.csv",
        "allowed-wire.csv",
        "prompt.txt",
        "concept.png",
    ):
        entry = next(
            item
            for item in manifest["input_manifest"]
            if item["path"].endswith("/" + filename)
        )
        assert (Path(args.workspace_root) / entry["path"]).read_bytes() == (
            directory / filename
        ).read_bytes()
