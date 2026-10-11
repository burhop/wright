"""Review exact saved evidence without requiring its producer to remain online.

These isolated fixtures use the actual continuation/decision owners. No native
engineering provider, real review subject or external operation is involved.
"""

from dataclasses import replace

import pytest

from workspace_service import workflow_approval_execution as owner
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from .test_workflow_approval_execution import setup_case


@pytest.mark.asyncio
@pytest.mark.parametrize("integration", [False, True])
@pytest.mark.parametrize("decision", ["approved", "changes_requested"])
async def test_disconnected_producer_allows_exact_review_but_not_execution(
    tmp_path, integration, decision
):
    case = await setup_case(
        tmp_path, integration=integration, package_artifact=b"saved evidence"
    )
    gateway = case.args["gateway"]
    gateway.enabled = False
    calls = list(gateway.calls)
    model_calls = list(case.calls)
    inspected = await owner.inspect_workflow_approval(**case.args)
    assert inspected.can_decide and not inspected.can_resume
    decided = await owner.decide_workflow_approval(
        **case.args,
        decision=decision,
        reason="Isolated review fixture",
        request_id="review-offline",
    )
    assert decided.state == decision and decided.external_action is None
    assert gateway.calls == calls and case.calls == model_calls
    if decision == "approved":
        with pytest.raises(WorkflowSourceExecutionError):
            await owner.resume_workflow_approval(
                **case.args,
                response_generator=case.generate,
                request_id="offline-continue",
            )
        retained = case.services.workflow_external_actions.lookup(decided.checkpoint_id)
        assert retained.state == "approved" and retained.external_action is None
        assert gateway.calls == calls and case.calls == model_calls


@pytest.mark.asyncio
async def test_offline_review_preserves_exact_artifact_checks(tmp_path):
    case = await setup_case(tmp_path, package_artifact=b"saved evidence")
    case.args["gateway"].enabled = False
    (tmp_path / "outputs/attempt/large-artifact.pdf").write_bytes(b"replaced evidence")
    with pytest.raises(owner.WorkflowExternalActionError, match="artifact changed"):
        await owner.decide_workflow_approval(
            **case.args, decision="approved", reason="Must reject changed evidence"
        )
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", ["source", "input", "deleted", "subject", "revoked", "expired"]
)
async def test_offline_decision_still_rejects_stale_or_unenrolled_subjects(
    tmp_path, monkeypatch, failure
):
    import time

    now = int(time.time())
    case = await setup_case(
        tmp_path,
        package_artifact=b"saved evidence",
        expires_at=now + 60 if failure == "expired" else None,
    )
    case.args["gateway"].enabled = False
    if failure == "source":
        (tmp_path / case.checkpoint.workflow_id).write_text(
            "different source", encoding="utf-8"
        )
    elif failure == "input":
        (tmp_path / "brief.md").write_text("different input", encoding="utf-8")
    elif failure == "deleted":
        (tmp_path / "outputs/attempt/large-artifact.pdf").unlink()
    elif failure == "subject":
        case.args["subject_digest"] = "0" * 64
    elif failure == "revoked":
        case.services.workflow_integration_policies.revoke(
            case.context["integration_policy_digest"]
        )
    else:
        from workspace_service import workflow_integration_policy as policies

        # Expiry is checked in the real owner, not bypassed by a missing tool.
        monkeypatch.setattr(policies.time, "time", lambda: now + 120)
    with pytest.raises(
        (owner.WorkflowExternalActionError, WorkflowSourceExecutionError)
    ):
        await owner.decide_workflow_approval(
            **case.args, decision="approved", reason="Invalid isolated subject"
        )
    retained = case.services.workflow_external_actions.lookup(
        case.checkpoint.checkpoint_id
    )
    assert retained.state == "pending" and retained.external_action is None


