"""Canonical process checks inspect actual previous-step outputs without an LLM."""

import json
import asyncio
from types import SimpleNamespace

import pytest

from workspace_service.process_validation.profiles import load_profile
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from .test_workflow_source_execution import source, task, service


def configuration():
    profile = load_profile("structured-demo")
    return {
        "profile": {
            "source": "packaged",
            "name": "structured-demo",
            "reference": profile.reference().model_dump(),
        },
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"result": "inspect_subject"},
    }


def validator(config=None, **settings):
    return f"""task inspect
  name: "Inspect produced output"
  step_type: work
  performed_by: configured_tool
  inputs: [{{"key":"inspect_subject","name":"Produced output","kind":"engineering_document","required":true}}]
  outputs: [{{"key":"inspect_assessment","name":"Assessment","kind":"engineering_document"}}]
  prompt: ""
  settings: {json.dumps({"authoring_template": "process-validator", "validation": configuration() if config is None else config, **settings})}
  tool: null
  reusable_step: null
end
"""


def workflow(check=None, connection=True, consumer=False):
    result = source(task("produce", fmt="json"), check or validator())
    if consumer:
        result += task("consume", fmt="text")
        result += """connection release
  type: approval
  from: "inspect"
  to: "consume"
  label: "Validated output"
  when: pass
end
"""
    if connection:
        result += """connection subject
  type: item
  from: "produce.produce_response"
  to: "inspect.inspect_subject"
  label: "Output to inspect"
  when: null
end
"""
    return result


def test_compile_local_validator_without_mcp_or_model_prompt():
    plan = compile_prompt_workflow(workflow(consumer=True))
    check = plan.steps[1]
    assert (
        check.validation["profile"]["reference"]
        == configuration()["profile"]["reference"]
    )
    assert check.validation_sources == (("result", "produce.produce_response"),)
    assert check.design_check and not check.agent_task and not check.tool_name
    assert check.max_revisions == 0 and not check.save
    assert plan.steps[2].id == "consume"


@pytest.mark.parametrize("fault", ["profile", "baseline", "roles"])
def test_profile_preflight_rejects_changed_pins_and_missing_profile_roles(
    tmp_path, fault
):
    from workspace_service.process_validation.configuration import (
        ValidatorConfiguration,
    )

    config = configuration()
    if fault == "profile":
        config["profile"]["reference"]["sha256"] = "a" * 64
    elif fault == "baseline":
        config["baseline"]["sha256"] = "b" * 64
    else:
        config["subjects"] = {"wrong_role": "inspect_subject"}
    with pytest.raises(ValueError):
        ValidatorConfiguration.model_validate(config).load(str(tmp_path))


def test_profile_preflight_accepts_the_exact_frozen_profile(tmp_path):
    from workspace_service.process_validation.configuration import (
        ValidatorConfiguration,
    )

    assert ValidatorConfiguration.model_validate(configuration()).load(
        str(tmp_path)
    ) == load_profile("structured-demo")


@pytest.mark.parametrize(
    "fault",
    [
        "missing_pin",
        "bad_digest",
        "unknown_field",
        "unknown_source",
        "unsafe_path",
        "missing_role",
        "unknown_port",
        "two_roles_one_port",
        "too_many_bytes",
        "missing_settings",
        "executable",
        "negative_revisions",
        "unconnected",
        "input_instead_of_producer",
        "mixed_mcp",
        "overwrite",
        "wrong_performer",
        "unexpected_output",
        "collection",
    ],
)
def test_compile_rejects_ambiguous_or_unsafe_validator_bindings(fault):
    config, settings = configuration(), {}
    if fault == "missing_pin":
        del config["profile"]["reference"]
    if fault == "bad_digest":
        config["baseline"]["sha256"] = "unversioned"
    if fault == "unknown_field":
        config["ignore_failed_checks"] = True
    if fault == "unknown_source":
        config["profile"]["source"] = "url"
    if fault == "unsafe_path":
        config["profile"].update(source="workspace", name="../secret.json")
    if fault == "missing_role":
        config["subjects"] = {}
    if fault == "unknown_port":
        config["subjects"]["result"] = "missing"
    if fault == "two_roles_one_port":
        config["subjects"]["second"] = "inspect_subject"
    if fault == "too_many_bytes":
        config["budget"] = {"max_bytes": 10**12}
    if fault == "missing_settings":
        config = {}
    if fault == "executable":
        config["predicate"] = "eval(input)"
    if fault == "negative_revisions":
        settings["max_revisions"] = -1
    if fault == "mixed_mcp":
        settings["mcp_server"] = "some-server"
    if fault == "overwrite":
        settings["file_policy"] = "overwrite"
    text = workflow(validator(config, **settings), connection=fault != "unconnected")
    if fault == "input_instead_of_producer":
        text = text.replace("task produce", "input produce")
    if fault == "wrong_performer":
        text = text.replace(
            "performed_by: configured_tool", "performed_by: ai_assisted"
        )
    if fault == "unexpected_output":
        text = text.replace(
            '"key":"inspect_assessment"', '"key":"inspect_assessment","quantity":"many"'
        )
    if fault == "collection":
        text = text.replace(
            '"key":"inspect_subject"', '"key":"inspect_subject","quantity":"many"'
        ).replace(
            '"key":"produce_response"', '"key":"produce_response","quantity":"many"'
        )
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(text)


