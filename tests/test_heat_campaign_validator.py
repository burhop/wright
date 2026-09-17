"""The qualified heat campaign case carries the runtime validator in its graph."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from workspace_service.workflow_source_execution import compile_prompt_workflow


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "heat_campaign_preparer", ROOT / "scripts/prepare-heat-dataset-campaign.py"
)
PREPARER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARER)


def _tools():
    catalog = {
        "agentcad": ("context", "docs", "run", "measure", "inspect"),
        "wright-workspace-files": ("write_text_document", "inspect_file"),
        "oasis-test": ("run_simulation",),
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


def test_only_qualified_heat_case_compiles_with_validator(tmp_path):
    scenarios = ROOT / "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing"
    for ordinal in (1, 2):
        directory = next(path for path in scenarios.iterdir() if path.name.startswith(f"{ordinal:02d}"))
        args = SimpleNamespace(
            workspace_root=str(tmp_path / f"workspace-{ordinal}"),
            container_workspace="/campaign-workspace",
            draft_root=str(tmp_path / f"draft-{ordinal}"),
            attempt="validator-unit",
            instance_source=None,
            initialize_agentcad=False,
            oasis_server_id="oasis-test",
        )
        result = PREPARER.prepare(args, directory, _tools())
        plan = compile_prompt_workflow(Path(result["draft"]).read_text(encoding="utf-8"))
        validators = [step for step in plan.steps if step.validation]
        if ordinal == 1:
            assert len(validators) == 1
            validator = validators[0]
            assert validator.validation["profile"]["name"] == "heat-spreader-sizing-01"
            assert set(validator.validation["subjects"]) == {
                "baseline_coarse", "baseline_fine", "revision_coarse",
                "revision_fine", "decision",
            }
            solver = next(step for step in plan.steps if step.id.startswith("execute_recorded_fe_call_"))
            assert set(solver.expected_file_ports) == set(validator.validation["subjects"])
        else:
            assert validators == []
        manifest = json.loads(
            Path(result["draft"]).with_name("staging-manifest.json").read_text()
        )
        assert manifest["scenario_id"].endswith(f"-{ordinal:02d}")
        binding = json.loads(
            Path(manifest["input_binding_evidence"]["path"]).read_text(encoding="utf-8")
        )
        assert binding["complete"] is True
        assert next(
            row for row in binding["bindings"] if row["raw_file"] == "concept.svg"
        )["status"] == "mapped"
