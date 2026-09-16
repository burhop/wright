import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "pi_fixed_prepare_tests", ROOT / "scripts/prepare-pi-fixed-dataset-campaign.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_fixed_pi_preserves_real_stages_review_and_bounded_artifacts(tmp_path, ordinal):
    config = json.loads(preparer.BINDING.read_text())
    tools = [
        {"server_id": server, "tool_name": name, "schema_digest": "a" * 64}
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
    assert len(plan.steps) == 8
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
    assert "read_pi_reference_page" in source and "4000characters" in source
    assert "cfd-contract-a.json" in source and "cfd-contract-b.json" in source
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
