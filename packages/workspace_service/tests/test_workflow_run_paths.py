"""Repeat a canonical process without rewriting source, UI bindings or old outputs."""

from dataclasses import replace
import hashlib
import json

import pytest

from workspace_service.workflow_run_paths import (
    TOKEN, VERSION, bind_run_paths, bind_run_input_values, reserve_run_paths,
)
from workspace_service.workflow_source_execution import (
    PromptStep, PromptWorkflow, WorkflowSourceExecutionError,
)
from workspace_service.workflow_references import WorkflowReference
from workspace_service.workflow_execution_continuation import (
    input_identities, encode_value, decode_value,
)


def plan(**changes):
    first = PromptStep(
        id="first", title="First", prompt=f"Use outputs/{TOKEN}/model.stl",
        prompt_from=None, references=(), output_format="text",
        output_path=f"outputs/{TOKEN}/report.txt", save=True, file_policy="overwrite",
        expected_files=(f"outputs/{TOKEN}/model.stl",),
        expected_file_ports={"mesh": f"outputs/{TOKEN}/model.stl"},
        arguments={"path": f"/provider/workspace/outputs/{TOKEN}/model.stl"},
        run_path_template=VERSION,
    )
    return PromptWorkflow("Reusable process", (replace(first, **changes),), {})


def test_declared_fields_resolve_before_provider_checks_without_changing_identity():
    original = plan()
    bound = bind_run_paths(original, "run-one")
    assert bound.steps[0].id == original.steps[0].id
    assert bound.steps[0].output_path == "outputs/run-one/report.txt"
    assert bound.steps[0].expected_file_ports == {"mesh": "outputs/run-one/model.stl"}
    assert bound.steps[0].arguments == {"path": "/provider/workspace/outputs/run-one/model.stl"}
    assert bound.run_path_roots == ("outputs/run-one",)
    assert TOKEN in original.steps[0].output_path
    assert bind_run_paths(bound, "run-one") == bound
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(bound, "run-two")


@pytest.mark.parametrize("identity", [None, "../other", "run/other", ".hidden", "run:ads", "run$()", "run`cmd`"])
def test_run_identity_is_a_safe_backend_path_component(identity):
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(plan(), identity)


@pytest.mark.parametrize("changes", [
    {"run_path_template": "unsupported/2"},
    {"run_path_template": ""},
    {"output_path": "outputs/shared.txt"},
    {"output_path": f"outputs/{TOKEN}/{TOKEN}/report.txt"},
    {"output_path": f"outputs/../{TOKEN}/report.txt"},
    {"prompt": "Use {{wright.secret}}"},
    {"arguments": {TOKEN: "value"}},
    {"external_action": {"destination": {"id": TOKEN}}},
])
def test_missing_unsupported_or_unsafe_declarations_fail_before_execution(changes):
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_paths(plan(**changes), "run-one")


def test_literal_legacy_process_remains_unchanged():
    original = plan(run_path_template="", prompt="Literal prompt", arguments={},
                    output_path="legacy.txt", expected_files=(), expected_file_ports={})
    assert bind_run_paths(original, None) is original


def test_only_declared_text_inputs_resolve_and_pin_template_plus_resolved_content():
    raw = f'{{"path":"outputs/{TOKEN}/model.stl"}}'.encode()
    reference = WorkflowReference.from_bytes("arguments.json", raw, image=False)
    original = replace(plan(), inputs={
        "arguments": {"settings": {"run_path_template": VERSION}},
        "literal": {"settings": {}},
    })
    bound = bind_run_paths(original, "run-one")
    values = {"arguments": reference, "literal": "Keep " + TOKEN}
    resolved = bind_run_input_values(bound, values)
    value = resolved["arguments"]
    assert value.text == '{"path":"outputs/run-one/model.stl"}'
    assert value.sha256 == hashlib.sha256(raw).hexdigest()
    assert value.resolved_sha256 == hashlib.sha256(value.text.encode()).hexdigest()
    assert value.run_path_id == "run-one"
    assert resolved["literal"] == values["literal"]
    assert input_identities(resolved) != input_identities(values)
    assert decode_value(encode_value(value)) == value
    assert bind_run_input_values(bound, resolved) == resolved
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_input_values(bound, {**resolved, "arguments": replace(value, text="Changed")})
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_input_values(bind_run_paths(original, "run-two"), resolved)


