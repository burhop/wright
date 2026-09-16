import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import compile_prompt_workflow
from workspace_service.workflow_source_execution import _parse
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("ordinal", [1, 2, 3])
@pytest.mark.parametrize(
    "script,template,observation,originals",
    [
        (
            "heat",
            "heat-spreader-sizing",
            "inspect_plate_exports",
            ("define_thermal_case", "create_plate_geometry", "solve_and_verify"),
        ),
        (
            "bracket",
            "lightweight-equipment-bracket",
            "inspect_bracket_exports",
            ("define_load_case", "create_bracket", "solve_and_compare"),
        ),
        (
            "drill-jig",
            "parametric-drill-jig",
            "inspect_jig_exports",
            ("validate_inputs", "generate_jig", "check_alignment"),
        ),
    ],
)
def test_canonical_preparers_preserve_stages_and_bind_actual_observations(
    tmp_path, ordinal, script, template, observation, originals
):
    spec = importlib.util.spec_from_file_location(
        "prepare_" + script, ROOT / f"scripts/prepare-{script}-dataset-campaign.py"
    )
    preparer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparer)
    names = {
        "agentcad": ["context", "docs", "run", "measure", "inspect", "export"],
        "wright-workspace-files": ["write_text_document", "inspect_file"],
        "oasis": ["run_simulation"],
        "solver": [
            "calculix_mesh_preflight",
            "calculix_solve_static_recorded",
            "calculix_run_get",
        ],
        "fields": ["export_recorded_fields_and_reactions"],
    }
    tools = [
        {
            "server_id": server,
            "tool_name": name,
            "name": server + "__" + name,
            "schema_digest": "a" * 64,
        }
        for server, tools in names.items()
        for name in tools
    ]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"),
        attempt="unit-read",
        instance_source=None,
        initialize_agentcad=False,
        container_workspace="/workspace",
        oasis_server_id="oasis",
        solver_server_id="solver",
        field_server_id="fields",
    )
    directory = next(
        path
        for path in (
            ROOT / "tests/datasets/engineering-workflows/scenarios" / template
        ).iterdir()
        if path.name.startswith(f"{ordinal:02d}")
    )
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    inspection = next(
        step for step in plan.steps if step.id.startswith(observation + "_")
    )
    assert inspection.agent_task and inspection.server_id == "wright-workspace-files"
    assert (
        "inspect_file" in inspection.prompt and "nextOffsetBytes" in inspection.prompt
    )
    assert not inspection.expected_files
    for prefix in originals:
        assert (
            len([step for step in plan.steps if step.id.startswith(prefix + "_")]) == 1
        )
    cad_index = next(
        i for i, step in enumerate(plan.steps) if step.id.startswith(originals[1] + "_")
    )
    assert plan.steps.index(inspection) > cad_index
    manifest = json.loads(
        Path(result["draft"])
        .with_name("staging-manifest.json")
        .read_text(encoding="utf-8")
    )
    assert any(
        tool["tool_name"] == "inspect_file" for tool in manifest["tool_allowlist"]
    )
    assert not (Path(args.workspace_root) / manifest["output_root"]).exists()
    assert any(
        path.endswith(".step") for path in manifest["expected_tool_created_files"]
    )
    from scripts.agentcad_source_contract import GUIDANCE

    source_authors = [
        step
        for step in plan.steps
        if step.expected_files
        and any(path.endswith(".py") for path in step.expected_files)
    ]
    assert source_authors and all(GUIDANCE in step.prompt for step in source_authors)
    if script == "bracket":
        basis = next(
            step for step in plan.steps if step.id.startswith("define_load_case_")
        )
        review = next(
            step for step in plan.steps if step.id.startswith("review_bracket_basis_")
        )
        preflight = next(
            step
            for step in plan.steps
            if step.id.startswith("preflight_bracket_project_")
        )
        author = next(
            step for step in plan.steps if step.id.startswith("author_bracket_source_")
        )
        cad = next(step for step in plan.steps if step.id.startswith("create_bracket_"))
        sections = _parse(source)
        # The same staged, scenario-specific authority is an actual connected
        # input to both basis and author; it is not only stray prompt prose.
        contract_input = next(
            section
            for section in sections
            if section["kind"] == "input"
            and section["fields"]
            .get("settings", {})
            .get("workspace_file", "")
            .endswith("/selected-solver-contract.json")
        )
        contract_refs = [
            reference
            for _, reference in basis.references
            if reference.split(".")[0] == contract_input["id"]
        ]
        assert (
            len(contract_refs) == 1
            and contract_refs[0] in dict(author.references).values()
        )
        contract_path = (
            Path(args.workspace_root)
            / contract_input["fields"]["settings"]["workspace_file"]
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        authority = contract["provisional_geometry_authority"]
        identity = json.loads(
            (directory / "scenario.json").read_text(encoding="utf-8")
        )["scenario_id"]
        original_contract = json.loads(preparer.BINDING.read_text(encoding="utf-8"))
        assert contract["selected_scenario"] == original_contract["scenarios"][identity]
        assert all(contract[key] == value for key, value in original_contract.items())
        assert (
            authority["scenario_id"] == identity
            and authority["release_authorized"] is False
        )
        assert (
            authority["status"]
            == "authored_provisional_engineering_design_not_customer_or_supplier_evidence"
        )
        assert authority["scope"] == preparer.PROVISIONAL_REVISION_SCOPES[identity]
        assert (
            authority["selection_and_disclosure"]
            == preparer.PROVISIONAL_REVISION_GUIDANCE
        )
        assert authority["selection_and_disclosure"] in basis.prompt
        assert "numbered Boolean-operation/parameter table" in basis.prompt
        assert "original target as an unproven acceptance criterion" in basis.prompt
        assert "genuine conflict among mandatory constraints" in basis.prompt
        assert (
            "Do not substitute a new unreviewed pocket design after the gate"
            in author.prompt
        )
        assert "model-measurements.json" in author.prompt
        # Compile and inspect the actual execution graph, keeping the unchanged
        # local review action before authoring and any native generation.
        assert review.external_action["action"]["kind"] == "local_review"
        assert review.external_action["action"]["mode"] == "review_only"
        assert (
            plan.steps.index(basis)
            < plan.steps.index(review)
            < plan.steps.index(author)
            < plan.steps.index(cad)
        )
        order_edges = {
            (section["fields"]["from"], section["fields"]["to"])
            for section in sections
            if section["kind"] == "connection" and section["fields"]["type"] == "order"
        }
        assert {
            (basis.id, review.id),
            (review.id, preflight.id),
            (preflight.id, author.id),
            (author.id, cad.id),
        } <= order_edges
        # Original uploads are byte-preserved; new design authority never
        # rewrites customer geometry, manufacturing constraints or targets.
        for item in manifest["input_manifest"]:
            name = item["path"].rsplit("/", 1)[-1]
            if item.get("role") == "original_customer_input":
                assert (Path(args.workspace_root) / item["path"]).read_bytes() == (
                    directory / name
                ).read_bytes()
        assert len(plan.steps) == 12 and len(manifest["tool_allowlist"]) == 11
    if script == "drill-jig":
        author = next(
            step for step in plan.steps if step.id.startswith("author_jig_source_")
        )
        checker = next(
            step for step in plan.steps if step.id.startswith("author_jig_inspection_")
        )
        for step in (author, checker):
            assert preparer.CIRCLE_CENTER_GUIDANCE in step.prompt
            assert "edge.geom_type == GeomType.CIRCLE" in step.prompt
            assert "edge.arc_center (a property)" in step.prompt
            assert "must not be used as the hole/axis center" in step.prompt
            assert "loosen extraction/alignment tolerances" in step.prompt
        assert (
            "must reopen actual" in checker.prompt
            and "Do not modify or regenerate jig.step" in checker.prompt
        )
        assert "boolean intersection volumes" in checker.prompt
        assert any(
            path.endswith("/hole-layout.dxf")
            for path in manifest["expected_tool_created_files"]
        )
        assert any(
            path.endswith("/dimension-report.json")
            for path in manifest["expected_tool_created_files"]
        )
    if script == "heat":
        execution = next(
            step
            for step in plan.steps
            if step.id.startswith("execute_recorded_fe_call_")
        )
        verification = next(
            step for step in plan.steps if step.id.startswith("solve_and_verify_")
        )
        assert (
            execution.tool_name == "oasis__run_simulation"
            and execution.schema_digest == "a" * 64
        )
        assert (
            not execution.agent_task
            and execution.arguments_from
            and not execution.arguments
        )
        candidate_count = (
            len(
                (directory / "alternatives.csv")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            - 1
        )
        assert (
            len(execution.expected_files) == candidate_count * 4 + 3
            and not verification.expected_files
        )
        assert (
            verification.agent_task
            and verification.server_id == "wright-workspace-files"
        )
        assert plan.steps.index(execution) < plan.steps.index(verification)
        assert (
            "critic_approved=false" in verification.prompt
            and "unverified pending an independent critic" in verification.prompt
        )
        assert (
            "two-percent" in verification.prompt
            and "one-percent" in verification.prompt
        )
        assert "Do not dispatch a solver again" in verification.prompt
        sections = _parse(source)
        input_id = execution.arguments_from.split(".")[0]
        uploaded = next(section for section in sections if section["id"] == input_id)
        arguments_path = (
            Path(args.workspace_root) / uploaded["fields"]["settings"]["workspace_file"]
        )
        exact = arguments_path.read_text(encoding="utf-8")
        from jsonschema import Draft202012Validator

        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["solver", "input_content", "job_name", "critic_approved"],
            "properties": {
                "solver": {"const": "skfem"},
                "input_content": {"type": "string"},
                "job_name": {"type": "string"},
                "critic_approved": {"const": False},
            },
        }
        runtime = SimpleNamespace(
            resolve=lambda step: SimpleNamespace(input_schema=schema),
            validate=lambda step, value, schema: Draft202012Validator(schema).validate(
                value
            ),
        )
        arguments = WorkflowMcpRuntime.arguments(
            runtime, execution, {execution.arguments_from: exact}
        )
        assert arguments == json.loads(exact) and arguments["critic_approved"] is False
        assert "heat_conduction_skfem.py" in arguments["input_content"]
        assert (
            'measurements_document.get("cases", measurements_document)'
            in arguments["input_content"]
        )
        original_edges = [
            section
            for section in _parse(
                preparer.TEMPLATE.read_text().replace(
                    "__instance__",
                    template.replace("-", "_") + f"_{ordinal:02d}_unit_read",
                )
            )
            if section["kind"] == "connection"
        ]
        assert len(original_edges) == 2
        for original in original_edges:
            assert original in sections
