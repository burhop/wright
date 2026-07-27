import pytest

from tool_registry.gateway_models import (
    GatewayError,
    GatewayRequest,
    GatewaySessionContext,
    RequestState,
    SessionState,
)


def test_gateway_session_requires_explicit_immutable_binding() -> None:
    with pytest.raises(GatewayError, match="workspace_id"):
        GatewaySessionContext(
            session_id="s1",
            principal_id="p1",
            workspace_id="",
            workspace_path="/workspace/a",
            transport="stdio",
        )

    session = GatewaySessionContext(
        session_id="s1",
        principal_id="p1",
        workspace_id="w1",
        workspace_path="/workspace/a",
        transport="stdio",
    )
    initialized = session.initialized(
        protocol_version="2025-11-25",
        client_name="codex",
        client_version="0.144.1",
        client_capabilities={"roots": {}},
    )
    active = initialized.activate()

    assert session.state is SessionState.CREATED
    assert active.state is SessionState.ACTIVE
    assert active.workspace_id == "w1"
    with pytest.raises(TypeError):
        active.client_capabilities["foreign"] = {}  # type: ignore[index]
    with pytest.raises(GatewayError, match="exactly once"):
        initialized.initialized(
            protocol_version="2025-11-25",
            client_name="other",
            client_version="1",
            client_capabilities={},
        )


def test_gateway_request_terminal_states_are_irreversible() -> None:
    request = GatewayRequest(
        session_id="s1",
        request_id="r1",
        method="tools/call",
        correlation_id="c1",
        deadline=10.0,
        maximum_deadline=20.0,
    )
    request.transition(RequestState.RUNNING)
    request.transition(RequestState.SUCCEEDED)

    with pytest.raises(GatewayError, match="already terminal"):
        request.cancel("too late")


def test_gateway_request_can_cancel_before_dispatch() -> None:
    request = GatewayRequest("s1", "r1", "tools/call", "c1", 10.0, 20.0)
    request.cancel("operator")
    assert request.state is RequestState.CANCELLED
    assert request.cancellation_reason == "operator"
