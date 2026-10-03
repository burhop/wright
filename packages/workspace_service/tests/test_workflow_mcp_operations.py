"""Digital isolated operation subjects; no physical provider is dispatched here."""

import asyncio
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import pytest
from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_approval_execution import (
    decide_workflow_approval,
    resume_workflow_approval,
)
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_mcp_operations import (
    operation_step,
    qualify_operation,
    resolved_operation_settings,
)
from workspace_service.workflow_source_execution import (
    _parse,
    _resolved_approval_settings,
    compile_prompt_workflow,
    execute_prompt_workflow,
    prepare_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_run_record import record_workflow_run
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
    source,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway


def digest(value):
    from core.process_validation import canonical_json

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


QUALIFICATION = {
    "version": 1,
    "effect": "digital",
    "destination_argument": "destination",
    "status_field": "status",
    "accepted_values": ["accepted"],
    "rejected_values": ["rejected"],
    "reference_field": "operation_id",
    "file_arguments": ["package"],
}
TOOL = GatewayTool(
    name="digital-proof__submit",
    server_id="digital-proof",
    tool_name="submit",
    description="Submit a nonphysical private digital artifact proof",
    input_schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "destination": {"type": "string"},
            "package": {"type": "string"},
        },
        "required": ["destination", "package"],
    },
    upstream_meta={"wright/approved-operation": QUALIFICATION},
)


class DigitalGateway(Gateway):
    def __init__(self, tool=TOOL):
        super().__init__()
        self.tool = tool
        self.response = {"status": "accepted", "operation_id": "digital-private-1"}
        self.is_error = False
        self.exception = None

    def list_tools(self, *args):
        return (self.tool,) if self.enabled else ()

    async def call_tool(self, *args, **kwargs):
        if kwargs.get("before_dispatch"):
            kwargs["before_dispatch"](self.tool)
        self.calls.append((args, kwargs))
        if self.exception:
            raise self.exception
        return GatewayToolResult(
            content=(), structured_content=self.response, is_error=self.is_error
        )


def configured_source(*, settings_patch=None, action_patch=None, tool=TOOL):
    blocks = _parse(source())
    blocks[0]["fields"]["name"] = "Private digital operation proof"
    approval = next(block for block in blocks if block["id"] == "approve")
    approval["fields"]["name"] = "Review the digital submission"
    approval["fields"]["instructions"] = (
        "Review the exact package and private digital destination."
    )
    approval["fields"]["inputs"] = [
        {
            "key": "submission_file",
            "kind": "workspace_file",
            "name": "Package",
        }
    ]
    config = {
        "authoring_template": "external-action-approval",
        "action_kind": "mcp-operation",
        "approval_binding": {
            "server": tool.server_id,
            "tool": tool.name,
            "schema": schema_digest(tool),
        },
        "approval_destination": {
            "kind": "digital",
            "id": "test://private/digital-proof",
        },
        "approval_settings": {
            "arguments": {"destination": "test://private/digital-proof"},
            "argument_sources": {
                "package": {
                    "source": "package.package_file",
                    "representation": "workspace_file",
                }
            },
            "destination_argument": "destination",
            "timeout_seconds": 10,
            "operation_policy": {
                "mode": "receipt",
                "qualification_digest": digest(QUALIFICATION),
                "profile_digest": None,
            },
            **(settings_patch or {}),
        },
        "approval_action": {"kind": "mcp-operation", "mode": "submit"},
        **(action_patch or {}),
    }
    approval["fields"]["settings"] = config
    policy = config["approval_settings"]["operation_policy"]
    if policy["mode"] == "observe" and "tool_bindings" not in policy:
        qualified = {
            "status": STATUS_TOOL,
            "cancel": replace(
                STATUS_TOOL,
                name="digital-proof__cancel",
                tool_name="cancel",
                annotations={"readOnlyHint": False},
            ),
        }
        policy["tool_bindings"] = {
            name: {
                "name": qualified[name].name,
                "schema": schema_digest(qualified[name]),
            }
            for key in ("status_tool", "result_tool", "cancel_tool")
            if (name := tool.upstream_meta.get("wright/operation", {}).get(key))
        }
    if config["approval_settings"].get("receipt_path"):
        approval["fields"]["outputs"] = [
            {
                "key": "submission_receipt",
                "kind": "workspace_file",
                "name": "Actual receipt",
            }
        ]
    blocks.append(
        {
            "kind": "connection",
            "id": "package_item",
            "fields": {
                "type": "item",
                "from": "package.package_file",
                "to": "approve.submission_file",
                "label": "Actual file",
                "when": None,
            },
        }
    )
    for block in blocks:
        fields = block["fields"]
        if block["kind"] == "workflow":
            fields.update(
                discipline="engineering",
                purpose="Private digital proof",
                reviewed_ai_suggestions=[],
            )
        if block["kind"] in {"input", "task"}:
            fields.update(
                purpose="Execute the declared private digital proof", group=None
            )
            for port in fields.get("inputs", []) + fields.get("outputs", []):
                port.update(
                    item=None,
                    required=False,
                    quantity="one",
                    description="Test artifact",
                )
    return "\n".join(
        section(block["kind"], block["id"], **block["fields"]) for block in blocks
    )


