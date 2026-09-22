"""Robot bag inspection keeps exact conversion counts across the task boundary."""

from __future__ import annotations

import importlib.util
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


def test_conversion_counts_are_available_to_bag_inspection(tmp_path):
    scenario = next(
        (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"
        ).glob("01-*")
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
        _tools(),
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
