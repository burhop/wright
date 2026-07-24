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
        annotations={"approval_gates": ["machine_control_approval"]},
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


def test_solid_edge_profile_lists_creation_and_hides_inspection() -> None:
    session = GatewaySessionContext("s1", "p1", "w1", "/w1", "stdio")
    provenance = {"source_url": "https://github.com/burhop/SolidEdgeMCP"}
    create = GatewayTool(
        "cad__create",
        "solid-edge",
        "cad.create_part_from_recipe",
        "Create part",
        {"type": "object"},
        provenance=provenance,
    )
    inspect = GatewayTool(
        "cad__faces",
        "solid-edge",
        "cad.list_faces",
        "List faces",
        {"type": "object"},
        provenance=provenance,
    )

    policy = GatewayPolicy()
    assert policy.can_list(session, create).allowed
    hidden = policy.can_list(session, inspect)
    assert not hidden.allowed
    assert hidden.reason_code == "solid_edge_creation_profile_hidden"
    assert not policy.can_call(session, inspect, {}).allowed
