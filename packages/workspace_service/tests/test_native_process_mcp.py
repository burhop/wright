"""Native boundary tests using the real gateway with explicitly fake child ports."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace

import pytest
from tool_registry.gateway_models import GatewayTool, SessionState
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service.native_process_mcp import NativeMcpAdapter, schema_digest
from workspace_service.native_process_service import NativeServiceError


INPUT = {
    "type": "object",
    "properties": {"value": {"type": "number", "minimum": 0.25}},
    "required": ["value"],
    "additionalProperties": False,
}
OUTPUT = {
    "type": "object",
    "properties": {"value": {"type": "number"}},
    "required": ["value"],
    "additionalProperties": False,
}


class Workspaces:
    def __init__(self, path):
        self.path = str(path)
        self.enabled = {"fixture"}
        self.archived = False

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        if self.archived or session_id != "s1" or workspace_id != "w1":
            raise RuntimeError("Workspace session unavailable")
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": self.path,
        }

    def enabled_server_ids(self, session):
        return self.enabled

    def resolve(self, session_id):
        return {"workspace_id": "w1", "local_path": self.path}


class Catalog:
    def __init__(self):
        self.tool = GatewayTool(
            name="fixture__measure",
            server_id="fixture",
            tool_name="measure",
            description="Safe local measurement fixture",
            input_schema=INPUT,
            output_schema=OUTPUT,
        )

    def servers(self):
        return (
            McpServer(
                server_id="fixture",
                name="fixture",
                type="stdio",
                command=["fixture-only"],
                is_installed=True,
                is_active=False,
                status="inactive",
                created_at=1,
                updated_at=1,
            ),
        )

    def tools(self, server_id):
        return (self.tool,)

    def resources(self, session):
        return ()


class Audit:
    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


class Lifecycle:
    def __init__(self):
        self.calls = []
        self.starts = 0
        self.on_start = lambda: None
        self.result = {"structuredContent": {"value": 0.5}}
        self.wait = False
        self.entered = asyncio.Event()
        self.cancelled = False

    async def ensure_started(self, server_id, *, workspace_path, approval_context):
        self.starts += 1
        self.on_start()

    async def call_tool(self, server_id, tool_name, arguments, *, approval_context):
        self.calls.append((server_id, tool_name, arguments, approval_context))
        self.entered.set()
        if self.wait:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        return self.result

    async def shutdown(self):
        pass


@pytest.fixture
def harness(tmp_path):
    workspaces, catalog, lifecycle, audit = (
        Workspaces(tmp_path),
        Catalog(),
        Lifecycle(),
        Audit(),
    )
    gateway = GatewayService(
        workspaces=workspaces,
        catalog=catalog,
        lifecycle=lifecycle,
        audit=audit,
        notifier=GatewayNotificationHub(),
    )
    adapter = NativeMcpAdapter(gateway, workspaces.resolve)
    return adapter, gateway, workspaces, catalog, lifecycle, audit


def select(adapter):
    item = adapter.discover("s1")["bindings"][0]
    return {
        key: item[key]
        for key in (
            "server_id",
            "tool_name",
            "input_schema_digest",
            "output_schema_digest",
        )
    }


def reason(error):
    return error.value.findings[0].code


def test_schema_digest_accepts_fractions_and_hashes_null():
    assert schema_digest(None) == hashlib.sha256(b"null").hexdigest()
    assert (
        schema_digest({"minimum": 0.25, "title": "Métrique"})
        == hashlib.sha256('{"minimum":0.25,"title":"Métrique"}'.encode()).hexdigest()
    )
    assert schema_digest({"b": 2, "a": 1}) == schema_digest({"a": 1, "b": 2})
    with pytest.raises(ValueError):
        schema_digest({"minimum": float("nan")})


def test_discovery_and_preflight_are_read_only_and_snapshot_schemas(harness):
    adapter, _, _, catalog, lifecycle, _ = harness
    binding = select(adapter)
    descriptor = adapter.preflight("s1", binding)
    descriptor["input_schema"]["properties"].clear()
    assert "value" in catalog.tool.input_schema["properties"]
    assert lifecycle.starts == 0 and lifecycle.calls == []


@pytest.mark.parametrize("change", ["input", "output", "missing_output"])
def test_exact_schema_changes_fail_before_start(harness, change):
    adapter, _, _, catalog, lifecycle, _ = harness
    binding = select(adapter)
    if change == "input":
        catalog.tool = replace(catalog.tool, input_schema={"type": "object"})
    else:
        catalog.tool = replace(
            catalog.tool,
            output_schema=None if change == "missing_output" else {"type": "object"},
        )
    with pytest.raises(NativeServiceError) as error:
        adapter.preflight("s1", binding)
    assert error.value.code == "NATIVE_BINDING_CHANGED"
    assert reason(error) == "MCP_BINDING_CHANGED"
    assert lifecycle.starts == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["schema", "enabled", "approval", "archived"])
async def test_post_startup_guard_prevents_changed_dispatch(harness, change):
    adapter, gateway, workspaces, catalog, lifecycle, audit = harness
    binding = select(adapter)

    def mutate():
        if change == "schema":
            catalog.tool = replace(catalog.tool, input_schema={"type": "object"})
        elif change == "enabled":
            workspaces.enabled.clear()
        elif change == "approval":
            catalog.tool = replace(
                catalog.tool, required_approvals=frozenset({"paid_service"})
            )
        else:
            workspaces.archived = True

    lifecycle.on_start = mutate
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", binding, {"value": 1}, 1, "guard-trace")
    assert error.value.code in {"NATIVE_BINDING_CHANGED", "NATIVE_DENIED"}
    assert lifecycle.calls == []
    assert any(
        event["metadata"].get("trace_id") == "guard-trace"
        and event["outcome"] == "failed"
        for event in audit.events
    )
    assert gateway._requests == {}


def test_denied_and_unavailable_tools_never_discover(harness):
    adapter, _, workspaces, catalog, lifecycle, _ = harness
    binding = select(adapter)
    catalog.tool = replace(
        catalog.tool, required_approvals=frozenset({"physical_action"})
    )
    assert adapter.discover("s1") == {"bindings": []}
    with pytest.raises(NativeServiceError) as error:
        adapter.preflight("s1", binding)
    assert error.value.code == "NATIVE_DENIED"
    workspaces.archived = True
    with pytest.raises(NativeServiceError):
        adapter.discover("s1")
    assert lifecycle.starts == 0


@pytest.mark.parametrize(
    "invalid", [{}, {"command": "arbitrary"}, {"input_schema_digest": "0" * 64}]
)
def test_malformed_bindings_cannot_dispatch(harness, invalid):
    adapter, _, _, _, lifecycle, _ = harness
    with pytest.raises(NativeServiceError) as error:
        adapter.preflight("s1", invalid)
    assert reason(error) == "MCP_BINDING_INVALID"
    assert lifecycle.starts == 0


@pytest.mark.asyncio
async def test_actual_gateway_route_preserves_trace_and_canonical_structured_text(
    harness,
):
    adapter, _, _, _, lifecycle, audit = harness
    result = await adapter.call(
        "s1", select(adapter), {"value": 0.5}, 1, "native-trace"
    )
    assert result == '{"value":0.5}'
    assert lifecycle.calls[0][:3] == ("fixture", "measure", {"value": 0.5})
    assert "workspace_approvals" not in lifecycle.calls[0][3]
    assert any(
        item["outcome"] == "succeeded"
        and item["metadata"]["trace_id"] == "native-trace"
        for item in audit.events
    )
    assert "value" not in json.dumps(audit.events)


@pytest.mark.asyncio
async def test_schema_input_and_output_errors_are_actionable(harness):
    adapter, _, _, _, lifecycle, _ = harness
    binding = select(adapter)
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", binding, {"value": 0.1}, 1, "bad-input")
    assert reason(error) == "MCP_INPUT_INVALID" and not lifecycle.calls
    lifecycle.result = {"structuredContent": {"value": "bad"}}
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", binding, {"value": 1}, 1, "bad-output")
    assert reason(error) == "MCP_OUTPUT_INVALID"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "schema",
    [
        {"type": "object", "$ref": "#/$defs/absent"},
        {"type": "object", "$ref": "#absent-anchor"},
        {"$ref": "#"},
    ],
)
async def test_unusable_local_schema_references_fail_inside_native_boundary(
    harness, schema, monkeypatch
):
    adapter, gateway, _, catalog, lifecycle, _ = harness

    def deny_network(*_args, **_kwargs):
        pytest.fail("Local schema validation must not retrieve remote resources")

    monkeypatch.setattr("urllib.request.urlopen", deny_network)
    catalog.tool = replace(catalog.tool, input_schema=schema)
    binding = select(adapter)
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", binding, {"value": 1}, 1, "local-schema")
    assert error.value.code == "NATIVE_NOT_READY"
    assert reason(error) == "MCP_SCHEMA_INVALID"
    assert "absent" not in str(error.value)
    assert lifecycle.starts == 0 and lifecycle.calls == []
    assert gateway._requests == {}

    catalog.tool = replace(catalog.tool, input_schema=INPUT)
    assert (
        await adapter.call("s1", select(adapter), {"value": 1}, 1, "repaired-schema")
        == '{"value":0.5}'
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "output,expected",
    [
        (
            {
                "content": [
                    {"type": "text", "text": "hello"},
                    {"type": "text", "text": "world"},
                ]
            },
            "hello\nworld",
        ),
        ({"structuredContent": {}}, "{}"),
    ],
)
async def test_text_and_empty_structured_results(harness, output, expected):
    adapter, _, _, catalog, lifecycle, _ = harness
    catalog.tool = replace(catalog.tool, output_schema=None)
    lifecycle.result = output
    assert (
        await adapter.call("s1", select(adapter), {"value": 1}, 1, "text-trace")
        == expected
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "output",
    [
        {"content": [{"type": "image", "data": "unsafe", "mimeType": "image/png"}]},
        {"structuredContent": {"value": float("inf")}},
        {"content": [{"type": "text", "text": "x" * (1024 * 1024 + 1)}]},
        {
            "isError": True,
            "content": [{"type": "text", "text": "secret-provider-detail"}],
        },
    ],
)
async def test_invalid_or_provider_error_results_fail_bounded(harness, output):
    adapter, _, _, catalog, lifecycle, _ = harness
    catalog.tool = replace(catalog.tool, output_schema=None)
    lifecycle.result = output
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", select(adapter), {"value": 1}, 1, "invalid-output")
    assert error.value.code in {"NATIVE_NOT_READY", "NATIVE_LIMIT"}
    assert "secret-provider-detail" not in str(error.value)


@pytest.mark.asyncio
async def test_timeout_and_cancellation_stop_forwarding(harness):
    adapter, gateway, _, _, lifecycle, audit = harness
    binding = select(adapter)
    lifecycle.wait = True
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", binding, {"value": 1}, 0.01, "timeout")
    assert reason(error) == "MCP_TIMEOUT" and lifecycle.cancelled
    lifecycle.entered.clear()
    task = asyncio.create_task(adapter.call("s1", binding, {"value": 1}, 1, "cancel"))
    await lifecycle.entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert gateway._requests == {}
    terminal = next(event for event in audit.events if event["outcome"] == "cancelled")
    assert terminal["metadata"]["trace_id"] == "cancel"


def test_remote_schema_reference_is_rejected_without_resolution(harness):
    adapter, _, _, catalog, lifecycle, _ = harness
    catalog.tool = replace(
        catalog.tool, input_schema={"$ref": "https://invalid.test/schema"}
    )
    with pytest.raises(NativeServiceError):
        adapter.discover("s1")
    assert lifecycle.starts == 0


@pytest.mark.asyncio
async def test_adapter_closes_owned_sessions(harness):
    adapter, gateway, _, _, _, _ = harness
    select(adapter)
    await adapter.close()
    assert all(
        session.state is SessionState.CLOSED for session in gateway._sessions.values()
    )
    with pytest.raises(NativeServiceError):
        adapter.discover("s1")


@pytest.mark.asyncio
async def test_arguments_are_frozen_before_startup_and_timeout_is_capped(harness):
    adapter, _, _, _, lifecycle, audit = harness
    arguments = {"value": 0.5}
    lifecycle.on_start = lambda: arguments.update(value=99)
    await adapter.call("s1", select(adapter), arguments, 60, "snapshot")
    assert lifecycle.calls[0][2] == {"value": 0.5}
    assert (
        next(item for item in audit.events if item["outcome"] == "started")["metadata"][
            "timeout_ms"
        ]
        == 15000
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "arguments,timeout",
    [
        ({"value": float("nan")}, 1),
        ({"value": 1}, 0),
        ({"value": 1}, float("inf")),
        ([1], 1),
    ],
)
async def test_invalid_arguments_and_timeout_never_start(harness, arguments, timeout):
    adapter, _, _, _, lifecycle, _ = harness
    with pytest.raises(NativeServiceError) as error:
        await adapter.call("s1", select(adapter), arguments, timeout, "invalid-input")
    assert reason(error) == "MCP_INPUT_INVALID"
    assert lifecycle.starts == 0


@pytest.mark.asyncio
async def test_input_size_and_adapter_session_limits(harness):
    adapter, _, _, _, lifecycle, _ = harness
    binding = select(adapter)
    with pytest.raises(NativeServiceError) as error:
        await adapter.call(
            "s1", binding, {"text": "x" * (1024 * 1024)}, 1, "large-input"
        )
    assert error.value.code == "NATIVE_LIMIT" and lifecycle.starts == 0
    adapter._owned_sessions = {f"other-{index}" for index in range(128)}
    with pytest.raises(NativeServiceError) as error:
        adapter.discover("s1")
    assert error.value.code == "NATIVE_LIMIT"


def test_workspace_location_change_fails_closed(harness, tmp_path):
    adapter, _, workspaces, _, lifecycle, _ = harness
    binding = select(adapter)
    workspaces.path = str(tmp_path / "relocated")
    with pytest.raises(NativeServiceError) as error:
        adapter.preflight("s1", binding)
    assert error.value.code == "NATIVE_BINDING_CHANGED" and lifecycle.starts == 0
