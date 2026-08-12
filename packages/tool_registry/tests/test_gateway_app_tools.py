from __future__ import annotations

import asyncio

import pytest

from tool_registry.gateway_models import GatewayError, GatewayTool
from tool_registry.models import McpUiToolMetadata
from tool_registry.models import McpUiResourceMetadata
from tool_registry.ui.policy import McpUiPolicy
from tool_registry.ui.resources import McpUiBinding
from test_gateway_service import service


def _tools(server_id: str) -> list[GatewayTool]:
    return [
        GatewayTool(
            name=f"{server_id}__model",
            server_id=server_id,
            tool_name="model",
            description="Model-only operation",
            input_schema={"type": "object"},
            ui=McpUiToolMetadata.from_upstream({"ui": {"visibility": ["model"]}}),
        ),
        GatewayTool(
            name=f"{server_id}__app",
            server_id=server_id,
            tool_name="app",
            description="App-only operation",
            input_schema={"type": "object"},
            ui=McpUiToolMetadata.from_upstream({"ui": {"visibility": ["app"]}}),
        ),
        GatewayTool(
            name=f"{server_id}__both",
            server_id=server_id,
            tool_name="both",
            description="Shared operation",
            input_schema={"type": "object"},
        ),
        GatewayTool(
            name=f"{server_id}__approved",
            server_id=server_id,
            tool_name="approved",
            description="Approved app operation",
            input_schema={"type": "object"},
            ui=McpUiToolMetadata.from_upstream({"ui": {"visibility": ["app"]}}),
            required_approvals=frozenset({"workspace_write"}),
        ),
    ]


def _app_service():
    gateway, lifecycle, audit = service()
    gateway.catalog.tools = _tools
    return gateway, lifecycle, audit


def test_model_and_app_tool_visibility_are_distinct_and_same_server_scoped() -> None:
    gateway, _, audit = _app_service()

    assert [tool.name for tool in gateway.list_tools("s1")] == [
        "cad__model",
        "cad__both",
    ]
    assert [tool.name for tool in gateway.list_app_tools("s1", "cad")] == [
        "cad__app",
        "cad__both",
        "cad__approved",
    ]
    assert gateway.list_app_tools("s1", "fea") == ()
    assert any(
        event["operation"] == "tool.list"
        and event["target_name"] == "app"
        and event["reason_code"] == "app_only"
        for event in audit.events
    )


@pytest.mark.asyncio
async def test_same_server_app_call_is_allowed_but_cross_server_and_model_only_fail() -> (
    None
):
    gateway, lifecycle, audit = _app_service()

    result = await gateway.call_app_tool(
        "s1", "app-call", "cad", "cad__app", {"value": 1}
    )
    assert result.structured_content == {"server": "cad", "workspace": "w1"}
    assert lifecycle.calls[-1][0] == "cad"
    assert any(
        event["operation"] == "app.tool.call" and event["outcome"] == "succeeded"
        for event in audit.events
    )

    with pytest.raises(GatewayError, match="Unknown or disabled"):
        await gateway.call_app_tool("s1", "cross-server", "cad", "fea__app", {})
    with pytest.raises(GatewayError, match="Unknown or disabled"):
        await gateway.call_app_tool("s1", "model-only", "cad", "cad__model", {})
    with pytest.raises(GatewayError, match="Unknown or disabled"):
        await gateway.call_tool("s1", "model-app-only", "cad__app", {})


@pytest.mark.asyncio
async def test_app_calls_use_workspace_approval_not_client_hints() -> None:
    gateway, lifecycle, _ = _app_service()

    denied = await gateway.call_app_tool("s1", "denied", "cad", "cad__approved", {})
    assert denied.is_error
    assert denied.structured_content == {"error": "approval_required"}
    allowed = await gateway.call_app_tool(
        "s1",
        "allowed",
        "cad",
        "cad__approved",
        {},
        workspace_approvals={"workspace_write"},
    )
    assert not allowed.is_error
    assert lifecycle.calls[-1][3] == {
        "session_id": "s1",
        "workspace_id": "w1",
        "workspace_approvals": ["workspace_write"],
    }


@pytest.mark.asyncio
async def test_app_call_cancellation_is_owned_and_audited() -> None:
    gateway, lifecycle, audit = _app_service()
    lifecycle.gate = asyncio.Event()
    call = asyncio.create_task(
        gateway.call_app_tool("s1", "owned-app", "cad", "cad__app", {})
    )
    while ("s1", "owned-app") not in gateway._requests:
        await asyncio.sleep(0)

    assert gateway.cancel("s2", "owned-app", "foreign") is False
    assert gateway.cancel("s1", "owned-app", "disposed") is True
    with pytest.raises(asyncio.CancelledError):
        await call
    assert any(
        event["operation"] == "app.tool.call" and event["outcome"] == "cancelled"
        for event in audit.events
    )


