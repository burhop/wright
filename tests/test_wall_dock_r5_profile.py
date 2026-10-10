"""R5 configuration and numeric negative controls; no CAD qualification claim."""

import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.process_validation import ValidationProfile
from workspace_service.process_validation.evaluation import compare
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_process_validation import (
    runtime_service,
    validator,
    workflow,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles/sheet-metal-supplier-handoff-01.json"
VARIANT = ROOT / "examples/process-interfaces/sheet-metal-wall-dock/validation-profile-r5.json"


def test_variant_retains_all_original_checks_and_review_obligations():
    original = json.loads(ORIGINAL.read_bytes())
    variant = json.loads(VARIANT.read_bytes())
    assert variant["id"] != original["id"]
    assert variant["baseline"]["id"] != original["baseline"]["id"]
    current = {c["id"]: c for c in variant["checks"]}
    for check in original["checks"]:
        expected = json.loads(json.dumps(check))
        if expected["parameters"].get("operation") == "simulated_handoff":
            expected["parameters"]["destination"] = "test://083-mechanical-engineering-dock-130-088/supplier/sheet-metal-supplier-handoff-01"
        assert current[check["id"]] == expected
    before = {r["id"]: (r["mandatory"], r["review_required"]) for r in original["baseline"]["requirements"]}
    after = {r["id"]: (r["mandatory"], r["review_required"]) for r in variant["baseline"]["requirements"]}
    assert after == before
    assert len(current) == len(original["checks"]) + 3


def test_variant_baseline_references_exact_preserved_inputs_and_r5():
    profile = ValidationProfile.model_validate_json(VARIANT.read_bytes())
    refs = [*profile.baseline.amendments]
    refs.extend(ref for requirement in profile.baseline.requirements for ref in requirement.sources)
    assert any(ref.artifact_ref.endswith("shelf-depth-revision-r5.md") for ref in refs)
    for ref in refs:
        assert hashlib.sha256((ROOT / ref.artifact_ref).read_bytes()).hexdigest() == ref.sha256
    original = ValidationProfile.model_validate_json(ORIGINAL.read_bytes())
    old_geometry = next(r for r in original.baseline.requirements if r.id == "SHEET01-GEOMETRY")
    assert "75" in old_geometry.text and "130" not in old_geometry.text


@pytest.mark.parametrize("depth,expected", [(130, "pass"), (75, "fail"), (129.9, "fail"), (130.1, "fail")])
def test_variant_depth_requirement_rejects_original_and_out_of_tolerance_observations(depth, expected):
    profile = ValidationProfile.model_validate_json(VARIANT.read_bytes())
    check = next(c for c in profile.checks if c.id == "r5-step-y-envelope")
    assert check.subject_role == "wall_dock_step"
    assert check.selector == "box/y_span_mm"
    observation = SimpleNamespace(value=depth, unit="mm", uncertainty=0, frame="model_axes", id="synthetic-depth", reader=SimpleNamespace(id="test-fixture"))
    subject = SimpleNamespace(producer=SimpleNamespace(run_id="r5-fixture", step_id="fixture-producer"), sha256="0" * 64)
    assert compare(check, observation, subject) == expected


@pytest.mark.parametrize("case,passing", [("native", True), ("ai_summary", False), ("incomplete", False), ("ambiguous", False)])
def test_material_handoff_gate_blocks_invalid_inventory_before_consumer(tmp_path, case, passing):
    """Software fixtures match observed shapes; no native application is invoked."""
    path = ROOT / "examples/process-interfaces/sheet-metal-wall-dock/material-inventory-profile.json"
    profile = ValidationProfile.model_validate_json(path.read_bytes())
    value = {
        "providerId": "solid_edge",
        "materials": [{"name": "Aluminum Alloy:3.3523 , AlMg2.5, EN-AW 5052 ", "library": "Materials-DIN"}],
        "totalMatches": 1,
        "hasMore": False,
    }
    if case == "ai_summary":
        value = {"material_query": value}
    elif case == "incomplete":
        value["hasMore"] = True
    elif case == "ambiguous":
        value["totalMatches"] = 2
    (tmp_path / "inventory-profile.json").write_bytes(path.read_bytes())
    config = {
        "profile": {"source": "workspace", "name": "inventory-profile.json", "reference": profile.reference().model_dump()},
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"inventory": "inspect_subject"},
    }
    plan = compile_prompt_workflow(workflow(validator(config), consumer=True))
    calls = []

    async def generate(prompt, fmt):
        calls.append(fmt)
        return json.dumps(value) if fmt == "json" else "Consumer permitted"

    invocation = execute_prompt_workflow(service=runtime_service(tmp_path), workspace_dir=str(tmp_path), plan=plan, input_values={}, response_generator=generate, run_id="inventory-fixture")
    if passing:
        result = asyncio.run(invocation)
        assert result["steps"][-1]["task_id"] == "consume"
        assert calls == ["json", "text"]
    else:
        with pytest.raises(WorkflowSourceExecutionError) as stopped:
            asyncio.run(invocation)
        assert stopped.value.code == "PROCESS_VALIDATION_REJECTED"
        assert calls == ["json"]
        assert not (tmp_path / "consume.txt").exists()
