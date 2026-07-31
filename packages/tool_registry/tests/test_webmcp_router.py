from __future__ import annotations

import asyncio
import json

import pytest

from tool_registry.webmcp_router import (
    WebMcpBinding,
    WebMcpRegistration,
    WebMcpRouter,
    WebMcpRoutingError,
)


class Socket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send_text(self, message: str) -> None:
        self.messages.append(message)


def binding(surface: str, *, generation: int = 2) -> WebMcpBinding:
    return WebMcpBinding(
        principal_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        surface_id=surface,
        instance_id=f"instance-{surface}",
        generation=generation,
        document_origin=f"https://{surface}.preview.example.test",
        server_id="web-app",
        tool_name="select_part",
    )


def registration(surface: str) -> WebMcpRegistration:
    return WebMcpRegistration(
        binding(surface),
        "Select a visible part",
        {
            "type": "object",
            "properties": {"partId": {"type": "string"}},
            "required": ["partId"],
            "additionalProperties": False,
        },
    )


@pytest.mark.asyncio
async def test_identical_tool_names_route_only_to_exact_composite_binding() -> None:
    router = WebMcpRouter()
    first, second = Socket(), Socket()
    router.register(first, registration("surface-a"))
    router.register(second, registration("surface-b"))

    call = asyncio.create_task(
        router.invoke(binding("surface-b"), {"partId": "part-2"})
    )
    await asyncio.sleep(0)
    assert first.messages == []
    request = json.loads(second.messages[0])
    assert request["operation"] == "webmcp.tool.call"
    assert request["payload"] == {"partId": "part-2"}
    assert request["binding"]["surfaceId"] == "surface-b"
    response = {
        "protocolVersion": "1.0",
        "kind": "result",
        "messageId": "11111111-1111-4111-8111-111111111111",
        "correlationId": request["correlationId"],
        "replyTo": request["messageId"],
        "binding": binding("surface-b").envelope(),
        "operation": "webmcp.tool.result",
        "toolName": "select_part",
        "sequence": 0,
        "createdAt": request["createdAt"],
        "deadlineAt": request["deadlineAt"],
        "payload": {"selected": "part-2"},
    }
    assert router.handle_message(second, json.dumps(response))
    assert await call == {"selected": "part-2"}


@pytest.mark.asyncio
async def test_wrong_socket_stale_generation_and_late_results_are_ignored() -> None:
    audit: list[tuple[str, dict]] = []
    router = WebMcpRouter(
        audit=lambda event, fields: audit.append((event, dict(fields)))
    )
    owner, foreign = Socket(), Socket()
    router.register(owner, registration("surface-a"))
    call = asyncio.create_task(router.invoke(binding("surface-a"), {"partId": "one"}))
    await asyncio.sleep(0)
    request = json.loads(owner.messages[0])
    response = {
        "protocolVersion": "1.0",
        "kind": "result",
        "messageId": "11111111-1111-4111-8111-111111111111",
        "correlationId": request["correlationId"],
        "replyTo": request["messageId"],
        "binding": binding("surface-a").envelope(),
        "operation": "webmcp.tool.result",
        "toolName": "select_part",
        "sequence": 0,
        "createdAt": request["createdAt"],
        "deadlineAt": request["deadlineAt"],
        "payload": {"ok": True},
    }
    assert not router.handle_message(foreign, json.dumps(response))
    response["binding"] = binding("surface-a", generation=3).envelope()
    assert not router.handle_message(owner, json.dumps(response))
    response["binding"] = binding("surface-a").envelope()
    assert router.handle_message(owner, json.dumps(response))
    assert await call == {"ok": True}
    assert not router.handle_message(owner, json.dumps(response))
    assert {event for event, _ in audit} >= {
        "webmcp.response.wrong_socket",
        "webmcp.response.stale_scope",
        "webmcp.response.late",
    }


@pytest.mark.asyncio
async def test_abort_dispose_disconnect_schema_size_and_rate_fail_closed() -> None:
    router = WebMcpRouter(maximum_message_bytes=2048, maximum_calls_per_minute=1)
    socket = Socket()
    exact = registration("surface-a")
    router.register(socket, exact)
    with pytest.raises(WebMcpRoutingError) as invalid:
        await router.invoke(exact.binding, {"partId": 42})
    assert invalid.value.code == "SURFACE_PROTOCOL_WEBMCP_ARGUMENTS_INVALID"
    with pytest.raises(WebMcpRoutingError) as large:
        await router.invoke(exact.binding, {"partId": "x" * 3000})
    assert large.value.code == "SURFACE_LIMIT_WEBMCP_MESSAGE_BYTES"

    call = asyncio.create_task(router.invoke(exact.binding, {"partId": "one"}))
    await asyncio.sleep(0)
    call.cancel()
    with pytest.raises(asyncio.CancelledError):
        await call
    assert json.loads(socket.messages[-1])["operation"] == "webmcp.tool.cancel"
    with pytest.raises(WebMcpRoutingError) as rate:
        await router.invoke(exact.binding, {"partId": "two"})
    assert rate.value.code == "SURFACE_LIMIT_WEBMCP_RATE"

    replacement = WebMcpRouter()
    replacement.register(socket, exact)
    pending = asyncio.create_task(replacement.invoke(exact.binding, {"partId": "one"}))
    await asyncio.sleep(0)
    assert replacement.unregister(socket, exact.binding, reason="navigation")
    with pytest.raises(WebMcpRoutingError) as disposed:
        await pending
    assert disposed.value.code == "SURFACE_STATE_WEBMCP_DISPOSED"
    replacement.register(socket, exact)
    assert replacement.disconnect(socket) == 1
    assert (
        replacement.matching(
            workspace_id="workspace-1",
            server_id="web-app",
            tool_name="select_part",
        )
        == ()
    )


def test_registration_rejects_duplicate_owner_and_invalid_origin() -> None:
    router = WebMcpRouter()
    router.register(Socket(), registration("surface-a"))
    with pytest.raises(WebMcpRoutingError) as duplicate:
        router.register(Socket(), registration("surface-a"))
    assert duplicate.value.code == "SURFACE_PROTOCOL_WEBMCP_DUPLICATE"
    with pytest.raises(ValueError, match="origin"):
        WebMcpBinding(
            principal_id="user",
            workspace_id="workspace",
            session_id="session",
            surface_id="surface",
            instance_id="instance",
            generation=1,
            document_origin="https://example.test/path",
            server_id="server",
            tool_name="tool",
        )
