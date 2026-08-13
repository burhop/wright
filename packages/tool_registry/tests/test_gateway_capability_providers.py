from __future__ import annotations

import asyncio

import pytest

from tool_registry.gateway_models import (
    GatewayError,
    GatewaySessionContext,
    GatewayTool,
)

from test_gateway_service import service


class Provider:
    provider_id = "models"
    declared_tool_names = frozenset({"wright_model__affine__predict"})

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.cancelled: list[tuple[str, str]] = []
        self.closed: list[str] = []
        self.stopped = False
        self.gate: asyncio.Event | None = None

    def tools(self, session: GatewaySessionContext):
        if session.workspace_id != "w1":
            return ()
        return (
            GatewayTool(
                name="wright_model__affine__predict",
                server_id="wright-models",
                tool_name="predict",
                description="Deterministic reviewed prediction.",
                input_schema={
                    "type": "object",
                    "required": ["x"],
                    "properties": {"x": {"type": "number"}},
                    "additionalProperties": False,
                },
                output_schema={
                    "type": "object",
                    "required": ["y"],
                    "properties": {"y": {"type": "number"}},
                    "additionalProperties": False,
                },
                annotations={"readOnlyHint": True},
                provenance={"binding_digest": "a" * 64},
            ),
        )

    async def call(
        self,
        session,
        tool,
        arguments,
        *,
        request_id,
        approval_context,
        progress_callback,
    ):
        if self.gate is not None:
            await self.gate.wait()
        if progress_callback is not None:
            await progress_callback({"phase": "infer", "sequence": 1})
        self.calls.append((session.workspace_id, request_id, dict(arguments)))
        return {"structuredContent": {"y": arguments["x"] * 2 + 1}}

    async def cancel(self, session, request_id):
        self.cancelled.append((session.workspace_id, request_id))

    async def close_session(self, session):
        self.closed.append(session.session_id)

    async def shutdown(self):
        self.stopped = True


def test_provider_discovery_is_workspace_scoped_and_mcp_compatible() -> None:
    gateway, _, audit = service()
    provider = Provider()
    gateway.add_capability_provider(provider)

    assert [tool.name for tool in gateway.list_tools("s1")] == [
        "cad__run",
        "wright_model__affine__predict",
    ]
    assert [tool.name for tool in gateway.list_tools("s2")] == ["fea__run"]
    assert any(
        event["server_id"] == "wright-models" and event["outcome"] == "listed"
        for event in audit.events
    )


@pytest.mark.asyncio
async def test_provider_call_uses_existing_validation_progress_and_audit() -> None:
    gateway, _, audit = service()
    provider = Provider()
    gateway.add_capability_provider(provider)
    updates: list[dict] = []

    result = await gateway.call_tool(
        "s1",
        "model-request",
        "wright_model__affine__predict",
        {"x": 2},
        progress_callback=lambda update: updates.append(dict(update)),
    )

    assert result.structured_content == {"y": 5}
    assert provider.calls == [("w1", "model-request", {"x": 2})]
    assert updates[0]["server"] == "wright-models"
    assert updates[0]["correlationId"]
    assert any(
        event["request_id"] == "model-request" and event["outcome"] == "succeeded"
        for event in audit.events
    )


def test_provider_identity_and_tool_collisions_fail_closed() -> None:
    gateway, _, _ = service()
    gateway.add_capability_provider(Provider())
    with pytest.raises(GatewayError, match="provider identity"):
        gateway.add_capability_provider(Provider())

    class Collision(Provider):
        provider_id = "collision"
        declared_tool_names = frozenset({"cad__run"})

    with pytest.raises(GatewayError, match="tool name collision"):
        gateway.add_capability_provider(Collision())

    class Undeclared(Provider):
        provider_id = "undeclared"
        declared_tool_names = frozenset({"wright_model__different__predict"})

    other, _, _ = service()
    other.add_capability_provider(Undeclared())
    with pytest.raises(GatewayError, match="undeclared tool"):
        other.list_tools("s1")


@pytest.mark.asyncio
async def test_provider_cancellation_close_and_shutdown_are_forwarded() -> None:
    gateway, _, _ = service()
    provider = Provider()
    provider.gate = asyncio.Event()
    gateway.add_capability_provider(provider)
    call = asyncio.create_task(
        gateway.call_tool(
            "s1", "cancel-model", "wright_model__affine__predict", {"x": 2}
        )
    )
    await asyncio.sleep(0)

    assert gateway.cancel("s1", "cancel-model", "operator") is True
    with pytest.raises(asyncio.CancelledError):
        await call
    await asyncio.sleep(0)
    assert provider.cancelled == [("w1", "cancel-model")]

    await gateway.close_session("s1")
    assert provider.closed == ["s1"]
    await gateway.shutdown()
    assert provider.stopped is True