@pytest.mark.asyncio
@pytest.mark.parametrize("integration", [False, True])
async def test_offline_automatic_decision_requires_exact_test_enrollment(
    tmp_path, integration
):
    case = await setup_case(
        tmp_path, integration=integration, package_artifact=b"saved evidence"
    )
    case.args["gateway"].enabled = False
    if not integration:
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await owner.decide_workflow_approval(
                **case.args, decision="approved", auto=True
            )
        assert error.value.code == "WORKFLOW_INTEGRATION_POLICY_INVALID"
    else:
        result = await owner.decide_workflow_approval(
            **case.args,
            decision="approved",
            auto=True,
            request_id="exact-test-decision",
        )
        assert (
            result.actor == "integration_test:campaign"
            and result.external_action is None
        )
        duplicate = await owner.decide_workflow_approval(
            **case.args,
            decision="approved",
            auto=True,
            request_id="exact-test-decision",
        )
        assert duplicate == result


@pytest.mark.asyncio
async def test_restored_provider_allows_same_run_without_repeating_producer(tmp_path):
    case = await setup_case(tmp_path, package_artifact=b"saved evidence")
    gateway = case.args["gateway"]
    gateway.enabled = False
    calls = list(gateway.calls)
    await owner.decide_workflow_approval(**case.args, decision="approved", auto=True)
    gateway.enabled = True
    assert (await owner.inspect_workflow_approval(**case.args)).can_resume
    _, result = await owner.resume_workflow_approval(
        **case.args, response_generator=case.generate, request_id="restored-continue"
    )
    assert (
        result["status"] == "completed" and result["run_id"] == case.checkpoint.run_id
    )
    assert gateway.calls == calls


@pytest.mark.asyncio
async def test_review_plan_cannot_be_passed_to_executor(tmp_path):
    from workspace_service.workflow_source_execution import execute_prompt_workflow

    case = await setup_case(tmp_path, integration=False)
    args = {key: value for key, value in case.args.items() if key != "subject_digest"}
    plan, inputs, runtime, context = await owner._prepare(
        **args, gateway=None, for_decision=True
    )
    assert plan.review_only and runtime is None
    calls = list(case.calls)
    with pytest.raises(WorkflowSourceExecutionError, match="review-only"):
        await execute_prompt_workflow(
            service=case.services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values=inputs,
            response_generator=case.generate,
        )
    assert case.calls == calls


@pytest.mark.asyncio
@pytest.mark.parametrize("integration", [False, True])
async def test_decision_restores_saved_model_identity_but_resume_requalifies(
    tmp_path, integration
):
    from workspace_service.workflow_model_routing import freeze_workflow_model_routing
    from .test_workflow_model_routing import owner as model_owner, route

    case = await setup_case(tmp_path, integration=integration)
    model = model_owner(route())
    _, context = await freeze_workflow_model_routing(model, case.plan, case.context)
    checkpoint = replace(
        case.checkpoint,
        continuation={**case.checkpoint.continuation, "execution_context": context},
    )
    args = {
        **{
            key: value
            for key, value in case.args.items()
            if key not in {"subject_digest", "checkpoint"}
        },
        "checkpoint": checkpoint,
        "gateway": None,
    }

    async def offline():
        raise AssertionError("Recording a decision must not query the model provider")

    case.services.workflow_model_capabilities = offline
    plan, _, runtime, restored = await owner._prepare(**args, for_decision=True)
    assert plan.review_only and runtime is None and restored == context
    assert any(step.model_resolution == route() for step in plan.steps)
    case.services.workflow_model_capabilities = model_owner(
        route("B")
    ).workflow_model_capabilities
    with pytest.raises(WorkflowSourceExecutionError) as error:
        await owner._prepare(**args)
    assert error.value.code == "WORKFLOW_MODEL_CHANGED"


