import asyncio
from dataclasses import replace
import hashlib
from types import SimpleNamespace

import pytest

from core.process_validation import canonical_digest
from workspace_service.workflow_model_routing import freeze_workflow_model_routing
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import source, task


def route(model="A"):
    public = {
        "adapter": "hermes-http",
        "provider": "configured-provider",
        "model_reference": model,
        "profile": "wright",
        "endpoint_digest": hashlib.sha256(b"http://gateway.test").hexdigest(),
    }
    return {**public, "configuration_digest": canonical_digest(public)}


def owner(resolution):
    async def reader():
        return {"available": True, "resolution": resolution}

    return SimpleNamespace(workflow_model_capabilities=reader)


def test_sdk_route_continuation_stays_exact_and_cannot_replace_http_run():
    from agent_adapters.workflow_sdk import sdk_workflow_resolution
    from workspace_service.workflow_model_routing import validate_frozen_model_plan

    sdk = sdk_workflow_resolution(
        {
            "provider": "configured-provider",
            "model_reference": "A",
            "api_mode": "chat_completions",
            "endpoint_digest": "a" * 64,
            "sdk_digest": "b" * 64,
        }
    )
    plan = compile_prompt_workflow(source(task()))
    original, context = asyncio.run(
        freeze_workflow_model_routing(owner(sdk), plan, None)
    )
    restored, same = asyncio.run(
        freeze_workflow_model_routing(owner(sdk), plan, None, context)
    )
    assert (
        same == context
        and original.steps[0].model_resolution == restored.steps[0].model_resolution
    )
    validate_frozen_model_plan(restored, same)
    _, http_context = asyncio.run(
        freeze_workflow_model_routing(owner(route()), plan, None)
    )
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        asyncio.run(freeze_workflow_model_routing(owner(sdk), plan, None, http_context))
    assert failed.value.code == "WORKFLOW_MODEL_CHANGED"


def test_initial_route_is_frozen_with_integration_context_not_permission_replaced():
    plan = compile_prompt_workflow(source(task()))
    bound, context = asyncio.run(
        freeze_workflow_model_routing(
            owner(route()),
            plan,
            {"integration_policy_digest": "policy", "actor": "integration-test"},
        )
    )
    assert bound.steps[0].model_resolution == route()
    assert context["integration_policy_digest"] == "policy"
    assert context["actor"] == "integration-test"
    assert context["model_routing"]["text"] == route()
    assert not plan.steps[0].model_resolution


def test_service_recreation_reuses_route_and_changed_default_fails_before_continuation():
    plan = compile_prompt_workflow(source(task()))
    original, context = asyncio.run(
        freeze_workflow_model_routing(owner(route()), plan, None)
    )
    recreated = owner(route())
    restored, same_context = asyncio.run(
        freeze_workflow_model_routing(recreated, plan, None, context)
    )
    assert restored.steps[0].model_resolution == original.steps[0].model_resolution
    assert same_context == context
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        asyncio.run(
            freeze_workflow_model_routing(owner(route("B")), plan, None, context)
        )
    assert failed.value.code == "WORKFLOW_MODEL_CHANGED"


