"""Direct tools publish actual verified files through canonical output ports."""

import asyncio
import json
from dataclasses import replace

import pytest

from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import (
    mcp,
    runtime,
    edge,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    source,
    service,
    task,
)


@pytest.mark.parametrize("behavior", ["created", "missing", "stale"])
def test_direct_tool_requires_actual_new_nonempty_file_and_feeds_its_contents(
    tmp_path, behavior
):
    block = mcp(
        mcp_arguments=json.dumps({"query": "CAD geometry"}),
        mcp_argument_ports="{}",
        expected_files="design.md",
        expected_file_ports=json.dumps({"search_result": "design.md"}),
    )
    block = block.replace('"kind":"structured_result"', '"kind":"workspace_file"')
    downstream = task(
        "after", fmt="text", prompt="Read the design", save_output=True
    ).replace('"kind":"engineering_document"', '"kind":"workspace_file"', 1)
    plan = compile_prompt_workflow(
        source(block, downstream) + edge("search.search_result", "after.after_prompt")
    )
    gateway, tool_runtime = runtime()
    call = gateway.call_tool

    async def create(*args, **kwargs):
        if behavior == "created":
            (tmp_path / "design.md").write_text("Actual generated tool file")
        return await call(*args, **kwargs)

    gateway.call_tool = create
    if behavior == "stale":
        (tmp_path / "design.md").write_text("Old file")
    tool_runtime.preflight(plan.steps[0])
    prompts = []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Report"

    services = service(tmp_path)

    async def read_reference(workspace_dir, path):
        return (tmp_path / path).read_bytes()

    services.files.read_reference = read_reference

    async def execute():
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=tool_runtime,
        )

    if behavior != "created":
        with pytest.raises(WorkflowSourceExecutionError, match="expected file"):
            asyncio.run(execute())
        assert not prompts
        return
    result = asyncio.run(execute())
    assert "Actual generated tool file" in prompts[0]
    output = next(
        item for item in result["outputs"] if item["output_path"] == "design.md"
    )
    assert output["output_port"] == "search_result"
    artifact = next(item for item in result["results"] if item["name"] == "design.md")
    assert artifact["provenance"]["run_id"] == result["run_id"]
    assert artifact["provenance"]["task_id"] == "search"


def test_direct_tool_file_survives_approval_restart_without_replaying_tool(tmp_path):
    from packages.workspace_service.tests.test_workflow_external_action_execution import (
        source as approval_source,
        service as checkpoint_service,
    )
    from packages.workspace_service.tests.test_workflow_execution_continuation import (
        authorize,
        order,
    )

    block = mcp(
        mcp_arguments=json.dumps({"query": "Generate file"}),
        mcp_argument_ports="{}",
        expected_files="design.md",
        expected_file_ports={"search_result": "design.md"},
    )
    block = block.replace('"kind":"structured_result"', '"kind":"workspace_file"')
    downstream = task("after", fmt="text", prompt="Read the approved design").replace(
        '"kind":"engineering_document"', '"kind":"workspace_file"', 1
    )
    gate = approval_source()
    gate = gate[
        gate.index("task approve") : gate.index("connection package_to_approval")
    ]
    text = (
        source(block, gate, downstream)
        + edge("search.search_result", "after.after_prompt")
        + order("release", "search", "approve")
        + order("continue", "approve", "after")
    )
    plan = replace(compile_prompt_workflow(text), definition_digest="a" * 64)
    gateway, tool_runtime = runtime()
    call = gateway.call_tool

    async def create(*args, **kwargs):
        (tmp_path / "design.md").write_text("Authoritative tool-generated design")
        return await call(*args, **kwargs)

    gateway.call_tool = create
    tool_runtime.preflight(plan.steps[0])
    prompts = []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Read the real design"

    async def execute(**kwargs):
        return await execute_prompt_workflow(
            service=checkpoint_service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=tool_runtime,
            **kwargs,
        )

    first = asyncio.run(execute())
    assert len(gateway.calls) == 1 and not prompts
    checkpoint = authorize(checkpoint_service(tmp_path), first)
    snapshot = json.loads(json.dumps(checkpoint["continuation"]))
    final = asyncio.run(execute(continuation=snapshot, completed_checkpoint=checkpoint))
    assert len(gateway.calls) == 1
    assert "Authoritative tool-generated design" in prompts[0]
    assert final["run_id"] == first["run_id"]
    assert {item["output_path"] for item in final["outputs"]} == {
        "design.md",
        "after.txt",
    }
