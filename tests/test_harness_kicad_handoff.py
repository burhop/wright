from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from workspace_service.workflow_source_execution import compile_prompt_workflow


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
        assert verify.expected_file_ports["kicad_erc"].endswith("/interconnect/erc.json")
        assert verify.expected_file_ports["net_correspondence"].endswith(
            "/interconnect/net-correspondence.json"
        )
        assert "Zero ERC errors alone is not correspondence" in verify.prompt
        assert {"kicad_schematic", "kicad_erc", "net_correspondence"}.issubset(
            validator.validation["subjects"]
        )
        coverage = json.loads(PREPARER.VALIDATION_COVERAGE.read_text(encoding="utf-8"))
        support = next(
            row for row in coverage["scenarios"] if row["scenario_id"] == result["scenario_id"]
        )
        assert set(validator.validation["subjects"]) == set(
            support["campaign_credit"]["subject_roles"]
        )
        manifest = json.loads(
            Path(result["draft"]).with_name("staging-manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["kicad_server_id"] == "kicad-test"
        assert "independent_interconnect_check" in {
            item["role"] for item in manifest["expected_outputs"]
        }
