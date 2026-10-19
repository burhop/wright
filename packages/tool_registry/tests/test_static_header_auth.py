"""Explicit static HTTPS headers; no account, live provider or fallback."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest
from tool_registry.models import EnvVarDefinition
from tool_registry.runners.sse import SseRunner

PLACEHOLDER = "placeholder-wire-credential"


def test_legacy_environment_shape_and_header_validation():
    assert EnvVarDefinition(name="KEY", label="Key").model_dump() == {
        "name": "KEY",
        "label": "Key",
        "description": "",
        "required": True,
        "secret": False,
    }
    assert (
        EnvVarDefinition(
            name="Authorization", label="Header", target="http_header"
        ).model_dump()["target"]
        == "http_header"
    )
    for name in ("Host", "MCP-Session-Id", "Content-Type", "Cookie", "bad\nheader"):
        with pytest.raises(ValueError):
            EnvVarDefinition(name=name, label="Header", target="http_header")
    for kwargs in (
        {"oauth_enabled": True},
        {"oauth_enabled": False, "static_headers": {"Host": "example.invalid"}},
        {"oauth_enabled": False, "static_headers": {"X-Key": "bad\r\nvalue"}},
    ):
        with pytest.raises(ValueError):
            SseRunner(
                "https://example.invalid/mcp",
                **{"static_headers": {"X-Key": PLACEHOLDER}, **kwargs},
            )
    with pytest.raises(ValueError):
        SseRunner(
            "http://127.0.0.1/mcp",
            oauth_enabled=False,
            static_headers={"X-Key": PLACEHOLDER},
        )


def wire_client(monkeypatch, response):
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(response)
        return original(*args, **kwargs)

    monkeypatch.setattr("tool_registry.runners.sse.httpx.AsyncClient", factory)


@pytest.mark.asyncio
async def test_explicit_header_reaches_only_resource_and_reflected_error_is_private(
    monkeypatch,
):
    requests = []

    def respond(request):
        requests.append(request)
        assert str(request.url) == "https://provider.example/mcp"
        assert request.headers["X-Key"] == PLACEHOLDER
        if request.method == "GET":
            return httpx.Response(405)
        data = json.loads(request.content)
        if data["method"] == "initialize":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": data["id"],
                    "result": {
                        "protocolVersion": data["params"]["protocolVersion"],
                        "capabilities": {},
                        "serverInfo": {"name": "fixture", "version": "1"},
                    },
                },
            )
        if "id" not in data:
            return httpx.Response(202)
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": data["id"],
                "error": {
                    "code": -32603,
                    "message": "provider reflected " + PLACEHOLDER,
                },
            },
        )

    wire_client(monkeypatch, respond)
    presenter = AsyncMock()
    runner = SseRunner(
        "https://provider.example/mcp",
        oauth_enabled=False,
        static_headers={"X-Key": PLACEHOLDER},
        device_authorization_presenter=presenter,
    )
    try:
        await runner.start()
        with pytest.raises(RuntimeError) as error:
            await runner.list_tools()
        assert PLACEHOLDER not in str(error.value)
        assert "[REDACTED]" in str(error.value)
        assert runner._oauth_provider is None
        presenter.assert_not_awaited()
        assert len([r for r in requests if r.method == "POST"]) >= 2
    finally:
        await runner.stop()


@pytest.mark.parametrize("status", [401, 403, 307])
@pytest.mark.asyncio
async def test_denied_or_redirected_auth_never_changes_grant_transport_or_origin(
    monkeypatch, status
):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            status,
            headers={
                "Location": "https://other.example/mcp",
                "WWW-Authenticate": 'Bearer resource_metadata="https://identity.example/resource"',
            },
        )

    wire_client(monkeypatch, respond)
    presenter = AsyncMock()
    runner = SseRunner(
        "https://provider.example/mcp",
        oauth_enabled=False,
        static_headers={"Authorization": "Bearer " + PLACEHOLDER},
        device_authorization_presenter=presenter,
    )
    with pytest.raises(RuntimeError):
        await runner.start()
    assert len(requests) == 1 and str(requests[0].url) == "https://provider.example/mcp"
    presenter.assert_not_awaited()
    assert runner.client is None and not runner.is_running()


@pytest.mark.asyncio
async def test_cancelled_header_request_not_replayed_and_notifies_same_resource(
    monkeypatch,
):
    import asyncio

    ready = asyncio.Event()
    hold = asyncio.Event()
    methods = []

    async def respond(request):
        assert (
            str(request.url) == "https://provider.example/mcp"
            and request.headers["X-Key"] == PLACEHOLDER
        )
        if request.method == "GET":
            return httpx.Response(405)
        data = json.loads(request.content)
        methods.append(data["method"])
        if data["method"] == "initialize":
            return httpx.Response(
                200,
                json={
                    "id": data["id"],
                    "result": {
                        "protocolVersion": data["params"]["protocolVersion"],
                        "capabilities": {},
                        "serverInfo": {"name": "fixture", "version": "1"},
                    },
                },
            )
        if data["method"] == "tools/list":
            ready.set()
            await hold.wait()
        return httpx.Response(202)

    wire_client(monkeypatch, respond)
    runner = SseRunner(
        "https://provider.example/mcp",
        oauth_enabled=False,
        static_headers={"X-Key": PLACEHOLDER},
    )
    try:
        await runner.start()
        task = asyncio.create_task(runner.list_tools())
        await asyncio.wait_for(ready.wait(), 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert (
            methods.count("tools/list") == 1
            and methods.count("notifications/cancelled") == 1
        )
        assert not runner._pending_requests
    finally:
        hold.set()
        await runner.stop()


def test_registry_lifecycle_uses_saved_header_owner_without_oauth_or_environment(
    monkeypatch, tmp_path
):
    from data_vault import upgrade_database
    from tool_registry.db import insert_server
    from tool_registry.models import McpServer
    from tool_registry.lifecycle_adapters import DatabaseLifecycleAdapter

    monkeypatch.delenv("WRIGHT_TESTING", raising=False)
    database = str(tmp_path / "headers.sqlite")
    upgrade_database(database)
    insert_server(
        database,
        McpServer(
            server_id="headers",
            name="Header fixture",
            type="sse",
            command="https://provider.example/mcp",
            is_installed=True,
            is_active=False,
            status="inactive",
            env_vars=[
                EnvVarDefinition(
                    name="X-Key", label="Key", secret=True, target="http_header"
                )
            ],
            created_at=1,
            updated_at=1,
        ),
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.has_credentials", lambda *a: {"X-Key": False}
    )
    adapter = DatabaseLifecycleAdapter(database)
    with pytest.raises(RuntimeError):
        adapter.build_runner("headers", None, None)
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.has_credentials", lambda *a: {"X-Key": True}
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.read_secrets",
        lambda *a: {"X-Key": PLACEHOLDER},
    )
    runner = adapter.build_runner("headers", None, None)
    assert runner.static_headers == {"X-Key": PLACEHOLDER}
    assert runner.oauth_enabled is False
    assert (
        adapter._environment(
            "headers",
            [EnvVarDefinition(name="X-Key", label="Key", target="http_header")],
        )
        == {}
    )