@pytest.mark.asyncio
async def test_model_only_context_never_enrolls_automatic_review_and_manual_resume_works(
    tmp_path, monkeypatch
):
    from workspace_service import workflow_approval_execution as approvals
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )

    case = await setup_case(tmp_path, integration=False)
    case.services.workflow_model_capabilities = owner(
        route()
    ).workflow_model_capabilities
    _, context = await freeze_workflow_model_routing(case.services, case.plan, None)
    original_prepare = approvals._prepare

    async def modern_prepare(**kwargs):
        prepared, inputs, runtime, _ = await original_prepare(**kwargs)
        prepared, modern = await freeze_workflow_model_routing(
            case.services, prepared, None, context
        )
        return prepared, inputs, runtime, modern

    monkeypatch.setattr(approvals, "_prepare", modern_prepare)
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        await approvals.decide_workflow_approval(
            **case.args, decision="approved", auto=True
        )
    assert failed.value.code == "WORKFLOW_INTEGRATION_POLICY_INVALID"
    pending = case.services.workflow_external_actions.lookup(
        case.checkpoint.checkpoint_id
    )
    assert pending.state == "pending" and pending.actor is None
    await approvals.decide_workflow_approval(
        **case.args, decision="approved", reason="Reviewed exact isolated document"
    )

    async def frozen_generate(prompt, fmt, *, expected_resolution=None, **kwargs):
        assert expected_resolution == route()
        return await case.generate(prompt, fmt)

    _, result = await approvals.resume_workflow_approval(
        **case.args,
        request_id="frozen-manual-review",
        response_generator=frozen_generate,
    )
    assert result["status"] == "completed"
    assert result["run_id"] == case.result["run_id"]
    assert len(case.calls) == 2


def test_model_only_context_cannot_select_enrolled_handoff_dispatch():
    from workspace_service.workflow_approval_execution import _dispatch_kind
    from workspace_service.workflow_integration_policy import TEST_HANDOFF_BINDING

    checkpoint = SimpleNamespace(
        action_kind="printer_transfer", subject={"binding": TEST_HANDOFF_BINDING}
    )
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        _dispatch_kind(checkpoint, {"model_routing": {"text": route()}})
    assert failed.value.code == "WORKFLOW_EXTERNAL_DISPATCH_UNSUPPORTED"


@pytest.mark.parametrize("enrolled", [False, True])
def test_final_operation_check_uses_only_exact_integration_enrollment(
    tmp_path, monkeypatch, enrolled
):
    from workspace_service.workflow_approval_execution import _operation_dispatch_check
    from workspace_service import workflow_mcp_operations, workflow_mcp_execution

    context = {"model_routing": {"text": route()}}
    if enrolled:
        context["integration_policy_digest"] = "enrolled"
    expected = []
    monkeypatch.setattr(
        workflow_mcp_operations,
        "qualify_operation",
        lambda runtime, step, *, integration: expected.append(integration),
    )
    monkeypatch.setattr(workflow_mcp_execution, "schema_digest", lambda tool: "schema")
    (tmp_path / "source.wflow").write_bytes(b"source")
    checkpoint = SimpleNamespace(
        workflow_id="source.wflow",
        continuation={"execution_context": context},
        subject={
            "definition_digest": hashlib.sha256(b"source").hexdigest(),
            "binding": {"server": "server", "tool": "submit", "schema": "schema"},
        },
    )
    _operation_dispatch_check(checkpoint, str(tmp_path), object(), object())(
        SimpleNamespace(server_id="server", name="submit")
    )
    assert expected == [enrolled]


@pytest.mark.asyncio
async def test_synthetic_review_attribution_is_durable_without_test_enrollment(
    tmp_path,
):
    from workspace_service.workflow_approval_execution import decide_workflow_approval
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )
    from workspace_service.workflow_external_actions import (
        WorkflowExternalActionService,
    )
    from data_vault.workflow_continuation_repository import (
        WorkflowContinuationRepository,
    )
    import json

    case = await setup_case(tmp_path, integration=False)
    decided = await decide_workflow_approval(
        **case.args,
        actor="integration_test:isolated-review",
        decision="approved",
        reason="Synthetic isolated exact review",
        request_id="synthetic-review",
    )
    assert decided.continuation["decision_receipt"]["integration_test"] is True
    assert decided.continuation["decision_attribution"] == {
        "actor": "integration_test:isolated-review",
        "integration_test": True,
    }
    assert "integration_policy_digest" not in (
        decided.continuation.get("execution_context") or {}
    )
    repository = case.services.workflow_external_actions._repository
    reopened = WorkflowExternalActionService(
        WorkflowContinuationRepository(repository.db_path)
    )
    assert reopened.lookup(decided.checkpoint_id) == decided
    record = json.loads((tmp_path / decided.continuation["run_log_path"]).read_text())
    event = next(
        item for item in record["events"] if item["kind"] == "approval_decided"
    )
    assert event["integration_test"] is True
    assert event["actor"] == "integration_test:isolated-review"
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    assert failed.value.code == "WORKFLOW_INTEGRATION_POLICY_INVALID"


