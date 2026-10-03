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
    assert report["source_acceptance_required"] is True
    assert report["source_path"] == (
        "process-proofs/heat-spreader-sizing/source-test/prepared.workflow.wflow"
    )
    assert report["accepted_source_path"] == (
        "workflows/heat-spreader-sizing-source-test.workflow.wflow"
    )
    assert not (workspace / report["accepted_source_path"]).exists()
    assert "Do not execute CAD here" in source
    assert "the next declared native CAD operation produces them" in source
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


def test_heat_run_paths_bind_geometry_and_solver_without_changing_requirements(configuration):
    from workspace_service.workflow_references import WorkflowReference
    from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths, bind_run_input_values, reserve_run_paths

    workspace, _, bindings, tools = configuration
    bindings["run_path_template"] = VERSION
    report = heat_preparer().prepare(workspace, "repeatable", tools, bindings)
    proposal = workspace / report["source_path"]
    source_bytes = proposal.read_bytes()
    plan = compile_prompt_workflow(source_bytes.decode())
    assert report["run_path_template"] == VERSION
    assert report["output_template"] == report["output_root"] + "/" + TOKEN
    assert not list((workspace / report["output_root"]).iterdir())
    assert not (workspace / report["accepted_source_path"]).exists()
    assert len(plan.steps) == 10
    for item in report["input_files"]:
        if item["original"]:
            assert (workspace / item["path"]).read_bytes() == (REPO / item["original"]).read_bytes()
    configured = {
        key: WorkflowReference.from_bytes(
            fields["settings"]["workspace_file"],
            (workspace / fields["settings"]["workspace_file"]).read_bytes(), image=False,
        )
        for key, fields in plan.inputs.items()
        if fields["settings"].get("run_path_template")
    }
    assert len(configured) == 2
    original_templates = {value.path: (workspace / value.path).read_bytes() for value in configured.values()}
    first = workspace / report["output_root"] / "heat-one" / "retained.txt"
    for run_id in ("heat-one", "heat-two"):
        bound = bind_run_paths(plan, run_id)
        values = bind_run_input_values(bound, configured)
        assert bound.run_path_roots == (report["output_root"] + "/" + run_id,)
        assert {step.id for step in bound.steps} == {step.id for step in plan.steps}
        for step in bound.steps:
            if step.save:
                assert step.output_path.startswith(report["output_root"] + "/" + run_id + "/")
            assert TOKEN not in step.prompt
            assert all(TOKEN not in path for path in step.expected_files)
            assert all(TOKEN not in path for path in step.file_dependencies.values())
        operations = {Path(value.path).name: json.loads(value.text) for value in values.values()}
        assert operations["cad-call.json"]["output"] == "plates_" + run_id
        assert run_id in operations["cad-call.json"]["script"]
        solver = operations["solver-call.json"]
        assert solver["job_name"] == "/workspace/" + report["output_root"] + "/" + run_id
        assert run_id in solver["input_content"] and TOKEN not in solver["input_content"]
        assert solver["critic_approved"] is False
        reserve_run_paths(bound, str(workspace), run_id)
        if run_id == "heat-one":
            first.write_bytes(b"first exact output")
        else:
            assert first.read_bytes() == b"first exact output"
    assert first.read_bytes() == b"first exact output"
    assert proposal.read_bytes() == source_bytes
    assert all((workspace / path).read_bytes() == raw for path, raw in original_templates.items())
    validation = next(step for step in plan.steps if step.validation)
    profile = ValidatorConfiguration.model_validate(validation.validation).load(str(workspace))
    assert len(profile.checks) == 26
    assert '"max_revisions":0' in source_bytes.decode()