def test_binary_inputs_cannot_become_templates():
    original = replace(plan(), inputs={"arguments": {"settings": {"run_path_template": VERSION}}})
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_input_values(bind_run_paths(original, "run-one"), {
            "arguments": WorkflowReference("model.stl", "a" * 64, file_only=True),
        })


@pytest.mark.parametrize("consumer", ["file", "application", "review"])
def test_text_template_cannot_be_consumed_as_an_opaque_artifact(consumer):
    changes = {
        "file": {"file_dependencies": ("arguments.out",)},
        "application": {"application_from": "arguments.out"},
        "review": {"external_action": {"action_kind": "local_review"},
                   "references": (("arguments", "arguments.out"),)},
    }[consumer]
    template = replace(plan(**changes), inputs={"arguments": {
        "outputs": [{"key": "out"}], "settings": {"run_path_template": VERSION},
    }})
    with pytest.raises(WorkflowSourceExecutionError):
        bind_run_input_values(bind_run_paths(template, "run-one"), {
            "arguments": WorkflowReference.from_bytes("arguments.json", TOKEN.encode(), image=False),
        })


def test_resolved_template_inline_budget_counts_resolved_bytes():
    from workspace_service.workflow_source_execution import _reference_prompt_context

    raw = TOKEN.encode()
    reference = WorkflowReference.from_bytes("arguments.txt", raw, image=False)
    template = replace(plan(), inputs={"arguments": {"settings": {"run_path_template": VERSION}}})
    bound = bind_run_paths(template, "r" * 96)
    resolved = bind_run_input_values(bound, {"arguments": reference})["arguments"]
    with pytest.raises(WorkflowSourceExecutionError):
        _reference_prompt_context("Arguments", resolved, len(raw))
    context, record = _reference_prompt_context("Arguments", resolved, 96)
    assert resolved.text in context
    assert record["sha256"] == reference.sha256
    assert record["resolved_content_sha256"] == resolved.resolved_sha256


def test_namespace_reservation_is_exclusive_and_resume_uses_the_retained_directory(tmp_path):
    bound = bind_run_paths(plan(), "run-one")
    assert not (tmp_path / "outputs").exists()
    reserve_run_paths(bound, str(tmp_path), "run-one")
    prior = tmp_path / "outputs/run-one/report.txt"
    prior.write_text("Retained exact evidence")
    with pytest.raises(WorkflowSourceExecutionError):
        reserve_run_paths(bound, str(tmp_path), "run-one")
    assert prior.read_text() == "Retained exact evidence"
    reserve_run_paths(bound, str(tmp_path), "run-one", continuing=True)
    with pytest.raises(WorkflowSourceExecutionError):
        reserve_run_paths(bound, str(tmp_path), "run-two", continuing=True)
    with pytest.raises(WorkflowSourceExecutionError):
        reserve_run_paths(plan(), str(tmp_path), "run-one")
    with pytest.raises(WorkflowSourceExecutionError):
        reserve_run_paths(bind_run_paths(plan(), "run-two"), str(tmp_path), "run-two", continuing=True)


