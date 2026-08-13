from __future__ import annotations

from datetime import UTC, datetime

from tool_registry.gateway_models import GatewayTool
from workspace_service.rivet_capabilities import RivetCapabilityService
from workspace_service.rivet_validation import RivetMcpNodeRequirement


class Gateway:
    def __init__(self) -> None:
        self.called = False
        self.tools = (
            GatewayTool(
                "alpha__inspect",
                "alpha",
                "inspect",
                "Inspect with Alpha",
                {"type": "object", "properties": {"value": {"type": "number"}}},
                output_schema={"type": "object"},
                annotations={"readOnlyHint": True},
                provenance={
                    "server_revision": "alpha-v1",
                    "validation_evidence_id": "alpha-evidence",
                },
            ),
            GatewayTool(
                "beta__inspect",
                "beta",
                "inspect",
                "Inspect with Beta",
                {"type": "object", "properties": {"path": {"type": "string"}}},
                output_schema={"type": "object"},
                required_approvals=frozenset({"engineering.write"}),
                provenance={
                    "server_revision": "beta-v1",
                    "validation_evidence_id": "beta-evidence",
                },
            ),
        )

    def list_tools(self, session_id: str):
        assert session_id == "session-1"
        return self.tools

    async def call_tool(self, *args, **kwargs):
        self.called = True
        raise AssertionError("discovery must not invoke a child")


def test_discovery_is_namespaced_bounded_and_has_no_child_effect():
    gateway = Gateway()
    service = RivetCapabilityService(gateway)
    snapshot = service.discover(session_id="session-1", workspace_id="workspace-1")
    assert [item.qualified_tool_name for item in snapshot.tools] == [
        "alpha__inspect",
        "beta__inspect",
    ]
    assert snapshot.tools[0].schema_digest != snapshot.tools[1].schema_digest
    assert snapshot.tools[1].required_approvals == ("engineering.write",)
    assert len(snapshot.snapshot_digest) == 64
    assert not gateway.called


def test_binding_is_exact_stable_and_schema_change_is_stale():
    gateway = Gateway()
    service = RivetCapabilityService(gateway)
    snapshot = service.discover(session_id="session-1", workspace_id="workspace-1")
    requirement = RivetMcpNodeRequirement("Main", "node-1", "mcpToolCall", None)
    first = service.bind(
        snapshot=snapshot,
        requirement=requirement,
        qualified_tool_name="alpha__inspect",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        units_policy={"length": "mm"},
        material_defaults={},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    second = service.bind(
        snapshot=snapshot,
        requirement=requirement,
        qualified_tool_name="alpha__inspect",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        units_policy={"length": "mm"},
        material_defaults={},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    assert first.binding_digest == second.binding_digest
    assert first.node_handle == second.node_handle
    assert service.stale_reasons(first, snapshot) == ()

    gateway.tools = (
        GatewayTool(
            "alpha__inspect",
            "alpha",
            "inspect",
            "Changed",
            {"type": "object", "properties": {"changed": {"type": "boolean"}}},
            output_schema={"type": "object"},
            provenance={
                "server_revision": "alpha-v1",
                "validation_evidence_id": "alpha-evidence",
            },
        ),
    )
    changed = service.discover(session_id="session-1", workspace_id="workspace-1")
    assert service.stale_reasons(first, changed) == ("tool_schema_changed",)
