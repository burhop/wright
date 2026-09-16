"""Application-level decisions/dispatch retain policy and same-run authority."""

import asyncio
import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from workspace_service.workflow_approval_execution import (
    decide_workflow_approval,
    resume_workflow_approval,
)
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
    TEST_HANDOFF_BINDING,
)
from workspace_service.workflow_source_execution import (
    prepare_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_external_actions import WorkflowExternalActionError
from workspace_service.workflow_run_record import record_workflow_run
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    source,
    service,
)
from packages.workspace_service.tests.test_workflow_execution_continuation import order
from packages.workspace_service.tests.test_workflow_source_execution import task


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


async def setup_case(
    tmp_path,
    *,
    integration=True,
    handoff=False,
    mode="auto",
    later_failure=False,
    expires_at=None,
    review_uploads=False,
    package_artifact=None,
):
    services = service(tmp_path)
    text = source()
    original = {
        "server": "bambu-adapter",
        "tool": "transfer_package",
        "schema": "d" * 64,
    }
    text = text.replace(
        json.dumps(original),
        json.dumps(TEST_HANDOFF_BINDING if handoff else LOCAL_REVIEW_BINDING),
    )
    destination = (
        {"kind": "test", "id": "test://campaign/printer"}
        if handoff
        else LOCAL_REVIEW_DESTINATION
    )
    text = text.replace(
        json.dumps({"kind": "printer", "id": "bambu-p1s-01"}), json.dumps(destination)
    )
    text = text.replace(
        json.dumps({"material": "PLA", "profile": "0.20-standard"}),
        json.dumps(
            {"receipt_path": "outputs/attempt/receipt.json"}
            if handoff
            else {"review_task_id": "approve"}
        ),
    )
    if not handoff:
        text = text.replace('"printer_transfer"', '"local_review"').replace(
            '"transfer_only"', '"review_only"'
        )
    text = text.replace("package.json", "outputs/attempt/package.json")
    text += task(
        "after",
        fmt="text",
        save_output=True,
        output_filename="outputs/attempt/after.txt",
    )
    text += order("continue", "approve", "after")
    from workspace_service.workflow_source_execution import _parse
    from packages.workspace_service.tests.test_workflow_artifact_review import section

    sections = _parse(text)
    tool_runtime, gateway, allowed_tools = None, None, []
    if package_artifact is not None:
        from packages.workspace_service.tests.test_workflow_mcp_execution import (
            Gateway,
            TOOL,
        )
        from workspace_service.workflow_mcp_execution import (
            WorkflowMcpRuntime,
            schema_digest,
        )

        gateway = Gateway()
        call_tool = gateway.call_tool

        async def create_file(*args, **kwargs):
            target = tmp_path / "outputs/attempt/large-artifact.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package_artifact)
            return await call_tool(*args, **kwargs)

        gateway.call_tool = create_file
        tool_runtime = WorkflowMcpRuntime(
            gateway, workspace_id="ws", session_id="session"
        )
        allowed_tools = [
            {
                "server_id": TOOL.server_id,
                "name": TOOL.name,
                "schema_digest": schema_digest(TOOL),
            }
        ]
        package = next(block for block in sections if block["id"] == "package")
        package["fields"]["performed_by"] = "configured_tool"
        package["fields"]["settings"].update(
            authoring_template="mcp-tool",
            mcp_tool=TOOL.name,
            mcp_server=TOOL.server_id,
            mcp_schema_digest=schema_digest(TOOL),
            mcp_arguments=json.dumps({"query": "Create isolated test file"}),
            mcp_argument_ports="{}",
            expected_files="outputs/attempt/large-artifact.pdf",
        )
    if review_uploads:
        package = next(block for block in sections if block["id"] == "package")
        package["kind"] = "input"
        package["fields"] = {
            "name": "Uploaded requirements",
            "purpose": "Review the human upload",
            "step_type": "work",
            "provided_by": "engineer",
            "group": None,
            "inputs": [],
            "outputs": [
                {
                    "key": "uploaded_document",
                    "kind": "engineering_document",
                    "name": "Requirements",
                }
            ],
            "instructions": "Read the original upload",
            "settings": {"input_mode": "workspace-file", "workspace_file": "brief.md"},
            "tool": None,
            "reusable_step": None,
        }
        approval = next(block for block in sections if block["id"] == "approve")
        approval["fields"]["inputs"] = [
            {
                "key": "review_document",
                "kind": "engineering_document",
                "name": "Requirements",
            }
        ]
        connection = next(
            block for block in sections if block["id"] == "package_to_approval"
        )
        connection["fields"].update(
            type="item",
            **{"from": "package.uploaded_document", "to": "approve.review_document"},
        )
    text = ""
    for block in sections:
        fields = block["fields"]
        if block["kind"] == "workflow":
            fields.update(
                purpose="Approval orchestration test",
                discipline="engineering",
                reviewed_ai_suggestions=False,
            )
        if block["kind"] in {"input", "task"}:
            fields.update(purpose="Execute the declared test step", group=None)
            for port in fields.get("inputs", []) + fields.get("outputs", []):
                port.update(
                    item=None,
                    required=False,
                    quantity="one",
                    description="Test artifact",
                )
        text += section(block["kind"], block["id"], **fields)
    source_path = "workflows/example.workflow.wflow"
    (tmp_path / "workflows").mkdir()
    (tmp_path / source_path).write_text(text, encoding="utf-8", newline="")
    (tmp_path / "brief.md").write_bytes(b"Fictional human brief")

    async def read(workspace_dir, path):
        raw = (tmp_path / path).read_bytes()
        return SimpleNamespace(source=raw.decode(), storage_digest=digest(raw))

    services.workflow_sources = SimpleNamespace(read=read)
    services.workflow_integration_policies = WorkflowIntegrationPolicyService(
        str(tmp_path / "policy.db"), enabled=True
    )
    plan, inputs = await prepare_prompt_workflow(
        service=services,
        workspace_dir=str(tmp_path),
        path=source_path,
        expected_digest=digest(text.encode()),
        tool_runtime=tool_runtime,
    )
    context = None
    if integration:
        policy = services.workflow_integration_policies.enroll(
            campaign_id="campaign",
            dataset_id="dataset",
            dataset_digest="a" * 64,
            workspace_id="ws",
            source_path=source_path,
            source_digest=plan.definition_digest,
            input_files={"brief.md": digest(b"Fictional human brief")},
            output_root="outputs/attempt",
            allowed_tools=allowed_tools,
            approval_mode=mode,
            test_destinations=["test://campaign/printer"],
            expires_at=expires_at,
        )
        context = await services.workflow_integration_policies.authorize(
            policy,
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            source_path=source_path,
            source_digest=plan.definition_digest,
            plan=plan,
            tool_runtime=tool_runtime,
            files=services.files,
        )
    calls = []
    run_id = uuid4().hex

    async def generate(prompt, fmt):
        calls.append(prompt)
        if fmt == "json":
            return '{"package":"ready"}'
        if later_failure:
            raise ValueError("Provider disconnected after approval")
        return "Final generated report"

    async def execute(emit):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values=inputs,
            response_generator=generate,
            on_event=emit,
            execution_context=context,
            run_id=run_id,
            tool_runtime=tool_runtime,
        )

    result = await record_workflow_run(
        service=services,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        source_path=source_path,
        source_digest=plan.definition_digest,
        execution_context=context,
        run_id=run_id,
        required_step_ids=[s.id for s in plan.steps],
        execute=execute,
    )
    checkpoint = services.workflow_external_actions.lookup(
        result["approval"]["checkpoint_id"]
    )
    arguments = dict(
        service=services,
        workspace_id="ws",
        workspace_dir=str(tmp_path),
        checkpoint=checkpoint,
        subject_digest=checkpoint.subject_digest,
        session_id="session",
    )
    if gateway is not None:
        arguments["gateway"] = gateway
    return SimpleNamespace(
        services=services,
        context=context,
        result=result,
        checkpoint=checkpoint,
        args=arguments,
        generate=generate,
        calls=calls,
        root=tmp_path,
        tool_calls=gateway.calls if gateway else [],
    )


