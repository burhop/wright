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


def test_heat_cad_container_mapping_keeps_host_and_provider_paths_distinct(configuration):
    from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths

    workspace, project, bindings, tools = configuration
    bindings.update(cad_workspace="/cad-workspace", run_path_template=VERSION)
    manifest = project / "build/agentcad.json"
    manifest.write_text(json.dumps({
        "runtime": "build123d", "project_root": "/cad-workspace/selected-cad-project", "versions": [],
    }))
    before = manifest.read_bytes()
    module = heat_preparer()
    report = module.prepare(workspace, "container", tools, bindings)
    plan = compile_prompt_workflow((workspace / report["source_path"]).read_text())
    root = workspace / "process-proofs/heat-spreader-sizing/container/inputs"
    mapping = json.loads((root / "cad-path-mapping.json").read_bytes())
    assert mapping == {
        "local_workspace": str(workspace.resolve()), "local_project": str(project.resolve()),
        "provider_workspace": "/cad-workspace", "provider_project": "/cad-workspace/selected-cad-project",
        "manifest_sha256": module.definition.sha(before), "mapping": "explicit_posix_mount",
    }
    operation = json.loads((root / "cad-call.json").read_bytes())
    assert operation["cwd"] == "/cad-workspace/selected-cad-project"
    assert operation["script"] == "/cad-workspace/" + report["output_template"] + "/plate-source.py"
    solver = json.loads((root / "solver-call.json").read_bytes())
    assert solver["job_name"].startswith("/workspace/")
    assert "/cad-workspace/" not in solver["input_content"]
    author = next(step for step in plan.steps if step.id == "author_cad_container")
    observed = next(step for step in plan.steps if step.id == "measure_candidates_container")
    assert operation["script"].rsplit("/", 1)[0] in author.prompt
    assert "/cad-workspace/" in observed.prompt
    assert str(workspace) not in author.prompt
    for run_id in ("first", "second"):
        bound = bind_run_paths(plan, run_id)
        for step in bound.steps:
            assert TOKEN not in step.prompt
            if step.save:
                assert step.output_path.startswith(report["output_root"] + "/" + run_id + "/")
    assert manifest.read_bytes() == before
    assert any(item["path"].endswith("cad-path-mapping.json") for item in report["input_files"])


