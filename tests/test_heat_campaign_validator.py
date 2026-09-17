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


def test_all_heat_cases_compile_with_full_validator(tmp_path):
    scenarios = ROOT / "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing"
    for ordinal in (1, 2, 3):
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
        assert len(validators) == 1
        validator = validators[0]
        scenario_id = f"heat-spreader-sizing-{ordinal:02d}"
        assert validator.validation["profile"]["name"] == scenario_id + "-full"
        candidates = [
            row.split(",", 1)[0]
            for row in (directory / "alternatives.csv")
            .read_text(encoding="utf-8")
            .splitlines()[1:]
            if row
        ]
        expected_roles = {
            "basis",
            "decision",
            *(
                candidate + "_" + suffix
                for candidate in candidates
                for suffix in ("geometry", "coarse", "fine")
            ),
        }
        assert set(validator.validation["subjects"]) == expected_roles
        solver = next(
            step
            for step in plan.steps
            if step.id.startswith("execute_recorded_fe_call_")
        )
        assert set(solver.expected_file_ports) == expected_roles - {
            "basis",
            *(candidate + "_geometry" for candidate in candidates),
        }
        geometry = next(
            step for step in plan.steps if step.id.startswith("create_plate_geometry_")
        )
        assert set(geometry.expected_file_ports) == {
            candidate + "_geometry" for candidate in candidates
        }
        review = next(
            step for step in plan.steps if step.id.startswith("review_thermal_basis_")
        )
        assert review.external_action["settings"]["validation_review"][
            "profile_ref"
        ] == validator.validation["profile"]["reference"]
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
