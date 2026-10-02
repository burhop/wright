"""Declarative proof preparation tests: no model, native host or provider call."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from workspace_service.workflow_source_execution import compile_prompt_workflow
from workspace_service.process_validation.configuration import ValidatorConfiguration


REPO = Path(__file__).resolve().parents[1]


def heat_preparer():
    spec = importlib.util.spec_from_file_location(
        "heat_process_example",
        REPO / "examples/process-interfaces/heat-spreader-sizing/prepare.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def configuration(tmp_path):
    workspace = tmp_path / "workspace"
    project = workspace / "selected-cad-project"
    (project / "build").mkdir(parents=True)
    # Fixture declaration only; this suite does not assert native initialization.
    (project / "build/agentcad.json").write_text(
        json.dumps(
            {"runtime": "build123d", "project_root": str(project), "versions": []}
        )
    )
    bindings = dict(
        cad_project=str(project),
        cad_server="fixture-cad",
        files_server="fixture-files",
        solver_server="fixture-solver",
        solver_workspace="/workspace",
    )
    tools = []
    for server, names in [
        ("fixture-cad", ("context", "docs", "run", "measure")),
        ("fixture-files", ("write_text_document", "inspect_file")),
        ("fixture-solver", ("run_simulation",)),
    ]:
        tools.extend(
            dict(
                server_id=server,
                tool_name=name,
                name=server + "__" + name,
                schema_digest="a" * 64,
            )
            for name in names
        )
    return workspace, project, bindings, tools


def test_heat_source_preserves_original_stages_and_exact_full_validation(configuration):
    workspace, _, bindings, tools = configuration
    module = heat_preparer()
    report = module.prepare(workspace, "source-test", tools, bindings)
    source = (workspace / report["source_path"]).read_text()
    plan = compile_prompt_workflow(source)
    assert report["status"] == "prepared_not_executed"
    assert report["physical_dispatch"] is False
    assert report["approval_policy_not_enrolled"] is True
    assert report["engineering_acceptance"] is False
    assert len(plan.steps) == 10
    assert {
        "define_thermal_case_source_test",
        "create_plate_geometry_source_test",
        "solve_and_verify_source_test",
    } <= {step.id for step in plan.steps}
    assert source.count('"action_kind":"local_review"') == 2
    assert '"name":"heat-spreader-sizing-01-full"' in source
    assert '"max_revisions":0' in source
    raw_call = (
        workspace
        / "process-proofs/heat-spreader-sizing/source-test/inputs/solver-call.json"
    )
    invocation = json.loads(raw_call.read_bytes())
    assert invocation["critic_approved"] is False
    assert "geometry_measurements" in invocation["input_content"]
    assert "heat_conduction_skfem.py" in invocation["input_content"]
    validator = next(
        step for step in plan.steps if step.id == "validate_outputs_source_test"
    )
    profile = ValidatorConfiguration.model_validate(validator.validation).load(
        str(workspace)
    )
    assert {check.subject_role for check in profile.checks} == {
        "basis",
        "baseline_40_geometry",
        "revision_60_geometry",
        "baseline_40_coarse",
        "baseline_40_fine",
        "revision_60_coarse",
        "revision_60_fine",
        "decision",
        "correspondence",
    }
    for item in report["input_files"]:
        staged = workspace / item["path"]
        assert module.definition.sha(staged.read_bytes()) == item["sha256"]
        if item["original"]:
            assert staged.read_bytes() == (REPO / item["original"]).read_bytes()
    assert not list((workspace / report["output_root"]).iterdir())
    assert not (workspace / "campaign").exists()
    assert "printer_transfer" not in source
    assert "wright-printed-part" not in source


def test_missing_selected_tool_blocks_before_creating_attempt(configuration):
    workspace, _, bindings, tools = configuration
    with pytest.raises(ValueError, match="capability is missing"):
        heat_preparer().prepare(workspace, "missing-tool", tools[:-1], bindings)
    assert not (workspace / "process-proofs").exists()


def test_wrong_project_manifest_is_not_rewritten(configuration):
    workspace, project, bindings, tools = configuration
    path = project / "build/agentcad.json"
    data = json.dumps(
        dict(
            runtime="build123d",
            project_root=str(workspace / "other-project"),
            versions=[],
        )
    ).encode()
    path.write_bytes(data)
    with pytest.raises(ValueError, match="exact root"):
        heat_preparer().prepare(workspace, "wrong-root", tools, bindings)
    assert path.read_bytes() == data
    assert not (workspace / "process-proofs").exists()


def test_existing_native_history_is_not_adopted(configuration):
    workspace, project, bindings, tools = configuration
    path = project / "build/agentcad.json"
    value = json.loads(path.read_bytes())
    value["versions"] = [{"version": 1, "label": "preexisting"}]
    path.write_text(json.dumps(value))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="fresh empty"):
        heat_preparer().prepare(workspace, "old-history", tools, bindings)
    assert path.read_bytes() == before
    assert not (workspace / "process-proofs").exists()


def test_existing_attempt_is_preserved(configuration):
    workspace, _, bindings, tools = configuration
    module = heat_preparer()
    report = module.prepare(workspace, "preserved", tools, bindings)
    source = workspace / report["source_path"]
    original = source.read_bytes()
    with pytest.raises(ValueError, match="fresh attempt"):
        module.prepare(workspace, "preserved", tools, bindings)
    assert source.read_bytes() == original


@pytest.mark.parametrize("mount", ["relative", "/workspace/../other"])
def test_bad_solver_mount_blocks_before_staging(configuration, mount):
    workspace, _, bindings, tools = configuration
    bindings["solver_workspace"] = mount
    with pytest.raises(ValueError, match="absolute workspace mount"):
        heat_preparer().prepare(workspace, "bad-mount", tools, bindings)
    assert not (workspace / "process-proofs").exists()
