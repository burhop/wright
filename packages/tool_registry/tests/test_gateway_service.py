from __future__ import annotations

import asyncio
import time

import pytest

from core.rivet_mcp import ProviderEvidence
from tool_registry.gateway_models import GatewayError, GatewayResource, GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.models import McpServer


class Workspaces:
    def __init__(self) -> None:
        self.bindings = {
            "s1": ("p1", "w1", "/workspace/one"),
            "s2": ("p2", "w2", "/workspace/two"),
        }
        self.enabled = {"w1": {"cad"}, "w2": {"fea"}}

    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        expected = self.bindings.get(session_id)
        if expected != (principal_id, workspace_id, expected[2] if expected else None):
            raise RuntimeError("binding denied")
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": expected[2],
        }

    def enabled_server_ids(self, session):
        return self.enabled[session.workspace_id]


class Catalog:
    def __init__(self) -> None:
        now = int(time.time())
        self._servers = [
            McpServer(
                server_id="cad",
                name="CAD",
                type="stdio",
                command="cad",
                is_active=False,
                is_installed=True,
                status="inactive",
                created_at=now,
                updated_at=now,
            ),
            McpServer(
                server_id="fea",
                name="FEA",
                type="stdio",
                command="fea",
                is_active=False,
                is_installed=True,
                status="inactive",
                created_at=now,
                updated_at=now,
            ),
        ]
        self.output_schema = {"type": "object"}

    def servers(self):
        return self._servers

    def tools(self, server_id):
        return [
            GatewayTool(
                name=f"{server_id}__run",
                server_id=server_id,
                tool_name="run",
                description=f"Run {server_id}",
                input_schema={"type": "object"},
                output_schema=self.output_schema,
            )
        ]

    def resources(self, session):
        return [
            GatewayResource(
                f"wright://workspace/{session.workspace_id}",
                "Workspace",
                "Bound workspace",
                "application/json",
            )
        ]


