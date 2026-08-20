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
    assert len(snapshot.policy_snapshot_digest) == 64
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


def test_healthy_validation_evidence_refresh_does_not_stale_a_binding():
    gateway = Gateway()
    service = RivetCapabilityService(gateway)
    snapshot = service.discover(session_id="session-1", workspace_id="workspace-1")
    binding = service.bind(
        snapshot=snapshot,
        requirement=RivetMcpNodeRequirement(
            "Main", "node-1", "mcpToolCall", None
        ),
        qualified_tool_name="alpha__inspect",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        units_policy={},
        material_defaults={},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    gateway.tools = (
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
                "validation_evidence_id": "alpha-evidence-refreshed",
            },
        ),
    )

    refreshed = service.discover(
        session_id="session-1", workspace_id="workspace-1"
    )

    assert refreshed.tools[0].validation_evidence_id != binding.validation_evidence_id
    assert (
        refreshed.tools[0].provider.provider_evidence_digest
        != binding.provider.provider_evidence_digest
    )
    assert service.stale_reasons(binding, refreshed) == ()


def test_binding_identity_changes_with_its_discovery_snapshot():
    gateway = Gateway()
    service = RivetCapabilityService(gateway)
    first_snapshot = service.discover(
        session_id="session-1", workspace_id="workspace-1"
    )
    requirement = RivetMcpNodeRequirement("Main", "node-1", "mcpToolCall", None)
    first = service.bind(
        snapshot=first_snapshot,
        requirement=requirement,
        qualified_tool_name="alpha__inspect",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        units_policy={},
        material_defaults={},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    gateway.tools = (
        *gateway.tools,
        GatewayTool(
            "gamma__status",
            "gamma",
            "status",
            "Unrelated current capability",
            {"type": "object"},
            provenance={
                "server_revision": "gamma-v1",
                "validation_evidence_id": "gamma-evidence",
            },
        ),
    )
    second_snapshot = service.discover(
        session_id="session-1", workspace_id="workspace-1"
    )
    second = service.bind(
        snapshot=second_snapshot,
        requirement=requirement,
        qualified_tool_name="alpha__inspect",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        units_policy={},
        material_defaults={},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )

    assert first_snapshot.snapshot_digest != second_snapshot.snapshot_digest
    assert first.node_handle != second.node_handle
    assert first.binding_digest != second.binding_digest
    assert service.stale_reasons(first, second_snapshot) == ()


def test_unqualified_collision_remains_distinct_and_oversized_schema_is_blocked():
    gateway = Gateway()
    gateway.tools = (
        *gateway.tools,
        GatewayTool(
            "gamma__huge",
            "gamma",
            "huge",
            "Too large",
            {"type": "object", "description": "x" * 70_000},
            provenance={
                "server_revision": "gamma-v1",
                "validation_evidence_id": "gamma-evidence",
            },
        ),
    )
    service = RivetCapabilityService(gateway)
    snapshot = service.discover(session_id="session-1", workspace_id="workspace-1")
    inspect = [item for item in snapshot.tools if item.tool_name == "inspect"]
    assert [item.qualified_tool_name for item in inspect] == [
        "alpha__inspect",
        "beta__inspect",
    ]
    huge = next(item for item in snapshot.tools if item.tool_name == "huge")
    assert not huge.binding_eligible
    assert huge.blocking_reasons == ("input_schema_too_large",)


def test_session_resolver_confines_discovery_to_the_workspace_session():
    gateway = Gateway()
    service = RivetCapabilityService(
        gateway,
        session_resolver=lambda session_id, workspace_id: (
            "session-1"
            if (session_id, workspace_id) == ("public", "workspace-1")
            else "denied"
        ),
    )
    snapshot = service.discover(session_id="public", workspace_id="workspace-1")
    assert snapshot.session_id == "session-1"


def test_already_resolved_gateway_session_is_not_resolved_twice():
    gateway = Gateway()
    resolved = []
    service = RivetCapabilityService(
        gateway,
        session_resolver=lambda session_id, workspace_id: (
            resolved.append((session_id, workspace_id)) or "denied"
        ),
    )

    snapshot = service.discover_gateway_session(
        session_id="session-1",
        workspace_id="workspace-1",
    )

    assert snapshot.session_id == "session-1"
    assert resolved == []
