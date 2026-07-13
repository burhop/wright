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
