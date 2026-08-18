from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from mcp.types import LATEST_PROTOCOL_VERSION

from tool_registry.runners.protocol import (
    MCP_APPS_EXTENSION,
    MCP_APP_MIME_TYPE,
    ChildProtocolState,
)
from tool_registry.runners.sse import _OAuthCallbackServer, SseRunner
from tool_registry.runners.stdio import StdioRunner


def test_child_initialize_uses_current_version_and_negotiates_ui_only_when_enabled() -> (
    None
):
    plain = ChildProtocolState()
    ui = ChildProtocolState(ui_enabled=True)

    assert plain.initialize_parameters() == {
        "protocolVersion": LATEST_PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "wright", "version": "0.1.0"},
    }
    assert ui.initialize_parameters()["capabilities"] == {
        "extensions": {MCP_APPS_EXTENSION: {"mimeTypes": [MCP_APP_MIME_TYPE]}}
    }


def test_child_initialize_preserves_server_capabilities_and_rejects_bad_results() -> (
    None
):
    protocol = ChildProtocolState(ui_enabled=True)
    protocol.accept_initialize(
        {
            "protocolVersion": LATEST_PROTOCOL_VERSION,
            "capabilities": {"resources": {"subscribe": True, "listChanged": True}},
            "serverInfo": {"name": "reference", "version": "1"},
        }
    )

    assert protocol.protocol_version == LATEST_PROTOCOL_VERSION
    assert protocol.supports("resources")
    assert protocol.supports("resources", "subscribe")
    assert protocol.server_info == {"name": "reference", "version": "1"}
    with pytest.raises(RuntimeError, match="protocolVersion"):
        ChildProtocolState().accept_initialize({"capabilities": {}})
    with pytest.raises(RuntimeError, match="capabilities"):
        ChildProtocolState().accept_initialize(
            {"protocolVersion": LATEST_PROTOCOL_VERSION}
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "runner",
    [StdioRunner(["reference"]), SseRunner("http://127.0.0.1:9/mcp")],
)
async def test_child_resource_template_read_and_subscription_operations(
    runner: StdioRunner | SseRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, Any] | None]] = []

    async def send(method: str, params: dict[str, Any] | None = None) -> dict:
        calls.append((method, params))
        return {"ok": True}

    monkeypatch.setattr(runner, "_send_request", send)

    assert await runner.list_resources("resource-cursor") == {"ok": True}
    assert await runner.list_resource_templates("template-cursor") == {"ok": True}
    assert await runner.read_resource("ui://reference/app") == {"ok": True}
    await runner.subscribe_resource("ui://reference/app")
    await runner.unsubscribe_resource("ui://reference/app")

    assert calls == [
        ("resources/list", {"cursor": "resource-cursor"}),
        ("resources/templates/list", {"cursor": "template-cursor"}),
        ("resources/read", {"uri": "ui://reference/app"}),
        ("resources/subscribe", {"uri": "ui://reference/app"}),
        ("resources/unsubscribe", {"uri": "ui://reference/app"}),
    ]


@pytest.mark.asyncio
async def test_oauth_callback_server_returns_code_and_state() -> None:
    callback = _OAuthCallbackServer(timeout=5.0)
    redirect_uri = await callback.start()
    parsed = redirect_uri.split(":", 2)
    port = int(parsed[2].split("/", 1)[0])

    result_task = asyncio.create_task(callback.wait_for_callback())
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(
        b"GET /oauth/callback?code=fixture-code&state=fixture-state HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n\r\n"
    )
    await writer.drain()

    assert await result_task == ("fixture-code", "fixture-state")
    response = await reader.read()
    assert b"Wright MCP sign-in complete" in response
    writer.close()
    await writer.wait_closed()
    await callback.close()


@pytest.mark.asyncio
async def test_oauth_callback_server_ignores_browser_asset_requests() -> None:
    callback = _OAuthCallbackServer(timeout=5.0)
    redirect_uri = await callback.start()
    port = int(redirect_uri.split(":", 2)[2].split("/", 1)[0])

    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(b"GET /favicon.ico HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
    await writer.drain()

    response = await reader.read()
    assert b"400 Bad Request" in response
    assert callback.future is not None
    assert not callback.future.done()
    writer.close()
    await writer.wait_closed()
    await callback.close()


@pytest.mark.asyncio
async def test_child_notifications_are_delivered_without_becoming_authority() -> None:
    protocol = ChildProtocolState(ui_enabled=True)
    received: list[tuple[str, dict[str, Any]]] = []

    async def handler(method: str, params: dict[str, Any]) -> None:
        received.append((method, params))

    protocol.add_notification_handler(handler)
    await protocol.handle_notification(
        "notifications/resources/updated",
        {"uri": "ui://reference/app", "vendor": "preserved"},
    )

    assert received == [
        (
            "notifications/resources/updated",
            {"uri": "ui://reference/app", "vendor": "preserved"},
        )
    ]


class _Stdin:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def write(self, value: bytes) -> None:
        import json

        self.payloads.append(json.loads(value))

    async def drain(self) -> None:
        return None


class _ClosedStdout:
    async def readline(self) -> bytes:
        return b""


@pytest.mark.asyncio
async def test_stdio_cancellation_notifies_child_and_clears_request() -> None:
    runner = StdioRunner(["reference"])
    stdin = _Stdin()
    runner.process = SimpleNamespace(
        stdin=stdin,
        stdout=_ClosedStdout(),
        returncode=None,
        pid=12,
    )
    request = asyncio.create_task(
        runner._send_request("resources/read", {"uri": "ui://x"})
    )
    while not runner._pending_requests:
        await asyncio.sleep(0)
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request

    assert runner._pending_requests == {}
    assert stdin.payloads[-1] == {
        "jsonrpc": "2.0",
        "method": "notifications/cancelled",
        "params": {"requestId": 1, "reason": "caller cancelled"},
    }


@pytest.mark.asyncio
async def test_stdio_transport_close_fails_pending_operations() -> None:
    runner = StdioRunner(["reference"])
    runner.process = SimpleNamespace(
        stdin=_Stdin(),
        stdout=_ClosedStdout(),
        returncode=None,
        pid=12,
    )
    pending = asyncio.get_running_loop().create_future()
    runner._pending_requests[9] = pending

    await runner._read_stdout()

    with pytest.raises(RuntimeError, match="transport closed"):
        await pending
    assert runner._pending_requests == {}