async def prepared_case(tmp_path, *, text=None, gateway=None, run_id=None):
    services = service(tmp_path)
    services.workflow_sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
    text = text or configured_source()
    path = "workflows/private-digital.workflow.wflow"
    document = await services.workflow_sources.create(str(tmp_path), path, text)
    gateway = gateway or DigitalGateway()
    runtime = WorkflowMcpRuntime(gateway, workspace_id="ws", session_id="session")
    plan, inputs = await prepare_prompt_workflow(
        service=services,
        workspace_dir=str(tmp_path),
        path=path,
        expected_digest=document.storage_digest,
        tool_runtime=runtime,
        run_id=run_id,
    )
    return services, plan, inputs, runtime, gateway


def test_exact_digital_subject_freezes_connected_file_and_survives_snapshot(tmp_path):
    async def run():
        services, plan, inputs, runtime, gateway = await prepared_case(tmp_path)

        async def generate(*args):
            return '{"artifact":"private digital proof"}'

        async def execute(emit):
            return await execute_prompt_workflow(
                service=services,
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values=inputs,
                response_generator=generate,
                tool_runtime=runtime,
                on_event=emit,
            )

        result = await record_workflow_run(
            service=services,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path="workflows/private-digital.workflow.wflow",
            source_digest=plan.definition_digest,
            execute=execute,
        )
        checkpoint = result["approval"]
        subject = checkpoint["subject"]
        assert checkpoint["action_kind"] == "mcp-operation"
        assert checkpoint["state"] == "pending"
        assert gateway.calls == []
        assert subject["settings"]["resolved_arguments"] == {
            "destination": "test://private/digital-proof",
            "package": "package.json",
        }
        assert subject["settings"]["argument_digest"] == digest(
            subject["settings"]["resolved_arguments"]
        )
        assert set(subject["settings"]["upstream_digests"]) == {"package.package_file"}
        assert subject["artifact_digests"] == [
            hashlib.sha256((tmp_path / "package.json").read_bytes()).hexdigest()
        ]
        restored = await _resolved_approval_settings(
            pending_action=plan.steps[-1],
            plan=plan,
            workspace_dir=str(tmp_path),
            service=services,
            continuation=checkpoint["continuation"],
        )
        assert restored == subject["settings"]
        (tmp_path / "package.json").write_text("changed", encoding="utf-8")
        with pytest.raises(
            WorkflowSourceExecutionError, match="changed before approval"
        ):
            await _resolved_approval_settings(
                pending_action=plan.steps[-1],
                plan=plan,
                workspace_dir=str(tmp_path),
                service=services,
                continuation=checkpoint["continuation"],
            )
        await runtime.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "patch",
    [
        {"timeout_seconds": 0},
        {"timeout_seconds": True},
        {"timeout_seconds": 3601},
        {"shell_command": "never allowed"},
        {
            "argument_sources": {
                "package": {"source": "other.out", "representation": "workspace_file"}
            }
        },
        {
            "argument_sources": {
                "package": {"source": "package.package_file", "representation": "guess"}
            }
        },
        {
            "arguments": {
                "destination": "test://private/digital-proof",
                "package": "unreviewed",
            }
        },
        {"operation_policy": {"mode": "receipt", "qualification_digest": "0" * 64}},
        {
            "operation_policy": {
                "mode": "observe",
                "qualification_digest": digest(QUALIFICATION),
                "profile_digest": None,
            }
        },
    ],
)
def test_invalid_operation_contract_rejected_by_compiler(patch):
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(configured_source(settings_patch=patch))


