"""Run-owned receipts reuse the existing approval and dispatch authority."""

from dataclasses import replace
import hashlib
import json
from uuid import uuid4

import pytest

from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths
from workspace_service.workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    prepare_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_approval_execution import (
    decide_workflow_approval,
    resume_workflow_approval,
)
from workspace_service.workflow_run_record import record_workflow_run
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    source,
)
from packages.workspace_service.tests.test_workflow_approval_execution import setup_case


def receipt_source(*, changes=None, outputs=None, kind=None):
    blocks = _parse(source())
    approval = next(block["fields"] for block in blocks if block["id"] == "approve")
    approval["outputs"] = (
        outputs
        if outputs is not None
        else [
            {"key": "handoff_receipt", "kind": "workspace_file", "name": "Receipt"},
        ]
    )
    approval["settings"].update(
        {
            "run_path_template": VERSION,
            "output_filename": f"outputs/{TOKEN}/receipt.json",
            **(changes or {}),
        }
    )
    if kind:
        approval["settings"]["action_kind"] = kind
        approval["settings"]["approval_action"]["kind"] = kind
    return "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)


def test_receipt_path_is_bound_from_declared_output_without_templating_authority():
    original = compile_prompt_workflow(receipt_source())
    action = original.steps[-1]
    assert "receipt_path" not in action.external_action["settings"]
    assert not action.save and action.output_format == "json"
    assert action.expected_files == (action.output_path,)
    bound = bind_run_paths(original, "run-one")
    receipt = bound.steps[-1]
    assert receipt.output_path == "outputs/run-one/receipt.json"
    assert receipt.external_action["settings"]["receipt_path"] == receipt.output_path
    assert receipt.external_action["binding"] == action.external_action["binding"]
    assert (
        receipt.external_action["destination"] == action.external_action["destination"]
    )
    assert "receipt_path" not in action.external_action["settings"]
    assert bound.run_path_roots == ("outputs/run-one",)
    assert bind_run_paths(bound, "run-one") == bound
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(bound, "run-two")


@pytest.mark.parametrize(
    "changes,outputs,kind",
    [
        ({"run_path_template": ""}, None, None),
        ({"run_path_template": "unsupported/2"}, None, None),
        ({"output_filename": "outputs/shared.json"}, None, None),
        ({"output_filename": f"outputs/../{TOKEN}/receipt.json"}, None, None),
        ({"output_filename": f"outputs/{TOKEN}/receipt.txt"}, None, None),
        ({"output_filename": f"outputs/{TOKEN}/{TOKEN}/receipt.json"}, None, None),
        ({"approval_settings": {"receipt_path": "literal.json"}}, None, None),
        ({}, [], None),
        ({}, [{"key": "receipt", "kind": "text", "name": "Receipt"}], None),
        ({}, [{"key": "document", "kind": "workspace_file", "name": "Receipt"}], None),
        ({}, None, "local_review"),
    ],
)
def test_receipt_declaration_errors_are_readiness_defects(changes, outputs, kind):
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(
            compile_prompt_workflow(
                receipt_source(
                    changes=changes,
                    outputs=outputs,
                    kind=kind,
                )
            ),
            "run-one",
        )


@pytest.mark.asyncio
async def test_same_source_two_simulated_handoffs_keep_receipts_and_resume_without_replay(
    tmp_path,
):
    case = await setup_case(tmp_path, handoff=True, run_paths=True, run_receipt=True)
    source_path = "workflows/example.workflow.wflow"
    first_source = (tmp_path / source_path).read_bytes()
    frozen = {}
    first_subject = None
    for index in range(2):
        if index:
            run_id = uuid4().hex
            plan, inputs = await prepare_prompt_workflow(
                service=case.services,
                workspace_dir=str(tmp_path),
                path=source_path,
                expected_digest=case.plan.definition_digest,
                run_id=run_id,
            )
            policy = case.context["integration_policy_digest"]
            context = await case.services.workflow_integration_policies.authorize(
                policy,
                workspace_id="ws",
                workspace_dir=str(tmp_path),
                source_path=source_path,
                source_digest=plan.definition_digest,
                plan=plan,
                files=case.services.files,
                tool_runtime=None,
            )

            async def execute(emit):
                return await execute_prompt_workflow(
                    service=case.services,
                    workspace_dir=str(tmp_path),
                    plan=plan,
                    input_values=inputs,
                    response_generator=case.generate,
                    execution_context=context,
                    run_id=run_id,
                    on_event=emit,
                )

            result = await record_workflow_run(
                service=case.services,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                source_path=source_path,
                source_digest=plan.definition_digest,
                execution_context=context,
                run_id=run_id,
                required_step_ids=[step.id for step in plan.steps],
                execute=execute,
            )
            checkpoint = case.services.workflow_external_actions.lookup(
                result["approval"]["checkpoint_id"]
            )
            args = {
                **case.args,
                "checkpoint": checkpoint,
                "subject_digest": checkpoint.subject_digest,
            }
        else:
            run_id, checkpoint, args = case.result["run_id"], case.checkpoint, case.args
        expected = f"outputs/attempt/{run_id}/receipt.json"
        assert checkpoint.subject["settings"]["receipt_path"] == expected
        assert not (tmp_path / expected).exists()
        if first_subject:
            assert checkpoint.subject_digest != first_subject
        else:
            first_subject = checkpoint.subject_digest
        await decide_workflow_approval(**args, decision="approved", auto=True)
        _, finished = await resume_workflow_approval(
            **args,
            request_id=f"run-receipt-{index}",
            response_generator=case.generate,
        )
        assert finished["status"] == "completed" and finished["run_id"] == run_id
        raw = (tmp_path / expected).read_bytes()
        receipt = json.loads(raw)
        assert receipt["run_id"] == run_id
        assert receipt["integration_test"] and receipt["network_dispatch"] is False
        typed = [
            r
            for r in finished["results"]
            if r["artifact_role"] == "external_action_receipt"
        ]
        assert len(typed) == 1 and typed[0]["provenance"]["task_id"] == "approve"
        calls = len(case.calls)
        _, duplicate = await resume_workflow_approval(
            **args,
            request_id=f"run-receipt-{index}",
            response_generator=case.generate,
        )
        assert duplicate["run_id"] == run_id and len(case.calls) == calls
        frozen.update(
            {
                output["output_path"]: hashlib.sha256(
                    (tmp_path / output["output_path"]).read_bytes()
                ).hexdigest()
                for output in finished["outputs"]
            }
        )
        for path, sha in frozen.items():
            assert hashlib.sha256((tmp_path / path).read_bytes()).hexdigest() == sha
    assert (tmp_path / source_path).read_bytes() == first_source
    assert len(list((tmp_path / "outputs/attempt").glob("*/receipt.json"))) == 2


