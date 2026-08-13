from __future__ import annotations

import pytest

from model_registry.gateway_provider import EngineeringModelGatewayProvider
from tool_registry.gateway_models import GatewayError, GatewaySessionContext


def session(workspace_id="workspace-one"):
    return (
        GatewaySessionContext(
            session_id="session-one",
            principal_id="principal-one",
            workspace_id=workspace_id,
            workspace_path="/workspace",
            transport="legacy",
        )
        .initialized(
            protocol_version="2025-11-25",
            client_name="test",
            client_version="1",
            client_capabilities={},
        )
        .activate()
    )


def descriptor(**changes):
    value = {
        "model_id": "wright-affine-test",
        "task_id": "predict",
        "description": "Apply a deterministic affine transform. Limitation: test only.",
        "input_schema": {
            "type": "object",
            "required": ["x"],
            "properties": {"x": {"type": "number"}},
            "additionalProperties": False,
        },
        "output_schema": {
            "type": "object",
            "required": ["y"],
            "properties": {"y": {"type": "number"}},
            "additionalProperties": False,
        },
        "workspace_id": "workspace-one",
        "binding_id": "binding-one",
        "binding_digest": "a" * 64,
        "binding_state": "enabled",
        "installation_id": "installation-one",
        "installation_digest": "b" * 64,
        "installation_state": "ready",
        "adapter_id": "wright-deterministic",
        "adapter_version": "1.0.0",
        "evidence_id": "evidence-one",
        "evidence_state": "passed",
        "material_digest": "c" * 64,
        "policy_snapshot_digest": "d" * 64,
        "policy_current": True,
    }
    value.update(changes)
    return value


class Application:
    def __init__(self):
        self.values = [descriptor()]
        self.calls = []
        self.cancelled = []
        self.closed = []
        self.stopped = False

    def declared_model_tool_names(self):
        return frozenset({"wright_model__wright_affine_test__predict"})

    def discover_model_capabilities(self, *, principal_id, workspace_id, session_id):
        return tuple(self.values)

    async def invoke_model_capability(self, **values):
        self.calls.append(values)
        return {"structuredContent": {"y": values["arguments"]["x"] * 2 + 1}}

    async def cancel_model_request(self, *, session_id, request_id):
        self.cancelled.append((session_id, request_id))

    async def close_model_session(self, *, session_id):
        self.closed.append(session_id)

    async def shutdown_model_runtime(self):
        self.stopped = True


def test_exact_ready_enabled_binding_projects_a_typed_base_tool_contract() -> None:
    application = Application()
    provider = EngineeringModelGatewayProvider(application)

    tools = provider.tools(session())

    assert provider.provider_id == "engineering-models"
    assert provider.declared_tool_names == frozenset(
        {"wright_model__wright_affine_test__predict"}
    )
    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "wright_model__wright_affine_test__predict"
    assert tool.server_id == "wright-models"
    assert tool.input_schema["required"] == ["x"]
    assert tool.output_schema["required"] == ["y"]
    assert tool.annotations["readOnlyHint"] is True
    assert tool.annotations["model"]["adapter_version"] == "1.0.0"
    assert tool.provenance == {
        "server_revision": "b" * 64,
        "capability_digest": "a" * 64,
        "validation_evidence_id": "evidence-one",
        "binding_digest": "a" * 64,
        "installation_digest": "b" * 64,
        "material_evidence_digest": "c" * 64,
        "policy_snapshot_digest": "d" * 64,
    }
    assert "command" not in repr(tool)
    assert "endpoint" not in repr(tool)


@pytest.mark.parametrize(
    "change",
    [
        {"workspace_id": "workspace-two"},
        {"binding_state": "disabled"},
        {"binding_state": "stale"},
        {"installation_state": "unhealthy"},
        {"evidence_state": "failed"},
        {"policy_current": False},
        {"binding_digest": "bad"},
        {"task_id": "start-spindle"},
    ],
)
def test_cross_workspace_disabled_stale_unhealthy_or_invalid_bindings_are_hidden(
    change,
) -> None:
    application = Application()
    application.values = [descriptor(**change)]
    provider = EngineeringModelGatewayProvider(application)
    assert provider.tools(session()) == ()


@pytest.mark.asyncio
async def test_call_re_resolves_exact_identity_and_forwards_runtime_progress() -> None:
    application = Application()
    provider = EngineeringModelGatewayProvider(application)
    context = session()
    tool = provider.tools(context)[0]
    progress = []

    result = await provider.call(
        context,
        tool,
        {"x": 2},
        request_id="request-one",
        approval_context={"workspace_id": "workspace-one"},
        progress_callback=lambda event: progress.append(event),
    )

    assert result == {"structuredContent": {"y": 5}}
    assert application.calls[0]["binding_digest"] == "a" * 64
    assert application.calls[0]["request_id"] == "request-one"


@pytest.mark.asyncio
async def test_toctou_binding_change_fails_before_runtime_invocation() -> None:
    application = Application()
    provider = EngineeringModelGatewayProvider(application)
    context = session()
    tool = provider.tools(context)[0]
    application.values = [descriptor(binding_digest="e" * 64)]

    with pytest.raises(GatewayError) as caught:
        await provider.call(
            context,
            tool,
            {"x": 2},
            request_id="request-one",
            approval_context={},
            progress_callback=None,
        )
    assert caught.value.code.value == "invalid_binding"
    assert application.calls == []


@pytest.mark.asyncio
async def test_cancel_session_close_and_shutdown_delegate_without_runtime_authority() -> (
    None
):
    application = Application()
    provider = EngineeringModelGatewayProvider(application)
    context = session()
    await provider.cancel(context, "request-one")
    await provider.close_session(context)
    await provider.shutdown()
    assert application.cancelled == [("session-one", "request-one")]
    assert application.closed == ["session-one"]
    assert application.stopped is True