@pytest.mark.parametrize("change", ["missing", "changed", "authority", "arguments"])
def test_later_provider_preflight_blocks_before_any_upstream_model_or_dispatch(
    tmp_path, change
):
    tool = TOOL
    gateway = DigitalGateway()
    text = configured_source()
    if change == "missing":
        gateway.enabled = False
    elif change == "changed":
        tool = replace(
            TOOL,
            upstream_meta={
                "wright/approved-operation": {**QUALIFICATION, "effect": "physical"}
            },
        )
        gateway.tool = tool
    elif change == "authority":
        tool = replace(TOOL, required_approvals=("explicit-provider-authority",))
        gateway.tool = tool
        text = configured_source(tool=tool)
    else:
        text = configured_source(settings_patch={"argument_sources": {}})
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(prepared_case(tmp_path, text=text, gateway=gateway))
    assert gateway.calls == []
    assert not (tmp_path / "package.json").exists()


@pytest.mark.parametrize("effect", ["physical", "supplier"])
def test_test_authority_cannot_qualify_non_digital_provider(effect):
    metadata = {**QUALIFICATION, "effect": effect}
    tool = replace(TOOL, upstream_meta={"wright/approved-operation": metadata})
    text = configured_source(
        tool=tool,
        settings_patch={
            "operation_policy": {
                "mode": "receipt",
                "qualification_digest": digest(metadata),
                "profile_digest": None,
            }
        },
    )
    step = compile_prompt_workflow(text).steps[-1]
    gateway = DigitalGateway(tool)
    runtime = WorkflowMcpRuntime(gateway, workspace_id="ws", session_id="session")
    with pytest.raises(WorkflowSourceExecutionError, match="test authority"):
        qualify_operation(runtime, step, integration=True)
    assert gateway.calls == []


def test_submission_metadata_is_part_of_existing_schema_identity():
    changed = replace(
        TOOL,
        upstream_meta={
            "wright/approved-operation": {
                **QUALIFICATION,
                "accepted_values": ["different"],
            }
        },
    )
    assert schema_digest(changed) != schema_digest(TOOL)


@pytest.mark.parametrize(
    "representation, supplied, expected",
    [
        ("json", '{"option":"explicit"}', {"option": "explicit"}),
        ("json", {"option": "explicit"}, {"option": "explicit"}),
        ("text", "explicit option", "explicit option"),
    ],
)
def test_connected_document_arguments_are_explicit_and_detached(
    tmp_path, representation, supplied, expected
):
    step = compile_prompt_workflow(
        configured_source(
            settings_patch={
                "argument_sources": {
                    "package": {
                        "source": "package.package_file",
                        "representation": representation,
                    },
                }
            }
        )
    ).steps[-1]
    settings = asyncio.run(
        resolved_operation_settings(
            step,
            {"package.package_file": supplied},
            service=SimpleNamespace(),
            workspace_dir=str(tmp_path),
        )
    )
    assert settings["resolved_arguments"]["package"] == expected
    if isinstance(supplied, dict):
        supplied["option"] = "mutated"
        assert settings["resolved_arguments"]["package"] == {"option": "explicit"}
    assert operation_step(step).tool_name == TOOL.name


def test_enrolled_exact_digital_operation_records_test_actor_and_receipt(tmp_path):
    async def run():
        text = configured_source().replace(
            '"package.json"', '"outputs/private/package.json"'
        )
        services, checkpoint, gateway, generate, models, initial = await approved_case(
            tmp_path, text=text, integration=True
        )
        assert checkpoint.actor == "integration_test:083-private-unit"
        completed = await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert completed["run_id"] == initial["run_id"]
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.external_action["evidence"]["integration_test"] is True
        assert stored.external_action["evidence"]["effect"] == "digital"
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


