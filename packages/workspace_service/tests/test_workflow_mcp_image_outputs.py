"""Returned MCP images remain actual, immutable files with call provenance."""

import asyncio
import base64
import json
from dataclasses import replace

import pytest

from .test_workflow_image_outputs import PNG
from .test_workflow_ai_task import call, done, source
from .test_workflow_mcp_execution import runtime
from .test_workflow_source_execution import service, task
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_mcp_images import image_observation
from workspace_service.workflow_mcp_image_outputs import (
    publish_image_outputs,
    validate_image_output_bindings,
)


def graph():
    node = task(
        "inspect",
        fmt="text",
        authoring_template="mcp-task",
        mcp_server="docs",
        mcp_task_tools=["search"],
        expected_files="capture.png",
        expected_file_ports={"capture": "capture.png"},
        mcp_image_outputs={
            "capture": {
                "tool": "search",
                "arguments": {"query": "bracket"},
                "image_index": 0,
            }
        },
    )
    return source(
        node.replace(
            '[{"key":"inspect_response","kind":"engineering_document","name":"Response"}]',
            '[{"key":"inspect_response","kind":"engineering_document","name":"Response"},'
            '{"key":"capture","kind":"workspace_file","name":"Actual capture"}]',
        )
    )


def observation():
    _, parts, evidence, errors = image_observation(
        [
            {
                "type": "image",
                "mimeType": "image/png",
                "data": base64.b64encode(PNG).decode(),
            }
        ]
    )
    assert not errors
    return dict(
        tool="docs__search",
        tool_name="search",
        arguments={"query": "bracket"},
        tool_call_number=1,
        parts=parts,
        evidence=evidence,
    )


def test_successful_tool_image_becomes_exact_output_and_retains_provenance(tmp_path):
    plan = compile_prompt_workflow(graph())
    gateway, runner = runtime()
    gateway.result = GatewayToolResult(
        content=(
            {"type": "text", "text": "Observed drawing"},
            {
                "type": "image",
                "mimeType": "image/png",
                "data": base64.b64encode(PNG).decode(),
            },
        )
    )
    replies = iter([call(), done("Actual drawing inspected")])

    async def decide(*args, **kwargs):
        return next(replies)

    events = []

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=runner,
            on_event=emit,
        )
    )
    assert (tmp_path / "capture.png").read_bytes() == PNG
    assert len(gateway.calls) == 1
    receipt = next(e for e in events if e["kind"] == "mcp_images_saved")["images"][0]
    assert receipt["tool_call_number"] == 1 and receipt["output_port"] == "capture"
    assert any(r["kind"] == "image" for r in result["results"])


@pytest.mark.parametrize(
    "variant", ["missing", "ambiguous", "changed", "existing", "wrong_format"]
)
def test_inexact_or_existing_image_is_rejected_without_overwrite(tmp_path, variant):
    step = compile_prompt_workflow(graph()).steps[0]
    observations = [observation()]
    if variant == "missing":
        observations = []
    if variant == "ambiguous":
        observations *= 2
    if variant == "changed":
        observations[0]["evidence"][0]["sha256"] = "0" * 64
    if variant == "existing":
        (tmp_path / "capture.png").write_bytes(b"prior")
    if variant == "wrong_format":
        step = replace(step, expected_file_ports={"capture": "capture.jpg"})
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            publish_image_outputs(service(tmp_path), str(tmp_path), step, observations)
        )
    assert list(tmp_path.iterdir()) == (
        [tmp_path / "capture.png"] if variant == "existing" else []
    )
    if variant == "existing":
        assert (tmp_path / "capture.png").read_bytes() == b"prior"


def test_unselected_tool_and_non_image_output_fail_compilation():
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(graph().replace('"tool": "search"', '"tool": "other"'))
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(graph().replace("capture.png", "capture.txt"))


def test_missing_group_order_is_rejected_before_a_run_can_start():
    group = 'group views\n  name: "Views"\n  purpose: "Presentation"\nend\n'
    with pytest.raises(WorkflowSourceExecutionError, match="order"):
        validate_workspace_authoring_shape(group)
    validate_workspace_authoring_shape(group.replace("end\n", "  order: 6\nend\n"))


def test_editor_scalar_roundtrip_preserves_image_selector_and_rejects_alias_paths():
    selector = {"tool": "search", "arguments": {"query": "bracket"}, "image_index": 0}
    raw = {"capture": selector}
    options = dict(
        agent_task=True, file_ports={"capture": "capture.png"}, allowed_tools=["search"]
    )
    assert validate_image_output_bindings(json.dumps(raw), **options) == raw
    with pytest.raises(WorkflowSourceExecutionError, match="JSON object"):
        validate_image_output_bindings("{bad", **options)
    with pytest.raises(WorkflowSourceExecutionError, match="distinct file path"):
        validate_image_output_bindings(
            {**raw, "other": {**selector, "arguments": {"query": "other"}}},
            **{
                **options,
                "file_ports": {"capture": "capture.png", "other": "capture.png"},
            },
        )


def test_resolved_path_aliases_fail_before_any_image_is_published(tmp_path):
    step = compile_prompt_workflow(graph()).steps[0]
    step = replace(
        step,
        expected_file_ports={"capture": "capture.png", "other": "./capture.png"},
        mcp_image_outputs={
            **step.mcp_image_outputs,
            "other": {
                "tool": "search",
                "arguments": {"query": "other"},
                "image_index": 0,
            },
        },
    )
    second = {**observation(), "arguments": {"query": "other"}, "tool_call_number": 2}
    with pytest.raises(WorkflowSourceExecutionError, match="same destination"):
        asyncio.run(
            publish_image_outputs(
                service(tmp_path), str(tmp_path), step, [observation(), second]
            )
        )
    assert list(tmp_path.iterdir()) == []