def runtime_service(tmp_path):
    app = service(tmp_path)
    app.db_path = str(tmp_path / "validation.db")
    app.repository = SimpleNamespace(
        get_by_path=lambda _: {"workspace_id": "workspace"}
    )
    return app


@pytest.mark.parametrize("length,passing", [(100, True), (98, False)])
def test_canonical_gate_inspects_producer_output_and_publishes_evidence_before_holding(
    tmp_path, length, passing
):
    from core.process_validation import Assessment
    from workspace_service.process_validation.application import ValidationApplication
    from workspace_service.process_validation_tools import ProcessValidationTool
    from core.tools import ToolContext

    plan = compile_prompt_workflow(workflow(consumer=True))
    app, calls, events = runtime_service(tmp_path), [], []

    async def generate(prompt, fmt):
        calls.append(fmt)
        return (
            json.dumps({"part_id": "demo-plate", "length_mm": length})
            if fmt == "json"
            else "Released after validation"
        )

    async def emit(event):
        events.append(event)

    async def run():
        return await execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="run",
        )

    if passing:
        result = asyncio.run(run())
        assert result["steps"][-1]["task_id"] == "consume"
        assert result["steps"][1]["execution_kind"] == "validator"
        assert calls == ["json", "text"]
    else:
        with pytest.raises(WorkflowSourceExecutionError) as error:
            asyncio.run(run())
        assert error.value.code == "PROCESS_VALIDATION_REJECTED"
        assert calls == ["json"] and not (tmp_path / "consume.txt").exists()
    report = next(e["report"] for e in events if e["kind"] == "design_check")
    path = tmp_path / report["assessment_path"]
    assert path.exists()
    assessment = Assessment.model_validate_json(path.read_bytes())
    assert assessment.summary.release_eligible is passing
    assert assessment.request.subjects[0].producer.attempt == 1
    assert assessment.request.subjects[0].producer.step_id == "produce"
    assert assessment.request.subjects[0].value == json.dumps(
        {"part_id": "demo-plate", "length_mm": length}
    )
    evidence_event = next(
        e
        for e in events
        if e["kind"] == "result_ready" and e.get("task_id") == "inspect"
    )
    assert evidence_event["artifact_role"] == (
        "verification" if passing else "diagnostic"
    )
    application = ValidationApplication(app.db_path, "workspace", str(tmp_path))
    read = asyncio.run(
        ProcessValidationTool(application, "read").execute(
            {"assessment_id": assessment.id},
            context=ToolContext("local", "workspace", "trace", "read"),
        )
    )
    assert read["release_eligible"] is passing
    assert read["assessment_digest"] == report["assessment_digest"]


def test_unavailable_reader_persists_blocked_assessment_and_holds_consumer(tmp_path):
    from core.process_validation import Assessment, ValidationProfile

    raw = load_profile("structured-demo").model_dump(mode="json")
    raw["checks"][0]["reader"] = "not-installed"
    profile = ValidationProfile.model_validate(raw)
    (tmp_path / "profile.json").write_text(profile.model_dump_json(), encoding="utf-8")
    config = configuration()
    config["profile"] = {
        "source": "workspace",
        "name": "profile.json",
        "reference": profile.reference().model_dump(),
    }
    plan = compile_prompt_workflow(workflow(validator(config), consumer=True))
    events, calls = [], []

    async def generate(prompt, fmt):
        calls.append(fmt)
        return '{"part_id":"demo-plate","length_mm":100}'

    async def emit(event):
        events.append(event)

    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            execute_prompt_workflow(
                service=runtime_service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                on_event=emit,
                run_id="run",
            )
        )
    assert error.value.code == "PROCESS_VALIDATION_NEEDS_INPUT"
    assert calls == ["json"]
    report = next(e["report"] for e in events if e["kind"] == "design_check")
    assessment = Assessment.model_validate_json(
        (tmp_path / report["assessment_path"]).read_bytes()
    )
    assert not assessment.summary.release_eligible
    assert any(f.category == "capability_unavailable" for f in assessment.findings)