@pytest.mark.parametrize("mount", ["", "relative", "//server/share", "/workspace/../other", "/a/./b", "/a//b", "C:\\workspace", "/workspace\\project", None])
def test_bad_cad_mount_blocks_before_staging(configuration, mount):
    workspace, _, bindings, tools = configuration
    bindings["cad_workspace"] = mount
    with pytest.raises(ValueError, match="explicit absolute POSIX workspace mount"):
        heat_preparer().prepare(workspace, "bad-cad-mount", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_container_mapping_does_not_adopt_a_host_manifest(configuration):
    workspace, project, bindings, tools = configuration
    bindings["cad_workspace"] = "/workspace"
    before = (project / "build/agentcad.json").read_bytes()
    with pytest.raises(ValueError, match="exact root"):
        heat_preparer().prepare(workspace, "wrong-provider-root", tools, bindings)
    assert (project / "build/agentcad.json").read_bytes() == before
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
    assert "Preserve that original text verbatim" in create.prompt
    assert "do not replace it with a task summary" in create.prompt
    for step in (create, repair):
        references = dict(step.references)
        for role, filename in (
            ("original_user_prompt", "prompt.txt"),
            ("original_context", "context.md"),
            ("original_user_profile", "user-profile.md"),
        ):
            address = next(
                address for name, address in references.items()
                if name.replace(" ", "_").endswith(role)
            )
            settings = plan.inputs[address.split(".")[0]]["settings"]
            staged = workspace / settings["workspace_file"]
            assert staged.name == filename
            assert staged.read_bytes() == (
                REPO / "tests/datasets/engineering-workflows/scenarios"
                / "printed-replacement-part/01-observatory-focus-wheel" / filename
            ).read_bytes()
        assert "user_prompt" in step.prompt
    image_addresses = [
        address for name, address in create.references
        if name.replace(" ", "_").endswith("original_reference")
    ]
    assert len(image_addresses) == 1
    image_settings = plan.inputs[image_addresses[0].split(".")[0]]["settings"]
    assert image_settings["workspace_file"].endswith("/concept.png")
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
    review = next(step for step in plan.steps if step.id == "review_preparation_source_test")
    assert plan.steps.index(review) < plan.steps.index(validator)
    assert review.external_action["action_kind"] == "local_review"
    assert review.external_action["settings"]["validation_review"] == {
        "profile_ref": profile.reference().model_dump(mode="json"),
        "requirement_ids": sorted(
            requirement.id for requirement in profile.baseline.requirements
            if requirement.review_required
        ),
    }
    # The review must be reachable before assessment, with the same exact subjects.
    review_sources = {address for _, address in review.references}
    assert set(dict(validator.validation_sources).values()) <= review_sources
    assert not any(address.startswith(validator.id + ".") for address in review_sources)
    assert plan.steps[-1].id == validator.id
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


@pytest.mark.parametrize("mode", ["generated", "qualified", "configured", "mixed", "retained"])
def test_printed_run_paths_bind_all_write_boundaries_and_keep_opaque_inputs(printed_configuration, mode):
    from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths, bind_run_input_values
    from workspace_service.workflow_references import WorkflowReference

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    bindings["run_path_template"] = VERSION
    if mode == "configured":
        bindings["geometry_operation_mode"] = "configured_tool"
    if mode == "mixed":
        bindings["geometry_operation_modes"] = {
            "construction": "ai_task", "repair": "configured_tool",
        }
    if mode != "generated":
        configured_geometry(bindings, workspace, module)
        for role in ("construction", "repair"):
            reference = bindings["geometry_operation_files"][role]
            path = Path(reference["path"])
            path.write_text(json.dumps({"code": f"print('fixture-only outputs/{TOKEN}/{role}.stl')"}))
            reference["sha256"] = module.definition.sha(path.read_bytes())
    if mode == "retained":
        configured_retained_source(bindings, workspace, module)
    report = module.prepare(workspace, "repeatable-" + mode, tools, bindings)
    source_path = workspace / report["source_path"]
    source_bytes = source_path.read_bytes()
    plan = compile_prompt_workflow(source_bytes.decode())
    assert report["output_template"] == report["output_root"] + "/" + TOKEN
    assert not list((workspace / report["output_root"]).iterdir())
    assert not (workspace / report["accepted_source_path"]).exists()
    configured = {}
    for key, fields in plan.inputs.items():
        settings = fields["settings"]
        raw = (workspace / settings["workspace_file"]).read_bytes()
        if settings.get("run_path_template"):
            configured[key] = WorkflowReference.from_bytes(settings["workspace_file"], raw, image=False)
        elif Path(settings["workspace_file"]).name in {
            "machine-profile.json", "process-profile.json", "filament-profile.json",
            "retained-source.stl", "configured-geometry-basis.json", "passive-representations.py",
            "inspect_manufacturing_package.py", "concept.png",
        }:
            assert settings.get("run_path_template") is None
    original_templates = {v.path: (workspace / v.path).read_bytes() for v in configured.values()}
    for run_id in ("printed-one", "printed-two"):
        bound = bind_run_paths(plan, run_id)
        values = bind_run_input_values(bound, configured)
        assert bound.run_path_roots == (report["output_root"] + "/" + run_id,)
        for step in bound.steps:
            if step.save or step.external_action and step.output_path:
                assert step.output_path.startswith(report["output_root"] + "/" + run_id + "/")
            assert TOKEN not in step.prompt
            assert all(TOKEN not in p for p in step.expected_files)
            assert all(TOKEN not in p for p in step.file_dependencies.values())
        operations = {Path(value.path).name: json.loads(value.text) for value in values.values()}
        slicer = operations["slice-call.json"]
        assert run_id in slicer["source"] and run_id in slicer["output"]
        inspection = operations["inspection-call.json"]
        assert inspection["job_name"] == report["output_root"] + "/" + run_id + "/package-inspection"
        assert TOKEN not in inspection["input_content"] and run_id in inspection["input_content"]
        assert inspection["critic_approved"] is False
        transfer = next(s for s in bound.steps if (s.external_action or {}).get("action_kind") == "printer_transfer")
        assert transfer.external_action["settings"]["receipt_path"] == report["output_root"] + "/" + run_id + "/simulated-transfer-receipt.json"
        assert "package_path" not in transfer.external_action["settings"]
        assert transfer.external_action["settings"]["material"] == "PETG"
        assert transfer.external_action["destination"]["id"] == bindings["simulator_destination"]
        validator = next(s for s in bound.steps if s.validation)
        profile = ValidatorConfiguration.model_validate(validator.validation).load(str(workspace))
        assert profile.id == "printed-replacement-part-01-full" and len(profile.checks) == 18
    assert source_path.read_bytes() == source_bytes
    assert all((workspace / p).read_bytes() == raw for p, raw in original_templates.items())


def test_qualified_geometry_can_explicitly_use_existing_configured_tool_binding(
    printed_configuration,
):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = "configured_tool"
    report = module.prepare(workspace, "configured-operations", tools, bindings)
    source = (workspace / report["source_path"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 11
    for prefix, role in (("create_mesh", "construction"), ("repair_measure_orient", "repair")):
        step = next(s for s in plan.steps if s.id.startswith(prefix))
        assert step.agent_task is False
        assert step.server_id == "fixture-geometry"
        assert step.tool_name == "fixture-geometry__execute_blender_code"
        assert step.timeout_seconds == 360
        assert step.prompt == ""
        assert step.arguments_from
        input_id = step.arguments_from.split(".")[0]
        raw = (workspace / plan.inputs[input_id]["settings"]["workspace_file"]).read_bytes()
        assert raw == Path(bindings["geometry_operation_files"][role]["path"]).read_bytes()
        assert step.save and step.output_path.endswith("report.json")
        assert any(source == step.arguments_from for _, source in step.references)
        assert step.expected_files
    create = next(s for s in plan.steps if s.id.startswith("create_mesh"))
    assert len(create.references) == 1
    basis_review = next(s for s in plan.steps if s.id.startswith("review_basis"))
    assert len(basis_review.references) == 4
    for role in ("construction", "repair"):
        address = next(address for name, address in basis_review.references if role + "_operation" in name.replace(" ", "_"))
        fields = plan.inputs[address.split(".")[0]]["settings"]
        assert "run_path_template" not in fields
        assert (workspace / fields["workspace_file"]).read_bytes() == Path(bindings["geometry_operation_files"][role]["path"]).read_bytes()
    assert [s.id for s in plan.steps].index(basis_review.id) < [s.id for s in plan.steps].index(create.id)
    repair = next(s for s in plan.steps if s.id.startswith("repair_measure_orient"))
    assert len(repair.file_dependencies) == 1
    assert next(iter(repair.file_dependencies)).endswith(".source_mesh")
    assert source.count('"action_kind":"local_review"') == 2
    assert next(s for s in plan.steps if s.id.startswith("define_geometry_basis")).agent_task is False
    validator = next(s for s in plan.steps if s.validation)
    profile = ValidatorConfiguration.model_validate(validator.validation).load(str(workspace))
    assert profile.id == "printed-replacement-part-01-full" and len(profile.checks) == 18
    assert profile.checks[-1].constraint.operator == "review"
    assert report["physical_dispatch"] is False
    assert not list((workspace / report["output_root"]).iterdir())


@pytest.mark.parametrize("mode", [None, "", "automatic", [], {}, 1, False])
def test_invalid_geometry_operation_mode_blocks_before_staging(printed_configuration, mode):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = mode
    with pytest.raises(ValueError, match="geometry operation mode"):
        module.prepare(workspace, "invalid-operation-mode", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_configured_geometry_requires_qualified_inputs_before_staging(printed_configuration):
    workspace, bindings, tools = printed_configuration
    bindings["geometry_operation_mode"] = "configured_tool"
    with pytest.raises(ValueError, match="pinned basis and both qualified"):
        printed_preparer().prepare(workspace, "missing-operations", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_printed_independent_construction_keeps_downstream_owners_and_full_gate(printed_configuration):
    from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = "configured_tool"
    bindings["run_path_template"] = VERSION
    for role in ("construction", "repair"):
        reference = bindings["geometry_operation_files"][role]
        path = Path(reference["path"])
        path.write_text(json.dumps({"code": f"print('fixture-only/{TOKEN}/{role}')"}))
        reference["sha256"] = module.definition.sha(path.read_bytes())
    outputs = {"source_mesh": "source_mesh.stl", "native_cad": "native-design.FCStd",
               "neutral_cad": "native-design.step", "cad_preview": "native-design.png",
               "native_measurements": "native-measurements.json"}
    bindings["construction_binding"] = {"server": "fixture-native-cad", "tool": "execute_code", "outputs": outputs}
    tools.append(dict(server_id="fixture-native-cad", tool_name="execute_code",
                      name="fixture-native-cad__execute_code", schema_digest="b" * 64))
    report = module.prepare(workspace, "independent-construction", tools, bindings)
    plan = compile_prompt_workflow((workspace / report["source_path"]).read_text())
    for run_id in ("native-one", "native-two"):
        bound = bind_run_paths(plan, run_id)
        create = next(s for s in bound.steps if s.id.startswith("create_mesh"))
        repair = next(s for s in bound.steps if s.id.startswith("repair_measure_orient"))
        assert create.server_id == "fixture-native-cad" and create.tool_name.endswith("__execute_code")
        assert create.agent_task is False and create.prompt == ""
        assert set(create.expected_files) == {report["output_root"] + "/" + run_id + "/" + name for name in outputs.values()}
        assert repair.server_id == "fixture-geometry" and repair.tool_name.endswith("__execute_blender_code")
        assert list(repair.file_dependencies.values()) == [report["output_root"] + "/" + run_id + "/source_mesh.stl"]
        assert {s.server_id for s in bound.steps if s.id.startswith("supports_and_slice")} == {"fixture-slicer"}
        gate = next(s for s in bound.steps if s.validation)
        profile = ValidatorConfiguration.model_validate(gate.validation).load(str(workspace))
        assert profile.id == "printed-replacement-part-01-full" and len(profile.checks) == 18
        assert profile.checks[-1].constraint.operator == "review"
    assert report["physical_dispatch"] is False
    assert not list((workspace / report["output_root"]).iterdir())


@pytest.mark.parametrize("binding", [None, {}, {"server": "cad", "tool": "execute_code"},
    {"server": "cad", "tool": "execute_code", "outputs": {"source_mesh": "other.stl"}},
    {"server": "cad", "tool": "execute_code", "outputs": {"source_mesh": "source_mesh.stl", "cad": "../escaped.step"}},
    {"server": "cad", "tool": "execute_code", "outputs": {"source_mesh": "source_mesh.stl", "cad": "source-model-report.json"}},
    {"server": "cad", "tool": "execute_code", "outputs": {"source_mesh": "source_mesh.stl", "cad": "source_mesh.stl"}},
])
def test_invalid_independent_construction_binding_never_stages(printed_configuration, binding):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = "configured_tool"
    bindings["construction_binding"] = binding
    with pytest.raises(ValueError, match="construction"):
        module.prepare(workspace, "bad-independent-construction", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_missing_independent_construction_capability_never_stages(printed_configuration):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = "configured_tool"
    bindings["construction_binding"] = {"server": "absent-native-cad", "tool": "execute_code", "outputs": {"source_mesh": "source_mesh.stl"}}
    with pytest.raises(ValueError, match="absent-native-cad/execute_code"):
        module.prepare(workspace, "missing-independent-construction", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_independent_construction_requires_explicit_configured_mode(printed_configuration):
    workspace, bindings, tools = printed_configuration
    bindings["construction_binding"] = {"server": "native-cad", "tool": "execute_code", "outputs": {"source_mesh": "source_mesh.stl"}}
    with pytest.raises(ValueError, match="configured tool"):
        printed_preparer().prepare(workspace, "implicit-construction", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def repair_completion_binding(workspace, bindings, module):
    """Declare a fixture inspector without running any engineering provider."""
    path = workspace.parent / "completion-arguments.json"
    path.write_text(json.dumps({"code": "print('fixture completion inspector')"}))
    bindings["repair_completion_operation"] = {
        "server": "fixture-inspection", "tool": "run_simulation",
        "arguments_file": {"path": str(path), "sha256": module.definition.sha(path.read_bytes())},
    }


def test_printed_repair_completion_gate_preserves_checks_and_precedes_slice(printed_configuration):
    from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings.update(geometry_operation_mode="configured_tool", run_path_template=VERSION)
    for role in ("construction", "repair"):
        reference = bindings["geometry_operation_files"][role]
        path = Path(reference["path"])
        path.write_text(json.dumps({"code": f"print('fixture-only/{TOKEN}/{role}')"}))
        reference["sha256"] = module.definition.sha(path.read_bytes())
    repair_completion_binding(workspace, bindings, module)
    result = module.prepare(workspace, "completion-gate", tools, bindings)
    plan = compile_prompt_workflow((workspace / result["source_path"]).read_text())
    for run_id in ("completion-first", "completion-second"):
        bound = bind_run_paths(plan, run_id)
        early = next(s for s in bound.steps if s.id.startswith("validate_mesh_before_slice"))
        final = next(s for s in bound.steps if s.validation and s != early)
        early_profile = ValidatorConfiguration.model_validate(early.validation).load(str(workspace))
        final_profile = ValidatorConfiguration.model_validate(final.validation).load(str(workspace))
        mesh_checks = [c for c in final_profile.checks if c.subject_role == "repaired_mesh"]
        assert len(mesh_checks) == 5
        assert list(early_profile.checks[:-1]) == mesh_checks
        assert early_profile.checks[-1].selector == "/completed_program_record"
        assert early_profile.checks[-1].constraint.expected is True
        completion_requirement = next(r for r in early_profile.baseline.requirements if r.id == "PRINT01-REPAIR-COMPLETION")
        staged_reference = completion_requirement.sources[0]
        assert not Path(staged_reference.artifact_ref).is_absolute()
        assert module.definition.sha((workspace / staged_reference.artifact_ref).read_bytes()) == staged_reference.sha256
        assert len(final_profile.checks) == 18
        assert final_profile.checks[-1].constraint.operator == "review"
        inspector = next(s for s in bound.steps if s.id.startswith("inspect_repair_completion"))
        slicer = next(s for s in bound.steps if s.id.startswith("supports_and_slice"))
        order = [s.id for s in bound.steps]
        assert order.index(inspector.id) < order.index(early.id) < order.index(slicer.id)
        assert inspector.agent_task is False and inspector.prompt == ""
        assert inspector.expected_files == (result["output_root"] + "/" + run_id + "/repair-completion.json",)
        assert any(p.endswith("/" + run_id + "/repair-provider-response.json") for p in inspector.file_dependencies.values())
        assert len(inspector.file_dependencies) == 5
        assert {c.subject_role for c in early_profile.checks} == {"repaired_mesh", "completion"}
    assert result["physical_dispatch"] is False
    assert not list((workspace / result["output_root"]).iterdir())


def native_inspection_binding(workspace, bindings, tools, module):
    """Authored fixture declarations only; no native provider call."""
    configured_geometry(bindings, workspace, module)
    bindings.update(geometry_operation_mode="configured_tool", run_path_template="wright.run-path/1")
    for role in ("construction", "repair"):
        ref = bindings["geometry_operation_files"][role]
        path = Path(ref["path"])
        path.write_text(json.dumps({"code": "print('fixture/{{wright.run_id}}')"}))
        ref["sha256"] = module.definition.sha(path.read_bytes())
    bindings["construction_binding"] = {
        "server": "fixture-native", "tool": "execute_code",
        "outputs": {"native_cad": "native.FCStd", "neutral_cad": "neutral.step", "source_mesh": "source_mesh.stl"},
    }
    tools.append(dict(server_id="fixture-native", tool_name="execute_code", name="fixture-native__execute_code", schema_digest="c" * 64))
    path = workspace.parent / "native-inspection-arguments.json"
    path.write_text(json.dumps({"code": "print('fixture inspection/{{wright.run_id}}')"}))
    bindings["native_inspection_operation"] = {
        "server": "fixture-native", "tool": "execute_code",
        "arguments_file": {"path": str(path), "sha256": module.definition.sha(path.read_bytes())},
    }


def test_integrated_native_inspection_preserves_full_profile_and_exact_handoffs(printed_configuration):
    from workspace_service.workflow_run_paths import bind_run_paths

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    native_inspection_binding(workspace, bindings, tools, module)
    result = module.prepare(workspace, "native-inspection", tools, bindings)
    plan = compile_prompt_workflow((workspace / result["source_path"]).read_text(encoding="utf-8"))
    for run_id in ("inspection-first", "inspection-second"):
        bound = bind_run_paths(plan, run_id)
        create, inspect, early, repair, final, review = (
            next(s for s in bound.steps if s.id.startswith(prefix))
            for prefix in ("create_mesh", "inspect_native_and_draw", "validate_native_inspection", "repair_measure_orient", "validate_outputs", "review_preparation")
        )
        order = [s.id for s in bound.steps]
        assert order.index(create.id) < order.index(inspect.id) < order.index(early.id) < order.index(repair.id)
        assert inspect.agent_task is False and inspect.prompt == ""
        assert inspect.server_id == "fixture-native"
        report_step = next(s for s in bound.steps if s.id.startswith("summarize_preparation"))
        assert "maxTextBytes=32768" in report_step.prompt
        assert "maxTextBytes=65536" not in report_step.prompt
        assert "truncated or unavailable" in report_step.prompt
        root = result["output_root"] + "/" + run_id + "/"
        assert set(inspect.file_dependencies.values()) == {root + name for name in ("native.FCStd", "neutral.step", "source_mesh.stl")}
        assert set(inspect.expected_files) == {root + name for name in module.native_inspection.OUTPUTS.values()}
        early_profile = ValidatorConfiguration.model_validate(early.validation).load(str(workspace))
        final_profile = ValidatorConfiguration.model_validate(final.validation).load(str(workspace))
        assert early_profile.version == "2" and len(early_profile.checks) == 20
        assert any(check.selector == "/drawing/dimension_values_mm/SocketAcrossFlat" for check in early_profile.checks)
        assert all(r.id.endswith("-DIGITAL-OBSERVATION") for r in early_profile.baseline.requirements)
        assert final_profile.id == "printed-replacement-part-01-full" and len(final_profile.checks) == 18
        assert final_profile.checks[-1].constraint.operator == "review"
        references = [ref for _, ref in review.references]
        assert inspect.id + ".drawing_pdf" in references
        assert inspect.id + ".drawing_preview" in references
        assert inspect.id + ".matrix" in references
        assert early.id + ".native_inspection_assessment" in references
    assert result["physical_dispatch"] is False
    assert not list((workspace / result["output_root"]).iterdir())


def test_native_orientation_study_uses_same_run_geometry_and_preserves_reviews(printed_configuration):
    from workspace_service.workflow_run_paths import bind_run_paths

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    native_inspection_binding(workspace, bindings, tools, module)
    bindings.update(orientation_comparison=True, nominal_layer_section=None)
    result = module.prepare(workspace, "integrated-orientation", tools, bindings)
    comparison_args = workspace / "process-proofs/printed-replacement-part/integrated-orientation/inputs/orientation/compare_orientations-arguments.json"
    comparison_code = json.loads(comparison_args.read_bytes())["input_content"]
    assert "filament mass (g)" in comparison_code
    assert "filament length (mm)" in comparison_code
    source = (workspace / result["source_path"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    for run_id in ("first", "second"):
        steps = bind_run_paths(plan, run_id).steps
        create, native, orient, compare, review, final = (
            next(s for s in steps if s.id.startswith(prefix)) for prefix in (
                "create_mesh", "validate_native_inspection", "orient_geometry",
                "compare_orientations", "review_preparation", "validate_outputs"))
        root = result["output_root"] + "/" + run_id + "/"
        assert root + "source_mesh.stl" in orient.file_dependencies.values()
        assert root + "source_mesh.stl" in compare.file_dependencies.values()
        assert root + "orientation/source_mesh.stl" in compare.file_dependencies.values()
        assert steps.index(create) < steps.index(native) < steps.index(orient) < steps.index(compare) < steps.index(review)
        assert sum(s.id.startswith("slice_socket_") for s in steps) == 2
        refs = [ref for _, ref in review.references]
        assert any(ref.startswith(compare.id + ".") for ref in refs)
        assert any("inspect_native_and_draw" in ref and ref.endswith("drawing_pdf") for ref in refs)
        full = ValidatorConfiguration.model_validate(final.validation).load(str(workspace))
        assert len(full.checks) == 18 and full.checks[-1].constraint.operator == "review"
    assert source.count('"action_kind":"local_review"') == 2
    assert result["physical_dispatch"] is False
    assert not list((workspace / result["output_root"]).iterdir())


@pytest.mark.parametrize("value", ["true", 1, None])
def test_orientation_selection_requires_typed_configuration(printed_configuration, value):
    workspace, bindings, tools = printed_configuration
    bindings["orientation_comparison"] = value
    with pytest.raises(ValueError, match="boolean"):
        printed_preparer().prepare(workspace, "invalid-orientation", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize("fault", ["missing_provider", "missing_native_output", "changed_arguments", "nonobject_arguments", "unexpected_binding", "ai_construction"])
def test_native_inspection_invalid_binding_does_not_stage(printed_configuration, fault):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    native_inspection_binding(workspace, bindings, tools, module)
    binding = bindings["native_inspection_operation"]
    if fault == "missing_provider":
        binding["server"] = "unavailable-inspector"
    elif fault == "missing_native_output":
        bindings["construction_binding"]["outputs"].pop("native_cad")
    elif fault == "unexpected_binding":
        binding["approve"] = True
    elif fault == "ai_construction":
        bindings.pop("construction_binding")
        bindings["geometry_operation_mode"] = "ai_task"
    else:
        path = Path(binding["arguments_file"]["path"])
        path.write_text("[]")
        if fault == "nonobject_arguments":
            binding["arguments_file"]["sha256"] = module.definition.sha(path.read_bytes())
    with pytest.raises(ValueError):
        module.prepare(workspace, "invalid-native-inspection", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize("fault", ["missing_server", "changed_arguments", "non_object_arguments", "extra_binding_field"])
def test_printed_repair_completion_bad_binding_never_stages(printed_configuration, fault):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = "configured_tool"
    repair_completion_binding(workspace, bindings, module)
    binding = bindings["repair_completion_operation"]
    if fault == "missing_server":
        binding["server"] = "missing-inspector"
    elif fault == "extra_binding_field":
        binding["approval"] = True
    else:
        path = Path(binding["arguments_file"]["path"])
        path.write_text("[]")
        if fault == "non_object_arguments":
            binding["arguments_file"]["sha256"] = module.definition.sha(path.read_bytes())
    with pytest.raises(ValueError):
        module.prepare(workspace, "invalid-completion-gate", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize("construction", ["ai_task", "configured_tool"])
@pytest.mark.parametrize("repair", ["ai_task", "configured_tool"])
def test_printed_geometry_stage_modes_reuse_existing_bindings(
    printed_configuration, construction, repair,
):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_modes"] = {
        "construction": construction, "repair": repair,
    }
    report = module.prepare(workspace, "separate-stage-modes", tools, bindings)
    source = (workspace / report["source_path"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 11
    review = next(step for step in plan.steps if step.id.startswith("review_basis"))
    for prefix, role, mode in (
        ("create_mesh", "construction", construction),
        ("repair_measure_orient", "repair", repair),
    ):
        step = next(step for step in plan.steps if step.id.startswith(prefix))
        assert step.agent_task is (mode == "ai_task")
        assert step.server_id == "fixture-geometry" and step.timeout_seconds == 360
        if mode == "configured_tool":
            assert step.arguments_from and step.tool_name.endswith("__execute_blender_code")
            assert step.prompt == ""
            assert any(role + " operation" in name for name, _ in review.references)
            address = step.arguments_from.split(".")[0]
            path = workspace / plan.inputs[address]["settings"]["workspace_file"]
            assert path.read_bytes() == Path(bindings["geometry_operation_files"][role]["path"]).read_bytes()
        else:
            assert step.max_tool_calls == 2 and not step.arguments_from
            assert any("original user prompt" in name for name, _ in step.references)
            assert "user_prompt" in step.prompt
    repair_step = next(step for step in plan.steps if step.id.startswith("repair_measure_orient"))
    assert list(repair_step.file_dependencies.values()) == [report["output_root"] + "/source_mesh.stl"]
    assert source.count('"action_kind":"local_review"') == 2
    gate = next(step for step in plan.steps if step.validation)
    profile = ValidatorConfiguration.model_validate(gate.validation).load(str(workspace))
    assert len(profile.checks) == 18 and profile.checks[-1].constraint.operator == "review"
    assert report["physical_dispatch"] is False


@pytest.mark.parametrize("modes", [None, {}, [], False,
    {"repair": "configured_tool"},
    {"construction": "ai_task", "repair": "unknown"},
    {"construction": "ai_task", "repair": "configured_tool", "slice": "configured_tool"},
])
def test_invalid_geometry_stage_modes_block_before_staging(printed_configuration, modes):
    workspace, bindings, tools = printed_configuration
    bindings["geometry_operation_modes"] = modes
    with pytest.raises(ValueError, match="both supported geometry operation modes"):
        printed_preparer().prepare(workspace, "invalid-stage-modes", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_mixed_geometry_stage_modes_require_pinned_inputs(printed_configuration):
    workspace, bindings, tools = printed_configuration
    bindings["geometry_operation_modes"] = {"construction": "ai_task", "repair": "configured_tool"}
    with pytest.raises(ValueError, match="pinned basis and both qualified"):
        printed_preparer().prepare(workspace, "missing-mixed-inputs", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_reusable_printed_recipe_does_not_rewrite_fixed_vendor_code(printed_configuration):
    from workspace_service.workflow_run_paths import VERSION

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["run_path_template"] = VERSION
    with pytest.raises(ValueError, match="fixed recipes are not rewritten"):
        module.prepare(workspace, "fixed-recipe", tools, bindings)
    assert not (workspace / "process-proofs").exists()


def test_published_printed_bindings_select_supported_run_paths():
    from workspace_service.workflow_run_paths import VERSION

    bindings = json.loads((REPO / "examples/process-interfaces/printed-replacement-part/bindings.example.json").read_bytes())
    assert bindings["run_path_template"] == VERSION


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


@pytest.mark.parametrize("mode", ["ai_task", "configured_tool"])
def test_retained_consumer_uses_exact_repair_and_original_full_gate(
    printed_configuration, mode,
):
    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    bindings["geometry_operation_mode"] = mode
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

@pytest.fixture
def handle_configuration(printed_configuration):
    from workspace_service.workflow_run_paths import VERSION

    workspace, bindings, tools = printed_configuration
    module = printed_preparer()
    profile = json.loads(
        (
            REPO
            / "packages/workspace_service/src/workspace_service/process_validation/profiles/printed-replacement-part-02.json"
        ).read_bytes()
    )
    bindings.update(
        scenario_id="printed-replacement-part-02",
        orientation_comparison=True,
        run_path_template=VERSION,
        inspection_workspace="/mounted-workspace",
    )
    for role, ref in bindings["profiles"].items():
        raw = json.dumps(
            {
                check["selector"].removeprefix("/"): check["constraint"]["expected"]
                for check in profile["checks"]
                if check["subject_role"] == role + "_profile"
            }
        ).encode()
        Path(ref["path"]).write_bytes(raw)
        ref["sha256"] = module.definition.sha(raw)
    return workspace, bindings, tools


def handle_basis_input_references(plan):
    review = next(step for step in plan.steps if step.id.startswith("review_basis"))
    references = {}
    for alias, address in review.references:
        fields = plan.inputs.get(address.split(".")[0])
        if fields:
            references[Path(fields["settings"]["workspace_file"]).name] = (alias, fields)
    for filename, role, kind in (
        ("concept.png", "original_concept_png", "reference_images"),
        ("concept.svg", "original_concept_svg", "engineering_document"),
        ("context.md", "original_context_md", "engineering_document"),
        ("prompt.txt", "original_prompt_txt", "engineering_document"),
        ("scenario.json", "original_scenario_json", "engineering_document"),
        ("user-profile.md", "original_user_profile_md", "engineering_document"),
        ("requirements.md", "original_requirements", "engineering_document"),
    ):
        alias, fields = references[filename]
        assert alias.replace(" ", "_") == review.id + "_" + role
        assert fields["outputs"][0]["kind"] == kind
    return review, references


def test_handle_uses_frozen_assignment_exact_full_profile_and_preslice_review(
    handle_configuration,
):
    from workspace_service.workflow_run_paths import bind_run_paths

    workspace, bindings, tools = handle_configuration
    module = printed_preparer()
    result = module.prepare(workspace, "handle-source", tools, bindings)
    source = (workspace / result["source_path"]).read_text()
    plan = compile_prompt_workflow(source)
    full_stage = next(s for s in plan.steps if s.id.startswith("validate_outputs"))
    profile = ValidatorConfiguration.model_validate(full_stage.validation).load(
        str(workspace)
    )
    assert profile.id == "printed-replacement-part-02-full"
    assert len(profile.checks) == 18
    assert len(profile.baseline.requirements) == 10
    assert {r.id for r in profile.baseline.requirements} == {
        "PRINT02-" + suffix
        for suffix in (
            "MOUNTING",
            "LABEL-KEEPOUT",
            "ENVELOPE",
            "FINGER-CLEARANCE",
            "GRIP",
            "MESH-LINEAGE",
            "SLICE",
            "ORIENTATION",
            "DELIVERABLES",
            "ACTION-SCOPE",
        )
    }
    for item in result["input_files"]:
        assert (
            module.definition.sha((workspace / item["path"]).read_bytes())
            == item["sha256"]
        )
        if "02-repair-cart-bow-handle" in (item["original"] or ""):
            assert (workspace / item["path"]).read_bytes() == (
                REPO / item["original"]
            ).read_bytes()
    assert source.count('"action_kind":"local_review"') == 3
    assert '"reference_dimension_mm":96.0' in source
    assert "focus wheel" not in source and "socket interpretation" not in source
    assert not (workspace / result["accepted_source_path"]).exists()
    assert (
        result["physical_dispatch"] is False
        and result["engineering_acceptance"] is False
    )
    assert not list((workspace / result["output_root"]).iterdir())
    _, review_inputs = handle_basis_input_references(plan)
    assert "configured-geometry-basis.json" not in review_inputs
    for filename in (
        "concept.png", "concept.svg", "context.md", "prompt.txt",
        "scenario.json", "user-profile.md",
    ):
        fields = review_inputs[filename][1]
        original = (
            REPO
            / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle"
            / filename
        ).read_bytes()
        assert (workspace / fields["settings"]["workspace_file"]).read_bytes() == original
        if filename == "prompt.txt":
            assert b"\r\n" in original
    requirement_bytes = "\n".join(
        requirement.id + ": " + requirement.text
        for requirement in profile.baseline.requirements
    ).encode()
    assert (
        workspace / review_inputs["requirements.md"][1]["settings"]["workspace_file"]
    ).read_bytes() == requirement_bytes
    for run_id in ("first-handle", "second-handle"):
        steps = bind_run_paths(plan, run_id).steps
        review = next(
            s for s in steps if s.id.startswith("review_geometry_before_slice")
        )
        repair = next(s for s in steps if s.id.startswith("repair_measure_orient"))
        orient = next(s for s in steps if s.id.startswith("orient_geometry"))
        comparison = next(s for s in steps if s.id.startswith("compare_orientations"))
        final = next(s for s in steps if s.id.startswith("review_preparation"))
        slicers = [s for s in steps if s.tool_name.endswith("__slice_model_file")]
        assert len(slicers) == 3
        assert (
            steps.index(repair) < steps.index(review) < min(map(steps.index, slicers))
        )
        assert steps.index(comparison) < steps.index(final)
        root = result["output_root"] + "/" + run_id + "/"
        assert root + "repaired_mesh.stl" in orient.file_dependencies.values()
        assert root + "source_mesh.stl" not in orient.file_dependencies.values()
        for name in ("pads_down", "side"):
            slicer = next(s for s in slicers if s.id.startswith("slice_" + name))
            assert (
                root + "orientation/" + name + "/oriented.stl"
                in slicer.file_dependencies.values()
            )
        args = (
            workspace
            / "process-proofs/printed-replacement-part/handle-source/inputs/orientation/orient_geometry-arguments.json"
        )
        assert "/mounted-workspace/" in json.loads(args.read_bytes())["input_content"]
    staged = workspace / "process-proofs/printed-replacement-part/handle-source/inputs"
    binding = json.loads((staged / "scenario-binding.json").read_bytes())
    assert binding["starter_id"] == "replacement-drawer-handle"
    operation = (staged / "orientation/orientation-study.py").read_text()
    assert (
        "socket" not in operation and "CANDIDATES = ('pads_down', 'side')" in operation
    )
    assert (staged / "scenario-instructions.json").read_bytes() == (
        REPO
        / "examples/process-interfaces/printed-replacement-part/scenarios/printed-replacement-part-02.instructions.json"
    ).read_bytes()
    disclosure = json.loads((staged / "run-disclosure.json").read_bytes())
    rows = {row["step_id"]: row for row in disclosure["stages"]}
    review_basis = next(s for s in plan.steps if s.id.startswith("review_basis"))
    addresses = [
        source.split(".")[0]
        for _, source in review_basis.references
        if source.split(".")[0] in plan.inputs
    ]
    assert any(
        plan.inputs[address]["settings"]["workspace_file"].endswith(
            "/run-disclosure.md"
        )
        for address in addresses
    )
    assert any(
        plan.inputs[address]["settings"]["workspace_file"].endswith(
            "/run-disclosure.json"
        )
        for address in addresses
    )
    for step in plan.steps:
        row = rows[step.id]
        if row["kind"] in ("mcp-task", "mcp-tool"):
            assert row["timeout_seconds"] == step.timeout_seconds
            if row["kind"] == "mcp-task":
                assert row["timeout_scope"] == "agent_loop"
                assert row["max_tool_calls"] == step.max_tool_calls
        else:
            assert "timeout_seconds" not in row and "max_tool_calls" not in row
    for name in ("pads_down", "side"):
        candidate_profile = json.loads(
            (staged / f"orientation/validate_{name}-profile.json").read_bytes()
        )
        assert [c["id"] for c in candidate_profile["checks"]] == [
            "repaired-mesh-integrity"
        ]


@pytest.mark.parametrize(
    "fault",
    [
        "unknown",
        "no_comparison",
        "no_run_paths",
        "wheel_native",
        "wheel_retained",
        "wheel_profiles",
    ],
)
def test_handle_incompatible_binding_fails_before_staging(handle_configuration, fault):
    workspace, bindings, tools = handle_configuration
    if fault == "unknown":
        bindings["scenario_id"] = "printed-replacement-part-03"
    elif fault == "no_comparison":
        bindings["orientation_comparison"] = False
    elif fault == "no_run_paths":
        bindings.pop("run_path_template")
    elif fault == "wheel_native":
        bindings["native_inspection_operation"] = {}
    elif fault == "wheel_retained":
        bindings["retained_geometry_source"] = {}
    else:
        path = Path(bindings["profiles"]["process"]["path"])
        data = json.loads(path.read_bytes())
        data.update(wall_loops="4", sparse_infill_density="35%")
        path.write_text(json.dumps(data))
        bindings["profiles"]["process"]["sha256"] = printed_preparer().definition.sha(
            path.read_bytes()
        )
    with pytest.raises(ValueError):
        printed_preparer().prepare(workspace, "invalid-handle", tools, bindings)
    assert not (workspace / "process-proofs").exists()


@pytest.mark.parametrize(
    "scenario,resource",
    [
        ("printed-replacement-part-02", "printed-replacement-part-01"),
        ("printed-replacement-part-01", "printed-replacement-part-02"),
        ("heat-spreader-sizing-01", "printed-replacement-part-01"),
    ],
)
def test_validator_cannot_bind_another_scenario_profile(
    printed_configuration, scenario, resource
):
    workspace, _, tools = printed_configuration
    flow = printed_preparer().definition.Definition(
        "printed-replacement-part", workspace, "mismatch", tools
    )
    with pytest.raises(ValueError, match="scenario"):
        flow.validator(resource, {}, scenario_id=scenario)


@pytest.mark.parametrize("matching_scenario", [True, False])
def test_configured_handle_basis_identity_is_explicit(
    handle_configuration, matching_scenario
):
    from workspace_service.workflow_run_paths import (
        TOKEN,
        bind_run_paths,
        bind_run_input_values,
    )
    from workspace_service.workflow_references import WorkflowReference

    workspace, bindings, tools = handle_configuration
    module = printed_preparer()
    configured_geometry(bindings, workspace, module)
    basis_ref = bindings["geometry_operation_files"]["basis"]
    path = Path(basis_ref["path"])
    basis = json.loads(path.read_bytes())
    basis["scenario_id"] = (
        "printed-replacement-part-02"
        if matching_scenario
        else "printed-replacement-part-01"
    )
    basis["proposed_geometry"] = {
        "bolt_centers_xy_mm": [[0, 0], [96, 0]],
        "pad_dimensions_mm": [18, 24, 5],
        "minimum_finger_clearance_mm": 25,
    }
    path.write_text(json.dumps(basis))
    basis_ref["sha256"] = module.definition.sha(path.read_bytes())
    for role in ("construction", "repair"):
        ref = bindings["geometry_operation_files"][role]
        path = Path(ref["path"])
        path.write_text(
            json.dumps({"code": f"print('fixture-only outputs/{TOKEN}/{role}.stl')"})
        )
        ref["sha256"] = module.definition.sha(path.read_bytes())
    bindings["geometry_operation_mode"] = "configured_tool"
    if not matching_scenario:
        with pytest.raises(ValueError, match="basis does not match"):
            module.prepare(workspace, "handle-configured", tools, bindings)
        assert not (workspace / "process-proofs").exists()
        return
    result = module.prepare(workspace, "handle-configured", tools, bindings)
    source = (workspace / result["source_path"]).read_text()
    plan = compile_prompt_workflow(source)
    review, review_inputs = handle_basis_input_references(plan)
    alias, fields = review_inputs["configured-geometry-basis.json"]
    assert alias.replace(" ", "_") == review.id + "_configured_geometry_basis"
    configured_bytes = (workspace / fields["settings"]["workspace_file"]).read_bytes()
    assert configured_bytes == Path(basis_ref["path"]).read_bytes()
    assert json.loads(configured_bytes)["proposed_geometry"] == basis["proposed_geometry"]
    assert json.loads(configured_bytes)["engineering_acceptance"] is False
    original_prompt = (
        REPO
        / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/prompt.txt"
    ).read_bytes()
    assert b"\r\n" in original_prompt
    for prefix, role in (
        ("create_mesh", "construction"),
        ("repair_measure_orient", "repair"),
    ):
        step = next(s for s in plan.steps if s.id.startswith(prefix))
        assert step.tool_name.endswith("__execute_blender_code") and step.prompt == ""
        input_id = step.arguments_from.split(".")[0]
        settings = plan.inputs[input_id]["settings"]
        call_path = workspace / settings["workspace_file"]
        assert call_path.name == role + "-blender-call.json"
        submitted = json.loads(call_path.read_bytes())
        pinned = Path(bindings["geometry_operation_files"][role]["path"]).read_bytes()
        assert submitted["code"] == json.loads(pinned)["code"]
        assert submitted["user_prompt"].encode("utf-8") == original_prompt
        assert (
            call_path.parent / (role + "-provider-arguments.json")
        ).read_bytes() == pinned
        assert (
            call_path.parent / (role + "-operation-review.json")
        ).read_bytes() == pinned
        values = bind_run_input_values(
            bind_run_paths(plan, "real-run"),
            {
                input_id: WorkflowReference.from_bytes(
                    settings["workspace_file"], call_path.read_bytes(), image=False
                )
            },
        )
        resolved = json.loads(values[input_id].text)
        assert "real-run" in resolved["code"] and TOKEN not in resolved["code"]
        assert resolved["user_prompt"].encode("utf-8") == original_prompt
    assert "socket interpretation" not in source
    assert "printed-replacement-part-02-full" in source


@pytest.fixture
def orca_configuration(handle_configuration):
    workspace, bindings, tools = handle_configuration
    module = printed_preparer()
    path = Path(bindings["profiles"]["process"]["path"])
    original = {
        **json.loads(path.read_bytes()),
        "tree_support_wall_count": "-1",
        "enable_support": "1",
        "support_type": "tree(auto)",
    }
    original_path = workspace / "original-process.json"
    original_path.write_text(json.dumps(original))
    path.write_text(json.dumps({**original, "tree_support_wall_count": "0"}))
    bindings["profiles"]["process"]["sha256"] = module.definition.sha(path.read_bytes())
    bindings["workflow_id"] = "replacement_handle_existing_starter"
    bindings.pop("slice_success_contract")
    bindings["slice_binding"] = dict(
        kind="orca-shell-3mf-v1",
        engine_version="2.4.2",
        executable="/opt/orca/AppRun",
        workspace_mount="/mounted-workspace",
        selected_orientation="pads_down",
        original_process_profile=dict(
            path=str(original_path),
            sha256=module.definition.sha(original_path.read_bytes()),
        ),
    )
    tools.append(
        dict(
            server_id=bindings["slicer_server"],
            tool_name="shell_execute",
            name=bindings["slicer_server"] + "__shell_execute",
            schema_digest="c" * 64,
        )
    )
    return workspace, bindings, tools


@pytest.mark.parametrize("orientation", ["pads_down", "side"])
def test_explicit_orca_binding_keeps_original_requirements_and_two_exact_candidates(
    orca_configuration, orientation
):
    from workspace_service.workflow_run_paths import bind_run_paths

    workspace, bindings, tools = orca_configuration
    bindings["slice_binding"]["selected_orientation"] = orientation
    module = printed_preparer()
    result = module.prepare(
        workspace, "orca-" + orientation.replace("_", "-"), tools, bindings
    )
    source = (workspace / result["source_path"]).read_text()
    assert source.startswith("workflow replacement_handle_existing_starter\n")
    plan = compile_prompt_workflow(source)
    assert len(plan.steps) == 16
    handle_basis_input_references(plan)
    assert not any(step.tool_name.endswith("__slice_model_file") for step in plan.steps)
    slicers = [
        step for step in plan.steps if step.tool_name.endswith("__shell_execute")
    ]
    assert len(slicers) == 2 and all(step.timeout_seconds == 60 for step in slicers)
    final = next(step for step in plan.steps if step.id.startswith("validate_outputs"))
    profile = ValidatorConfiguration.model_validate(final.validation).load(
        str(workspace)
    )
    original = json.loads(
        (
            REPO
            / "packages/workspace_service/src/workspace_service/process_validation/profiles/printed-replacement-part-02.json"
        ).read_bytes()
    )
    assert profile.baseline.model_dump(mode="json") == original["baseline"]
    assert len(profile.checks) == 43
    actual = {check.id: check.model_dump(mode="json") for check in profile.checks}
    for check in original["checks"]:
        if check["id"] != "slice-lineage":
            assert actual[check["id"]] == check
    assert (
        actual["slice-lineage"]["parameters"]["expected_operation"]
        == "actual_local_orca_slice"
    )
    assert (
        actual["prepared-geometry-lineage"]["parameters"]["rotation"]
        == module.orca_binding.ROTATIONS[orientation]
    )
    assert (
        actual["comparison-prepared-geometry-lineage"]["parameters"]["prepared_role"]
        == "comparison_prepared_3mf"
    )
    for run_id in ("run-one", "run-two"):
        resolved = bind_run_paths(plan, run_id).steps
        review = next(
            s for s in resolved if s.id.startswith("review_geometry_before_slice")
        )
        prepare = [s for s in resolved if s.id.startswith("prepare_build_instance")]
        native = [s for s in resolved if s.tool_name.endswith("__shell_execute")]
        assert len(prepare) == len(native) == 2
        assert resolved.index(review) < min(resolved.index(s) for s in prepare + native)
        root = result["output_root"] + "/" + run_id + "/"
        for step in prepare + native:
            assert root + "repaired_mesh.stl" in step.file_dependencies.values()
        final_subject = next(s for s in resolved if s.id.startswith("validate_outputs"))
        assert "comparison_prepared_3mf" in final_subject.validation["subjects"]
    staged = workspace / Path(result["source_path"]).parent / "inputs"
    for path in (
        staged / "orca-slice-call.json",
        staged / "comparison/orca-slice-call.json",
    ):
        arguments = json.loads(path.read_bytes())
        assert arguments["command"].count("--load-settings") == 2
        assert not any(arg.startswith("--rotate") for arg in arguments["command"])
        assert arguments["command"][-1].endswith("/prepared-model.3mf")
        assert arguments["timeout"] == 60
    binding = json.loads((staged / "orca-binding.json").read_bytes())
    assert (
        binding["original_validation_profile"]["id"]
        == "printed-replacement-part-02-full"
    )
    assert binding["derived_validation_profile"]["id"] == profile.id
    assert binding["mapped_process_sha256"] == bindings["profiles"]["process"]["sha256"]
    assert binding["selected_orientation"] == orientation
    mapping = json.loads((staged / "source-transformation.json").read_bytes())
    assert mapping["workflow_id"] == bindings["workflow_id"]
    assert mapping["starter_id"] == "replacement-drawer-handle"
    assert mapping["execution_authority"] is False
    assert mapping["additional_task_ids"]["supports_and_slice"] == slicers[0].id
    assert not list((workspace / result["output_root"]).iterdir())
    assert "actual_local_bambu_slice" not in source
    assert not any(step.id.startswith("retain_slice_response") for step in plan.steps)
    assert not any(
        step.tool_name.endswith(("__write_text_document", "__inspect_file"))
        or "inspect_file" in step.task_tool_allowlist
        for step in plan.steps
    )
    for step in slicers:
        assert step.file_policy == "publish_overwrite"
        assert step.saved_response_file_port.endswith("provider_response")
        assert step.output_path.endswith("/slice-provider-response.json")
        assert step.output_path not in step.expected_files
        inspector = next(
            candidate
            for candidate in plan.steps
            if candidate.file_dependencies.get(
                step.id + "." + step.saved_response_file_port
            )
            == step.output_path
        )
        assert inspector.id.startswith("inspect_slice_handoff")
    report = next(
        step for step in plan.steps if step.id.startswith("summarize_preparation")
    )
    assert not report.agent_task and not report.server_id
    assert report.reference_inline_max_bytes == 32768
    assert "engineering_acceptance=false" in report.prompt
    assert "inspect_file" not in report.prompt
    instructions = json.loads((staged / "scenario-instructions.json").read_bytes())
    assert instructions["version"] == "2"
    assert report.prompt == instructions["report"]
    assert {ref.split(".")[-1] for _, ref in report.references} >= {
        "slice_evidence",
        "toolpath_summary",
        "orientation_comparison",
    }


def test_orca_digital_preparation_does_not_require_private_file_tools(
    orca_configuration,
):
    workspace, bindings, tools = orca_configuration
    bindings.pop("files_server")
    tools = [
        tool
        for tool in tools
        if tool["tool_name"] not in {"write_text_document", "inspect_file"}
    ]
    result = printed_preparer().prepare(
        workspace, "ordinary-tool-readiness", tools, bindings
    )
    plan = compile_prompt_workflow((workspace / result["source_path"]).read_text())
    assert all(step.server_id != "wright-workspace-files" for step in plan.steps)
    assert not any(step.task_tool_allowlist == ("inspect_file",) for step in plan.steps)


def test_existing_thermal_basis_publishes_an_exact_plain_ai_reference(configuration):
    """Controlled transport proof using the existing thermal case, not a solver run."""
    import asyncio
    import hashlib
    from workspace_service.workflow_references import WorkflowReference
    from workspace_service.workflow_source_execution import (
        _parse,
        execute_prompt_workflow,
    )
    from packages.workspace_service.tests.test_workflow_source_execution import task
    from packages.workspace_service.tests.test_workflow_mcp_execution import edge
    from packages.workspace_service.tests.test_workflow_external_action_execution import (
        service,
    )

    workspace, _, bindings, tools = configuration
    result = heat_preparer().prepare(workspace, "plain-response-proof", tools, bindings)
    sections = _parse((workspace / result["source_path"]).read_text())
    basis = next(
        s for s in sections if s["id"] == "define_thermal_case_plain_response_proof"
    )
    basis["fields"]["outputs"].append(
        {"key": "basis_file", "kind": "workspace_file", "name": "Exact thermal basis"}
    )
    basis["fields"]["settings"].update(
        saved_response_file_port="basis_file", file_policy="publish_indexed"
    )
    incoming = [
        s
        for s in sections
        if s["kind"] == "connection"
        and str(s["fields"].get("to", "")).startswith(basis["id"] + ".")
    ]
    input_ids = {s["fields"]["from"].split(".")[0] for s in incoming}
    selected = (
        [s for s in sections if s["kind"] == "workflow" or s["id"] in input_ids]
        + [basis]
        + incoming
    )
    text = "\n".join(
        s["kind"]
        + " "
        + s["id"]
        + "\n"
        + "\n".join(
            "  " + key + ": " + json.dumps(value) for key, value in s["fields"].items()
        )
        + "\nend"
        for s in selected
    )
    text += "\n" + task(
        "read_basis",
        fmt="text",
        prompt="Read the exact thermal basis, retaining unresolved numerical verification.",
    ).replace('"kind":"engineering_document"', '"kind":"workspace_file"', 1)
    text += edge(basis["id"] + ".basis_file", "read_basis.read_basis_prompt")
    plan = compile_prompt_workflow(text)
    inputs = {}
    for key, fields in plan.inputs.items():
        path = fields["settings"]["workspace_file"]
        inputs[key] = WorkflowReference.from_bytes(
            path,
            (workspace / path).read_bytes(),
            image=fields["outputs"][0]["kind"] == "reference_images",
        )
    calls = []
    controlled = "# Controlled thermal basis response\n100 mm; 40/60 mm; 2 mm; 4 W. Numerical verification pending."

    async def generate(prompt, fmt, **kwargs):
        calls.append(prompt)
        return (
            controlled
            if len(calls) == 1
            else "Controlled downstream receipt observed; no solver or engineering acceptance."
        )

    final = asyncio.run(
        execute_prompt_workflow(
            service=service(workspace),
            workspace_dir=str(workspace),
            plan=plan,
            input_values=inputs,
            response_generator=generate,
        )
    )
    assert len(calls) == 2 and "k=200 W/(m K)" in calls[0]
    assert controlled in calls[1]
    receipt = next(o for o in final["outputs"] if o.get("output_port") == "basis_file")
    assert (workspace / receipt["output_path"]).read_text() == controlled
    assert receipt["sha256"] == hashlib.sha256(controlled.encode()).hexdigest()
    assert receipt["task_id"] == basis["id"]


@pytest.mark.parametrize(
    "fault",
    [
        "kind",
        "version",
        "executable",
        "orientation",
        "mount",
        "original_hash",
        "mapping",
        "extra",
        "workflow_id",
    ],
)
def test_orca_optin_mismatch_blocks_before_staging(orca_configuration, fault):
    workspace, bindings, tools = orca_configuration
    selected = bindings["slice_binding"]
    if fault in ("kind", "version", "executable", "orientation", "mount"):
        key = {
            "version": "engine_version",
            "orientation": "selected_orientation",
            "mount": "workspace_mount",
        }.get(fault, fault)
        selected[key] = "unsupported"
    elif fault == "original_hash":
        selected["original_process_profile"]["sha256"] = "0" * 64
    elif fault == "extra":
        selected["automatic_approval"] = True
    elif fault == "workflow_id":
        bindings["workflow_id"] = "invalid source id"
    else:
        path = Path(bindings["profiles"]["process"]["path"])
        value = json.loads(path.read_bytes())
        value["unapproved_setting"] = "changed"
        path.write_text(json.dumps(value))
        bindings["profiles"]["process"]["sha256"] = printed_preparer().definition.sha(
            path.read_bytes()
        )
    with pytest.raises(ValueError):
        printed_preparer().prepare(workspace, "invalid-orca", tools, bindings)
    assert not (workspace / "process-proofs").exists()
