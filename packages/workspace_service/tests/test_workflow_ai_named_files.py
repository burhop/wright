"""AI-created files keep exact output identities across validation and review."""

import asyncio
import hashlib
import json
from dataclasses import replace

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.process_validation.application import ValidationApplication
from workspace_service.process_validation.process import output_id
from .test_workflow_ai_task import call, done, source
from .test_workflow_mcp_execution import runtime, edge
from .test_workflow_source_execution import task
from .test_workflow_external_action_execution import service, source as approval_source
from .test_workflow_execution_continuation import authorize, order
from .test_workflow_process_validation import runtime_service, validator


@pytest.mark.parametrize("count", [17, 32, 33])
def test_complete_tool_evidence_pack_has_an_explicit_file_count_bound(count):
    files = [f"evidence-{index}.json" for index in range(count)]
    producer = task(
        "produce",
        fmt="text",
        authoring_template="mcp-task",
        mcp_server="docs",
        expected_files="\n".join(files),
    )
    if count > 32:
        with pytest.raises(WorkflowSourceExecutionError, match="maximum 32"):
            compile_prompt_workflow(source(producer))
    else:
        assert compile_prompt_workflow(source(producer)).steps[
            0
        ].expected_files == tuple(files)


def graph(*, pause=False, all_files=False, validate=False):
    producer = task(
        "produce",
        fmt="text",
        authoring_template="mcp-task",
        mcp_server="docs",
        save_output=True,
        expected_files="timeline.csv\nmetrics.json\nnotes.txt",
        expected_file_ports={"timeline": "timeline.csv", "metrics": "metrics.json"},
    )
    ports = [
        {"key": "timeline", "name": "Timeline", "kind": "workspace_file"},
        {"key": "metrics", "name": "Metrics", "kind": "workspace_file"},
    ]
    if not all_files:
        ports.append({"key": "produce_response", "name": "Summary", "kind": "text"})
    producer = producer.replace(
        '[{"key":"produce_response","kind":"engineering_document","name":"Response"}]',
        json.dumps(ports),
    )
    consumer = task("consume", fmt="text", prompt="Read measurements").replace(
        '"kind":"engineering_document"', '"kind":"workspace_file"', 1
    )
    gate = approval_source()
    gate = gate[
        gate.index("task approve") : gate.index("connection package_to_approval")
    ]
    check = validator().replace(
        '"kind":"engineering_document"', '"kind":"workspace_file"', 1
    )
    text = source(producer, gate if pause else "", check if validate else "", consumer)
    text += edge("produce.metrics", "consume.consume_prompt")
    if validate:
        text += edge("produce.metrics", "inspect.inspect_subject").replace(
            "connection link_produce_metrics", "connection inspection"
        )
        text += order("validated", "inspect", "consume")
    if pause:
        text += order("wait", "produce", "approve") + order(
            "continue", "approve", "inspect" if validate else "consume"
        )
    return replace(compile_prompt_workflow(text), definition_digest="a" * 64)


@pytest.mark.parametrize("pause", [False, True])
@pytest.mark.parametrize("all_files", [False, True])
def test_multiple_files_bind_exact_bytes_and_survive_durable_review_without_replay(
    tmp_path,
    pause,
    all_files,
):
    plan = graph(pause=pause, all_files=all_files, validate=True)
    gateway, runner = runtime()
    original_call = gateway.call_tool
    payloads = {
        "timeline.csv": b"t,x\n0,1\n",
        "metrics.json": b'{"rmse":0.25,"length_mm":100,"part_id":"demo-plate"}',
        "notes.txt": b"Support",
    }

    async def create(*args, **kwargs):
        for name, content in payloads.items():
            (tmp_path / name).write_bytes(content)
        return await original_call(*args, **kwargs)

    gateway.call_tool = create
    replies = iter([call(), done("Model summary, not file content")])
    prompts, events = [], []
    app = ValidationApplication(
        str(tmp_path / "validation.db"), "workspace", str(tmp_path)
    )

    async def decide(*args, **kwargs):
        return next(replies)

    async def generate(prompt, fmt, **kwargs):
        prompts.append(prompt)
        return "Read actual measurements"

    async def emit(event):
        events.append(event)

    async def execute(**kwargs):
        services = service(tmp_path)
        validation = runtime_service(tmp_path)
        services.db_path, services.repository = (
            validation.db_path,
            validation.repository,
        )
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=runner,
            on_event=emit,
            **kwargs,
        )

    first = asyncio.run(execute())
    for port, name in [("timeline", "timeline.csv"), ("metrics", "metrics.json")]:
        subject = app.repository.output(
            "workspace", output_id(first["run_id"], "produce", 1, port)
        )
        assert subject.locator == name
        assert subject.sha256 == hashlib.sha256(payloads[name]).hexdigest()
    if pause:
        assert not prompts and len(gateway.calls) == 1
        assert not any(event["kind"] == "validation_completed" for event in events)
        checkpoint = authorize(service(tmp_path), first)
        snapshot = json.loads(json.dumps(checkpoint["continuation"]))
        # Fresh service + JSON continuation; never replay the producer.
        final = asyncio.run(
            execute(continuation=snapshot, completed_checkpoint=checkpoint)
        )
        assert final["run_id"] == first["run_id"]
    else:
        final = first
    assert len(gateway.calls) == 1
    assert '"rmse":0.25' in prompts[0]
    assert "Model summary, not file content" not in prompts[0]
    producer = next(
        record for record in final["steps"] if record["task_id"] == "produce"
    )
    for port, name in [("timeline", "timeline.csv"), ("metrics", "metrics.json")]:
        receipt = next(
            item
            for item in producer["produced_files"]
            if item.get("output_port") == port
        )
        assert receipt["output_path"] == name
        assert receipt["sha256"] == hashlib.sha256(payloads[name]).hexdigest()
        files = [
            item
            for item in final["results"]
            if item["provenance"]["task_id"] == "produce"
            and item["provenance"]["output_port"] == port
        ]
        assert len(files) == 1
        assert files[0]["representations"][0]["location"] == name
        ready = [
            event["engineering_result"]
            for event in events
            if event["kind"] == "result_ready"
            and event["engineering_result"]["provenance"]["output_port"] == port
        ]
        assert ready and all(
            item["representations"][0]["location"] == name for item in ready
        )


@pytest.mark.parametrize("behavior", ["missing", "unchanged", "empty"])
def test_named_file_mapping_cannot_substitute_a_model_claim_for_created_files(
    tmp_path, behavior
):
    plan = graph()
    gateway, runner = runtime()
    original = gateway.call_tool
    if behavior == "unchanged":
        for name in ["timeline.csv", "metrics.json", "notes.txt"]:
            (tmp_path / name).write_text("old")

    async def create(*args, **kwargs):
        if behavior == "empty":
            for name in ["timeline.csv", "metrics.json", "notes.txt"]:
                (tmp_path / name).write_text("")
        return await original(*args, **kwargs)

    gateway.call_tool = create
    replies = iter([call(), done("All files are ready")])

    async def decide(*args, **kwargs):
        return next(replies)

    async def generate(*args, **kwargs):
        pytest.fail("Missing files must not reach the consumer")

    with pytest.raises(WorkflowSourceExecutionError, match="expected file"):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                action_generator=decide,
                tool_runtime=runner,
            )
        )
