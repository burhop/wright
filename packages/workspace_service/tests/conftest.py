from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import time
from typing import Any

import pytest
from core.rivet_mcp import CapabilityBinding
from data_vault import install_default_secret_provider
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service import (
    AuthorityClaims,
    RivetBoundInvocation,
    RivetGatewayBridge,
    RivetRunAuthorityService,
)


def pytest_configure() -> None:
    install_default_secret_provider()


class _LifecycleWorkspaces:
    def __init__(self, workspace_path: str, server_id: str) -> None:
        self.workspace_path = workspace_path
        self.server_id = server_id

    def resolve_binding(self, **_kwargs):
        return {
            "session_id": "gateway-session",
            "principal_id": "wright-rivet",
            "workspace_id": "workspace-1",
            "workspace_path": self.workspace_path,
        }

    def enabled_server_ids(self, _session):
        return {self.server_id}


class _LifecycleCatalog:
    def __init__(self, server_id: str) -> None:
        self.server_id = server_id
        now = int(time.time())
        self._server = McpServer(
            server_id=server_id,
            name="Lifecycle fixture",
            type="stdio",
            command=["fixture"],
            is_active=True,
            is_installed=True,
            status="active",
            created_at=now,
            updated_at=now,
        )

    def servers(self):
        return (self._server,)

    def tools(self, server_id):
        if server_id != self.server_id:
            return ()
        return (
            GatewayTool(
                name=f"{server_id}__inspect",
                server_id=server_id,
                tool_name="inspect",
                title="Inspect engineering application",
                description="Deterministic lifecycle fixture",
                input_schema={
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                    "required": ["value"],
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
                provenance={"server_revision": "fixture-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class _LifecycleAudit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event):
        self.events.append(dict(event))


@dataclass(slots=True)
class GovernedLifecycleHarness:
    gateway: GatewayService
    bridge: RivetGatewayBridge
    binding: CapabilityBinding
    token: str
    authority_id: str
    audience: str
    audit: _LifecycleAudit

    async def invoke(self, *, request_id: str, progress_callback=None):
        return await self.bridge.invoke_bound(
            self.token,
            self.audience,
            RivetBoundInvocation(
                run_id="run-lifecycle",
                generation=1,
                authority_id=self.authority_id,
                node_handle=self.binding.node_handle,
                binding_digest=self.binding.binding_digest,
                request_id=request_id,
                arguments={"value": 2},
            ),
            progress_callback=progress_callback,
        )


@pytest.fixture
def governed_lifecycle_harness(tmp_path):
    def build(lifecycle, *, server_id: str) -> GovernedLifecycleHarness:
        audit = _LifecycleAudit()
        gateway = GatewayService(
            workspaces=_LifecycleWorkspaces(str(tmp_path), server_id),
            catalog=_LifecycleCatalog(server_id),
            lifecycle=lifecycle,
            audit=audit,
            notifier=GatewayNotificationHub(),
            resources=GatewayResourceProvider(),
        )
        gateway.open_session(
            session_id="gateway-session",
            principal_id="wright-rivet",
            workspace_id="workspace-1",
            transport="legacy",
        )
        gateway.initialize_session(
            "gateway-session",
            protocol_version="2025-11-25",
            client_name="wright-rivet",
            client_version="2",
            client_capabilities={},
        )
        binding = CapabilityBinding.build(
            binding_id=f"binding-{server_id}",
            workspace_id="workspace-1",
            workflow_id="workflow-1",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="graph-1",
            node_id="node-1",
            node_handle="wright:abcdefghijklmnop",
            requirement_id=None,
            qualified_tool_name=f"{server_id}__inspect",
            server_id=server_id,
            server_revision="fixture-v1",
            capability_digest="b" * 64,
            validation_evidence_id="lifecycle-fixture-v1",
            workspace_grant_digest="c" * 64,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            risk={"required_approvals": []},
            units_policy={"value": "mm"},
            material_defaults={},
            argument_constraints={"type": "object"},
            created_at=datetime.now(UTC),
        )
        authorities = RivetRunAuthorityService()
        audience = "http://127.0.0.1:43123/internal/rivet-mcp/v1"
        now = datetime.now(UTC)
        issued = authorities.mint(
            AuthorityClaims(
                run_id="run-lifecycle",
                generation=1,
                workspace_id="workspace-1",
                session_id="gateway-session",
                workflow_id="workflow-1",
                workflow_revision=1,
                workflow_digest="a" * 64,
                graph_id="graph-1",
                review_digest="d" * 64,
                binding_set_digest="e" * 64,
                audience=audience,
                node_bindings={binding.node_handle: binding.binding_digest},
                issued_at=now,
                expires_at=now + timedelta(minutes=1),
            )
        )
        bridge = RivetGatewayBridge(
            gateway,
            authorities=authorities,
            resolve_binding=lambda digest: (
                binding if digest == binding.binding_digest else None
            ),
        )
        return GovernedLifecycleHarness(
            gateway,
            bridge,
            binding,
            issued.token,
            issued.authority_id,
            audience,
            audit,
        )

    return build