def test_unsupported_run_path_version_blocks_before_staging(configuration):
    workspace, _, bindings, tools = configuration
    bindings["run_path_template"] = "unsupported/2"
    with pytest.raises(ValueError, match="supported explicit"):
        heat_preparer().prepare(workspace, "wrong-path-version", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize("kind", ["workspace_file", "reference_images"])
def test_example_templates_cannot_relabel_opaque_inputs(configuration, kind):
    from workspace_service.workflow_run_paths import VERSION

    workspace, _, _, tools = configuration
    module = heat_preparer()
    flow = module.definition.Definition(
        "heat-spreader-sizing", workspace, "opaque-template", tools,
        run_path_template=VERSION,
    )
    with pytest.raises(ValueError, match="configuration text"):
        flow.input_bytes("opaque.bin", b"\x00original bytes", kind=kind, run_paths=True)
    assert not (workspace / flow.input_root / "opaque.bin").exists()


def test_published_heat_bindings_explicitly_select_run_path_version():
    from workspace_service.workflow_run_paths import VERSION

    bindings = json.loads((REPO / "examples/process-interfaces/heat-spreader-sizing/bindings.example.json").read_bytes())
    assert bindings["run_path_template"] == VERSION


@pytest.mark.parametrize("mount", ["relative", "/workspace/../other"])
def test_bad_solver_mount_blocks_before_staging(configuration, mount):
    workspace, _, bindings, tools = configuration
    bindings["solver_workspace"] = mount
    with pytest.raises(ValueError, match="absolute workspace mount"):
        heat_preparer().prepare(workspace, "bad-mount", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def printed_preparer():
    spec = importlib.util.spec_from_file_location(
        "printed_process_example",
        REPO / "examples/process-interfaces/printed-replacement-part/prepare.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def printed_configuration(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    bindings = dict(
        geometry_server="fixture-geometry",
        files_server="fixture-files",
        slicer_server="fixture-slicer",
        inspection_server="fixture-inspection",
        inspection_workspace="/workspace",
        inspection_backend="skfem",
        geometry_guidance="Fixture geometry guidance; no native operation is claimed",
        slice_success_contract="Fixture success declaration; no native execution is claimed",
        simulator_destination="test://private-fixture/printer/printed-replacement-part-01",
        profiles={},
    )
    module = printed_preparer()
    profile = json.loads(
        (
            REPO
            / "packages/workspace_service/src/workspace_service/process_validation/profiles/printed-replacement-part-01.json"
        ).read_bytes()
    )
    for role in ("machine", "process", "filament"):
        fields = {
            check["selector"].removeprefix("/"): check["constraint"]["expected"]
            for check in profile["checks"]
            if check["subject_role"] == role + "_profile"
        }
        target = tmp_path / (role + ".json")
        target.write_text(json.dumps(fields))
        bindings["profiles"][role] = {
            "path": str(target),
            "sha256": module.definition.sha(target.read_bytes()),
        }
    tools = []
    for server, names in [
        ("fixture-geometry", ("execute_blender_code",)),
        ("fixture-files", ("write_text_document", "inspect_file")),
        ("fixture-slicer", ("slice_model_file",)),
        ("fixture-inspection", ("run_simulation",)),
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
    return workspace, bindings, tools


def test_printed_proposal_preserves_assignment_and_full_gate(printed_configuration):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    report = module.prepare(workspace, "source-test", tools, bindings)
    source = (workspace / report["source_path"]).read_text()
    plan = compile_prompt_workflow(source)
    assert {
        "create_mesh_source_test",
        "repair_measure_orient_source_test",
        "supports_and_slice_source_test",
        "authorize_transfer_source_test",
    } <= {step.id for step in plan.steps}
    assert report["step_count"] == 11
    create = next(step for step in plan.steps if step.id == "create_mesh_source_test")
    assert create.timeout_seconds == 360 and create.max_tool_calls == 2
    repair = next(
        step for step in plan.steps if step.id == "repair_measure_orient_source_test"
    )
    assert repair.timeout_seconds == 360 and repair.max_tool_calls == 2
    assert list(repair.file_dependencies.values()) == [
        "process-proofs/printed-replacement-part/source-test/outputs/source_mesh.stl"
    ]
    assert any(
        source
        == "define_geometry_basis_source_test.define_geometry_basis_source_test_result"
        for _, source in create.references
    )
    assert [step.id for step in plan.steps].index("review_basis_source_test") < [
        step.id for step in plan.steps
    ].index(create.id)
    assert "not human engineering acceptance" in create.prompt
    assert (
        report["physical_dispatch"] is False
        and report["engineering_acceptance"] is False
    )
    assert report["approval_policy_not_enrolled"] is True
    assert not (workspace / report["accepted_source_path"]).exists()
    assert '"reference_dimension_mm":38.0' in source
    assert "guarded bpy/bmesh/mathutils" in source
    assert "geometry-only preview" in source
    assert '"tool":"test_handoff"' in source
    assert '"kind":"integration_test"' in source
    sections = module.definition._parse(source)
    endpoints = [
        (block["fields"]["from"], block["fields"]["to"])
        for block in sections
        if block["kind"] == "connection"
    ]
    assert len(endpoints) == len(set(endpoints))
    ports = {
        block["id"] + "." + port["key"]: port["kind"]
        for block in sections
        if block["kind"] in {"task", "input"}
        for direction in ("inputs", "outputs")
        for port in block["fields"].get(direction, [])
    }
    for block in sections:
        if block["kind"] == "connection" and block["fields"]["type"] == "item":
            fields = block["fields"]
            assert ports[fields["from"]] == ports[fields["to"]], fields
    assert '"max_revisions":0' in source
    assert "printer_print" not in source and "printer_upload" not in source
    validator = next(
        step for step in plan.steps if step.id == "validate_outputs_source_test"
    )
    profile = ValidatorConfiguration.model_validate(validator.validation).load(
        str(workspace)
    )
    assert profile.id == "printed-replacement-part-01-full"
    assert len(profile.checks) == 18
    assert profile.checks[-1].constraint.operator == "review"
    call = json.loads(
        (
            workspace
            / "process-proofs/printed-replacement-part/source-test/inputs/slice-call.json"
        ).read_bytes()
    )
    assert call["source"].endswith("repaired_mesh.stl") and call["orient"] is False
    inspect = json.loads(
        (
            workspace
            / "process-proofs/printed-replacement-part/source-test/inputs/inspection-call.json"
        ).read_bytes()
    )
    assert inspect["critic_approved"] is False
    assert "read_3mf_toolpaths" in inspect["input_content"]
    assert not list((workspace / report["output_root"]).iterdir())
    for item in report["input_files"]:
        assert (
            module.definition.sha((workspace / item["path"]).read_bytes())
            == item["sha256"]
        )
        if item["original"]:
            assert (workspace / item["path"]).read_bytes() == (
                REPO / item["original"]
            ).read_bytes()


def test_printed_missing_tool_never_stages_attempt(printed_configuration):
    workspace, bindings, tools = printed_configuration
    with pytest.raises(ValueError, match="capability is missing"):
        printed_preparer().prepare(workspace, "missing-tool", tools[:-1], bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_explicit_reader_budget_retains_original_criteria(
    printed_configuration,
):
    workspace, bindings, tools = printed_configuration
    bindings["validation_resource_budget"] = {"max_entities": 1_000_000}
    module = printed_preparer()
    report = module.prepare(workspace, "reader-budget", tools, bindings)
    plan = compile_prompt_workflow((workspace / report["source_path"]).read_text())
    step = next(s for s in plan.steps if s.validation)
    config = ValidatorConfiguration.model_validate(step.validation)
    assert config.budget.max_entities == 1_000_000
    assert config.budget.max_bytes == 16 * 1024 * 1024
    assert config.budget.timeout_seconds == 120
    profile = config.load(str(workspace))
    assert profile.id == "printed-replacement-part-01-full"
    assert (
        len(profile.checks) == 18 and profile.checks[-1].constraint.operator == "review"
    )
    assert step.max_revisions == 0


@pytest.mark.parametrize(
    "budget",
    [{"max_entities": 2_000_001}, {"max_entities": 0}, {"max_entities": "1000000"}],
)
def test_printed_invalid_reader_budget_blocks_before_staging(
    printed_configuration, budget
):
    workspace, bindings, tools = printed_configuration
    bindings["validation_resource_budget"] = budget
    with pytest.raises(ValueError):
        printed_preparer().prepare(workspace, "invalid-budget", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def configured_geometry(bindings, root, module):
    values = {
        "basis": {
            "proposed_geometry": {"body_diameter_mm": 38},
            "engineering_acceptance": False,
        },
        "construction": {"code": "print('fixture construction only')"},
        "repair": {"code": "print('fixture repair only')"},
    }
    bindings["geometry_operation_files"] = {}
    for role, value in values.items():
        path = root / (role + "-provider-input.json")
        path.write_text(json.dumps(value), encoding="utf-8")
        bindings["geometry_operation_files"][role] = {
            "path": str(path),
            "sha256": module.definition.sha(path.read_bytes()),
        }


def configured_retained_source(bindings, root, module):
    import struct

    values = {
        "mesh": b"fixture only".ljust(80, b"\0") + struct.pack("<I", 1) + bytes(50),
        "observations": json.dumps(
            {"fixture": True, "native_execution": False}
        ).encode(),
    }
    values["origin"] = json.dumps(
        {
            "producer_run_id": "fixture-failed-producer",
            "producer_source_path": "workflows/fixture.workflow.wflow",
            "producer_source_sha256": "b" * 64,
            "producer_status": "failed",
            "mesh_sha256": module.definition.sha(values["mesh"]),
            "observations_sha256": module.definition.sha(values["observations"]),
            "engineering_acceptance": False,
        }
    ).encode()
    bindings["retained_geometry_source"] = {}
    for role, raw in values.items():
        path = root / ("retained-" + role)
        path.write_bytes(raw)
        bindings["retained_geometry_source"][role] = {
            "path": str(path),
            "sha256": module.definition.sha(raw),
        }


def test_retained_consumer_uses_exact_repair_and_original_full_gate(
    printed_configuration,
):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    configured_retained_source(bindings, workspace, module)
    report = module.prepare(workspace, "retained-consumer", tools, bindings)
    source = (workspace / report["source_path"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 10
    assert not any(s.id.startswith("create_mesh") for s in plan.steps)
    repair = next(s for s in plan.steps if s.id.startswith("repair_measure_orient"))
    assert repair.agent_task is False
    assert repair.server_id == "fixture-geometry"
    assert repair.tool_name == "fixture-geometry__execute_blender_code"
    assert repair.timeout_seconds == 360
    assert len(repair.references) == 2
    from workspace_service.process_interfaces.inputs import input_file_reference

    binary_id = next(key for key in plan.inputs if "retained_source_stl" in key)
    input_file_reference(
        plan,
        plan.inputs[binary_id],
        binary_id,
        "inputs/retained-source.stl",
        Path(bindings["retained_geometry_source"]["mesh"]["path"]).read_bytes(),
    )
    assert list(repair.file_dependencies.values()) == [
        "process-proofs/printed-replacement-part/retained-consumer/inputs/retained-source.stl"
    ]
    validator = next(s for s in plan.steps if s.id.startswith("validate_outputs"))
    profile = ValidatorConfiguration.model_validate(validator.validation).load(
        str(workspace)
    )
    assert len(profile.checks) == 18
    assert profile.id == "printed-replacement-part-01-full"
    assert profile.checks[-1].constraint.operator == "review"
    assert source.count('"action_kind":"local_review"') == 2
    summarizer = next(s for s in plan.steps if s.id.startswith("summarize_preparation"))
    assert summarizer.agent_task is True
    assert summarizer.max_tool_calls == 2
    assert summarizer.timeout_seconds == 360
    assert summarizer.task_tool_allowlist == ("inspect_file",)
    assert "do not guess report filenames" in summarizer.prompt
    assert "Wright saves it" in summarizer.prompt
    assert any("toolpath_summary" in address for _, address in summarizer.references)
    assert not any(
        address.endswith(".support_preview") for _, address in summarizer.references
    )
    assert "retained geometry consumer" in source
    assert "without claiming the failed producer completed" in source
    assert "retained_source_stl" in source
    assert not list((workspace / report["output_root"]).iterdir())
    for reference in bindings["retained_geometry_source"].values():
        assert any(
            (workspace / item["path"]).read_bytes()
            == Path(reference["path"]).read_bytes()
            for item in report["input_files"]
        )
    assert report["source_acceptance_required"] is True
    assert report["physical_dispatch"] is False


@pytest.mark.parametrize(
    "fault", ["hash", "truncated", "accepted", "wrong_origin", "no_recipe"]
)
def test_retained_consumer_defects_block_before_staging(printed_configuration, fault):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    configured_retained_source(bindings, workspace, module)
    selected = bindings["retained_geometry_source"]
    if fault == "hash":
        selected["mesh"]["sha256"] = "f" * 64
    elif fault == "no_recipe":
        del bindings["geometry_operation_files"]
    else:
        role = "mesh" if fault == "truncated" else "origin"
        path = Path(selected[role]["path"])
        if fault == "truncated":
            path.write_bytes(path.read_bytes()[:-1])
        else:
            value = json.loads(path.read_bytes())
            value[
                "engineering_acceptance" if fault == "accepted" else "mesh_sha256"
            ] = True if fault == "accepted" else "f" * 64
            path.write_text(json.dumps(value), encoding="utf-8")
        selected[role]["sha256"] = module.definition.sha(path.read_bytes())
    with pytest.raises(ValueError):
        module.prepare(workspace, "invalid-retained", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_qualified_geometry_uses_existing_scoped_tasks_and_preserves_review_gate(
    printed_configuration,
):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    report = module.prepare(workspace, "qualified-inputs", tools, bindings)
    source = (workspace / report["source_path"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 11
    for prefix in ("create_mesh", "repair_measure_orient"):
        step = next(s for s in plan.steps if s.id.startswith(prefix))
        assert step.server_id == "fixture-geometry" and step.agent_task is True
        assert step.timeout_seconds == 360
        assert step.max_tool_calls == 2
        assert "Use the code argument in qualified_operation" in step.prompt
        assert any("provider_arguments_json" in source for _, source in step.references)
    basis = next(s for s in plan.steps if s.id.startswith("define_geometry_basis"))
    assert "Retain its numeric construction choices exactly" in basis.prompt
    assert source.count('"action_kind":"local_review"') == 2
    validator = next(s for s in plan.steps if s.id.startswith("validate_outputs"))
    profile = ValidatorConfiguration.model_validate(validator.validation).load(
        str(workspace)
    )
    assert (
        profile.id == "printed-replacement-part-01-full" and len(profile.checks) == 18
    )
    assert profile.checks[-1].constraint.operator == "review"
    repair = next(s for s in plan.steps if s.id.startswith("repair_measure_orient"))
    assert len(repair.file_dependencies) == 1
    for role in ("basis", "construction", "repair"):
        original = Path(bindings["geometry_operation_files"][role]["path"]).read_bytes()
        assert any(
            (workspace / item["path"]).read_bytes() == original
            for item in report["input_files"]
        )
    assert not list((workspace / report["output_root"]).iterdir())


@pytest.mark.parametrize("fault", ["missing", "hash", "accepted", "oversize"])
def test_qualified_geometry_defects_block_before_staging(printed_configuration, fault):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    if fault == "missing":
        del bindings["geometry_operation_files"]["repair"]
    elif fault == "hash":
        bindings["geometry_operation_files"]["construction"]["sha256"] = "f" * 64
    else:
        role = "basis" if fault == "accepted" else "repair"
        reference = bindings["geometry_operation_files"][role]
        path = Path(reference["path"])
        path.write_text(
            json.dumps(
                {
                    "proposed_geometry": {"body_diameter_mm": 38},
                    "engineering_acceptance": True,
                }
            )
            if fault == "accepted"
            else "x" * 65537,
            encoding="utf-8",
        )
        reference["sha256"] = module.definition.sha(path.read_bytes())
    with pytest.raises(ValueError):
        module.prepare(workspace, "invalid-geometry-input", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_profile_hash_is_required_before_staging(printed_configuration):
    workspace, bindings, tools = printed_configuration
    bindings["profiles"]["process"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="configuration changed"):
        printed_preparer().prepare(workspace, "changed-profile", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_wrong_material_is_never_substituted(printed_configuration):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    path = Path(bindings["profiles"]["filament"]["path"])
    value = json.loads(path.read_bytes())
    value["filament_type"] = ["PLA"]
    path.write_text(json.dumps(value))
    bindings["profiles"]["filament"]["sha256"] = module.definition.sha(
        path.read_bytes()
    )
    with pytest.raises(ValueError, match="original requirement"):
        module.prepare(workspace, "wrong-material", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_existing_proposal_is_not_overwritten(printed_configuration):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    report = module.prepare(workspace, "preserved", tools, bindings)
    path = workspace / report["source_path"]
    before = path.read_bytes()
    with pytest.raises(ValueError, match="fresh attempt"):
        module.prepare(workspace, "preserved", tools, bindings)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "destination",
    [
        "https://supplier.example/jobs",
        "test://campaign/../outside",
        "test://campaign/part?submit=true",
    ],
)
def test_printed_non_test_destination_blocks_before_staging(
    printed_configuration, destination
):
    workspace, bindings, tools = printed_configuration
    bindings["simulator_destination"] = destination
    with pytest.raises(ValueError, match="test:// destination"):
        printed_preparer().prepare(workspace, "bad-destination", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_unqualified_success_contract_blocks_before_staging(
    printed_configuration,
):
    workspace, bindings, tools = printed_configuration
    bindings["slice_success_contract"] = ""
    with pytest.raises(ValueError, match="qualified success contract"):
        printed_preparer().prepare(workspace, "missing-contract", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize("guidance", [None, "", "x" * 8193])
def test_printed_missing_or_excessive_geometry_guidance_blocks_before_staging(
    printed_configuration, guidance
):
    workspace, bindings, tools = printed_configuration
    bindings["geometry_guidance"] = guidance
    with pytest.raises(ValueError, match="qualified geometry application guidance"):
        printed_preparer().prepare(workspace, "missing-guidance", tools, bindings)
    assert not (workspace / "process-proofs").exists()