class Lifecycle:
    def __init__(self) -> None:
        self.calls = []
        self.gate: asyncio.Event | None = None
        self.result = None

    async def ensure_started(self, server_id, *, workspace_path, approval_context):
        return None

    async def call_tool(
        self,
        server_id,
        tool_name,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        if self.gate:
            await self.gate.wait()
        if progress_callback is not None:
            callback_result = progress_callback(
                {"progress": 1.0, "total": 2.0, "message": "Child update"}
            )
            if callback_result is not None:
                await callback_result
        self.calls.append(
            (server_id, tool_name, dict(arguments), dict(approval_context))
        )
        return self.result or {
            "server": server_id,
            "workspace": approval_context["workspace_id"],
        }

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


def service():
    lifecycle = Lifecycle()
    audit = Audit()
    instance = GatewayService(
        workspaces=Workspaces(),
        catalog=Catalog(),
        lifecycle=lifecycle,
        audit=audit,
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        operation_timeout=0.1,
    )
    for session_id, principal, workspace in (("s1", "p1", "w1"), ("s2", "p2", "w2")):
        instance.open_session(
            session_id=session_id,
            principal_id=principal,
            workspace_id=workspace,
            transport="stdio",
        )
        instance.initialize_session(
            session_id,
            protocol_version="2025-11-25",
            client_name="codex",
            client_version="0.144.1",
            client_capabilities={},
        )
    return instance, lifecycle, audit


def test_discovery_and_resources_are_workspace_scoped() -> None:
    instance, _, _ = service()
    assert [tool.name for tool in instance.list_tools("s1")] == ["cad__run"]
    assert [tool.name for tool in instance.list_tools("s2")] == ["fea__run"]
    assert instance.list_resources("s1")[1].uri.endswith("/w1")
    assert instance.list_resources("s2")[1].uri.endswith("/w2")
    assert (
        b'"workspace_id": "w1"'
        in instance.read_resource("s1", "wright://workspace/w1").content.encode()
    )


@pytest.mark.asyncio
async def test_structured_call_uses_bound_workspace_and_audits() -> None:
    instance, lifecycle, audit = service()
    result = await instance.call_tool("s1", "r1", "cad__run", {"shape": "cube"})

    assert result.structured_content == {"server": "cad", "workspace": "w1"}
    assert not result.is_error
    assert lifecycle.calls[0][3] == {
        "workspace_id": "w1",
        "session_id": "s1",
    }
    executed = next(event for event in audit.events if event["outcome"] == "succeeded")
    assert executed["workspace_id"] == "w1"
    assert executed["metadata"]["response_bytes"] > 0
    assert executed["metadata"]["argument_count"] == 1
    assert any(event["outcome"] == "started" for event in audit.events)


@pytest.mark.asyncio
async def test_call_forwards_generic_correlated_progress() -> None:
    instance, _, _ = service()
    updates: list[dict] = []

    await instance.call_tool(
        "s1",
        "progress-request",
        "cad__run",
        {},
        progress_callback=lambda update: updates.append(dict(update)),
    )

    assert len(updates) == 1
    assert updates[0] == {
        "progress": 1.0,
        "total": 2.0,
        "message": "Child update",
        "server": "cad",
        "tool": "cad__run",
        "title": "Run cad",
        "correlationId": updates[0]["correlationId"],
        "status": "running",
    }
    assert updates[0]["correlationId"]


@pytest.mark.asyncio
async def test_call_preserves_child_terminal_progress_status_and_title() -> None:
    instance, lifecycle, _ = service()
    updates: list[dict] = []

    async def completed_progress(_server_id, _tool_name, _arguments, **kwargs):
        callback = kwargs["progress_callback"]
        await callback(
            {
                "status": "completed",
                "title": "BREP panel ready",
                "message": "The visible panel is ready.",
            }
        )
        return {"server": "cad", "workspace": "w1"}

    lifecycle.call_tool = completed_progress
    await instance.call_tool(
        "s1",
        "terminal-progress",
        "cad__run",
        {},
        progress_callback=lambda update: updates.append(dict(update)),
    )

    assert updates[0]["status"] == "completed"
    assert updates[0]["title"] == "BREP panel ready"


@pytest.mark.asyncio
async def test_call_validates_and_preserves_child_structured_content() -> None:
    instance, lifecycle, _ = service()
    instance.catalog.output_schema = {
        "type": "object",
        "required": ["result"],
        "properties": {"result": {"type": "string"}},
    }
    lifecycle.result = {
        "content": [{"type": "text", "text": "Created"}],
        "structuredContent": {"result": "ok"},
        "isError": False,
    }

    result = await instance.call_tool("s1", "structured", "cad__run", {})

    assert result.content == ({"type": "text", "text": "Created"},)
    assert result.structured_content == {"result": "ok"}
    assert result.is_error is False


@pytest.mark.asyncio
async def test_foreign_tool_and_cancellation_are_denied() -> None:
    instance, lifecycle, _ = service()
    with pytest.raises(GatewayError, match="Unknown or disabled"):
        await instance.call_tool("s1", "foreign", "fea__run", {})

    lifecycle.gate = asyncio.Event()
    call = asyncio.create_task(instance.call_tool("s1", "owned", "cad__run", {}))
    await asyncio.sleep(0)
    assert instance.cancel("s2", "owned", "foreign") is False
    assert instance.cancel("s1", "owned", "operator") is True
    with pytest.raises(asyncio.CancelledError):
        await call


@pytest.mark.asyncio
async def test_configured_timeout_cancels_only_the_owned_request() -> None:
    instance, lifecycle, _ = service()
    lifecycle.gate = asyncio.Event()

    with pytest.raises(GatewayError) as caught:
        await instance.call_tool("s1", "slow", "cad__run", {}, timeout=0.01)

    assert caught.value.code.value == "timeout"
    assert ("s1", "slow") not in instance._requests
    assert instance.cancel("s2", "slow", "foreign") is False


def test_existing_session_cannot_be_rebound() -> None:
    instance, _, _ = service()
    with pytest.raises((GatewayError, RuntimeError)):
        instance.open_session(
            session_id="s1",
            principal_id="p1",
            workspace_id="w2",
            transport="stdio",
        )


def test_transport_session_preserves_distinct_workspace_binding_session() -> None:
    instance, _, _ = service()

    context = instance.open_session(
        session_id="transport-1",
        binding_session_id="s1",
        principal_id="p1",
        workspace_id="w1",
        transport="streamable_http",
    )

    assert context.session_id == "transport-1"
    assert context.binding_session_id == "s1"


def test_unsupported_protocol_fails_with_stable_error() -> None:
    instance, _, _ = service()
    instance.workspaces.bindings["unsupported"] = ("p3", "w1", "/workspace/one")
    instance.open_session(
        session_id="unsupported",
        principal_id="p3",
        workspace_id="w1",
        transport="stdio",
    )
    with pytest.raises(GatewayError) as captured:
        instance.initialize_session(
            "unsupported",
            protocol_version="1900-01-01",
            client_name="invalid",
            client_version="1",
            client_capabilities={},
        )
    assert captured.value.code.value == "unsupported_protocol"


def test_gateway_tool_provider_evidence_is_validated_at_the_projection_boundary() -> (
    None
):
    provider = ProviderEvidence(
        provider_kind="mcp",
        provider_id="cad",
        capability_id="inspect",
        resource_class="small",
        evidence={
            "server_id": "cad",
            "server_revision": "cad-v1",
            "tool_name": "inspect",
            "validation_evidence_id": "validation-cad-v1",
            "workspace_grant_digest": "a" * 64,
        },
    )
    tool = GatewayTool(
        name="cad__inspect",
        server_id="cad",
        tool_name="inspect",
        description="Inspect the exact CAD context.",
        input_schema={"type": "object"},
        provenance={
            "provider": provider.canonical(),
            "provider_evidence_digest": provider.provider_evidence_digest,
        },
    )
    assert tool.provenance["provider"]["provider_kind"] == "mcp"
    with pytest.raises(ValueError, match="digest changed"):
        GatewayTool(
            name="cad__changed",
            server_id="cad",
            tool_name="changed",
            description="Changed provider evidence.",
            input_schema={"type": "object"},
            provenance={
                "provider": provider.canonical(),
                "provider_evidence_digest": "f" * 64,
            },
        )