def test_incompatible_or_missing_reader_cannot_replace_a_frozen_route():
    plan = compile_prompt_workflow(source(task()))
    _, context = asyncio.run(freeze_workflow_model_routing(owner(route()), plan, None))
    with pytest.raises(WorkflowSourceExecutionError, match="revalidated"):
        asyncio.run(
            freeze_workflow_model_routing(SimpleNamespace(), plan, None, context)
        )
    raw = {
        **context,
        "model_routing": {
            **context["model_routing"],
            "text": {**route(), "model_reference": "forged"},
        },
    }
    with pytest.raises(WorkflowSourceExecutionError, match="revalidated"):
        asyncio.run(freeze_workflow_model_routing(owner(route()), plan, None, raw))


def test_legacy_wait_and_controlled_callback_keep_original_context_shape():
    plan = compile_prompt_workflow(source(task()))
    bound, context = asyncio.run(
        freeze_workflow_model_routing(owner(route("B")), plan, None, None)
    )
    assert not bound.steps[0].model_resolution and context is None
    bound, context = asyncio.run(
        freeze_workflow_model_routing(SimpleNamespace(), plan, {"old": "context"})
    )
    assert not bound.steps[0].model_resolution and context == {"old": "context"}


def test_native_image_configuration_is_retained_and_revalidated():
    import json

    public = {
        "provider": "configured-provider",
        "model_reference": "image-A",
        "api_mode": "codex_responses",
        "endpoint_digest": "1" * 64,
        "sdk_digest": "2" * 64,
    }
    image = {
        **public,
        "configuration_digest": hashlib.sha256(
            json.dumps(public, sort_keys=True).encode()
        ).hexdigest(),
    }
    plan = compile_prompt_workflow(source(task()))
    plan = replace(
        plan,
        steps=(
            replace(
                plan.steps[0], native_image_format="png", native_image_resolution=image
            ),
        ),
    )
    bound, context = asyncio.run(
        freeze_workflow_model_routing(owner(route()), plan, None)
    )
    assert context["model_routing"]["images"][plan.steps[0].id] == image
    assert not bound.steps[0].model_resolution
    changed = {**public, "model_reference": "image-B"}
    changed["configuration_digest"] = hashlib.sha256(
        json.dumps(changed, sort_keys=True).encode()
    ).hexdigest()
    edited = replace(
        plan, steps=(replace(plan.steps[0], native_image_resolution=changed),)
    )
    with pytest.raises(WorkflowSourceExecutionError, match="revalidated"):
        asyncio.run(
            freeze_workflow_model_routing(owner(route()), edited, None, context)
        )