def test_enrolled_test_policy_cannot_authorize_actual_physical_qualification(tmp_path):
    metadata = {**QUALIFICATION, "effect": "physical"}
    tool = replace(TOOL, upstream_meta={"wright/approved-operation": metadata})
    text = configured_source(
        tool=tool,
        settings_patch={
            "operation_policy": {
                "mode": "receipt",
                "qualification_digest": digest(metadata),
                "profile_digest": None,
            }
        },
    ).replace('"package.json"', '"outputs/private/package.json"')
    gateway = DigitalGateway(tool)
    with pytest.raises(WorkflowSourceExecutionError, match="test authority"):
        asyncio.run(
            approved_case(tmp_path, text=text, gateway=gateway, integration=True)
        )
    assert gateway.calls == []
    assert not (tmp_path / "outputs/private/package.json").exists()


def test_destination_must_match_reviewed_actual_argument(tmp_path):
    with pytest.raises(WorkflowSourceExecutionError, match="destination differs"):
        compile_prompt_workflow(
            configured_source(
                settings_patch={
                    "arguments": {
                        "destination": "test://other",
                        "package": "package.json",
                    },
                    "argument_sources": {},
                }
            )
        )


async def approved_case(tmp_path, *, gateway=None, text=None, integration=False, run_id=None):
    services, plan, inputs, runtime, gateway = await prepared_case(
        tmp_path, gateway=gateway, text=text, run_id=run_id
    )
    context = None
    if integration:
        from workspace_service.workflow_integration_policy import (
            WorkflowIntegrationPolicyService,
        )

        services.workflow_integration_policies = WorkflowIntegrationPolicyService(
            str(tmp_path / "policy.db"), enabled=True
        )
        staged = (
            b'{"integration_test":true,"purpose":"nonphysical operation unit proof"}'
        )
        (tmp_path / "private-input.json").write_bytes(staged)
        allowed = [
            {
                "server_id": tool["server_id"],
                "name": tool["name"],
                "schema_digest": tool["schema_digest"],
            }
            for tool in runtime.available()
        ]
        policy = services.workflow_integration_policies.enroll(
            campaign_id="083-private-unit",
            dataset_id="nonphysical-operation",
            dataset_digest=hashlib.sha256(staged).hexdigest(),
            workspace_id="ws",
            source_path="workflows/private-digital.workflow.wflow",
            source_digest=plan.definition_digest,
            input_files={"private-input.json": hashlib.sha256(staged).hexdigest()},
            output_root="outputs/private",
            allowed_tools=allowed,
            approval_mode="auto",
            test_destinations=["test://private/digital-proof"],
        )
        runtime.restrict_to(allowed)
        context = await services.workflow_integration_policies.authorize(
            policy,
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            source_path="workflows/private-digital.workflow.wflow",
            source_digest=plan.definition_digest,
            plan=plan,
            tool_runtime=runtime,
            files=services.files,
        )
    models = []

    async def generate(*args):
        models.append(args)
        return '{"artifact":"private digital proof"}'

    async def execute(emit):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values=inputs,
            response_generator=generate,
            tool_runtime=runtime,
            on_event=emit,
            execution_context=context,
            run_id=run_id,
        )

    result = await record_workflow_run(
        service=services,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        source_path="workflows/private-digital.workflow.wflow",
        source_digest=plan.definition_digest,
        execute=execute,
        execution_context=context,
        run_id=run_id,
    )
    checkpoint = services.workflow_external_actions.get(
        result["approval"]["checkpoint_id"],
        workspace_id="ws",
        run_id=result["run_id"],
    )
    decided = await decide_workflow_approval(
        service=services,
        workspace_id="ws",
        workspace_dir=str(tmp_path),
        checkpoint=checkpoint,
        subject_digest=checkpoint.subject_digest,
        decision="approved",
        auto=integration,
        gateway=gateway,
        session_id="session",
    )
    await runtime.close()
    return services, decided, gateway, generate, models, result


async def dispatch(
    tmp_path,
    services,
    checkpoint,
    gateway,
    generate,
    *,
    request_id="private-dispatch-1",
    on_event=None,
):
    _, result = await resume_workflow_approval(
        service=services,
        workspace_id="ws",
        workspace_dir=str(tmp_path),
        checkpoint=checkpoint,
        subject_digest=checkpoint.subject_digest,
        request_id=request_id,
        gateway=gateway,
        session_id="session",
        response_generator=generate,
        on_event=on_event,
    )
    return result


