from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from workspace_service.workflow_source_execution import compile_prompt_workflow
from workspace_service.process_validation.configuration import ValidatorConfiguration


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "harness_kicad_preparer", ROOT / "scripts/prepare-harness-dataset-campaign.py"
)
PREPARER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PREPARER)


def _tools() -> list[dict[str, str]]:
    config = json.loads(PREPARER.BINDING.read_text(encoding="utf-8"))
    catalog = {
        "harness-test": config["allowed_tools"],
        "kicad-test": config["kicad_tools"],
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


def test_all_harnesses_bind_wireviz_to_independent_kicad_check(tmp_path: Path) -> None:
    scenarios = ROOT / "tests/datasets/engineering-workflows/scenarios/sensor-fan-harness"
    for ordinal in (1, 2, 3):
        directory = next(path for path in scenarios.iterdir() if path.name.startswith(f"{ordinal:02d}"))
        result = PREPARER.prepare(
            SimpleNamespace(
                workspace_root=str(tmp_path / f"workspace-{ordinal}"),
                draft_root=str(tmp_path / f"draft-{ordinal}"),
                attempt="renewal-unit",
                instance_source=None,
                server_id="harness-test",
                kicad_server_id="kicad-test",
                contact_resistance_ohm=None,
                splice_port_resistance_ohm=None,
                resistance_basis=None,
            ),
            directory,
            _tools(),
        )
        plan = compile_prompt_workflow(Path(result["draft"]).read_text(encoding="utf-8"))
        author = next(step for step in plan.steps if step.id.startswith("author_kicad_interconnect_"))
        verify = next(step for step in plan.steps if step.id.startswith("verify_kicad_interconnect_"))
        validator = next(step for step in plan.steps if step.validation)
        assert author.server_id == "kicad-test"
        assert verify.server_id == "kicad-test"
        assert author.expected_file_ports["kicad_schematic"].endswith("/interconnect/harness.kicad_sch")
        assert verify.expected_file_ports["kicad_erc"].endswith("/interconnect/native/erc.json")
        assert verify.expected_file_ports["kicad_native_netlist"].endswith("/interconnect/native/netlist.xml")
        assert verify.expected_file_ports["kicad_native_inspection"].endswith("/interconnect/native/inspection.json")
        assert "native_interconnect_export" in verify.prompt
        assert verify.expected_file_ports["net_correspondence"].endswith(
            "/interconnect/net-correspondence.json"
        )
        assert "Zero ERC errors alone is not correspondence" in verify.prompt
        assert {"kicad_schematic", "kicad_erc", "net_correspondence", "kicad_native_netlist", "kicad_native_inspection"}.issubset(
            validator.validation["subjects"]
        )
        coverage = json.loads(PREPARER.VALIDATION_COVERAGE.read_text(encoding="utf-8"))
        support = next(
            row for row in coverage["scenarios"] if row["scenario_id"] == result["scenario_id"]
        )
        assert set(validator.validation["subjects"]) == set(
            support["campaign_credit"]["subject_roles"]
        )
        assert ValidatorConfiguration.model_validate(validator.validation).load(
            str(tmp_path / f"workspace-{ordinal}")
        ).reference().model_dump() == validator.validation["profile"]["reference"]
        manifest = json.loads(
            Path(result["draft"]).with_name("staging-manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["kicad_server_id"] == "kicad-test"
        assert manifest["prepared_output_directories"] == [
            f"campaign/{result['scenario_id']}/renewal-unit/artifacts/interconnect"
        ]
        assert (
            tmp_path
            / f"workspace-{ordinal}"
            / "campaign"
            / result["scenario_id"]
            / "renewal-unit"
            / "artifacts/interconnect"
        ).is_dir()
        assert "independent_interconnect_check" in {
            item["role"] for item in manifest["expected_outputs"]
        }


def test_missing_native_export_tool_blocks_staging_before_writing_files(tmp_path):
    directory = ROOT / "tests/datasets/engineering-workflows/scenarios/sensor-fan-harness/01-desktop-incubator"
    tools = [tool for tool in _tools() if tool["tool_name"] != "native_interconnect_export"]
    with pytest.raises(ValueError, match="native_interconnect_export"):
        PREPARER.prepare(SimpleNamespace(workspace_root=str(tmp_path / "workspace")), directory, tools)
    assert not (tmp_path / "workspace").exists()
