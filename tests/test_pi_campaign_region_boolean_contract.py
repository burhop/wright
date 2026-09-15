"""The Pi workflow must author mutually exclusive multi-solid CFD regions."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from workspace_service.workflow_source_execution import _parse


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "pi_region_boolean_preparer",
    ROOT / "scripts/prepare-pi-visual-dataset-campaign.py",
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


def test_authored_cad_contract_subtracts_each_target_and_cutter_solid(tmp_path):
    config = json.loads(preparer.BINDING.read_text(encoding="utf-8"))
    available = [
        {
            "server_id": server_id,
            "tool_name": tool_name,
            "name": f"{server_id}__{tool_name}",
            "schema_digest": f"digest-{server_id}-{tool_name}",
        }
        for server_id, tool_names in config["allowed_tools"].items()
        for tool_name in tool_names
    ]
    scenario_dir = next(
        (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure"
        ).glob("02-*")
    )
    result = preparer.prepare(
        SimpleNamespace(
            workspace_root=str(tmp_path / "workspace"),
            draft_root=str(tmp_path / "draft"),
            attempt="contract-test",
            instance_source=None,
            server_map={},
            initialize_agentcad=False,
        ),
        scenario_dir,
        available,
    )
    sections = _parse(Path(result["draft"]).read_text(encoding="utf-8"))
    author = next(
        section
        for section in sections
        if section["kind"] == "task"
        and section["id"].startswith("author_cad_source_")
    )
    prompt = author["fields"]["prompt"]

    assert "every material-region Boolean per target solid and per cutter solid" in prompt
    assert "Never subtract a cutter from a multi-solid target Compound" in prompt
    assert "flattens list(boolean_result.solids()) after every cut" in prompt
    assert "individual brass-insert cylinders as a list" in prompt
    assert "PETG floor must occupy Z=0.0..2.5 mm" in prompt
    assert "Do not place the floor at Z=2.0" in prompt
    assert "final fluid bounding_box() must retain zmin=2.5" in prompt
    assert "fluid_domain_observed_bounds_mm as an object with exactly x_min, x_max, y_min, y_max, z_min and z_max numeric keys" in prompt
    assert "Never encode domain or face bounds as a six-item list" in prompt
    assert "never use area_mm2, matching_count or selected_face aliases" in prompt


def test_cad_lineage_inspection_has_context_bounded_call_budget(tmp_path):
    config = json.loads(preparer.BINDING.read_text(encoding="utf-8"))
    available = [
        {
            "server_id": server_id,
            "tool_name": tool_name,
            "name": f"{server_id}__{tool_name}",
            "schema_digest": f"digest-{server_id}-{tool_name}",
        }
        for server_id, tool_names in config["allowed_tools"].items()
        for tool_name in tool_names
    ]
    scenario_dir = next(
        (ROOT / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure").glob("02-*")
    )
    result = preparer.prepare(
        SimpleNamespace(
            workspace_root=str(tmp_path / "workspace"),
            draft_root=str(tmp_path / "draft"),
            attempt="budget-test",
            instance_source=None,
            server_map={},
            initialize_agentcad=False,
        ),
        scenario_dir,
        available,
    )
    sections = _parse(Path(result["draft"]).read_text(encoding="utf-8"))
    inspection = next(section for section in sections if section["id"].startswith("inspect_cad_exports_"))
    assert inspection["fields"]["settings"]["max_tool_calls"] == 18
    assert "includeText=false for every file" in inspection["fields"]["prompt"]
    assert "Set includeText=false on every call" in inspection["fields"]["settings"]["task_guidance"]