def test_qualified_digital_submission_and_duplicate_resume_never_repeat_effect(
    tmp_path,
):
    async def run():
        services, checkpoint, gateway, generate, models, initial = await approved_case(
            tmp_path
        )
        completed = await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert completed["run_id"] == initial["run_id"]
        assert completed["status"] == "completed"
        assert len(models) == 1
        assert len(gateway.calls) == 1
        args, kwargs = gateway.calls[0]
        assert args[2] == TOOL.name
        assert args[3] == {
            "destination": "test://private/digital-proof",
            "package": "package.json",
        }
        assert kwargs["workspace_approvals"] == {"workspace_enabled"}
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        evidence = stored.external_action["evidence"]
        assert stored.state == "consumed"
        assert stored.external_action["outcome"] == "dispatched"
        assert evidence["submission"] == "accepted"
        assert evidence["provider_reference"] == "digital-private-1"
        assert evidence["observed_outcome"] is None
        assert evidence["delivery_completed"] is True
        assert evidence["replay_permitted"] is False
        duplicate = await dispatch(tmp_path, services, stored, gateway, generate)
        assert duplicate["run_id"] == completed["run_id"]
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


@pytest.mark.parametrize("is_error", [False, True])
def test_qualified_rejection_retained_and_never_replayed(tmp_path, is_error):
    async def run():
        gateway = DigitalGateway()
        gateway.response = {"status": "rejected", "operation_id": None}
        gateway.is_error = is_error
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=gateway
        )
        with pytest.raises(WorkflowSourceExecutionError) as failure:
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert failure.value.code == "WORKFLOW_MCP_OPERATION_REJECTED"
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.external_action["outcome"] == "not_dispatched"
        assert stored.external_action["evidence"]["submission"] == "rejected"
        with pytest.raises(WorkflowSourceExecutionError):
            await dispatch(
                tmp_path, services, stored, gateway, generate, request_id="another-id"
            )
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "outcome",
    ["timeout", "disconnect", "unknown_status", "no_reference", "unqualified_error"],
)
def test_uncertain_submission_retains_consumption_and_blocks_repeat(tmp_path, outcome):
    async def run():
        gateway = DigitalGateway()
        if outcome == "timeout":
            gateway.exception = TimeoutError("private transient details")
        elif outcome == "disconnect":
            gateway.exception = ConnectionError("private transient details")
        elif outcome == "unknown_status":
            gateway.response = {"status": "maybe", "operation_id": "digital-private-1"}
        elif outcome == "no_reference":
            gateway.response = {"status": "accepted"}
        else:
            gateway.is_error = True
            gateway.response = {"message": "error after possible effect"}
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=gateway
        )
        with pytest.raises(WorkflowSourceExecutionError) as failure:
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert failure.value.code == "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN"
        assert "private transient" not in str(failure.value)
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.external_action["outcome"] == "outcome_unknown"
        assert stored.external_action["evidence"]["replay_permitted"] is False
        with pytest.raises(WorkflowSourceExecutionError):
            await dispatch(
                tmp_path, services, stored, gateway, generate, request_id="another-id"
            )
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


PROFILE = {
    "version": 1,
    "status_tool": "status",
    "id_field": "operation_id",
    "id_argument": "operation_id",
    "status_field": "job_state",
    "poll_seconds": 0.05,
}
STATUS_TOOL = GatewayTool(
    name="digital-proof__status",
    server_id="digital-proof",
    tool_name="status",
    description="Read exact private operation",
    annotations={"readOnlyHint": True},
    input_schema={
        "type": "object",
        "properties": {"operation_id": {"type": "string"}},
        "required": ["operation_id"],
        "additionalProperties": False,
    },
)


