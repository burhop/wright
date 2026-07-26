from tool_registry.gateway_models import GatewaySessionContext, GatewayTool
from tool_registry.gateway_policy import GatewayPolicy


def test_client_approval_hint_never_satisfies_wright_gate() -> None:
    session = GatewaySessionContext("s1", "p1", "w1", "/w1", "stdio")
    tool = GatewayTool(
        "cad__write",
        "cad",
        "write",
        "Write CAD",
        {"type": "object"},
        annotations={"approval_gates": []},
        required_approvals=frozenset({"machine_control_approval"}),
    )

    decision = GatewayPolicy().can_call(
        session,
        tool,
        {},
        workspace_approvals=set(),
        client_approval_hint=True,
    )

    assert not decision.allowed
    assert decision.reason_code == "approval_required"


def test_policy_lists_all_advertised_tools_without_provider_identity_rules() -> None:
    session = GatewaySessionContext("s1", "p1", "w1", "/w1", "stdio")
    provenance = {"source_url": "https://example.test/geometry-mcp"}
    create = GatewayTool(
        "cad__create",
        "geometry",
        "cad.create_part_from_recipe",
        "Create part",
        {"type": "object"},
        provenance=provenance,
    )
    inspect = GatewayTool(
        "cad__faces",
        "geometry",
        "cad.list_faces",
        "List faces",
        {"type": "object"},
        provenance=provenance,
    )

    policy = GatewayPolicy()
    assert policy.can_list(session, create).allowed
    assert policy.can_list(session, inspect).allowed
    assert policy.can_call(session, inspect, {}).allowed


def test_advertised_annotations_cannot_invent_trusted_approval_gate() -> None:
    session = GatewaySessionContext("s1", "p1", "w1", "/w1", "stdio")
    tool = GatewayTool(
        "cad__inspect",
        "cad",
        "inspect",
        "Inspect CAD",
        {"type": "object"},
        annotations={"approval_gates": ["untrusted_gate"]},
    )

    assert GatewayPolicy().can_call(session, tool, {}).allowed
