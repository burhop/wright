"""Robot bag inspection keeps exact conversion counts across the task boundary."""

from __future__ import annotations

import importlib.util
import json

import pytest
from pathlib import Path
from types import SimpleNamespace

from workspace_service.workflow_source_execution import compile_prompt_workflow


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "robot_campaign_preparer", ROOT / "scripts/prepare-robot-dataset-campaign.py"
)
PREPARER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARER)


def _tools() -> list[dict[str, str]]:
    catalog = {
        "wright-campaign-rosbag": (
            "bag_info",
            "get_topic_schema",
            "get_messages_in_range",
            "get_message_at_time",
        ),
        "wright-campaign-robot-operations": (
            "normalize_csv_to_ros2",
            "calculate_tracking_metrics",
        ),
        "agentcad": ("context", "docs", "run"),
        "wright-workspace-files": ("write_text_document", "inspect_file"),
        "calculix": (
            "calculix_mesh_preflight",
            "calculix_solve_static_recorded",
            "calculix_run_get",
        ),
        "calculix-fields": ("export_recorded_fields_and_reactions",),
    }
    return [
        {
            "server_id": server,
            "tool_name": name,
            "name": server + "__" + name,
            "schema_digest": "a" * 64,
        }
        for server, names in catalog.items()
        for name in names
    ]


@pytest.mark.parametrize("scenario_prefix", ["01-", "02-", "03-"])
def test_conversion_counts_are_available_to_bag_inspection(tmp_path, scenario_prefix):
    scenario = next(
        (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"
        ).glob(scenario_prefix + "*")
    )
    result = PREPARER.prepare(
        SimpleNamespace(
            workspace_root=str(tmp_path / "workspace"),
            draft_root=str(tmp_path / "draft"),
            attempt="manifest-handoff-test",
            instance_source=None,
            server_map=None,
        ),
        scenario,
        [tool for tool in _tools() if tool["tool_name"] != "get_message_at_time"],
    )
    plan = compile_prompt_workflow(Path(result["draft"]).read_text(encoding="utf-8"))
    normalize = next(step for step in plan.steps if step.id.startswith("normalize_csv_"))
    inspect = next(step for step in plan.steps if step.id.startswith("inspect_bag_"))

    assert "exact topics array with every topic, schema and count" in normalize.prompt
    assert "do not replace these values with only a path or hash" in normalize.prompt
    assert "same_run_conversion response's exact topics array" in inspect.prompt
    assert "not expected to read conversion-manifest.json" in inspect.prompt
    assert "independently observed bag count" in inspect.prompt
    assert any(
        source == f"{normalize.id}.{normalize.id}_result"
        for _, source in inspect.references
    )
    corrective = next(
        step for step in plan.steps if step.id.startswith("build_corrective_hardware_")
    )
    assert set(corrective.expected_file_ports) == {
        "corrective_step",
        "corrective_measurements",
        "corrective_request",
    }
    validator = next(step for step in plan.steps if step.validation)
    assert {
        "corrective_step",
        "corrective_measurements",
        "corrective_fea",
        "commissioning",
    } <= {role for role, _ in validator.validation_sources}

    expected = {
        "normalize_csv": {"normalize_csv_to_ros2"},
        "inspect_bag": {"bag_info", "get_topic_schema", "get_messages_in_range"},
        "align_and_measure": {"calculate_tracking_metrics"},
        "preflight_corrective_cad": {"context", "docs"},
        "author_corrective_cad_source": {"write_text_document"},
        "build_corrective_hardware": {"run"},
        "solve_corrective_hardware": {"calculix_mesh_preflight", "calculix_solve_static_recorded", "calculix_run_get"},
        "export_corrective_fields": {"export_recorded_fields_and_reactions"},
        "verify_corrective_design": {"inspect_file"},
    }
    tasks = [step for step in plan.steps if step.agent_task]
    assert len(tasks) == len(expected)
    for prefix, tools in expected.items():
        step = next(step for step in tasks if step.id.startswith(prefix + "_"))
        assert set(step.task_tool_allowlist) == tools
    receipt = json.loads(Path(result["draft"]).with_name("staging-manifest.json").read_text())
    assert {(t["server_id"], t["tool_name"]) for t in receipt["tool_allowlist"]} == {
        (step.server_id, name) for step in tasks for name in step.task_tool_allowlist
    }
    assert all(t["tool_name"] != "get_message_at_time" for t in receipt["tool_allowlist"])


@pytest.mark.parametrize("fault", ["missing", "duplicate"])
def test_required_corrective_tool_registration_fails_closed(tmp_path, fault):
    tools = _tools()
    required = next(tool for tool in tools if tool["tool_name"] == "run")
    if fault == "missing":
        tools.remove(required)
    else:
        tools.append(dict(required))
    scenario = next((ROOT / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis").glob("01-*"))
    with pytest.raises(ValueError, match="unavailable or ambiguous: agentcad/run"):
        PREPARER.prepare(
            SimpleNamespace(workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "draft"), attempt="registration-fault", instance_source=None, server_map=None),
            scenario,
            tools,
        )
    assert not list((tmp_path / "draft").rglob("bound.workflow.wflow"))