class ObservedGateway(DigitalGateway):
    def __init__(self):
        super().__init__(
            replace(
                TOOL, upstream_meta={**TOOL.upstream_meta, "wright/operation": PROFILE}
            )
        )
        self.observations = 0
        self.status_failure = False

    def list_tools(self, *args):
        return (self.tool, getattr(self, "status_definition", STATUS_TOOL))

    async def call_tool(self, *args, **kwargs):
        if args[2] == STATUS_TOOL.name:
            self.calls.append((args, kwargs))
            if self.status_failure:
                raise ConnectionError("lost provider status")
            self.observations += 1
            return GatewayToolResult(
                content=(),
                structured_content={
                    "operation_id": "digital-private-1",
                    "job_state": "working" if self.observations == 1 else "completed",
                    "result": {"digital_proof": "done"},
                },
            )
        return await super().call_tool(*args, **kwargs)


def observation_source(gateway):
    return configured_source(
        tool=gateway.tool,
        settings_patch={
            "operation_policy": {
                "mode": "observe",
                "qualification_digest": digest(QUALIFICATION),
                "profile_digest": digest(PROFILE),
            }
        },
    )


def test_accepted_receipt_precedes_actual_observed_completion(tmp_path):
    async def run():
        gateway = ObservedGateway()
        services, checkpoint, gateway, generate, models, initial = await approved_case(
            tmp_path,
            gateway=gateway,
            text=observation_source(gateway),
        )
        events = []

        async def event(data):
            if data["kind"] != "operation_progress":
                return
            events.append((data["kind"], data))
            stored = services.workflow_external_actions.get(
                checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
            )
            assert stored.external_action["evidence"]["submission"] == "accepted"
            assert stored.external_action["evidence"]["observed_outcome"] is None

        completed = await dispatch(
            tmp_path, services, checkpoint, gateway, generate, on_event=event
        )
        assert completed["run_id"] == initial["run_id"]
        assert [data["state"] for _, data in events] == [
            "submitted",
            "working",
            "completed",
            "results_collected",
        ]
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.external_action["evidence"]["observed_outcome"] == "completed"
        raw = json.loads(
            await services.files.read_reference(str(tmp_path), initial["run_log_path"])
        )
        assert [
            event["state"]
            for event in raw["events"]
            if event["kind"] == "operation_progress"
        ] == ["submitted", "working", "completed", "results_collected"]
        assert [call[0][2] for call in gateway.calls] == [
            TOOL.name,
            STATUS_TOOL.name,
            STATUS_TOOL.name,
        ]
        assert len(models) == 1

    asyncio.run(run())


def test_monitor_disconnect_keeps_acceptance_but_cannot_release_or_resubmit(tmp_path):
    async def run():
        gateway = ObservedGateway()
        gateway.status_failure = True
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=gateway, text=observation_source(gateway)
        )
        with pytest.raises(ConnectionError):
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.external_action["outcome"] == "dispatched"
        assert stored.external_action["evidence"]["submission"] == "accepted"
        assert stored.external_action["evidence"]["observed_outcome"] == "unknown"
        assert stored.external_action["evidence"]["delivery_completed"] is False
        with pytest.raises(WorkflowSourceExecutionError):
            await dispatch(tmp_path, services, stored, gateway, generate)
        assert [call[0][2] for call in gateway.calls].count(TOOL.name) == 1
        assert len(models) == 1

    asyncio.run(run())


def test_observation_schema_changes_cannot_acquire_dispatch_authority(tmp_path):
    async def run():
        gateway = ObservedGateway()
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=gateway, text=observation_source(gateway)
        )
        gateway.status_definition = replace(
            STATUS_TOOL,
            input_schema={
                **STATUS_TOOL.input_schema,
                "description": "Changed exact status schema",
            },
        )
        with pytest.raises(WorkflowSourceExecutionError, match="tool changed"):
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.state == "approved" and stored.external_action is None
        assert gateway.calls == [] and len(models) == 1

    asyncio.run(run())


def test_gateway_dispatch_hook_rechecks_artifact_after_consumption(tmp_path):
    class RacingGateway(DigitalGateway):
        async def call_tool(self, *args, **kwargs):
            (tmp_path / "package.json").write_text(
                "changed at gateway boundary", encoding="utf-8"
            )
            return await super().call_tool(*args, **kwargs)

    async def run():
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=RacingGateway()
        )
        with pytest.raises(WorkflowSourceExecutionError) as failure:
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert failure.value.code == "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN"
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.state == "consumed"
        assert stored.external_action["outcome"] == "outcome_unknown"
        assert gateway.calls == [] and len(models) == 1

    asyncio.run(run())