@pytest.mark.asyncio
async def test_first_local_review_approves_exact_upload_then_produces_real_output(
    tmp_path,
):
    case = await setup_case(tmp_path, review_uploads=True)
    assert case.calls == []
    assert case.result["outputs"] == []
    continuation = case.checkpoint.continuation
    assert continuation["completed_step_ids"] == []
    assert continuation["artifact_files"] == [
        {"path": "brief.md", "sha256": digest(b"Fictional human brief")}
    ]
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    checkpoint, result = await resume_workflow_approval(
        **case.args,
        request_id="review-original-upload",
        response_generator=case.generate,
    )
    assert result["status"] == "completed"
    assert result["run_id"] == case.result["run_id"]
    assert checkpoint.external_action["outcome"] == "dispatched"
    assert len(case.calls) == 1
    assert (
        tmp_path / "outputs/attempt/after.txt"
    ).read_text() == "Final generated report"


@pytest.mark.asyncio
async def test_changed_initial_review_upload_cannot_be_auto_approved(tmp_path):
    case = await setup_case(tmp_path, review_uploads=True)
    (tmp_path / "brief.md").write_text("Changed requirements")
    with pytest.raises(
        WorkflowExternalActionError, match="inputs or approval action changed"
    ):
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    assert case.calls == []
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )


