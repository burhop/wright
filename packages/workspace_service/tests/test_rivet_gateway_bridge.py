import pytest

from workspace_service.rivet_gateway_bridge import (
    RivetGatewayBridge,
    RivetNodeInvocation,
)


class Gateway:
    async def call_tool(
        self,
        session_id,
        request_id,
        name,
        arguments,
        *,
        workspace_approvals=None,
        client_approval_hint=False,
    ):
        return {
            "session": session_id,
            "name": name,
            "approvals": workspace_approvals,
            "hint": client_approval_hint,
        }


@pytest.mark.asyncio
async def test_bridge_binds_run_scope_and_never_sets_client_approval():
    bridge = RivetGatewayBridge(Gateway(), run_scope={"run": ("workspace", "session")})
    result = await bridge.invoke(
        RivetNodeInvocation(
            "run", "node", "workspace", "session", "tool", {}, "request"
        ),
        workspace_approvals={"approve"},
    )
    assert result["hint"] is False
    with pytest.raises(PermissionError):
        await bridge.invoke(
            RivetNodeInvocation(
                "run", "node", "other", "session", "tool", {}, "request"
            )
        )
    with pytest.raises(PermissionError):
        await bridge.invoke(
            RivetNodeInvocation(
                "run", "node", "workspace", "other-session", "tool", {}, "request"
            )
        )
