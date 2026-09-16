import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "robot_preparer", ROOT / "scripts/prepare-robot-dataset-campaign.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_original_robot_stages_and_review_survive_real_binding(tmp_path, ordinal):
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
        attempt="test",
    )
    directory = next(
        p
        for p in (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"
        ).iterdir()
        if p.name.startswith(f"{ordinal:02d}")
    )
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text()
    plan = compile_prompt_workflow(source)
    manifest = json.loads(
        Path(result["draft"]).with_name("staging-manifest.json").read_text()
    )
    assert len(plan.steps) == 6
    assert len(manifest["preserved_original_stages"]) == 3
    assert len(manifest["preserved_original_edges"]) == 2
    assert plan.steps[0].id.startswith("normalize_csv_")
    assert plan.steps[1].id.startswith("inspect_bag_")
    assert plan.steps[2].id.startswith("align_and_measure_")
    assert plan.steps[3].id.startswith("draft_diagnosis_")
    assert plan.steps[4].external_action["action_kind"] == "local_review"
    assert plan.steps[5].id.startswith("collect_robot_evidence_")
    assert "one percent" in source
    assert "metric_tolerance_percent" in source
    assert any(p.endswith("recording.db3") for p in plan.steps[0].expected_files)
    assert "get_topic_schema" in source and "get_messages_in_range" in source
    assert "max_messages=2" in source and "max_messages=100" not in source
    assert not any(
        path.endswith(".py") for path in manifest["expected_tool_created_files"]
    )
    for path in directory.glob("*.csv"):
        staged = next(
            item
            for item in manifest["input_manifest"]
            if item["path"].endswith("/" + path.name)
        )
        assert (
            Path(args.workspace_root) / staged["path"]
        ).read_bytes() == path.read_bytes()
    assert not (Path(args.workspace_root) / manifest["output_root"]).exists()
    inspection, measurement, diagnosis, review = plan.steps[1:5]
    # Actual canonical ownership remains split across the enrolled servers:
    # inspection produces only its response, metrics produces real artifacts.
    assert inspection.server_id == config["bag_server"]
    assert inspection.expected_files == ()
    assert inspection.output_path.endswith("/bag-inspection.json")
    assert measurement.server_id == config["operation_server"] != inspection.server_id
    assert {Path(path).name for path in measurement.expected_files} == {
        "timeline.csv",
        "trajectory-overlay.svg",
        "tracking-metrics.json",
    }
    assert diagnosis.output_path.endswith("/diagnosis.md")
    assert "calculate_tracking_metrics exactly once" in measurement.prompt
    assert "independently reads every actual message" in inspection.prompt
    assert (
        "original 1% independent metrics and one-sample event gates"
        in measurement.prompt
    )
    assert "preserve the visual occlusion as missing samples" in measurement.prompt
    for prompt in (inspection.prompt, inspection.task_guidance):
        assert preparer.INSPECTION_STAGE_GUIDANCE in prompt
        assert measurement.id in prompt and config["operation_server"] in prompt
        assert "status='completed'" in prompt
        assert (
            "missing or inconsistent inspection evidence or tool errors still block"
            in prompt
        )
        assert "not an inspection blocker" in prompt
        assert "do not fill gaps or require equal counts" in prompt
        assert "Do not compute full-run metrics from the at-most-two samples" in prompt
    assert (
        "report error strings as failures, even when isError is false"
        in inspection.prompt
    )
    assert (
        "start_time=1767225600,end_time=1767225630.01,max_messages=2"
        in inspection.prompt
    )
    assert inspection.max_tool_calls == 12 and inspection.timeout_seconds == 600
    assert any(
        value.startswith(inspection.id + ".") for _, value in measurement.references
    )
    assert any(
        value.startswith(measurement.id + ".") for _, value in diagnosis.references
    )
    assert any(value.startswith(diagnosis.id + ".") for _, value in review.references)
    assert review.external_action["action"]["kind"] == "local_review"
    assert review.external_action["action"]["mode"] == "review_only"
    expected_tools = {
        (server, name)
        for server, names in config["allowed_tools"].items()
        for name in names
    }
    assert {
        (tool["server_id"], tool["tool_name"]) for tool in manifest["tool_allowlist"]
    } == expected_tools
    # Preserve actual original edges as well as their count; inspection's
    # narrowed prompt must not bypass measurement or the engineering review.
    scenario = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    suffix = scenario["scenario_id"].replace("-", "_") + "_test"
    original_edges = [
        item
        for item in _parse(
            preparer.TEMPLATE.read_text(encoding="utf-8").replace(
                "__instance__", suffix
            )
        )
        if item["kind"] == "connection"
    ]
    assert all(edge in _parse(source) for edge in original_edges)


def test_scoped_inspection_does_not_waive_missing_downstream_metric_capability(
    tmp_path,
):
    config = json.loads(preparer.BINDING.read_text(encoding="utf-8"))
    tools = [
        {"server_id": server, "tool_name": name, "schema_digest": "a" * 64}
        for server, names in config["allowed_tools"].items()
        for name in names
        if name != "calculate_tracking_metrics"
    ]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"),
        instance_source=None,
        attempt="missing-metric",
    )
    directory = next(
        p
        for p in (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"
        ).iterdir()
        if p.name.startswith("03")
    )
    with pytest.raises(
        ValueError,
        match="Required selected workspace tool unavailable.*calculate_tracking_metrics",
    ):
        preparer.prepare(args, directory, tools)
    assert not list((tmp_path / "draft").rglob("bound.workflow.wflow"))
    assert not list((tmp_path / "workspace").rglob("tracking-metrics.json"))