def test_durable_initial_question_restores_route_before_response_consumption(tmp_path):
    from dataclasses import asdict
    from workspace_service.process_interfaces import ProcessInterfaceService
    from workspace_service.workflow_run_record import (
        record_workflow_run,
        record_workflow_resume,
    )
    from workspace_service.workflow_source_execution import execute_prompt_workflow
    from packages.workspace_service.tests.test_process_first_human_input import (
        initial_case,
    )
    from packages.workspace_service.tests.test_workflow_external_action_execution import (
        service,
    )

    app, frozen, unbound = initial_case(tmp_path)
    app.workflow_model_capabilities = owner(route()).workflow_model_capabilities
    plan, context = asyncio.run(freeze_workflow_model_routing(app, unbound, None))
    calls = []

    async def generate(prompt, fmt, **kwargs):
        calls.append(kwargs["expected_resolution"])
        return "Synthetic response using the original model route."

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="frozen-question",
            execution_context=context,
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=frozen.process.source_path,
            source_digest=plan.definition_digest,
            execution_context=context,
            execute=execute,
            run_id="frozen-question",
            required_step_ids=[step.id for step in plan.steps],
        )
    )
    assert first["status"] == "waiting_human" and calls == []
    checkpoint_id = first["input_checkpoint"]["checkpoint_id"]
    app = service(tmp_path)
    app.db_path = str(tmp_path / "state.db")
    app.process_interfaces = ProcessInterfaceService(app)
    checkpoint = app.process_interfaces.human_inputs.get(
        checkpoint_id, workspace_id="ws", run_id="frozen-question"
    )
    durable_context = checkpoint.continuation["execution_context"]
    assert durable_context == context
    from workspace_service.workflow_execution_continuation import (
        inspect_input_continuation,
    )

    with pytest.raises(WorkflowSourceExecutionError) as unqualified:
        asyncio.run(
            inspect_input_continuation(
                state=checkpoint.continuation,
                checkpoint=asdict(checkpoint),
                plan=unbound,
                input_values={},
                service=app,
                workspace_dir=str(tmp_path),
            )
        )
    assert unqualified.value.code == "WORKFLOW_CONTINUATION_STALE"
    app.workflow_model_capabilities = owner(route("B")).workflow_model_capabilities
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        asyncio.run(freeze_workflow_model_routing(app, unbound, None, durable_context))
    assert failed.value.code == "WORKFLOW_MODEL_CHANGED"
    assert (
        app.process_interfaces.human_inputs.get(
            checkpoint_id, workspace_id="ws", run_id="frozen-question"
        )
        == checkpoint
    )

    app.workflow_model_capabilities = owner(route()).workflow_model_capabilities
    plan, context = asyncio.run(
        freeze_workflow_model_routing(app, unbound, None, durable_context)
    )
    _, answer, _ = app.process_interfaces.human_inputs.respond(
        checkpoint_id,
        workspace_id="ws",
        run_id="frozen-question",
        expected_subject_digest=checkpoint.subject_digest,
        value={"selection": "a"},
        actor="integration_test:model-freeze",
        reason="Isolated synthetic input",
        request_id="frozen-answer",
        integration_test=True,
    )
    consumed = app.process_interfaces.human_inputs.consume(
        checkpoint_id,
        workspace_id="ws",
        run_id="frozen-question",
        response_id=answer.response_id,
    )

    def resume():
        return asyncio.run(
            record_workflow_resume(
                service=app,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                checkpoint=consumed,
                execute=lambda emit: execute(emit, consumed),
            )
        )

    final = resume()
    assert final["status"] == "completed"
    assert canonical_digest(resume()) == canonical_digest(final) and calls == [route()]


@pytest.mark.asyncio
@pytest.mark.parametrize("integration", [False, True])
async def test_approval_preparation_revalidates_frozen_route_without_replacing_grant(
    tmp_path, integration
):
    from workspace_service.workflow_approval_execution import _prepare
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )

    c = await setup_case(tmp_path, integration=integration)
    c.services.workflow_model_capabilities = owner(route()).workflow_model_capabilities
    _, context = await freeze_workflow_model_routing(c.services, c.plan, c.context)
    checkpoint = replace(
        c.checkpoint,
        continuation={**c.checkpoint.continuation, "execution_context": context},
    )
    plan, _, runtime, restored = await _prepare(
        service=c.services,
        workspace_id="ws",
        workspace_dir=str(tmp_path),
        checkpoint=checkpoint,
        gateway=None,
        session_id="test",
    )
    assert runtime is None and restored == context
    assert any(step.model_resolution == route() for step in plan.steps)
    c.services.workflow_model_capabilities = owner(
        route("B")
    ).workflow_model_capabilities
    with pytest.raises(WorkflowSourceExecutionError) as failed:
        await _prepare(
            service=c.services,
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            checkpoint=checkpoint,
            gateway=None,
            session_id="test",
        )
    assert failed.value.code == "WORKFLOW_MODEL_CHANGED"