def test_neutral_mcp_operation_accepts_same_declared_receipt_output():
    from packages.workspace_service.tests.test_workflow_mcp_operations import (
        configured_source,
    )

    blocks = _parse(configured_source())
    approval = next(b["fields"] for b in blocks if b["id"] == "approve")
    approval["outputs"] = [
        {"key": "submission_receipt", "kind": "workspace_file", "name": "Receipt"}
    ]
    approval["settings"].update(
        run_path_template=VERSION, output_filename=f"receipts/{TOKEN}/submit.json"
    )
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    bound = bind_run_paths(compile_prompt_workflow(text), "digital-one")
    assert (
        bound.steps[-1].external_action["settings"]["receipt_path"]
        == "receipts/digital-one/submit.json"
    )


@pytest.mark.asyncio
async def test_run_receipt_dispatches_neutral_digital_operation_once(tmp_path):
    from packages.workspace_service.tests.test_workflow_mcp_operations import (
        configured_source,
        approved_case,
        dispatch,
    )

    blocks = _parse(configured_source())
    for block in blocks:
        if block["id"] == "package":
            block["fields"]["settings"].update(
                run_path_template=VERSION,
                output_filename=f"outputs/private/{TOKEN}/package.json",
            )
        if block["id"] == "approve":
            block["fields"]["settings"].update(
                run_path_template=VERSION,
                output_filename=f"outputs/private/{TOKEN}/submit.json",
            )
            block["fields"]["outputs"] = [
                {
                    "key": "submission_receipt",
                    "kind": "workspace_file",
                    "name": "Receipt",
                    "item": None,
                    "quantity": "one",
                    "required": False,
                    "description": "Exact submission receipt",
                }
            ]
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    services, checkpoint, gateway, generate, models, initial = await approved_case(
        tmp_path,
        text=text,
        integration=True,
        run_id="digital-one",
    )
    assert (
        checkpoint.subject["settings"]["receipt_path"]
        == "outputs/private/digital-one/submit.json"
    )
    completed = await dispatch(tmp_path, services, checkpoint, gateway, generate)
    assert (
        completed["status"] == "completed" and completed["run_id"] == initial["run_id"]
    )
    receipt_path = tmp_path / "outputs/private/digital-one/submit.json"
    raw = receipt_path.read_bytes()
    receipt = json.loads(raw)
    assert receipt["subject_digest"] == checkpoint.subject_digest
    assert receipt["submission"] == "accepted" and receipt["observed_outcome"] is None
    assert len(gateway.calls) == len(models) == 1
    await dispatch(tmp_path, services, checkpoint, gateway, generate)
    assert len(gateway.calls) == len(models) == 1 and receipt_path.read_bytes() == raw


@pytest.mark.asyncio
async def test_declared_receipt_keeps_existing_enrolled_output_boundary(tmp_path):
    case = await setup_case(tmp_path, handoff=True, run_paths=True, run_receipt=True)
    step = case.plan.steps[-2]
    assert step.external_action
    altered = replace(
        step,
        external_action={
            **step.external_action,
            "settings": {"receipt_path": "other/output/receipt.json"},
        },
    )
    changed = replace(
        case.plan,
        steps=tuple(altered if s.id == step.id else s for s in case.plan.steps),
    )
    with pytest.raises(WorkflowSourceExecutionError):
        await case.services.workflow_integration_policies.authorize(
            case.context["integration_policy_digest"],
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            source_path="workflows/example.workflow.wflow",
            source_digest=case.plan.definition_digest,
            plan=changed,
            files=case.services.files,
            tool_runtime=None,
        )
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )
    assert not list((tmp_path / "outputs/attempt").glob("*/receipt.json"))


def test_bound_receipt_cannot_hide_unsupported_authority_tokens():
    bound = bind_run_paths(compile_prompt_workflow(receipt_source()), "run-one")
    action = bound.steps[-1]
    changed = replace(
        action, external_action={**action.external_action, "destination": {"id": TOKEN}}
    )
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(replace(bound, steps=(*bound.steps[:-1], changed)), "run-one")


def test_receipt_cannot_collide_with_another_declared_output():
    blocks = _parse(receipt_source())
    package = next(b["fields"] for b in blocks if b["id"] == "package")
    package["settings"].update(
        run_path_template=VERSION,
        output_filename=f"outputs/{TOKEN}/receipt.json",
    )
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    with pytest.raises(WorkflowSourceExecutionError, match="overwrite the same output"):
        compile_prompt_workflow(text)