@pytest.mark.asyncio
async def test_two_actual_source_runs_share_the_accepted_process_and_preserve_first_outputs(tmp_path):
    from packages.workspace_service.tests.test_process_input_readiness import source, process
    from packages.workspace_service.tests.test_process_preparation_service import owner, scope
    from packages.workspace_service.tests.test_workflow_artifact_review import section
    from workspace_service.workflow_source_execution import _parse

    blocks = _parse(source(default="Exact requirements", later=True))
    for block in blocks:
        if block["kind"] == "task":
            settings = block["fields"]["settings"]
            settings.update(run_path_template=VERSION,
                            output_filename=f"outputs/{TOKEN}/{block['id']}.txt",
                            file_policy="overwrite")
            block["fields"]["prompt"] += f" Run path: outputs/{TOKEN}."
    text = "".join(section(block["kind"], block["id"], **block["fields"]) for block in blocks)
    reference = process(text)
    path = tmp_path / reference.source_path
    path.parent.mkdir(parents=True)
    path.write_text(text)
    application = owner(tmp_path, text)
    frozen = (await application.set_inputs(scope(), reference)).snapshot
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return f"Actual controlled result {len(calls)}"

    try:
        receipts = []
        for request in ("start-one", "start-two"):
            receipt = await application.runs.start(
                scope(), reference, frozen.snapshot_id, request,
                expected_input_digest=frozen.digest, response_generator=generate,
            )
            result = await application.runs.wait(scope(), reference, receipt.run_id)
            assert result["status"] == "completed"
            receipts.append(receipt)
        assert receipts[0].run_id != receipts[1].run_id
        assert receipts[0].process == receipts[1].process == reference
        assert receipts[0].input_digest == receipts[1].input_digest == frozen.digest
        for index, receipt in enumerate(receipts):
            assert (tmp_path / f"outputs/{receipt.run_id}/first.txt").read_text() == f"Actual controlled result {index * 2 + 1}"
            assert (tmp_path / f"outputs/{receipt.run_id}/later.txt").read_text() == f"Actual controlled result {index * 2 + 2}"
            assert receipt.run_id in calls[index * 2]
        assert path.read_text() == text
        assert len(calls) == 4
        retry = await application.runs.start(
            scope(), reference, frozen.snapshot_id, "start-one",
            expected_input_digest=frozen.digest, response_generator=generate,
        )
        assert retry == receipts[0] and len(calls) == 4
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_connected_mcp_template_is_resolved_before_checks_and_each_dispatch(tmp_path):
    from packages.workspace_service.tests.test_process_input_readiness import source, process
    from packages.workspace_service.tests.test_process_preparation_service import owner, scope
    from packages.workspace_service.tests.test_workflow_artifact_review import section
    from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL, Gateway
    from workspace_service.workflow_mcp_execution import schema_digest
    from workspace_service.workflow_source_execution import _parse

    raw = json.dumps({"query": f"Use outputs/{TOKEN}/model", "limit": 3}).encode()
    template_file = tmp_path / "arguments.json"
    template_file.write_bytes(raw)
    blocks = _parse(source(file="arguments.json"))
    for block in blocks:
        fields = block["fields"]
        if block["kind"] == "input":
            fields["settings"]["run_path_template"] = VERSION
        elif block["kind"] == "task":
            fields["performed_by"] = "configured_tool"
            fields["settings"].update(
                authoring_template="mcp-tool", mcp_tool=TOOL.name,
                mcp_server=TOOL.server_id, mcp_schema_digest=schema_digest(TOOL),
                mcp_arguments="{}", mcp_arguments_source="connection",
                mcp_arguments_input="first_in", output_format="json",
                output_filename=f"outputs/{TOKEN}/first.json",
                run_path_template=VERSION,
            )
    text = "".join(section(block["kind"], block["id"], **block["fields"]) for block in blocks)
    reference = process(text)
    source_file = tmp_path / reference.source_path
    source_file.parent.mkdir(parents=True)
    source_file.write_text(text)
    app = owner(tmp_path, text)
    gateway = Gateway()
    checked_arguments = []

    # Observe the existing schema authority, not a substitute validation path.
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
    original_validate = WorkflowMcpRuntime.validate
    from unittest.mock import patch

    def validate(runtime, step, arguments, schema):
        checked_arguments.append(dict(arguments))
        return original_validate(runtime, step, arguments, schema)

    async def unexpected_model(*args):
        pytest.fail("An exact MCP operation must not invoke a model")

    try:
        frozen = (await app.set_inputs(scope(), reference)).snapshot
        with patch.object(WorkflowMcpRuntime, "validate", validate):
            readiness = await app.check_readiness(
                scope(), reference, frozen.snapshot_id, gateway=gateway, session_id="session",
            )
            assert readiness.state == "ready", readiness.reasons
            assert checked_arguments and all(TOKEN not in value["query"] for value in checked_arguments)
            assert gateway.calls == [] and not (tmp_path / "outputs").exists()
            retained = None
            for request in ("tool-start-one", "tool-start-two"):
                receipt = await app.runs.start(
                    scope(), reference, frozen.snapshot_id, request,
                    expected_input_digest=frozen.digest, gateway=gateway, session_id="session",
                    response_generator=unexpected_model,
                )
                result = await app.runs.wait(scope(), reference, receipt.run_id)
                assert result["status"] == "completed", result
                actual_arguments = gateway.calls[-1][0][3]
                assert actual_arguments == {"query": f"Use outputs/{receipt.run_id}/model", "limit": 3}
                output = tmp_path / f"outputs/{receipt.run_id}/first.json"
                assert json.loads(output.read_text())["documents"] == [{"title": "Found"}]
                if retained:
                    assert retained[0].read_bytes() == retained[1]
                else:
                    retained = (output, output.read_bytes())
            assert len(gateway.calls) == 2
            assert source_file.read_text() == text and template_file.read_bytes() == raw
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_enrolled_local_review_resumes_same_paths_and_duplicate_never_replays(tmp_path):
    from packages.workspace_service.tests.test_workflow_approval_execution import setup_case
    from workspace_service.workflow_approval_execution import decide_workflow_approval, resume_workflow_approval

    case = await setup_case(tmp_path, run_paths=True)
    run_id = case.result["run_id"]
    first = tmp_path / f"outputs/attempt/{run_id}/package.json"
    retained = first.read_bytes()
    assert case.checkpoint.state == "pending"
    assert len(case.calls) == 1
    approved = await decide_workflow_approval(**case.args, decision="approved", auto=True)
    assert approved.actor == "integration_test:campaign"
    checkpoint, completed = await resume_workflow_approval(
        **case.args, request_id="run-path-review-resume", response_generator=case.generate,
    )
    assert completed["status"] == "completed" and completed["run_id"] == run_id
    assert checkpoint.actor == "integration_test:campaign"
    assert first.read_bytes() == retained
    assert (tmp_path / f"outputs/attempt/{run_id}/after.txt").read_text() == "Final generated report"
    assert len(case.calls) == 2
    _, repeated = await resume_workflow_approval(
        **case.args, request_id="run-path-review-after-reopen", response_generator=case.generate,
    )
    assert repeated == json.loads(json.dumps(completed)) and len(case.calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("changed_template", [False, True])
async def test_declared_file_template_resumes_after_owner_reopen_with_the_same_run_paths(tmp_path, changed_template):
    from packages.workspace_service.tests.test_process_human_input_source import human_source
    from packages.workspace_service.tests.test_process_input_supervision import waiting_case, answer, control
    from packages.workspace_service.tests.test_workflow_artifact_review import section
    from workspace_service.process_interfaces import ProcessInterfaceService
    from workspace_service.process_interfaces.errors import ProcessInterfaceError
    from workspace_service.workflow_source_execution import _parse

    raw = f'{{"scratch":"outputs/{TOKEN}"}}'.encode()
    template = tmp_path / "arguments.json"
    template.write_bytes(raw)
    blocks = _parse(human_source())
    for block in blocks:
        fields = block["fields"]
        if block["kind"] == "input":
            fields["settings"] = {"input_mode": "workspace-file", "workspace_file": "arguments.json",
                                  "run_path_template": VERSION}
        elif block["kind"] == "task" and fields.get("performed_by") == "ai_assisted":
            fields["settings"].update(run_path_template=VERSION,
                                      output_filename=f"outputs/{TOKEN}/{block['id']}.txt")
    text = "".join(section(block["kind"], block["id"], **block["fields"]) for block in blocks)
    app, reference, receipt, checkpoint, calls, generate = await waiting_case(tmp_path, text)
    assert receipt.run_id in calls[0] and TOKEN not in calls[0]
    first = tmp_path / f"outputs/{receipt.run_id}/first.txt"
    retained = first.read_bytes()
    await app.close()
    reopened = ProcessInterfaceService(app.workspace)
    app.workspace.process_interfaces = reopened
    try:
        if changed_template:
            template.write_text("Changed frozen template")
            with pytest.raises(ProcessInterfaceError):
                await answer(reopened, reference, checkpoint, generate, actor="unit-test")
            assert len(calls) == 1 and first.read_bytes() == retained
            assert reopened.human_inputs.repository.get(checkpoint.checkpoint_id).state == "pending"
            return
        response = await answer(reopened, reference, checkpoint, generate, actor="unit-test")
        completed = await reopened.runs.wait(control("unit-test"), reference, receipt.run_id)
        assert completed["status"] == "completed"
        assert response.run_id == receipt.run_id
        assert first.read_bytes() == retained
        assert (tmp_path / f"outputs/{receipt.run_id}/second.txt").is_file()
        assert template.read_bytes() == raw
        assert len(calls) == 2
        assert await answer(reopened, reference, checkpoint, generate, actor="unit-test") == response
        assert len(calls) == 2
    finally:
        await reopened.close()
