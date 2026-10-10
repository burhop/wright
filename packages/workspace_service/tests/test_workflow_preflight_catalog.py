"""Preparation shares discovery within one synchronous batch, never a grant."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _preflight_tools,
    compile_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import (
    Gateway,
    TOOL,
    mcp,
    source,
)


class CountingGateway(Gateway):
    def __init__(self):
        super().__init__()
        self.observations = 0
        self.tool = TOOL

    def list_tools(self, *args):
        self.observations += 1
        return (self.tool,) if self.enabled else ()


def prepared_runtime():
    gateway = CountingGateway()
    runtime = WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="test")
    step = replace(
        compile_prompt_workflow(source(mcp())).steps[0],
        argument_sources={"query": "source.text"},
    )
    return gateway, runtime, step


def test_many_steps_and_connected_values_use_one_authorized_catalog():
    gateway, runtime, step = prepared_runtime()
    runtime.preflight_many((step,) * 20, responses={"source.text": "design brief"})
    assert gateway.observations == 1
    assert runtime._preflight_catalog is None
    assert gateway.calls == []
    runtime.preflight_many((step,))
    assert gateway.observations == 2


@pytest.mark.parametrize("change", ["disabled", "schema", "authority"])
@pytest.mark.asyncio
async def test_dispatch_rechecks_changes_after_preparation(change):
    gateway, runtime, step = prepared_runtime()
    runtime.preflight_many((step,))
    if change == "disabled":
        gateway.enabled = False
    elif change == "schema":
        gateway.tool = replace(TOOL, input_schema={"type": "object"})
    else:
        gateway.tool = replace(TOOL, provenance={"server_revision": "changed"})
    with pytest.raises(WorkflowSourceExecutionError):
        await runtime.call(step, {"query": "design brief", "limit": 3})
    assert gateway.observations == 2
    assert gateway.calls == []


def test_failed_batch_does_not_retain_catalog_or_skip_later_checks():
    gateway, runtime, step = prepared_runtime()
    invalid = replace(step, schema_digest="0" * 64)
    with pytest.raises(WorkflowSourceExecutionError):
        runtime.preflight_many((step, invalid))
    assert runtime._preflight_catalog is None
    gateway.enabled = False
    with pytest.raises(WorkflowSourceExecutionError):
        runtime.preflight_many((step,))
    assert gateway.observations == 2
    assert gateway.calls == []


def test_batch_preserves_integration_tool_restrictions():
    gateway, runtime, step = prepared_runtime()
    runtime.restrict_to(
        [
            {
                "server_id": TOOL.server_id,
                "name": TOOL.name,
                "schema_digest": schema_digest(TOOL),
            }
        ]
    )
    runtime.preflight_many((step,))
    gateway.tool = replace(TOOL, provenance={"server_revision": "changed"})
    with pytest.raises(WorkflowSourceExecutionError):
        runtime.preflight_many((step,))
    assert gateway.observations == 2


def test_batch_still_rejects_invalid_connected_values():
    gateway, runtime, step = prepared_runtime()
    step = replace(step, argument_sources={"query": "source.text"})
    with pytest.raises(WorkflowSourceExecutionError):
        runtime.preflight_many((step,), responses={"source.text": "x"})
    assert gateway.observations == 1
    assert gateway.calls == []


def test_source_preflight_keeps_separately_supplied_adapter_contract():
    _, _, step = prepared_runtime()
    calls = []
    runtime = SimpleNamespace(
        preflight=lambda value: calls.append(("definition", value.id)),
        preflight_values=lambda value, responses: calls.append(("values", responses)),
    )
    _preflight_tools(runtime, (step,), responses={"source.text": "design brief"})
    assert calls == [
        ("definition", step.id),
        ("values", {"source.text": "design brief"}),
    ]


def test_source_uses_native_batch_without_catalog_for_non_tool_steps():
    gateway, runtime, step = prepared_runtime()
    _preflight_tools(runtime, (replace(step, tool_name=None, agent_task=False),))
    assert gateway.observations == 0
    _preflight_tools(runtime, (step,) * 20, responses={})
    assert gateway.observations == 1