@pytest.mark.asyncio
async def test_initial_upload_review_does_not_enable_external_transfer(tmp_path):
    with pytest.raises(
        WorkflowSourceExecutionError, match="exact source and artifact digests"
    ):
        await setup_case(tmp_path, review_uploads=True, handoff=True)
    assert not (tmp_path / "outputs/attempt/receipt.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("handoff", [False, True])
async def test_auto_resume_and_restart_retry_complete_same_run_without_replay(
    tmp_path, handoff
):
    case = await setup_case(tmp_path, handoff=handoff)
    decided = await decide_workflow_approval(
        **case.args, decision="approved", auto=True
    )
    assert decided.actor == "integration_test:campaign"
    repeated_decision = await decide_workflow_approval(
        **case.args, decision="approved", auto=True
    )
    assert decided == repeated_decision
    checkpoint, result = await resume_workflow_approval(
        **case.args, request_id="resume-1", response_generator=case.generate
    )
    assert result["status"] == "completed"
    assert result["run_id"] == case.result["run_id"]
    assert checkpoint.external_action["outcome"] == "dispatched"
    assert len(case.calls) == 2
    _, repeated = await resume_workflow_approval(
        **case.args, request_id="resume-after-restart", response_generator=case.generate
    )
    assert repeated == json.loads(json.dumps(result))
    assert len(case.calls) == 2
    record = json.loads((tmp_path / result["run_log_path"]).read_text())
    assert [event["kind"] for event in record["events"]].count("run_started") == 1
    assert [event["kind"] for event in record["events"]].count("run_resumed") == 1
    assert [event["kind"] for event in record["events"]].count("approval_decided") == 1
    assert [step["task_id"] for step in result["steps"]] == [
        "package",
        "approve",
        "after",
    ]
    if handoff:
        receipt = json.loads((tmp_path / "outputs/attempt/receipt.json").read_text())
        assert (
            receipt["integration_test"] is True and receipt["network_dispatch"] is False
        )
        assert receipt["run_id"] == result["run_id"]
        assert any(
            output["output_path"].endswith("receipt.json")
            for output in result["outputs"]
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["artifact", "source", "input", "revoked"])
async def test_changes_after_checkpoint_block_decision_and_resume_before_dispatch(
    tmp_path, change
):
    case = await setup_case(tmp_path, handoff=True)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    if change == "revoked":
        case.services.workflow_integration_policies.revoke(
            case.context["integration_policy_digest"]
        )
    else:
        path = {
            "artifact": "outputs/attempt/package.json",
            "source": "workflows/example.workflow.wflow",
            "input": "brief.md",
        }[change]
        (tmp_path / path).write_bytes(b"Changed")
    with pytest.raises((WorkflowSourceExecutionError, WorkflowExternalActionError)):
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    with pytest.raises((WorkflowSourceExecutionError, WorkflowExternalActionError)):
        await resume_workflow_approval(
            **case.args, request_id="resume", response_generator=case.generate
        )
    assert not (tmp_path / "outputs/attempt/receipt.json").exists()
    assert len(case.calls) == 1
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "approved"
    )


