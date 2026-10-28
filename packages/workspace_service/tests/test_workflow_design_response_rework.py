"""Synthetic exact-design fields exercise the real validator and correction runner."""

import asyncio
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import pytest

from core.process_validation import (
    Baseline,
    CheckDefinition,
    Constraint,
    Requirement,
    SourceReference,
    ValidationProfile,
)
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.workflow_run_paths import bind_run_paths
from workspace_service.workflow_design_check import validate_rework
from .test_workflow_file_revision_paths import file_rework_source
from .test_workflow_process_validation import runtime_service


def design_plan(tmp_path):
    original = compile_prompt_workflow(file_rework_source())
    template, check = original.steps[:2]

    def producer(identity, port, extension, dependencies=()):
        path = f"outputs/{{{{wright.run_id}}}}/{identity}/{{{{wright.producer_attempt}}}}/output.{extension}"
        return replace(
            template,
            id=identity,
            title=identity,
            save=False,
            output_path="",
            output_ports=((port, "workspace_file"),),
            expected_files=(path,),
            expected_file_ports={port: path},
            references=tuple((key, key) for key in dependencies),
            file_dependencies={
                key: {"source": "connected_output"} for key in dependencies
            },
        )

    basis = producer("basis", "basis", "json")
    cad = producer("cad", "geometry", "step", ("basis.basis",))
    analysis = producer("analysis", "field", "csv", ("cad.geometry", "basis.basis"))
    profile = ValidationProfile(
        id="synthetic-design-strength",
        version="1",
        baseline=Baseline(
            id="synthetic-strength-basis",
            version="1",
            requirements=(
                Requirement(
                    id="stress",
                    text="Synthetic stress must be below 20 MPa; not a physical qualification",
                    scope="design",
                    sources=(
                        SourceReference(
                            artifact_ref="synthetic-requirement",
                            sha256="a" * 64,
                            locator="stress",
                        ),
                    ),
                ),
            ),
        ),
        checks=(
            CheckDefinition(
                id="stress",
                requirement_ids=("stress",),
                subject_role="design",
                reader="design-response",
                constraint=Constraint(operator="range", maximum=20),
                unit="MPa",
                evidence_method="independent_measurement",
                parameters={
                    "operation": "stress_maximum",
                    "field_role": "field",
                    "basis_roles": ["basis"],
                    "related_roles": ["field", "basis"],
                },
            ),
        ),
        limitations=("Synthetic fields; no CAD solver or physical safety evidence",),
    )
    (tmp_path / "strength-profile.json").write_text(profile.model_dump_json())
    config = {
        "profile": {
            "source": "workspace",
            "name": "strength-profile.json",
            "reference": profile.reference().model_dump(),
        },
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"design": "geometry", "field": "stress", "basis": "assumptions"},
        "rework_scope": "verified_segment",
        "repair_subjects": ["design"],
    }
    check = replace(
        check,
        validation=config,
        validation_sources=(
            ("design", "cad.geometry"),
            ("field", "analysis.field"),
            ("basis", "basis.basis"),
        ),
    )
    plan = replace(
        original, steps=(basis, cad, analysis, check), revisions={"inspect": "cad"}
    )
    validate_rework(plan.steps, plan.revisions)
    return bind_run_paths(plan, "design-response-run")


@pytest.mark.parametrize("tamper", [False, True])
def test_strength_failure_revises_actual_design_subject_and_repeats_analysis(
    tmp_path, tamper
):
    from .test_workflow_external_action_execution import (
        source as approval_source,
        service as approval_service,
    )
    from .test_workflow_execution_continuation import authorize

    plan = design_plan(tmp_path)
    approval = compile_prompt_workflow(approval_source()).steps[-1]
    plan = replace(plan, steps=(*plan.steps, approval), definition_digest="a" * 64)

    def fresh_service():
        app = runtime_service(tmp_path)
        owner = approval_service(tmp_path)
        app.files = owner.files
        app.workflow_external_actions = owner.workflow_external_actions
        return app

    calls, files, prompts, events = [], {}, [], []

    async def run_task(step, prompt, *args, **kwargs):
        calls.append(step.id)
        prompts.append(prompt)
        if step.id == "basis":
            data = b'{"fixture":"synthetic fixed analysis basis"}'
        elif step.id == "cad":
            data = f"synthetic STEP revision {calls.count('cad')}".encode()
        else:
            assert hashlib.sha256(files["cad"][-1][1]).hexdigest() in prompt
            assert hashlib.sha256(files["basis"][-1][1]).hexdigest() in prompt
            stress = 30 if calls.count("cad") == 1 else 10
            data = (
                "element_id,integration_point,sxx_mpa,syy_mpa,szz_mpa,sxy_mpa,sxz_mpa,syz_mpa\n"
                f"1,1,{stress},0,0,0,0,0\n"
            ).encode()
        path = tmp_path / step.expected_files[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files.setdefault(step.id, []).append((path, data))
        return "{}", []

    async def generate(*args):
        raise AssertionError("No independent model call expected")

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=fresh_service(),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            run_id="design-response-run",
            tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=generate,
            on_event=emit,
        )
    )
    assert calls == ["basis", "cad", "analysis", "cad", "analysis"]
    assert all(
        path.read_bytes() == data
        for attempts in files.values()
        for path, data in attempts
    )
    checks = [event["report"] for event in events if event["kind"] == "design_check"]
    assert [item["verdict"] for item in checks] == ["revise", "pass"]
    assert any(
        event["kind"] == "design_revision" and event["task_id"] == "cad"
        for event in events
    )
    assert '"target_step_id":"cad"' in prompts[3]
    assert len(result["steps"]) == 4
    assert len(result["revision_attempts"]) == 3

    # A synthetic decision only: no provider or physical action exists here.
    checkpoint = authorize(fresh_service(), result)
    retained_calls = list(calls)
    if tamper:
        files["cad"][0][0].write_bytes(b"tampered old attempt")
    resumption = execute_prompt_workflow(
        service=fresh_service(),
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values={},
        response_generator=generate,
        tool_runtime=SimpleNamespace(run_task=run_task),
        action_generator=generate,
        run_id=result["run_id"],
        continuation=json.loads(json.dumps(checkpoint["continuation"])),
        completed_checkpoint=checkpoint,
    )
    if tamper:
        from workspace_service.workflow_source_execution import (
            WorkflowSourceExecutionError,
        )

        with pytest.raises(
            WorkflowSourceExecutionError, match="retained correction attempt"
        ):
            asyncio.run(resumption)
        assert calls == retained_calls
        return
    resumed = asyncio.run(resumption)
    assert resumed["run_id"] == result["run_id"]
    assert resumed["revision_attempts"] == result["revision_attempts"]
    assert calls == retained_calls
    assert all(
        path.read_bytes() == data
        for attempts in files.values()
        for path, data in attempts
    )


@pytest.mark.parametrize("roles", [[], ["missing"], ["design", "design"], ["basis"]])
def test_segment_profile_cannot_reassign_design_failure_to_supporting_evidence(
    tmp_path, roles
):
    from workspace_service.process_validation.configuration import (
        ValidatorConfiguration,
    )

    plan = design_plan(tmp_path)
    config = {**plan.steps[-1].validation, "repair_subjects": roles}
    with pytest.raises(ValueError):
        ValidatorConfiguration.model_validate(config).load(str(tmp_path))
