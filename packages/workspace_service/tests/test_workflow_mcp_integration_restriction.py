"""Dynamic discovery and invocation may never widen an enrolled test policy."""

from dataclasses import replace

import pytest

from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    PromptStep,
    WorkflowSourceExecutionError,
)


class Gateway:
    def __init__(self, tools):
        self.tools = tools
        self.calls = []

    def open_session(self, **kwargs):
        pass

    def initialize_session(self, *args, **kwargs):
        pass

    def list_tools(self, session_id):
        return tuple(self.tools)

    def workspace_approvals_for_model_call(self, *args):
        return {"workspace_enabled"}

    async def call_tool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return GatewayToolResult(
            content=({"type": "text", "text": "Executed"},),
            structured_content={"status": "done"},
        )


def tool(name="cad__measure", server="cad", **kwargs):
    return GatewayTool(
        name=name,
        server_id=server,
        tool_name=name.split("__")[-1],
        description="Engineering operation",
        input_schema={"type": "object"},
        **kwargs,
    )


def enrollment(item):
    return {
        "server_id": item.server_id,
        "name": item.name,
        "schema_digest": schema_digest(item),
    }


def step(item):
    return PromptStep(
        "measure",
        "Measure",
        "Measure model",
        None,
        (),
        "json",
        "result.json",
        True,
        "indexed",
        tool_name=item.name,
        server_id=item.server_id,
        schema_digest=schema_digest(item),
    )


def runtime(gateway):
    return WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="binding")


def test_default_runtime_remains_unrestricted_and_management_stays_hidden():
    items = [tool(), tool("cad__create"), tool("manage", "wright")]
    service = runtime(Gateway(items))
    assert service.tools() == tuple(items[:2])


def test_restriction_pins_copies_and_filters_later_discovery():
    allowed = tool()
    gateway = Gateway([allowed, tool("cad__start_print")])
    service = runtime(gateway)
    identities = [enrollment(allowed)]
    service.restrict_to(identities)
    identities.clear()
    gateway.tools.extend(
        [tool("supplier__buy", "supplier"), tool(allowed.name, "other")]
    )
    assert service.tools() == (allowed,)
    assert service.available()[0]["name"] == allowed.name
    assert service.task_tools(replace(step(allowed), agent_task=True)) == (allowed,)
    with pytest.raises(WorkflowSourceExecutionError):
        service.resolve(step(gateway.tools[1]))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["schema", "authority", "approvals", "operation_adapter"]
)
async def test_schema_or_authority_drift_is_rejected_even_if_step_updates(change):
    allowed = tool()
    gateway = Gateway([allowed])
    service = runtime(gateway)
    service.restrict_to([enrollment(allowed)])
    if change == "schema":
        changed = replace(
            allowed, input_schema={"type": "object", "required": ["new_field"]}
        )
    elif change == "authority":
        changed = replace(allowed, provenance={"server_revision": "new-build"})
    elif change == "approvals":
        changed = replace(allowed, required_approvals=("new_authority",))
    else:
        changed = replace(allowed, upstream_meta={"wright/operation": {"revision": 2}})
    gateway.tools = [changed]
    assert service.available() == []
    with pytest.raises(WorkflowSourceExecutionError):
        service.task_tools(replace(step(changed), agent_task=True))
    with pytest.raises(WorkflowSourceExecutionError):
        await service.call(step(changed), {})
    assert gateway.calls == []


@pytest.mark.asyncio
async def test_only_enrolled_call_dispatches_and_empty_grant_denies_everything():
    allowed, forbidden = tool(), tool("cad__create")
    gateway = Gateway([allowed, forbidden])
    service = runtime(gateway)
    service.restrict_to([enrollment(allowed)])
    await service.call(step(allowed), {})
    with pytest.raises(WorkflowSourceExecutionError):
        await service.call(step(forbidden), {})
    assert len(gateway.calls) == 1
    denied = runtime(gateway)
    denied.restrict_to([])
    assert denied.available() == []
    with pytest.raises(WorkflowSourceExecutionError):
        await denied.call(step(allowed), {})
    assert len(gateway.calls) == 1


def test_runtime_authority_cannot_be_replaced_or_widened():
    allowed, forbidden = tool(), tool("cad__create")
    service = runtime(Gateway([allowed, forbidden]))
    service.restrict_to([enrollment(allowed)])
    service.restrict_to([enrollment(allowed)])
    with pytest.raises(WorkflowSourceExecutionError):
        service.restrict_to([enrollment(allowed), enrollment(forbidden)])
    with pytest.raises(WorkflowSourceExecutionError):
        service.restrict_to(None)
    assert service.tools() == (allowed,)


@pytest.mark.asyncio
async def test_agent_decision_cannot_use_a_schema_changed_during_inference():
    allowed = tool()
    gateway = Gateway([allowed])
    service = runtime(gateway)
    service.restrict_to([enrollment(allowed)])

    async def decide(messages, schemas, **kwargs):
        assert len(schemas) == 1
        gateway.tools = [replace(allowed, provenance={"server_revision": "changed"})]
        return {
            "tool_calls": [
                {
                    "id": "call-1",
                    "function": {
                        "name": schemas[0]["function"]["name"],
                        "arguments": "{}",
                    },
                }
            ]
        }

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(WorkflowSourceExecutionError):
        await service.run_task(
            replace(step(allowed), agent_task=True), "Inspect", decide, emit
        )
    assert gateway.calls == []