def test_real_gateway_runs_final_file_guard_after_lifecycle_before_provider(tmp_path):
    from packages.tool_registry.tests.test_gateway_service import (
        service as gateway_service,
    )
    from tool_registry.gateway_models import GatewayError
    from workspace_service.workflow_approval_execution import _operation_dispatch_check

    async def run():
        gateway, lifecycle, _ = gateway_service()
        tool = gateway.list_tools("s1")[0]
        workflow = tmp_path / "accepted.workflow.wflow"
        workflow.write_bytes(b"exact source")
        artifact = tmp_path / "actual-package.json"
        artifact.write_bytes(b"exact actual artifact")
        checkpoint = SimpleNamespace(
            subject={
                "binding": {
                    "server": tool.server_id,
                    "tool": tool.name,
                    "schema": schema_digest(tool),
                },
                "definition_digest": hashlib.sha256(workflow.read_bytes()).hexdigest(),
            },
            workflow_id=workflow.name,
            continuation={
                "artifact_files": [
                    {
                        "path": artifact.name,
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    }
                ]
            },
        )

        async def start(*args, **kwargs):
            artifact.write_bytes(b"changed while application starts")

        lifecycle.ensure_started = start
        with pytest.raises(GatewayError):
            await gateway.call_tool(
                "s1",
                "final-guard",
                tool.name,
                {},
                before_dispatch=_operation_dispatch_check(checkpoint, str(tmp_path)),
            )
        assert lifecycle.calls == []

    asyncio.run(run())


def test_actual_receipt_file_is_bound_to_same_run_and_provider_reference(tmp_path):
    async def run():
        text = configured_source(
            settings_patch={"receipt_path": "receipts/digital.json"}
        )
        services, checkpoint, gateway, generate, models, initial = await approved_case(
            tmp_path, text=text
        )
        completed = await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert completed["run_id"] == initial["run_id"]
        raw = (tmp_path / "receipts/digital.json").read_bytes()
        receipt = json.loads(raw)
        assert receipt["provider_reference"] == "digital-private-1"
        assert receipt["subject_digest"] == checkpoint.subject_digest
        assert receipt["submission"] == "accepted"
        assert receipt["observed_outcome"] is None
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        produced = stored.external_action["evidence"]["produced_files"][0]
        assert produced["sha256"] == hashlib.sha256(raw).hexdigest()
        typed = [
            result
            for result in completed["results"]
            if result["artifact_role"] == "external_action_receipt"
        ]
        assert len(typed) == 1
        assert typed[0]["provenance"]["task_id"] == "approve"
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


@pytest.mark.parametrize("change", ["schema", "artifact"])
def test_approved_action_currentness_is_rechecked_before_consumption(tmp_path, change):
    async def run():
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path
        )
        if change == "schema":
            gateway.tool = replace(
                TOOL, description="Changed", input_schema={"type": "object"}
            )
        else:
            (tmp_path / "package.json").write_text("changed", encoding="utf-8")
        with pytest.raises(WorkflowSourceExecutionError):
            await dispatch(tmp_path, services, checkpoint, gateway, generate)
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        assert stored.state == "approved"
        assert stored.external_action is None
        assert gateway.calls == [] and len(models) == 1

    asyncio.run(run())


def test_finite_decimal_arguments_are_exactly_pinned_and_dispatched(tmp_path):
    async def run():
        tool = replace(
            TOOL,
            input_schema={
                **TOOL.input_schema,
                "properties": {
                    **TOOL.input_schema["properties"],
                    "width": {"type": "number"},
                },
            },
        )
        text = configured_source(
            tool=tool,
            settings_patch={
                "arguments": {
                    "destination": "test://private/digital-proof",
                    "width": 12.5,
                }
            },
        )
        gateway = DigitalGateway(tool)
        services, checkpoint, gateway, generate, models, _ = await approved_case(
            tmp_path, gateway=gateway, text=text
        )
        assert checkpoint.subject["settings"]["resolved_arguments"]["width"] == 12.5
        await dispatch(tmp_path, services, checkpoint, gateway, generate)
        assert gateway.calls[0][0][3]["width"] == 12.5
        assert len(gateway.calls) == len(models) == 1

    asyncio.run(run())