@pytest.mark.asyncio
async def test_auto_cannot_borrow_manual_grant_and_normal_manual_review_still_runs(
    tmp_path,
):
    case = await setup_case(tmp_path, integration=False)
    with pytest.raises(WorkflowSourceExecutionError, match="enrolled"):
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    checkpoint = await decide_workflow_approval(
        **case.args, decision="approved", reason="Reviewed exact local document"
    )
    assert checkpoint.actor == "local_workspace_user"
    _, result = await resume_workflow_approval(
        **case.args, request_id="manual", response_generator=case.generate
    )
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_failed_continuation_has_unknown_mutation_protection_on_retry(tmp_path):
    case = await setup_case(tmp_path, later_failure=True)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    with pytest.raises(WorkflowSourceExecutionError, match="Provider disconnected"):
        await resume_workflow_approval(
            **case.args, request_id="resume", response_generator=case.generate
        )
    assert len(case.calls) == 2
    with pytest.raises(WorkflowSourceExecutionError, match="cannot be replayed"):
        await resume_workflow_approval(
            **case.args, request_id="resume-retry", response_generator=case.generate
        )
    assert len(case.calls) == 2


@pytest.mark.asyncio
async def test_uncertain_handoff_is_never_dispatched_again(tmp_path):
    case = await setup_case(tmp_path, handoff=True)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    write = case.services.files.write_generated

    async def fail_receipt(workspace_dir, path, content, policy):
        if path.endswith("receipt.json"):
            raise OSError("Output host disconnected")
        return await write(workspace_dir, path, content, policy)

    case.services.files.write_generated = fail_receipt
    with pytest.raises(OSError, match="disconnected"):
        await resume_workflow_approval(
            **case.args, request_id="resume", response_generator=case.generate
        )
    checkpoint = case.services.workflow_external_actions.lookup(
        case.checkpoint.checkpoint_id
    )
    assert checkpoint.external_action["outcome"] == "outcome_unknown"
    case.services.files.write_generated = write
    with pytest.raises(WorkflowSourceExecutionError, match="no confirmed"):
        await resume_workflow_approval(
            **case.args, request_id="retry", response_generator=case.generate
        )
    assert not (tmp_path / "outputs/attempt/receipt.json").exists()
    assert len(case.calls) == 1


@pytest.mark.asyncio
async def test_preexisting_test_receipt_blocks_before_consuming_authority(tmp_path):
    case = await setup_case(tmp_path, handoff=True)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    (tmp_path / "outputs/attempt/receipt.json").write_text("Previous output")
    with pytest.raises(WorkflowSourceExecutionError, match="already exists"):
        await resume_workflow_approval(
            **case.args, request_id="resume", response_generator=case.generate
        )
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "approved"
    )
    assert len(case.calls) == 1


@pytest.mark.asyncio
async def test_auto_request_cannot_upgrade_a_manually_enrolled_policy(tmp_path):
    case = await setup_case(tmp_path, mode="manual")
    with pytest.raises(WorkflowSourceExecutionError, match="Manual campaign"):
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )


@pytest.mark.asyncio
async def test_concurrent_resume_requests_share_one_dispatch_and_continuation(tmp_path):
    case = await setup_case(tmp_path, handoff=True)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    results = await asyncio.gather(
        *(
            resume_workflow_approval(
                **case.args,
                request_id=f"request-{index}",
                response_generator=case.generate,
            )
            for index in range(2)
        )
    )
    assert results[0][0] == results[1][0]
    assert json.loads(json.dumps(results[0][1])) == json.loads(
        json.dumps(results[1][1])
    )
    assert len(case.calls) == 2
    assert len(list((tmp_path / "outputs/attempt").glob("receipt*.json"))) == 1