def test_no_available_subject_still_produces_a_blocked_assessment(tmp_path):
    from core.process_validation import ValidationRequest
    from workspace_service.process_validation.application import ValidationApplication

    app = ValidationApplication(tmp_path / "state.db", "workspace", str(tmp_path))
    profile = load_profile("structured-demo")
    request = ValidationRequest(
        trace_id="trace",
        workspace_id="workspace",
        invocation_id="missing-output",
        subjects=(),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="once",
    )
    result = app.service.evaluate(request, profile)
    assert result.assessment and not result.release_eligible
    assert all(f.code == "subject.role_missing" for f in result.assessment.findings)


@pytest.mark.parametrize(
    ("review_actor", "passes"),
    [("reviewer-1", True), ("integration_test:campaign", False)],
)
def test_exact_local_review_satisfies_only_its_pinned_validator_requirements(
    tmp_path, review_actor, passes
):
    from dataclasses import asdict, replace

    from core.process_validation import ValidationProfile, canonical_json
    from data_vault import WorkflowContinuationRepository
    from workspace_service.process_validation.application import ValidationApplication
    from workspace_service.workflow_external_actions import WorkflowExternalActionService
    from workspace_service.workflow_integration_policy import (
        LOCAL_REVIEW_BINDING,
        LOCAL_REVIEW_DESTINATION,
    )

    profile = ValidationProfile.model_validate(
        {
            "id": "review-bridge-profile",
            "version": "1",
            "baseline": {
                "id": "review-bridge-basis",
                "version": "1",
                "requirements": [
                    {
                        "id": "REVIEW-001",
                        "text": "An authenticated reviewer accepts the exact result.",
                        "scope": "content",
                        "mandatory": True,
                        "review_required": True,
                        "sources": [
                            {
                                "artifact_ref": "requirements.md",
                                "locator": "R1",
                                "sha256": "a" * 64,
                            }
                        ],
                    }
                ],
            },
            "checks": [
                {
                    "id": "review-result",
                    "version": "1",
                    "requirement_ids": ["REVIEW-001"],
                    "subject_role": "result",
                    "reader": "structured",
                    "selector": "",
                    "constraint": {"operator": "review"},
                    "evidence_method": "human_review",
                }
            ],
            "supported_kinds": ["value"],
        }
    )
    (tmp_path / "review-profile.json").write_text(
        canonical_json(profile), encoding="utf-8"
    )
    config = {
        "profile": {
            "source": "workspace",
            "name": "review-profile.json",
            "reference": profile.reference().model_dump(mode="json"),
        },
        "baseline": profile.baseline.reference().model_dump(mode="json"),
        "subjects": {"result": "inspect_subject"},
    }
    review_settings = {
        "authoring_template": "external-action-approval",
        "action_kind": "local_review",
        "approval_binding": LOCAL_REVIEW_BINDING,
        "approval_destination": LOCAL_REVIEW_DESTINATION,
        "approval_settings": {
            "review_task_id": "review",
            "validation_review": {
                "profile_ref": profile.reference().model_dump(mode="json"),
                "requirement_ids": ["REVIEW-001"],
            },
        },
        "approval_action": {"kind": "local_review", "mode": "review_only"},
    }
    text = source(
        task("produce", fmt="json"),
        f'''task review
  name: "Review exact result"
  step_type: review
  performed_by: engineer
  inputs: [{{"key":"review_subject","name":"Result","kind":"engineering_document","required":true}}]
  outputs: []
  instructions: "Approve only when REVIEW-001 is satisfied by this exact result."
  settings: {json.dumps(review_settings)}
  tool: null
  reusable_step: null
end
''',
        validator(config),
        task("consume", fmt="text"),
    )
    text += '''connection review_subject
  type: item
  from: "produce.produce_response"
  to: "review.review_subject"
  label: "Exact result to review"
  when: null
end
connection validation_subject
  type: item
  from: "produce.produce_response"
  to: "inspect.inspect_subject"
  label: "Exact result to validate"
  when: null
end
connection review_before_validation
  type: order
  from: "review"
  to: "inspect"
  label: "Apply exact review"
  when: null
end
connection release
  type: approval
  from: "inspect"
  to: "consume"
  label: "Release reviewed result"
  when: pass
end
'''
    plan = replace(compile_prompt_workflow(text), definition_digest="b" * 64)
    app = runtime_service(tmp_path)

    async def read_reference(workspace_dir, path):
        return (tmp_path / path).read_bytes()

    async def hash_reference(workspace_dir, path):
        import hashlib

        return hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()

    app.files.read_reference = read_reference
    app.files.hash_reference = hash_reference
    app.workflow_external_actions = WorkflowExternalActionService(
        WorkflowContinuationRepository(str(tmp_path / "actions.db"))
    )
    calls = []

    async def generate(prompt, fmt):
        calls.append(fmt)
        return '{"reviewed":true}' if fmt == "json" else "released"

    first = asyncio.run(
        execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            run_id="review-bridge-run",
        )
    )
    request = first["_approval_request"]
    review_requirements = request["subject"]["settings"][
        "validation_review_requirements"
    ]
    assert review_requirements == [
        {
            "id": "REVIEW-001",
            "text": "An authenticated reviewer accepts the exact result.",
            "scope": "content",
            "sources": [
                {
                    "artifact_ref": "requirements.md",
                    "locator": "R1",
                    "sha256": "a" * 64,
                }
            ],
        }
    ]
    if passes:
        from workspace_service.workflow_source_execution import _approval_settings

        review_step = next(step for step in plan.steps if step.id == "review")
        bad_action = json.loads(json.dumps(review_step.external_action))
        bad_action["settings"]["validation_review"]["requirement_ids"] = [
            "REVIEW-MISSING"
        ]
        bad_review = replace(review_step, external_action=bad_action)
        with pytest.raises(WorkflowSourceExecutionError) as mismatch:
            _approval_settings(
                pending_action=bad_review,
                plan=replace(
                    plan,
                    steps=tuple(
                        bad_review if step.id == "review" else step
                        for step in plan.steps
                    ),
                ),
                workspace_dir=str(tmp_path),
            )
        assert "does not match the pinned profile" in str(mismatch.value)
    actions = app.workflow_external_actions
    checkpoint = actions.request(
        workspace_id="workspace",
        workflow_id="review-bridge.workflow.wflow",
        run_id=first["run_id"],
        step_id=request["step_id"],
        action_kind=request["action_kind"],
        subject=request["subject"],
        continuation=request["continuation"],
    )
    checkpoint = actions.decide(
        checkpoint.checkpoint_id,
        workspace_id="workspace",
        expected_subject_digest=checkpoint.subject_digest,
        actor=review_actor,
        approved=True,
        reason="Reviewed REVIEW-001 against the exact response.",
    )
    checkpoint = actions.consume_for_dispatch(
        checkpoint.checkpoint_id,
        workspace_id="workspace",
        current_subject=checkpoint.subject,
        action_id="local-review-1",
    )
    checkpoint = actions.reconcile(
        checkpoint.checkpoint_id,
        workspace_id="workspace",
        run_id=first["run_id"],
        expected_subject_digest=checkpoint.subject_digest,
        outcome="dispatched",
        evidence={"kind": "local_review"},
    )
    async def resume():
        return await execute_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                continuation=checkpoint.continuation,
                completed_checkpoint=asdict(checkpoint),
        )

    if not passes:
        with pytest.raises(WorkflowSourceExecutionError) as error:
            asyncio.run(resume())
        assert error.value.code == "PROCESS_VALIDATION_NEEDS_INPUT"
        assert calls == ["json"]
        return
    final = asyncio.run(resume())

    validation = next(step for step in final["steps"] if step["task_id"] == "inspect")
    assessment = ValidationApplication(
        app.db_path, "workspace", str(tmp_path)
    ).get_result(validation["validation"]["assessment_id"]).assessment
    assert validation["validation"]["release_eligible"]
    assert assessment.summary.release_eligible
    assert len(assessment.review_ids) == 1
    assert assessment.checks[0].state == "pass"
    assert assessment.checks[0].evidence_refs[0] == assessment.review_ids[0]
    assert calls == ["json", "text"]
