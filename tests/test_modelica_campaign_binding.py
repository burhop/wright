"""All heater variants resolve direct nodes against their enrolled tool pins."""
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tool_registry.gateway_models import GatewayTool
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import compile_prompt_workflow, WorkflowSourceExecutionError

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


preparer = module("modelica_binding_test", "scripts/prepare-modelica-dataset-campaign.py")
enroller = module("modelica_enrollment_test", "scripts/enroll_engineering_dataset_case.py")
installer = module("modelica_installer_test", "scripts/install-modelica-campaign-mcp.py")


@pytest.fixture
def catalog(tmp_path):
    tools = [GatewayTool(name="selected-modelica__" + name, server_id="selected-modelica", tool_name=name,
                         description="Static binding test", input_schema={"type": "object"}) for name in preparer.TOOLS]
    runtime = WorkflowMcpRuntime.__new__(WorkflowMcpRuntime)
    runtime.gateway = SimpleNamespace(list_tools=lambda _: tools)
    runtime.session_id = "static-test"
    runtime._allowed_tool_identities = None
    projected = runtime.available()
    runtime.restrict_to(projected)
    tool_path = tmp_path / "tools.json"
    tool_path.write_text(json.dumps({"tools": projected}))
    units = {"initial_water_temperature": "degC", "ambient_temperature": "degC", "water_mass": "kg",
             "boiler_heat_capacity": "J/K", "heat_loss_conductance": "W/K", "heater_efficiency": "1",
             "setpoint_temperature": "degC", "hysteresis": "K", "electrical_power": "W"}
    manifest = {"model": {"id": "wright-water-heater-v1", "source": {"sha256": "a" * 64}},
                "parameters": [{"id": key, "unit": unit} for key, unit in units.items()], "manifest_sha256": "b" * 64}
    manifest_path = tmp_path / "manifests.json"
    manifest_path.write_text(json.dumps({f"wright-{horizon}-{mode}": manifest
        for horizon in (300, 600, 700) for mode in ("baseline", "refined")}))
    return runtime, projected, tool_path, manifest_path


@pytest.mark.parametrize("index,steps,direct", [(1, 9, 7), (2, 9, 7), (3, 25, 23)])
def test_every_generated_heater_node_resolves_and_keeps_original_stages(tmp_path, catalog, index, steps, direct):
    runtime, projected, tool_path, manifest_path = catalog
    directory = next((ROOT / "tests/datasets/engineering-workflows/scenarios/water-heater-sizing").glob(f"{index:02}-*"))
    result = preparer.prepare(SimpleNamespace(workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"), attempt="attempt-test", instance_source=None,
        manifest_catalog=str(manifest_path), tool_catalog=str(tool_path), server_id="selected-modelica"), directory)
    plan = compile_prompt_workflow(Path(result["source"]).read_text())
    assert len(plan.steps) == steps
    assert sum(bool(step.tool_name) for step in plan.steps) == direct
    assert all(any(step.id.startswith(prefix + "_") for step in plan.steps) for prefix in preparer.ORIGINAL)
    assert any(step.external_action for step in plan.steps)
    verify = next(step for step in plan.steps if step.id.startswith("verify_selection_"))
    evidence_sources = [source for name, source in verify.references if "native baseline " in name]
    baseline_exports = [step for step in plan.steps if step.id.startswith("export_native_")]
    assert len(evidence_sources) == len(baseline_exports)
    for export in baseline_exports:
        key = export.id + "_computed_evidence"
        assert export.id + "." + key in evidence_sources
        path = export.expected_file_ports[key]
        assert path.endswith("/evidence.json")
        assert path in export.expected_files
        assert len(export.expected_files) == len(preparer.NATIVE_FILES)
    for step in plan.steps:
        if step.tool_name or step.agent_task:
            runtime.preflight(step)
        if step.tool_name:
            assert step.schema_digest == schema_digest(runtime.resolve(step))
    enroller.validate_tool_bindings(plan, projected, projected)
    native = next(step for step in plan.steps if step.tool_name)
    for bad in (replace(native, tool_name=native.tool_name.split("__", 1)[1]),
                replace(native, schema_digest=""), replace(native, schema_digest="f" * 64)):
        with pytest.raises(WorkflowSourceExecutionError):
            runtime.preflight(bad)
        with pytest.raises(ValueError, match="qualified tool name and current schema"):
            enroller.validate_tool_bindings(replace(plan, steps=tuple(bad if s.id == bad.id else s for s in plan.steps)), projected, projected)


@pytest.mark.parametrize("change", ["missing", "schema", "server"])
def test_enrollment_rejects_current_catalog_drift(catalog, change):
    _, projected, _, _ = catalog
    current = [dict(tool) for tool in projected]
    if change == "missing":
        current.pop()
    else:
        current[0]["schema_digest" if change == "schema" else "server_id"] = "c" * 64
    with pytest.raises(ValueError, match="unavailable or stale"):
        enroller.validate_tool_bindings(SimpleNamespace(steps=[]), projected, current)


def test_selected_modelica_mounts_keep_attempts_separate(tmp_path):
    mounts = installer.attempt_mounts(tmp_path, ["attempt-001", "attempt-002"])
    assert len(mounts) == 6
    assert len({m["host"] for m in mounts}) == 6
    assert {m["container"] for m in mounts} == {
        f"/exports/water-heater-sizing-{index:02}/{attempt}"
        for index in (1, 2, 3) for attempt in ("attempt-001", "attempt-002")}
    assert all(Path(m["host"]).is_relative_to(tmp_path) for m in mounts)
    assert not list(tmp_path.iterdir())  # Pure planning must not create roots.
    for attempts in (["attempt-001", "attempt-001"], ["attempt-../../outside"], ["outside"]):
        with pytest.raises(ValueError, match="Unique explicit attempt"):
            installer.attempt_mounts(tmp_path, attempts)


def test_existing_container_cannot_claim_new_attempt_mounts(tmp_path, monkeypatch):
    receipt = tmp_path / "installation.json"
    receipt.write_text(json.dumps({"container_started": True,
        "mounts": installer.attempt_mounts(tmp_path, ["attempt-001"])}))
    monkeypatch.setattr(sys, "argv", ["install-modelica", "--execute", "--prepare-only",
        "--workspace-root", str(tmp_path), "--output", str(receipt), "--attempt", "attempt-002"])

    def no_docker(*args, **kwargs):
        pytest.fail("A missing mount must be rejected before any container mutation")

    monkeypatch.setattr(installer.subprocess, "run", no_docker)
    with pytest.raises(ValueError, match="lacks requested attempt mounts"):
        installer.main()
    assert json.loads(receipt.read_text())["mounts"] == installer.attempt_mounts(tmp_path, ["attempt-001"])