@pytest.mark.asyncio
@pytest.mark.parametrize("default", [False, True])
async def test_saved_option_review_is_passive_but_execution_refreshes(
    tmp_path, default
):
    from workspace_service.process_interfaces import inputs
    from workspace_service.process_interfaces.errors import ProcessInterfaceError
    from .test_process_input_readiness import (
        OptionsRuntime,
        option_metadata,
        source,
        process,
        service,
    )

    metadata = option_metadata()
    if default:
        metadata["default_option_id"] = "material-a"
    text = source(metadata=metadata)
    services = service(tmp_path)
    runtime = OptionsRuntime()
    args = dict(
        service=services,
        workspace_dir=str(tmp_path),
        process=process(text),
        source=text,
    )
    prepared = await inputs.prepare_inputs(
        **args, tool_runtime=runtime, now="2026-09-30T12:00:00Z"
    )
    if not default:
        from core.process_interactions import OptionBinding

        definition = prepared.definitions[0]
        binding = OptionBinding(
            input_id="brief",
            option_id="material-a",
            capability=definition.option_source,
            value="PLA",
            observed_at=definition.options_observed_at,
            stale_after=definition.options_stale_after,
        )
        prepared = await inputs.prepare_inputs(
            **args,
            bindings=(binding,),
            tool_runtime=runtime,
            now="2026-09-30T12:00:01Z",
        )
    saved = prepared.snapshot
    frozen = dict(
        bindings=saved.bindings,
        snapshot_id=saved.snapshot_id,
        created_at=saved.created_at,
    )
    reviewed = await inputs.prepare_inputs(**args, **frozen, review_snapshot=saved)
    assert reviewed.snapshot == saved and reviewed.values == {"brief": "PLA"}
    assert reviewed.definitions[0].available_options == ()
    # The same values still require a live, fresh option catalog for execution.
    with pytest.raises(ProcessInterfaceError) as error:
        await inputs.prepare_inputs(**args, **frozen)
    assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"
    runtime.options[0]["value"] = "PETG"
    with pytest.raises(ProcessInterfaceError) as changed:
        await inputs.prepare_inputs(
            **args, **frozen, tool_runtime=runtime, now="2026-09-30T12:00:02Z"
        )
    assert changed.value.reason.code == "OPTION_STALE"


@pytest.mark.asyncio
async def test_scoped_process_view_exposes_review_without_provider_and_keeps_resume_blocked(
    tmp_path,
):
    from .test_process_review_decisions import (
        waiting_review_case,
        review_source,
        review_scope,
        decide,
    )
    from .test_workflow_mcp_execution import Gateway, TOOL
    from .test_workflow_artifact_review import section
    from workspace_service.workflow_mcp_execution import schema_digest
    from workspace_service.workflow_source_execution import _parse

    blocks = _parse(review_source())
    first = next(block for block in blocks if block["id"] == "first")
    first["fields"]["performed_by"] = "configured_tool"
    first["fields"]["settings"].update(
        authoring_template="mcp-tool",
        mcp_server=TOOL.server_id,
        mcp_tool=TOOL.name,
        mcp_schema_digest=schema_digest(TOOL),
        mcp_arguments="{}",
        mcp_argument_ports='{"first_in":"query"}',
        output_format="json",
        output_filename="first.json",
    )
    text = "".join(
        section(block["kind"], block["id"], **block["fields"]) for block in blocks
    )
    gateway = Gateway()
    case = await waiting_review_case(tmp_path, text=text, gateway=gateway)
    app, reference, receipt, cp, digest, calls, _ = case
    gateway.enabled = False
    tool_calls = list(gateway.calls)
    try:
        # The process contract owns the buttons; the UI needs no independent rule.
        snapshot = await app.get_snapshot(
            review_scope(), reference, run_id=receipt.run_id, gateway=gateway
        )
        review = next(
            action for action in snapshot.actions if action.operation == "review"
        )
        continuation = next(
            action for action in snapshot.actions if action.operation == "action"
        )
        assert review.enabled and not continuation.enabled
        assert review.subject_digest == digest and review.checkpoint_id == cp
        decided = await decide(case)
        assert decided.interactions[0].decision.decision == "approved"
        assert not any(
            action.enabled
            for action in decided.actions
            if action.operation in {"review", "action"}
        )
        assert calls == [] and gateway.calls == tool_calls
        assert (
            app.workspace.workflow_external_actions.lookup(cp).external_action is None
        )
    finally:
        await app.close()