def test_app_resource_context_and_user_message_policy_is_fail_closed() -> None:
    policy = McpUiPolicy()
    assert policy.can_read_resource(
        app_server_id="cad", resource_server_id="cad"
    ).allowed
    assert not policy.can_read_resource(
        app_server_id="cad", resource_server_id="fea"
    ).allowed

    missing_grant = policy.can_host_operation(
        "context.update",
        declared_capabilities={"context.update"},
        granted_capabilities=set(),
    )
    assert not missing_grant.allowed and missing_grant.reason_code == "grant_required"
    allowed = policy.can_host_operation(
        "user.message",
        declared_capabilities={"user.message"},
        granted_capabilities={"user.message"},
    )
    assert allowed.allowed
    unsupported = policy.can_host_operation(
        "host.shell",
        declared_capabilities={"host.shell"},
        granted_capabilities={"host.shell"},
    )
    assert not unsupported.allowed
    assert unsupported.reason_code == "unsupported_operation"


class _UiResources:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.gate: asyncio.Event | None = None
        self.reader = self

    async def list_resources(self, server_id: str):
        return {"resources": [{"uri": f"ui://{server_id}/app"}]}

    async def list_resource_templates(self, server_id: str):
        return {"resourceTemplates": [{"uriTemplate": f"ui://{server_id}/{{view}}"}]}

    async def read(self, session, server_id: str, uri: str) -> McpUiBinding:
        if self.gate is not None:
            await self.gate.wait()
        self.calls.append((session.session_id, server_id, uri))
        return McpUiBinding(
            gateway_session_id=session.session_id,
            workspace_id=session.workspace_id,
            server_id=server_id,
            server_connection_id=f"{server_id}:1",
            upstream_resource_uri=uri,
            content_hash="a" * 64,
            source_version="a" * 64,
            media_type="text/html;profile=mcp-app",
            content="<h1>App</h1>",
            metadata=McpUiResourceMetadata(),
            subscribed=True,
        )

    def close_session(self, session) -> None:
        return None


@pytest.mark.asyncio
async def test_app_resource_read_uses_same_server_policy_and_audit() -> None:
    gateway, _, audit = _app_service()
    resources = _UiResources()
    gateway.mcp_ui_resources = resources

    binding = await gateway.read_app_resource(
        "s1",
        "resource-read",
        "cad",
        "cad",
        "ui://cad/app",
    )
    assert binding.content_hash == "a" * 64
    assert resources.calls == [("s1", "cad", "ui://cad/app")]
    assert any(
        event["operation"] == "app.resource.read" and event["outcome"] == "succeeded"
        for event in audit.events
    )
    with pytest.raises(GatewayError) as denied:
        await gateway.read_app_resource(
            "s1",
            "cross-resource",
            "cad",
            "fea",
            "ui://collision/app",
        )
    assert denied.value.code.value == "policy_denied"


@pytest.mark.asyncio
async def test_app_resource_read_is_cancellable_by_owning_session() -> None:
    gateway, _, audit = _app_service()
    resources = _UiResources()
    resources.gate = asyncio.Event()
    gateway.mcp_ui_resources = resources
    read = asyncio.create_task(
        gateway.read_app_resource(
            "s1",
            "resource-owned",
            "cad",
            "cad",
            "ui://cad/app",
        )
    )
    while ("s1", "resource-owned") not in gateway._requests:
        await asyncio.sleep(0)
    assert gateway.cancel("s2", "resource-owned", "foreign") is False
    assert gateway.cancel("s1", "resource-owned", "surface disposed") is True
    with pytest.raises(asyncio.CancelledError):
        await read
    assert any(
        event["operation"] == "app.resource.read" and event["outcome"] == "cancelled"
        for event in audit.events
    )


@pytest.mark.asyncio
async def test_app_resource_discovery_is_same_server_scoped_and_audited() -> None:
    gateway, _, audit = _app_service()
    resources = _UiResources()
    gateway.mcp_ui_resources = resources

    listed = await gateway.list_app_resources("s1", "resources-list", "cad")
    templates = await gateway.list_app_resource_templates("s1", "templates-list", "cad")

    assert listed == {"resources": [{"uri": "ui://cad/app"}]}
    assert templates == {"resourceTemplates": [{"uriTemplate": "ui://cad/{view}"}]}
    assert any(
        event["operation"] == "app.resources.list" and event["outcome"] == "succeeded"
        for event in audit.events
    )
    assert any(
        event["operation"] == "app.resource_templates.list"
        and event["outcome"] == "succeeded"
        for event in audit.events
    )

    with pytest.raises(GatewayError, match="not enabled"):
        await gateway.list_app_resources("s1", "disabled-list", "fea")