@pytest.mark.parametrize(
    "args, code",
    [
        ({"password": "never-persist"}, "approval_subject_sensitive"),
        ({"width": float("nan")}, "approval_subject_invalid"),
        ({"width": float("inf")}, "approval_subject_invalid"),
    ],
)
def test_sensitive_or_nonfinite_arguments_are_rejected_before_upstream(args, code):
    from workspace_service.workflow_external_actions import WorkflowExternalActionError

    with pytest.raises(WorkflowExternalActionError) as failure:
        compile_prompt_workflow(
            configured_source(
                settings_patch={
                    "arguments": {"destination": "test://private/digital-proof", **args}
                }
            )
        )
    assert failure.value.code == code


def test_confirmed_cancellation_is_distinct_from_accepted_submission(
    tmp_path, monkeypatch
):
    from workspace_service import workflow_async_operations as operations

    cancel_profile = {**PROFILE, "cancel_tool": "cancel", "cancel_confirm_seconds": 0.2}
    cancel_tool = replace(
        STATUS_TOOL,
        name="digital-proof__cancel",
        tool_name="cancel",
        annotations={"readOnlyHint": False},
    )

    class CancelGateway(ObservedGateway):
        def __init__(self):
            super().__init__()
            self.tool = replace(
                TOOL,
                upstream_meta={
                    **TOOL.upstream_meta,
                    "wright/operation": cancel_profile,
                },
            )
            self.cancelled = False

        def list_tools(self, *args):
            return (self.tool, STATUS_TOOL, cancel_tool)

        async def call_tool(self, *args, **kwargs):
            if args[2] == cancel_tool.name:
                self.calls.append((args, kwargs))
                self.cancelled = True
                return GatewayToolResult(
                    content=(), structured_content={"request": "accepted"}
                )
            if args[2] == STATUS_TOOL.name:
                self.calls.append((args, kwargs))
                return GatewayToolResult(
                    content=(),
                    structured_content={
                        "operation_id": "digital-private-1",
                        "job_state": "cancelled" if self.cancelled else "working",
                    },
                )
            return await super().call_tool(*args, **kwargs)

    holder = {}
    monitor = operations.monitor_operation

    async def capture(runtime, *args, **kwargs):
        holder["runtime"] = runtime
        return await monitor(runtime, *args, **kwargs)

    monkeypatch.setattr(operations, "monitor_operation", capture)

    async def run():
        gateway = CancelGateway()
        text = configured_source(
            tool=gateway.tool,
            settings_patch={
                "operation_policy": {
                    "mode": "observe",
                    "qualification_digest": digest(QUALIFICATION),
                    "profile_digest": digest(cancel_profile),
                }
            },
        )
        services, checkpoint, gateway, generate, models, initial = await approved_case(
            tmp_path, gateway=gateway, text=text
        )
        states = []

        async def event(data):
            if data["kind"] == "operation_progress":
                states.append(data["state"])
                if data["state"] == "working":
                    target = operations.operation_cancellation(
                        holder["runtime"], reserve=True
                    )
                    assert target is not None
                    target.activate()  # Explicit synthetic test request, no hardware.

        with pytest.raises(asyncio.CancelledError):
            await dispatch(
                tmp_path, services, checkpoint, gateway, generate, on_event=event
            )
        stored = services.workflow_external_actions.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id=checkpoint.run_id
        )
        evidence = stored.external_action["evidence"]
        assert evidence["submission"] == "accepted"
        assert evidence["observed_outcome"] == "cancelled"
        assert evidence["cancellation_requested"] is True
        assert evidence["cancellation_outcome"] == "cancelled"
        assert evidence["delivery_completed"] is False
        assert states == ["submitted", "working", "cancellation_requested", "cancelled"]
        raw = json.loads(
            await services.files.read_reference(str(tmp_path), initial["run_log_path"])
        )
        assert raw["status"] == "cancelled"
        with pytest.raises(WorkflowSourceExecutionError):
            await dispatch(tmp_path, services, stored, gateway, generate)
        assert [call[0][2] for call in gateway.calls].count(TOOL.name) == 1
        assert len(models) == 1

    asyncio.run(run())
